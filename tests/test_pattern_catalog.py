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
    pattern_records = [
        item for item in catalog.get("entries", []) if isinstance(item, dict)
    ]
    extended = catalog.get("extended_templates", {})
    if isinstance(extended, dict) and isinstance(extended.get("entries"), list):
        pattern_records.extend(item for item in extended["entries"] if isinstance(item, dict))
    active_pattern_ids = {
        str(item.get("pattern_id") or item.get("id"))
        for item in pattern_records
        if item.get("status") == "active"
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
                "0.3.1",
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
                "0.3.1",
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
            "0.3.1",
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
            "0.3.1",
            errors,
            require_confirmed=True,
        )
        self.assertTrue(any("active pattern not found" in error for error in errors))
        self.assertTrue(any("missing source" in error for error in errors))
        self.assertTrue(any("screen_shell_candidates is required" in error for error in errors))

    def test_reference_prototype_static_contract_passes(self) -> None:
        checker = load_reference_checker()
        templates = checker.load_templates()
        entrypoints = checker.static_checks(templates)
        self.assertEqual(len(entrypoints), 13)

    def test_card_feed_has_distinct_pattern_application_and_screen_template(self) -> None:
        checker = load_checker()
        active_pattern_ids, application_templates = load_contracts(checker)
        catalog = checker.load_yaml(ROOT / "pattern-catalog.yml")
        manifest = json.loads((ROOT / "шаблоны-экранов" / "manifest.json").read_text(encoding="utf-8"))
        template = next(item for item in manifest["templates"] if item["template_id"] == "card-feed-list-screen")
        table_template = next(item for item in manifest["templates"] if item["template_id"] == "list-detail-table-screen")
        entries = {item["id"]: item for item in catalog["entries"] if isinstance(item, dict) and item.get("id")}
        selection = (ROOT / "ui-pattern-selection.md").read_text(encoding="utf-8")

        self.assertIn("ui-patterns.lists.card-feed", active_pattern_ids)
        self.assertNotEqual(template["pattern_id"], table_template["pattern_id"])
        self.assertNotEqual(template["application_template_id"], table_template["application_template_id"])
        self.assertIn("однородные строки и колонки", entries["ui-patterns.lists.data-table"]["selection_signals"])
        self.assertIn(
            "пользователю важно сопоставлять значения одних и тех же полей в строках и колонках",
            entries["ui-patterns.lists.card-feed"]["contraindications"],
        )
        self.assertIn("ui-patterns.lists.card-feed", selection)
        self.assertIn("ui-patterns.lists.data-table", selection)
        self.assertEqual(template["application_template_id"], "list-detail-ui-card-feed")
        self.assertEqual(template["pattern_id"], "ui-patterns.lists.card-feed")
        self.assertEqual(template["template_path"], "карточная-лента")
        self.assertEqual(application_templates["list-detail-ui-card-feed"]["selection_status"], "selectable")

    def test_screen_templates_are_content_compositions_not_viewport_shells(self) -> None:
        checker = load_checker()
        active_pattern_ids, application_templates = load_contracts(checker)
        errors: list[str] = []
        checker.check_screen_templates(
            ROOT,
            active_pattern_ids,
            application_templates,
            "0.3.1",
            errors,
        )
        self.assertEqual(errors, [])

        manifest = json.loads((ROOT / "шаблоны-экранов" / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["template_role"], "content-composition")
        self.assertFalse(manifest["includes_viewport_shells"])
        self.assertEqual(manifest["viewport_contract_scope"], "responsive-content-behavior-only")
        self.assertTrue((ROOT / "screen-shell-integration-contract.md").is_file())

    def test_screen_shell_gap_requires_reason_and_decision(self) -> None:
        checker = load_checker()
        viewport = {
            "viewport_id": "fixture-viewport",
            "width": 360,
            "height": 640,
            "unit": "css-px",
            "orientation": "portrait",
            "responsive_profile": "narrow",
            "breakpoint_conditions": "fixture condition",
            "purpose": "reference",
            "source": "fixture:viewport",
            "rationale": "Fixture validation only.",
            "status": "proposed",
            "screen_shell_candidates": [
                {
                    "status": "gap",
                    "reason": "No shell catalog is supplied in this fixture.",
                    "decision_needed": "Provide a matching shell catalog or approve another action.",
                }
            ],
        }
        errors: list[str] = []
        checker._check_viewport_candidate(viewport, "fixture.viewport", errors)
        self.assertEqual(errors, [])

        del viewport["screen_shell_candidates"][0]["decision_needed"]
        checker._check_viewport_candidate(viewport, "fixture.viewport", errors)
        self.assertTrue(any("gap requires decision_needed" in error for error in errors))

    def test_rejects_shell_viewport_mismatch(self) -> None:
        checker = load_checker()
        viewport = {
            "viewport_id": "fixture-viewport",
            "width": 360,
            "height": 640,
            "unit": "css-px",
            "orientation": "portrait",
            "responsive_profile": "narrow",
            "breakpoint_conditions": "fixture condition",
            "purpose": "reference",
            "source": "fixture:viewport",
            "rationale": "Fixture validation only.",
            "status": "confirmed",
            "screen_shell_candidates": [
                {
                    "status": "selected",
                    "catalog_url": "https://github.com/Druk83/sdd-template.git",
                    "catalog_revision": "fixture-revision",
                    "shell_id": "fixture-shell",
                    "rationale": "Fixture validation only.",
                    "shell_viewport": {
                        "width": 412,
                        "height": 640,
                        "unit": "css-px",
                        "orientation": "portrait",
                    },
                }
            ],
        }
        errors: list[str] = []
        checker._check_viewport_candidate(viewport, "fixture.viewport", errors)
        self.assertTrue(any("shell_viewport width does not match" in error for error in errors))

    def test_card_feed_runtime_script_passes_node_syntax_check(self) -> None:
        result = subprocess.run(
            ["node", "--check", str(ROOT / "шаблоны-экранов" / "карточная-лента" / "card-feed.js")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_card_feed_runtime_interactions(self) -> None:
        result = subprocess.run(
            ["node", str(ROOT / "tests" / "card-feed-runtime.test.cjs")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("CARD_FEED_RUNTIME_TEST: PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
