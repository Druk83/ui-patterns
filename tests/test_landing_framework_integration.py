from __future__ import annotations

import importlib.util
import json
import os
import unittest
from pathlib import Path
from typing import Any


class LandingFrameworkIntegrationTests(unittest.TestCase):
    def test_landing_content_fills_framework_shell(self) -> None:
        framework_setting = os.environ.get("SDD_FRAMEWORK_ROOT")
        if not framework_setting:
            self.skipTest("Для интеграции задайте SDD_FRAMEWORK_ROOT")
        framework_root = Path(framework_setting).resolve()
        fixture_path = framework_root / ".tools" / "ui-screen-scaffold" / "tests" / "test_generator.py"
        if not fixture_path.is_file():
            self.skipTest("В выбранном Framework нет fixture ui-screen-scaffold")

        spec = importlib.util.spec_from_file_location("framework_scaffold_fixture", fixture_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("Не удалось загрузить fixture Framework")
        fixture_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fixture_module)
        fixture = fixture_module.ScreenScaffoldTests(methodName="test_default_plan_is_read_only_and_uses_selected_shell")
        fixture.setUp()
        try:
            package = fixture.package
            pool_path = package / "пул-экранов.json"
            manifest_path = package / "манифест-спецификации-интерфейса.json"
            artifact_path = fixture.reference_root / "screen-manifest.json"
            pool = json.loads(pool_path.read_text(encoding="utf-8"))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            artifacts = json.loads(artifact_path.read_text(encoding="utf-8"))

            pattern_ref = "ui-patterns.forms.form-data-entry-validation"
            template_ref = "landing-page-composition-ui"
            for document in (pool, manifest, artifacts):
                document["template_set_version"] = "0.3.2"
            pool_screen = pool["screens"][0]
            pool_screen["screen_type"] = "single-page landing"
            pool_screen["purpose"] = "Проверить композицию содержимого на тестовых данных."
            pool_screen["pattern_candidates"] = [{"pattern_id": pattern_ref, "status": "selected", "rationale": "Форма включена в тестовый вариант."}]
            pool_screen["template_candidates"] = [{"template_id": template_ref, "status": "selected", "rationale": "Проверяется составной экран."}]
            manifest["screens"][0]["pattern_refs"] = [pattern_ref]
            manifest["screens"][0]["template_refs"] = [template_ref]
            artifacts["artifacts"][0]["pattern_refs"] = [pattern_ref]
            artifacts["artifacts"][0]["template_refs"] = [template_ref]
            for path, document in ((pool_path, pool), (manifest_path, manifest), (artifact_path, artifacts)):
                path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")

            plan: dict[str, Any] = fixture._build()
            self.assertEqual(plan["status"], "ready")
            fixture_module.ui_screen_scaffold.write_plan(plan)
            output = fixture.reference_root / "screens" / "screen-a" / fixture.shell["viewport_id"]
            page_path = output / "index.html"
            page = page_path.read_text(encoding="utf-8")
            placeholder = '<div class="slot-placeholder" data-slot-id="screen-content">screen-content</div>'
            self.assertIn(placeholder, page)
            content = (
                '<div data-slot-id="screen-content" style="height:100%;overflow:auto;padding:1rem">'
                '<section data-block-id="entry"><h2>Подтверждённое предложение</h2>'
                '<p>Адресат и предложение поступают из входов проекта.</p></section>'
                '<section data-block-id="supporting-content"><h2>Объяснение</h2>'
                '<p>Содержимое подтверждается реестром проекта.</p></section>'
                '<section data-block-id="form" data-pattern-refs="ui-patterns.forms.form-data-entry-validation">'
                '<h2>Тестовая форма</h2><label for="fixture-input">Тестовое поле</label>'
                '<input id="fixture-input" type="text"></section>'
                '<section data-block-id="primary-action"><h2>Основное действие</h2>'
                '<button type="button">Проверить результат действия</button></section></div>'
            )
            page_path.write_text(page.replace(placeholder, content, 1), encoding="utf-8")
            rendered = page_path.read_text(encoding="utf-8")
            self.assertLess(rendered.index('data-block-id="entry"'), rendered.index('data-block-id="primary-action"'))
            self.assertIn('data-shell-id="' + fixture.shell["shell_id"] + '"', rendered)
            result = fixture._validate_package()
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(json.loads(result.stdout)["status"], "pass")
        finally:
            fixture.tearDown()
