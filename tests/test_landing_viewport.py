from __future__ import annotations

import base64
import json
import os
import socket
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
LANDING = ROOT / "шаблоны-экранов" / "лендинг" / "index.html"


def _as_object_dict(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    return {str(key): item for key, item in value.items()}


class DevToolsConnection:
    def __init__(self, endpoint: str) -> None:
        parsed = urlparse(endpoint)
        self.connection = socket.create_connection((parsed.hostname or "127.0.0.1", parsed.port or 80), timeout=10)
        self.connection.settimeout(10)
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            f"GET {parsed.path} HTTP/1.1\r\n"
            f"Host: {parsed.hostname}:{parsed.port}\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        )
        self.connection.sendall(request.encode("ascii"))
        response = bytearray()
        while b"\r\n\r\n" not in response:
            response.extend(self.connection.recv(4096))
        if not response.startswith(b"HTTP/1.1 101"):
            raise RuntimeError(f"DevTools WebSocket rejected: {response[:200]!r}")
        self.next_id = 0

    def close(self) -> None:
        self.connection.close()

    def _read_exact(self, length: int) -> bytes:
        chunks = bytearray()
        while len(chunks) < length:
            part = self.connection.recv(length - len(chunks))
            if not part:
                raise RuntimeError("DevTools WebSocket closed")
            chunks.extend(part)
        return bytes(chunks)

    def _send(self, value: dict[str, object]) -> None:
        payload = json.dumps(value, separators=(",", ":")).encode("utf-8")
        header = bytearray([0x81])
        if len(payload) < 126:
            header.append(0x80 | len(payload))
        elif len(payload) < 65536:
            header.append(0x80 | 126)
            header.extend(len(payload).to_bytes(2, "big"))
        else:
            header.append(0x80 | 127)
            header.extend(len(payload).to_bytes(8, "big"))
        mask = os.urandom(4)
        masked = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
        self.connection.sendall(bytes(header) + mask + masked)

    def _receive(self) -> dict[str, object]:
        first, second = self._read_exact(2)
        length = second & 0x7F
        if length == 126:
            length = int.from_bytes(self._read_exact(2), "big")
        elif length == 127:
            length = int.from_bytes(self._read_exact(8), "big")
        mask = self._read_exact(4) if second & 0x80 else b""
        payload = self._read_exact(length)
        if mask:
            payload = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
        if first & 0x0F == 0x8:
            raise RuntimeError("DevTools WebSocket closed")
        return json.loads(payload)

    def call(self, method: str, params: dict[str, object] | None = None) -> dict[str, object]:
        self.next_id += 1
        identifier = self.next_id
        self._send({"id": identifier, "method": method, "params": params or {}})
        while True:
            response = self._receive()
            if response.get("id") != identifier:
                continue
            if "error" in response:
                raise RuntimeError(f"{method}: {response['error']}")
            result = response.get("result")
            return result if isinstance(result, dict) else {}


class LandingViewportTests(unittest.TestCase):
    def test_exact_viewports_and_form_variant(self) -> None:
        browser = Path(os.environ.get("CHROME_PATH", "C:/Program Files/Google/Chrome/Application/chrome.exe"))
        if not browser.is_file():
            self.skipTest("Headless Chrome не найден; задайте CHROME_PATH")
        with tempfile.TemporaryDirectory(prefix=".lp01-chrome-", dir=ROOT) as temporary:
            profile = Path(temporary) / "profile"
            process = subprocess.Popen(
                [
                    str(browser), "--headless=new", "--disable-gpu", "--disable-extensions",
                    "--disable-breakpad", "--disable-crash-reporter", "--disable-background-networking",
                    "--disable-dev-shm-usage", "--no-sandbox",
                    "--no-first-run", "--no-default-browser-check", "--remote-debugging-port=0",
                    "--remote-allow-origins=*", f"--user-data-dir={profile}", "about:blank",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            try:
                port_file = profile / "DevToolsActivePort"
                for _ in range(100):
                    if port_file.is_file():
                        break
                    if process.poll() is not None:
                        raise RuntimeError("Chrome завершился до запуска DevTools")
                    time.sleep(0.1)
                else:
                    raise RuntimeError("Chrome не открыл DevTools")
                port = int(port_file.read_text(encoding="ascii").splitlines()[0])
                with urlopen(f"http://127.0.0.1:{port}/json/list", timeout=10) as response:
                    targets = json.load(response)
                endpoint = next(item["webSocketDebuggerUrl"] for item in targets if item.get("type") == "page")
                connection = DevToolsConnection(endpoint)
                try:
                    connection.call("Page.enable")
                    connection.call("Runtime.enable")
                    for width, height, variant in ((1280, 800, "without-form"), (375, 812, "with-form")):
                        with self.subTest(width=width, variant=variant):
                            connection.call("Emulation.setDeviceMetricsOverride", {
                                "width": width, "height": height, "deviceScaleFactor": 1, "mobile": False,
                            })
                            suffix = "?variant=form" if variant == "with-form" else ""
                            connection.call("Page.navigate", {"url": LANDING.as_uri() + suffix})
                            metrics: dict[str, object] = {}
                            for _ in range(100):
                                evaluated = connection.call("Runtime.evaluate", {
                                    "expression": "({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,status:document.querySelector('#status')?.textContent,formHidden:document.querySelector('#form-variant')?.hidden,search:location.search,ready:document.readyState})",
                                    "returnByValue": True,
                                })
                                result = _as_object_dict(evaluated.get("result"))
                                metrics = _as_object_dict(result.get("value"))
                                expected_search = "?variant=form" if variant == "with-form" else ""
                                if (metrics.get("status") == "Начальное состояние"
                                        and metrics.get("search") == expected_search
                                        and metrics.get("ready") == "complete"):
                                    break
                                time.sleep(0.1)
                            self.assertEqual(metrics.get("width"), width)
                            scroll_width = metrics.get("scrollWidth", width + 1)
                            if not isinstance(scroll_width, int):
                                self.fail("scrollWidth must be an integer")
                            self.assertLessEqual(scroll_width, width)
                            self.assertEqual(metrics.get("formHidden"), variant != "with-form")
                            screenshot = connection.call("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False})
                            png = base64.b64decode(str(screenshot["data"]))
                            self.assertGreater(len(png), 1000)
                            self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
                            self.assertEqual(int.from_bytes(png[16:20], "big"), width)
                            self.assertEqual(int.from_bytes(png[20:24], "big"), height)
                            output = os.environ.get("LP01_SCREENSHOT_DIR")
                            if output:
                                target = Path(output)
                                target.mkdir(parents=True, exist_ok=True)
                                (target / f"landing-{width}-{variant}.png").write_bytes(png)
                            if variant == "with-form":
                                connection.call("Runtime.evaluate", {
                                    "expression": "document.querySelector('#primary-action').click()",
                                })
                                result = connection.call("Runtime.evaluate", {
                                    "expression": "document.querySelector('#status').textContent",
                                    "returnByValue": True,
                                })
                                self.assertEqual(_as_object_dict(result.get("result")).get("value"), "Требуется действие восстановления")
                                connection.call("Runtime.evaluate", {
                                    "expression": "document.querySelector('#fixture-field').value='fixture';document.querySelector('#primary-action').click()",
                                })
                                result = connection.call("Runtime.evaluate", {
                                    "expression": "document.querySelector('#status').textContent",
                                    "returnByValue": True,
                                })
                                self.assertEqual(_as_object_dict(result.get("result")).get("value"), "Основное действие выполнено с fixture-данными")
                finally:
                    connection.close()
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
                time.sleep(0.5)
