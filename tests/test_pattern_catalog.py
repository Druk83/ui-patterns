from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "pattern-catalog-check.py"


def load_checker() -> Any:
    spec = importlib.util.spec_from_file_location("pattern_catalog_check", CHECKER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Не удалось загрузить validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_reference_checker() -> Any:
    path = ROOT / "reference-prototype-check.py"
    spec = importlib.util.spec_from_file_location("reference_prototype_check", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Не удалось загрузить prototype checker")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_contracts(checker: Any) -> tuple[set[str], dict[str, dict[str, Any]]]:
    catalog = checker.load_yaml(ROOT / "pattern-catalog.yml")
    applications = checker.load_yaml(ROOT / "ui-pattern-application-templates.yml")
    active_pattern_ids = {
        str(item.get("pattern_id") or item.get("id"))
        for item in catalog.get("entries", [])
        if isinstance(item, dict)
        and item.get("status") == "active"
        and (item.get("pattern_id") or item.get("id"))
    }
    templates = {
        str(item["template_id"]): item
        for item in applications.get("templates", [])
        if isinstance(item, dict) and item.get("template_id")
    }
    return active_pattern_ids, templates


class PatternCatalogValidatorTests(unittest.TestCase):
    def test_public_catalog_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CHECKER_PATH)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PUBLIC_CATALOG_CHECK: PASS", result.stdout)

    def test_rejects_screen_template_with_unknown_pattern(self) -> None:
        checker = load_checker()
        active_pattern_ids, application_templates = load_contracts(checker)
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            shutil.copytree(
                ROOT / "шаблоны-экранов",
                temporary_root / "шаблоны-экранов",
            )
            manifest_path = temporary_root / "шаблоны-экранов" / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["templates"][0]["pattern_id"] = "missing-pattern"
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            errors: list[str] = []
            checker.check_screen_templates(
                temporary_root,
                active_pattern_ids,
                application_templates,
                errors,
            )
            self.assertTrue(any("active pattern not found" in error for error in errors))

    def test_rejects_product_data_reference_runtime(self) -> None:
        checker = load_checker()
        active_pattern_ids, application_templates = load_contracts(checker)
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            shutil.copytree(
                ROOT / "шаблоны-экранов",
                temporary_root / "шаблоны-экранов",
            )
            fixture = ROOT / "tests" / "fixtures" / "invalid-reference-manifest.json"
            target = (
                temporary_root
                / "шаблоны-экранов"
                / "эталонный-шаблон"
                / "манифест-эталонного-шаблона.json"
            )
            shutil.copyfile(fixture, target)
            errors: list[str] = []
            checker.check_screen_templates(
                temporary_root,
                active_pattern_ids,
                application_templates,
                errors,
            )
            self.assertIn("screen UI reference manifest must use fixture-only data", errors)

    def test_accepts_confirmed_screen_pool(self) -> None:
        checker = load_checker()
        active_pattern_ids, _ = load_contracts(checker)
        errors: list[str] = []
        checker.check_screen_pool(
            ROOT,
            ROOT / "tests" / "fixtures" / "valid-screen-pool.yml",
            active_pattern_ids,
            errors,
            require_confirmed=True,
        )
        self.assertEqual(errors, [])

    def test_rejects_invalid_screen_pool(self) -> None:
        checker = load_checker()
        active_pattern_ids, _ = load_contracts(checker)
        errors: list[str] = []
        checker.check_screen_pool(
            ROOT,
            ROOT / "tests" / "fixtures" / "invalid-screen-pool.yml",
            active_pattern_ids,
            errors,
            require_confirmed=True,
        )
        self.assertTrue(any("active pattern not found" in error for error in errors))
        self.assertTrue(any("missing source" in error for error in errors))

    def test_reference_prototype_static_contract_passes(self) -> None:
        checker = load_reference_checker()
        templates = checker.load_templates()
        entrypoints = checker.static_checks(templates)
        self.assertEqual(len(entrypoints), 12)


if __name__ == "__main__":
    unittest.main()
