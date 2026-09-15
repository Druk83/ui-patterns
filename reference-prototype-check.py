#!/usr/bin/env python3
"""Проверка запускаемых reference-прототипов и viewport из screen pool."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import Any, cast
from urllib.parse import quote


ROOT = Path(__file__).resolve().parent
TEMPLATES_ROOT = ROOT / "шаблоны-экранов"
RUNTIME_ROOT = TEMPLATES_ROOT / "эталонный-шаблон"
MANIFEST_PATH = TEMPLATES_ROOT / "manifest.json"
REFERENCE_MANIFEST_PATH = RUNTIME_ROOT / "манифест-эталонного-шаблона.json"


class QuietHandler(SimpleHTTPRequestHandler):
    """HTTP handler без вывода запросов в консоль."""

    def log_message(self, format: str, *args: object) -> None:
        return


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("Для проверки требуется PyYAML: python -m pip install pyyaml") from exc
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"Корень YAML должен быть объектом: {path}")
    return cast(dict[str, Any], value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Проверяет reference-only UI-прототипы и делает screenshots на подтверждённых viewport."
    )
    parser.add_argument(
        "--screen-pool",
        type=Path,
        help="Путь к подтверждённому machine-readable screen pool.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Каталог screenshots. Если не указан, результаты удаляются после проверки.",
    )
    parser.add_argument(
        "--all-templates",
        action="store_true",
        help="Проверить все зарегистрированные шаблоны на явно переданном viewport.",
    )
    parser.add_argument(
        "--viewport",
        action="append",
        default=[],
        metavar="WIDTHxHEIGHT",
        help="Явный runtime viewport для --all-templates; можно указать несколько раз.",
    )
    return parser.parse_args()


def find_browser() -> Path | None:
    configured = os.environ.get("CHROME_PATH")
    candidates = [
        Path(configured) if configured else None,
        Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
        Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
        Path("C:/Program Files/Microsoft/Edge/Application/msedge.exe"),
        Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
    ]
    for candidate in candidates:
        if candidate and candidate.is_file():
            return candidate
    for command in ("google-chrome", "chromium", "chromium-browser", "msedge"):
        resolved = shutil.which(command)
        if resolved:
            return Path(resolved)
    return None


def parse_viewport(value: Any, location: str) -> tuple[int, int] | None:
    if not isinstance(value, dict):
        raise RuntimeError(f"{location}: viewport должен быть объектом")
    width = value.get("width")
    height = value.get("height")
    unit = value.get("unit")
    if not isinstance(width, int) or not isinstance(height, int) or width <= 0 or height <= 0:
        raise RuntimeError(f"{location}: width и height должны быть положительными целыми числами")
    if unit != "css-px":
        raise RuntimeError(f"{location}: unit должен быть css-px")
    if value.get("status") != "confirmed":
        raise RuntimeError(f"{location}: viewport должен быть confirmed")
    for field in ("source", "rationale", "responsive_profile", "breakpoint_conditions"):
        if not isinstance(value.get(field), str) or not value[field].strip():
            raise RuntimeError(f"{location}: отсутствует {field}")
    return width, height


def load_templates() -> dict[str, dict[str, Any]]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {
        str(item["template_id"]): cast(dict[str, Any], item)
        for item in manifest["templates"]
        if isinstance(item, dict) and isinstance(item.get("template_id"), str)
    }


def static_checks(templates: dict[str, dict[str, Any]]) -> list[tuple[str, Path]]:
    errors: list[str] = []
    entrypoints: list[tuple[str, Path]] = []
    required_runtime_files = (
        RUNTIME_ROOT / "index.html",
        RUNTIME_ROOT / "styles.css",
        RUNTIME_ROOT / "script.js",
        REFERENCE_MANIFEST_PATH,
        RUNTIME_ROOT / "README.md",
    )
    for path in required_runtime_files:
        if not path.is_file():
            errors.append(f"runtime file not found: {path}")

    if (RUNTIME_ROOT / "script.js").is_file():
        result = subprocess.run(
            ["node", "--check", str(RUNTIME_ROOT / "script.js")],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            text=True,
            check=False,
        )
        if result.returncode != 0:
            errors.append(f"script syntax check failed: {result.stderr.strip()}")
        script = (RUNTIME_ROOT / "script.js").read_text(encoding="utf-8")
        for fragment in ("addEventListener", "Escape", "action-complete", "recovery-required"):
            if fragment not in script:
                errors.append(f"shared runtime is missing {fragment}")

    if (RUNTIME_ROOT / "styles.css").is_file():
        styles = (RUNTIME_ROOT / "styles.css").read_text(encoding="utf-8")
        for fragment in ("@media", ":focus-visible", "overflow"):
            if fragment not in styles:
                errors.append(f"shared styles are missing {fragment} hook")

    try:
        reference_manifest = json.loads(REFERENCE_MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid reference manifest: {exc}")
        reference_manifest = {}
    if isinstance(reference_manifest, dict):
        if reference_manifest.get("status") != "reference-only":
            errors.append("reference manifest must be reference-only")
        if reference_manifest.get("data_policy") != "fixture-only":
            errors.append("reference manifest must use fixture-only data")
        if not isinstance(reference_manifest.get("viewport_profiles"), list) or not reference_manifest["viewport_profiles"]:
            errors.append("reference manifest must declare viewport profiles")
        if not isinstance(reference_manifest.get("visual_baseline"), str):
            errors.append("reference manifest must link visual baseline")
        elif not (RUNTIME_ROOT / reference_manifest["visual_baseline"]).is_file():
            errors.append("reference manifest visual baseline is missing")

    for template_id, template in templates.items():
        template_path = template.get("template_path")
        if not isinstance(template_path, str):
            errors.append(f"{template_id}: template_path is missing")
            continue
        entrypoint = TEMPLATES_ROOT / template_path / "index.html"
        if not entrypoint.is_file():
            errors.append(f"{template_id}: entrypoint is missing: {entrypoint}")
            continue
        entrypoints.append((template_id, entrypoint))
        html = entrypoint.read_text(encoding="utf-8")
        for fragment in (
            "<meta name=\"viewport\"",
            "data-template-id=\"",
            "id=\"primary-action\"",
            "id=\"status\"",
            "id=\"error\"",
            "role=\"status\"",
            "role=\"alert\"",
            "stylesheet",
            "script src=",
        ):
            if fragment not in html:
                errors.append(f"{template_id}: entrypoint is missing {fragment}")
        if "https://" in html or "http://" in html or "fetch(" in html:
            errors.append(f"{template_id}: entrypoint contains external runtime dependency")

    if errors:
        raise RuntimeError("\n".join(errors))
    return entrypoints


def select_targets(
    pool_path: Path | None,
    templates: dict[str, dict[str, Any]],
) -> list[tuple[str, int, int, str]]:
    if pool_path is None:
        raise RuntimeError("Для screenshot-проверки требуется --screen-pool с подтверждёнными viewport")
    pool = load_yaml(pool_path.resolve())
    if pool.get("kind") != "screen-pool" or pool.get("status") != "confirmed":
        raise RuntimeError("screen pool должен иметь kind screen-pool и status confirmed")
    screens = pool.get("screens")
    if not isinstance(screens, list) or not screens:
        raise RuntimeError("screen pool не содержит screens")
    targets: list[tuple[str, int, int, str]] = []
    for index, screen in enumerate(screens):
        location = f"screens[{index}]"
        if not isinstance(screen, dict) or screen.get("status") != "confirmed":
            raise RuntimeError(f"{location}: экран должен быть confirmed")
        candidates = screen.get("template_candidates")
        if not isinstance(candidates, list):
            raise RuntimeError(f"{location}: отсутствуют template_candidates")
        selected = [
            item.get("template_id")
            for item in candidates
            if isinstance(item, dict) and item.get("status") == "confirmed"
        ]
        if len(selected) != 1 or selected[0] not in templates:
            raise RuntimeError(f"{location}: должен быть ровно один подтверждённый известный template_id")
        viewports = screen.get("viewport_candidates")
        if not isinstance(viewports, list) or not viewports:
            raise RuntimeError(f"{location}: отсутствуют viewport_candidates")
        confirmed_viewports = 0
        for viewport_index, viewport in enumerate(viewports):
            if not isinstance(viewport, dict) or viewport.get("status") != "confirmed":
                continue
            parsed = parse_viewport(viewport, f"{location}.viewport_candidates[{viewport_index}]")
            if parsed is not None:
                width, height = parsed
                targets.append((str(selected[0]), width, height, str(viewport["viewport_id"])))
                confirmed_viewports += 1
        if confirmed_viewports == 0:
            raise RuntimeError(f"{location}: отсутствует подтверждённый viewport")
    return list(dict.fromkeys(targets))


def select_all_targets(templates: dict[str, dict[str, Any]], values: list[str]) -> list[tuple[str, int, int, str]]:
    if not values:
        raise RuntimeError("Для --all-templates требуется хотя бы один --viewport WIDTHxHEIGHT")
    targets: list[tuple[str, int, int, str]] = []
    for index, value in enumerate(values):
        parts = value.lower().split("x")
        if len(parts) != 2 or not all(part.isdigit() for part in parts):
            raise RuntimeError(f"Некорректный runtime viewport: {value}; ожидается WIDTHxHEIGHT")
        width, height = (int(part) for part in parts)
        if width <= 0 or height <= 0:
            raise RuntimeError(f"Runtime viewport должен быть положительным: {value}")
        viewport_id = f"explicit-{index + 1}-{width}x{height}"
        targets.extend((template_id, width, height, viewport_id) for template_id in templates)
    return targets


def capture(
    browser: Path,
    server: ThreadingHTTPServer,
    output_dir: Path,
    template_id: str,
    entrypoint: Path,
    width: int,
    height: int,
    viewport_id: str,
    state: str,
) -> Path:
    relative_entrypoint = entrypoint.relative_to(ROOT).as_posix()
    url = f"http://127.0.0.1:{server.server_port}/{quote(relative_entrypoint)}?state={quote(state)}"
    output_path = output_dir / f"{template_id}__{viewport_id}__{state}.png"
    user_data_dir = tempfile.mkdtemp(prefix="ui-reference-chrome-")
    try:
        result = subprocess.run(
            [
                str(browser),
                "--headless=new",
                "--disable-gpu",
                "--in-process-gpu",
                "--disable-extensions",
                "--no-first-run",
                "--no-default-browser-check",
                f"--user-data-dir={user_data_dir}",
                f"--window-size={width},{height}",
                "--virtual-time-budget=1000",
                f"--screenshot={output_path}",
                "--dump-dom",
                url,
            ],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            text=True,
            timeout=45,
            check=False,
        )
    finally:
        shutil.rmtree(user_data_dir, ignore_errors=True)
    if result.returncode != 0:
        raise RuntimeError(f"{template_id}/{viewport_id}/{state}: browser failed: {result.stderr.strip()}")
    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise RuntimeError(f"{template_id}/{viewport_id}/{state}: screenshot was not created")
    expected_status = {
        "initial": "Начальное состояние",
        "action-complete": "Основное действие выполнено с fixture-данными",
        "recovery-required": "Требуется действие восстановления",
    }[state]
    if expected_status not in result.stdout:
        raise RuntimeError(f"{template_id}/{viewport_id}/{state}: state transition was not rendered")
    return output_path


def main() -> int:
    args = parse_args()
    try:
        templates = load_templates()
        entrypoints = static_checks(templates)
        browser = find_browser()
        if browser is None:
            raise RuntimeError("Headless Chrome/Edge не найден; задайте CHROME_PATH")
        entrypoint_map = {template_id: entrypoint for template_id, entrypoint in entrypoints}
        if args.all_templates and args.screen_pool:
            raise RuntimeError("Нельзя одновременно использовать --all-templates и --screen-pool")
        targets = (
            select_all_targets(templates, args.viewport)
            if args.all_templates
            else select_targets(args.screen_pool, templates)
        )
        states = ["initial", "action-complete", "recovery-required"]
        temporary_output: tempfile.TemporaryDirectory[str] | None = None
        if args.output_dir:
            output_dir = args.output_dir.resolve()
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            temporary_output = tempfile.TemporaryDirectory(prefix="ui-reference-screenshots-")
            output_dir = Path(temporary_output.name)

        handler = partial(QuietHandler, directory=str(ROOT))
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        screenshots: list[Path] = []
        try:
            for template_id, width, height, viewport_id in targets:
                for state in states:
                    screenshots.append(
                        capture(
                            browser,
                            server,
                            output_dir,
                            template_id,
                            entrypoint_map[template_id],
                            width,
                            height,
                            viewport_id,
                            state,
                        )
                    )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
            if temporary_output is not None:
                temporary_output.cleanup()
        print(f"REFERENCE_PROTOTYPE_CHECK: PASS ({len(screenshots)} screenshots)")
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"REFERENCE_PROTOTYPE_CHECK: FAIL ({exc})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
