#!/usr/bin/env python3
"""Проверка полноты публичного пакета UI-паттернов."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, cast


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("Для проверки требуется PyYAML: python -m pip install pyyaml") from exc

    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Не удалось прочитать YAML {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"Корень YAML должен быть объектом: {path}")
    return cast(dict[str, Any], value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pattern-catalog-check",
        description="Проверяет публичные active-записи UI-паттернов и их артефакты.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Корень публичного каталога. По умолчанию текущая директория.",
    )
    parser.add_argument(
        "--screen-pool",
        type=Path,
        help="Проверить machine-readable screen pool проекта-потребителя.",
    )
    parser.add_argument(
        "--require-confirmed-screen-pool",
        action="store_true",
        help="Требовать status: confirmed у screen pool.",
    )
    return parser.parse_args()


def add_error(errors: list[str], message: str) -> None:
    errors.append(message)


def check_screen_templates(
    root: Path,
    active_pattern_ids: set[str],
    application_templates: dict[str, dict[str, Any]],
    expected_version: str,
    errors: list[str],
) -> None:
    manifest_path = root / "шаблоны-экранов" / "manifest.json"
    if not manifest_path.is_file():
        add_error(errors, f"screen UI template manifest not found: {manifest_path}")
        return
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        add_error(errors, f"invalid screen UI template manifest: {exc}")
        return
    if not isinstance(manifest, dict):
        add_error(errors, "screen UI template manifest must be an object")
        return
    if manifest.get("schema_version") != 1:
        add_error(errors, "screen UI template manifest must use schema_version 1")
    if manifest.get("template_set_version") != expected_version:
        add_error(errors, f"screen UI template set must be version {expected_version}")
    if manifest.get("template_role") != "content-composition":
        add_error(errors, "screen UI template set must declare template_role content-composition")
    if manifest.get("includes_viewport_shells") is not False:
        add_error(errors, "screen UI template set must not claim to include viewport shells")
    if manifest.get("viewport_contract_scope") != "responsive-content-behavior-only":
        add_error(errors, "screen UI viewport contract must be scoped to responsive content behavior")
    if manifest.get("runtime") != "framework-neutral-html-css-js":
        add_error(errors, "screen UI templates must use the canonical runtime")
    if manifest.get("source_url") != "https://github.com/Druk83/ui-patterns.git":
        add_error(errors, "screen UI template source_url is invalid")
    pool_schema = manifest.get("screen_pool_schema")
    if not isinstance(pool_schema, str) or not pool_schema:
        add_error(errors, "screen UI template manifest has no screen_pool_schema")
    elif not (root / "шаблоны-экранов" / pool_schema).is_file():
        add_error(errors, f"screen pool schema not found: {pool_schema}")
    shell_contract = manifest.get("screen_shell_integration_contract")
    if not isinstance(shell_contract, str) or not shell_contract:
        add_error(errors, "screen UI template manifest has no screen_shell_integration_contract")
    else:
        shell_contract_path = (manifest_path.parent / shell_contract).resolve()
        try:
            shell_contract_path.relative_to(root.resolve())
        except ValueError:
            add_error(errors, "screen shell integration contract escapes the repository")
        else:
            if not shell_contract_path.is_file():
                add_error(errors, f"screen shell integration contract not found: {shell_contract}")
    templates = manifest.get("templates")
    if not isinstance(templates, list) or not templates:
        add_error(errors, "screen UI template manifest has no templates")
        return
    shared_runtime = manifest.get("shared_runtime")
    if not isinstance(shared_runtime, str) or not shared_runtime:
        add_error(errors, "screen UI template manifest has no shared_runtime")
        return
    runtime_dir = root / "шаблоны-экранов" / shared_runtime
    try:
        runtime_dir.relative_to(root / "шаблоны-экранов")
    except ValueError:
        add_error(errors, "screen UI shared_runtime escapes the template directory")
        return
    if not runtime_dir.is_dir():
        add_error(errors, f"screen UI runtime directory not found: {runtime_dir}")
        return
    template_ids: set[str] = set()
    for index, template in enumerate(templates):
        location = f"шаблоны-экранов.templates[{index}]"
        if not isinstance(template, dict):
            add_error(errors, f"{location} must be an object")
            continue
        for field in ("template_id", "application_template_id", "template_path", "screen_type", "pattern_id", "status"):
            if not isinstance(template.get(field), str) or not template[field]:
                add_error(errors, f"{location}: missing {field}")
        for field in ("version", "responsive_behavior"):
            if not isinstance(template.get(field), str) or not template[field]:
                add_error(errors, f"{location}: missing {field}")
        for field in ("inputs", "outputs", "states", "actions", "transitions", "accessibility_hooks", "acceptance_checks"):
            value = template.get(field)
            if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
                add_error(errors, f"{location}: {field} must be a non-empty string list")
        viewport_contract = template.get("viewport_contract")
        if not isinstance(viewport_contract, dict):
            add_error(errors, f"{location}: viewport_contract must be an object")
        else:
            for field in ("unit", "source_required", "rationale_required", "breakpoint_conditions_required"):
                if field not in viewport_contract:
                    add_error(errors, f"{location}: viewport_contract missing {field}")
        if template.get("status") != "active":
            add_error(errors, f"{location}: template is not active")
        template_id = template.get("template_id")
        pattern_id = template.get("pattern_id")
        template_path = template.get("template_path")
        if isinstance(template_path, str) and template_path:
            template_dir = root / "шаблоны-экранов" / template_path
            try:
                template_dir.relative_to(root / "шаблоны-экранов")
            except ValueError:
                add_error(errors, f"{location}: template_path escapes the template directory")
            else:
                if not (template_dir / "index.html").is_file():
                    add_error(errors, f"{location}: template entrypoint not found: {template_dir / 'index.html'}")
        if isinstance(template_id, str):
            if template_id in template_ids:
                add_error(errors, f"{location}: duplicate template_id: {template_id}")
            template_ids.add(template_id)
            application_template_id = template.get("application_template_id")
            application_template = (
                application_templates.get(application_template_id)
                if isinstance(application_template_id, str)
                else None
            )
            if application_template is None:
                add_error(errors, f"{location}: application template not found: {application_template_id}")
            else:
                if application_template.get("status") != "active":
                    add_error(errors, f"{location}: application template is not active: {application_template_id}")
                if application_template.get("selection_status") != "selectable":
                    add_error(errors, f"{location}: application template is not selectable: {application_template_id}")
                if application_template.get("pattern_id") != pattern_id:
                    add_error(errors, f"{location}: pattern_id does not match application template")
        if isinstance(pattern_id, str) and pattern_id not in active_pattern_ids:
            add_error(errors, f"{location}: active pattern not found: {pattern_id}")
    if len(template_ids) != len(templates):
        add_error(errors, "screen UI template manifest contains invalid template identifiers")
    for filename in ("index.html", "styles.css", "script.js", "манифест-эталонного-шаблона.json", "README.md"):
        if not (runtime_dir / filename).is_file():
            add_error(errors, f"screen UI runtime file not found: {runtime_dir / filename}")

    reference_manifest = runtime_dir / "манифест-эталонного-шаблона.json"
    try:
        reference_data = json.loads(reference_manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        add_error(errors, f"invalid screen UI reference manifest: {exc}")
    else:
        if not isinstance(reference_data, dict):
            add_error(errors, "screen UI reference manifest must be an object")
            return
        if reference_data.get("status") != "reference-only":
            add_error(errors, "screen UI reference manifest must be reference-only")
        if reference_data.get("data_policy") != "fixture-only":
            add_error(errors, "screen UI reference manifest must use fixture-only data")
        if reference_data.get("artifact_scope") != "content-composition-only":
            add_error(errors, "screen UI reference manifest must declare content-composition-only scope")
        if reference_data.get("includes_viewport_shell") is not False:
            add_error(errors, "screen UI reference manifest must not claim to include a viewport shell")
        if reference_data.get("version") != expected_version:
            add_error(errors, f"screen UI reference manifest must be version {expected_version}")
        if reference_data.get("source_url") != "https://github.com/Druk83/ui-patterns.git":
            add_error(errors, "screen UI reference manifest source_url is invalid")
        for field in ("responsive_contract", "accessibility_hooks", "visual_baseline"):
            value = reference_data.get(field)
            if not value:
                add_error(errors, f"screen UI reference manifest is missing {field}")
        visual_baseline = reference_data.get("visual_baseline")
        if isinstance(visual_baseline, str) and not (runtime_dir / visual_baseline).is_file():
            add_error(errors, f"screen UI visual baseline not found: {visual_baseline}")
        elif isinstance(visual_baseline, str):
            try:
                baseline_data = json.loads((runtime_dir / visual_baseline).read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                add_error(errors, f"invalid screen UI visual baseline: {exc}")
            else:
                if not isinstance(baseline_data, dict) or baseline_data.get("version") != expected_version:
                    add_error(errors, f"screen UI visual baseline must be version {expected_version}")
                if isinstance(baseline_data, dict):
                    if baseline_data.get("artifact_scope") != "content-composition-only":
                        add_error(errors, "screen UI visual baseline must declare content-composition-only scope")
                    if baseline_data.get("includes_viewport_shell") is not False:
                        add_error(errors, "screen UI visual baseline must not claim to include a viewport shell")


def _screen_template_index(root: Path) -> dict[str, dict[str, Any]]:
    manifest_path = root / "шаблоны-экранов" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    raw_templates = manifest.get("templates", []) if isinstance(manifest, dict) else []
    return {
        str(item["template_id"]): cast(dict[str, Any], item)
        for item in raw_templates
        if isinstance(item, dict) and isinstance(item.get("template_id"), str)
    }


def _require_string_list(value: Any, location: str, field: str, errors: list[str]) -> None:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
        add_error(errors, f"{location}: {field} must be a non-empty string list")


def _check_viewport_candidate(
    value: Any,
    location: str,
    errors: list[str],
    require_shell_candidates: bool = False,
) -> bool:
    if not isinstance(value, dict):
        add_error(errors, f"{location}: viewport candidate must be an object")
        return False
    required = (
        "viewport_id",
        "width",
        "height",
        "unit",
        "orientation",
        "responsive_profile",
        "breakpoint_conditions",
        "purpose",
        "source",
        "rationale",
        "status",
    )
    for field in required:
        if field not in value or value[field] in (None, "", []):
            add_error(errors, f"{location}: missing {field}")
    if not isinstance(value.get("viewport_id"), str) or not value.get("viewport_id"):
        return False
    if not isinstance(value.get("width"), int) or value["width"] <= 0:
        add_error(errors, f"{location}: width must be a positive integer")
    if not isinstance(value.get("height"), int) or value["height"] <= 0:
        add_error(errors, f"{location}: height must be a positive integer")
    if value.get("unit") != "css-px":
        add_error(errors, f"{location}: unit must be css-px")
    if value.get("orientation") not in {"portrait", "landscape", "any"}:
        add_error(errors, f"{location}: invalid orientation")
    if value.get("purpose") not in {"reference", "supported", "minimum", "maximum", "stress"}:
        add_error(errors, f"{location}: invalid purpose")
    if value.get("status") not in {"proposed", "confirmed", "rejected", "gap"}:
        add_error(errors, f"{location}: invalid status")
    shell_candidates = value.get("screen_shell_candidates")
    if shell_candidates is None:
        if require_shell_candidates:
            add_error(errors, f"{location}: screen_shell_candidates is required for this catalog version")
        return True
    if not isinstance(shell_candidates, list) or not shell_candidates:
        add_error(errors, f"{location}: screen_shell_candidates must be a non-empty list")
        return True

    selected_shell_count = 0
    for index, raw_candidate in enumerate(shell_candidates):
        candidate_location = f"{location}.screen_shell_candidates[{index}]"
        if not isinstance(raw_candidate, dict):
            add_error(errors, f"{candidate_location}: shell candidate must be an object")
            continue
        shell_status = raw_candidate.get("status")
        if shell_status not in {"selected", "proposed", "rejected", "gap", "not_applicable"}:
            add_error(errors, f"{candidate_location}: invalid status")
            continue
        if shell_status == "gap":
            for field in ("reason", "decision_needed"):
                if not isinstance(raw_candidate.get(field), str) or not raw_candidate[field].strip():
                    add_error(errors, f"{candidate_location}: gap requires {field}")
            continue
        if shell_status == "not_applicable":
            if not isinstance(raw_candidate.get("rationale"), str) or not raw_candidate["rationale"].strip():
                add_error(errors, f"{candidate_location}: not_applicable requires rationale")
            continue

        for field in ("catalog_url", "catalog_revision", "shell_id", "rationale"):
            if not isinstance(raw_candidate.get(field), str) or not raw_candidate[field].strip():
                add_error(errors, f"{candidate_location}: {shell_status} requires {field}")
        catalog_url = raw_candidate.get("catalog_url")
        if isinstance(catalog_url, str) and not catalog_url.startswith("https://"):
            add_error(errors, f"{candidate_location}: catalog_url must be an official HTTPS URL")
        shell_viewport = raw_candidate.get("shell_viewport")
        if not isinstance(shell_viewport, dict):
            add_error(errors, f"{candidate_location}: {shell_status} requires shell_viewport metadata")
        else:
            for field in ("width", "height", "unit", "orientation"):
                if field not in shell_viewport:
                    add_error(errors, f"{candidate_location}: shell_viewport missing {field}")
                elif shell_viewport[field] != value.get(field):
                    add_error(errors, f"{candidate_location}: shell_viewport {field} does not match viewport candidate")
        if shell_status == "selected":
            selected_shell_count += 1
            if value.get("status") != "confirmed":
                add_error(errors, f"{candidate_location}: selected shell requires a confirmed viewport candidate")
    if selected_shell_count > 1:
        add_error(errors, f"{location}: only one screen shell candidate may be selected")
    return True


def check_screen_pool(
    root: Path,
    pool_path: Path,
    active_pattern_ids: set[str],
    expected_version: str,
    errors: list[str],
    require_confirmed: bool = False,
) -> None:
    try:
        pool = load_yaml(pool_path)
    except (OSError, RuntimeError) as exc:
        add_error(errors, f"invalid screen pool: {exc}")
        return

    if pool.get("schema_version") != 1:
        add_error(errors, "screen pool must use schema_version 1")
    if pool.get("kind") != "screen-pool":
        add_error(errors, "screen pool kind must be screen-pool")
    if pool.get("template_set_version") != expected_version:
        add_error(errors, f"screen pool must declare template_set_version {expected_version}")
    pool_status = pool.get("status")
    if pool_status not in {"proposed", "confirmed", "superseded"}:
        add_error(errors, "screen pool has invalid status")
    _require_string_list(pool.get("source_refs"), "screen pool", "source_refs", errors)
    if require_confirmed and pool_status != "confirmed":
        add_error(errors, "screen pool must be confirmed before screen specification")
    if pool_status == "confirmed":
        for field in ("confirmed_by", "confirmed_at", "decision_ref"):
            if not isinstance(pool.get(field), str) or not pool[field].strip():
                add_error(errors, f"screen pool: missing confirmation field {field}")

    screens = pool.get("screens")
    if not isinstance(screens, list) or not screens:
        add_error(errors, "screen pool has no screens")
        return
    try:
        template_index = _screen_template_index(root)
    except (OSError, json.JSONDecodeError, AttributeError) as exc:
        add_error(errors, f"screen template manifest cannot be loaded for screen pool: {exc}")
        return

    screen_ids: set[str] = set()
    for index, screen in enumerate(screens):
        location = f"screen pool.screens[{index}]"
        if not isinstance(screen, dict):
            add_error(errors, f"{location} must be an object")
            continue
        required = (
            "screen_id",
            "title",
            "screen_type",
            "purpose",
            "route_or_entry_point",
            "roles",
            "user_task",
            "pattern_candidates",
            "template_candidates",
            "states",
            "actions",
            "transitions",
            "viewport_candidates",
            "reference_artifacts",
            "rationale",
            "source_refs",
            "status",
        )
        for field in required:
            if field not in screen or screen[field] in (None, "") or (
                field != "reference_artifacts" and screen[field] == []
            ):
                add_error(errors, f"{location}: missing {field}")
        screen_id = screen.get("screen_id")
        if isinstance(screen_id, str) and screen_id:
            if screen_id in screen_ids:
                add_error(errors, f"{location}: duplicate screen_id: {screen_id}")
            screen_ids.add(screen_id)
        status = screen.get("status")
        if status not in {"proposed", "confirmed", "rejected", "gap"}:
            add_error(errors, f"{location}: invalid status")
        if pool_status == "confirmed" and status != "confirmed":
            add_error(errors, f"{location}: confirmed pool contains non-confirmed screen")
        _require_string_list(screen.get("roles"), location, "roles", errors)
        _require_string_list(screen.get("states"), location, "states", errors)
        _require_string_list(screen.get("actions"), location, "actions", errors)
        if not isinstance(screen.get("transitions"), list) or not screen["transitions"]:
            add_error(errors, f"{location}: transitions must be a non-empty list")
        if not isinstance(screen.get("reference_artifacts"), list):
            add_error(errors, f"{location}: reference_artifacts must be a list")
        _require_string_list(screen.get("source_refs"), location, "source_refs", errors)

        pattern_candidates = screen.get("pattern_candidates")
        confirmed_patterns = 0
        if not isinstance(pattern_candidates, list) or not pattern_candidates:
            add_error(errors, f"{location}: pattern_candidates must be a non-empty list")
        else:
            for candidate_index, candidate in enumerate(pattern_candidates):
                candidate_location = f"{location}.pattern_candidates[{candidate_index}]"
                if not isinstance(candidate, dict):
                    add_error(errors, f"{candidate_location} must be an object")
                    continue
                for field in ("pattern_id", "rationale", "status"):
                    if not isinstance(candidate.get(field), str) or not candidate[field].strip():
                        add_error(errors, f"{candidate_location}: missing {field}")
                if candidate.get("status") not in {"proposed", "confirmed", "rejected", "gap"}:
                    add_error(errors, f"{candidate_location}: invalid status")
                pattern_id = candidate.get("pattern_id")
                if pattern_id not in active_pattern_ids:
                    add_error(errors, f"{candidate_location}: active pattern not found: {pattern_id}")
                if candidate.get("status") == "confirmed":
                    confirmed_patterns += 1

        template_candidates = screen.get("template_candidates")
        confirmed_templates = 0
        if not isinstance(template_candidates, list) or not template_candidates:
            add_error(errors, f"{location}: template_candidates must be a non-empty list")
        else:
            for candidate_index, candidate in enumerate(template_candidates):
                candidate_location = f"{location}.template_candidates[{candidate_index}]"
                if not isinstance(candidate, dict):
                    add_error(errors, f"{candidate_location} must be an object")
                    continue
                for field in ("template_id", "rationale", "status"):
                    if not isinstance(candidate.get(field), str) or not candidate[field].strip():
                        add_error(errors, f"{candidate_location}: missing {field}")
                template_id = candidate.get("template_id")
                template = (
                    template_index.get(template_id)
                    if isinstance(template_id, str)
                    else None
                )
                if template is None:
                    add_error(errors, f"{candidate_location}: template not found: {template_id}")
                elif template.get("status") != "active":
                    add_error(errors, f"{candidate_location}: template is not active: {template_id}")
                if candidate.get("status") not in {"proposed", "confirmed", "rejected", "gap"}:
                    add_error(errors, f"{candidate_location}: invalid status")
                if candidate.get("status") == "confirmed":
                    confirmed_templates += 1

        viewports = screen.get("viewport_candidates")
        confirmed_viewports = 0
        if not isinstance(viewports, list) or not viewports:
            add_error(errors, f"{location}: viewport_candidates must be a non-empty list")
        else:
            viewport_ids: set[str] = set()
            for viewport_index, viewport in enumerate(viewports):
                viewport_location = f"{location}.viewport_candidates[{viewport_index}]"
                valid = _check_viewport_candidate(
                    viewport,
                    viewport_location,
                    errors,
                    require_shell_candidates=pool.get("template_set_version") == expected_version,
                )
                if valid and isinstance(viewport, dict):
                    viewport_id = viewport.get("viewport_id")
                    if viewport_id in viewport_ids:
                        add_error(errors, f"{viewport_location}: duplicate viewport_id: {viewport_id}")
                    viewport_ids.add(str(viewport_id))
                    if viewport.get("status") == "confirmed":
                        confirmed_viewports += 1
        if status == "confirmed" and not (confirmed_patterns and confirmed_templates and confirmed_viewports):
            add_error(errors, f"{location}: confirmed screen requires confirmed pattern, template and viewport")


def check_project_structure(root: Path, errors: list[str]) -> None:
    structure_path = root / ".project-structure.json"
    try:
        structure = json.loads(structure_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        add_error(errors, f"project structure cannot be loaded: {exc}")
        return
    if not isinstance(structure, dict):
        add_error(errors, "project structure must be an object")
        return
    folders = structure.get("folders")
    if not isinstance(folders, list):
        add_error(errors, "project structure has no folders list")
    else:
        for index, folder in enumerate(folders):
            if not isinstance(folder, dict):
                add_error(errors, f"project structure folders[{index}] must be an object")
                continue
            path = folder.get("path")
            if not isinstance(path, str) or not path:
                add_error(errors, f"project structure folders[{index}] has no path")
                continue
            target = root / path
            if folder.get("required") is True and not target.is_dir():
                add_error(errors, f"required project directory is missing: {path}")
    catalog = structure.get("catalog")
    if not isinstance(catalog, dict):
        add_error(errors, "project structure has no catalog section")
        return
    for field in (
        "ui_specification_schema",
        "ui_screen_template",
        "screen_pool_schema",
        "screen_ui_templates",
        "screen_shell_integration_contract",
        "pattern_application_templates",
        "public_selection_procedure",
        "public_index",
        "reference_prototype_checker",
    ):
        value = catalog.get(field)
        if not isinstance(value, str) or not value or not (root / value).is_file():
            add_error(errors, f"project structure catalog path is missing: {field}")


def check_record(
    root: Path,
    record: dict[str, Any],
    location: str,
    templates: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    if record.get("status") != "active":
        return

    pattern_id = record.get("pattern_id") or record.get("id")
    template_id = record.get("template_id")
    card_path = record.get("card_path") or record.get("family_path")
    diagram_source = record.get("diagram_source")
    diagram_artifact = record.get("diagram_artifact")

    for field, value in (
        ("pattern_id", pattern_id),
        ("template_id", template_id),
        ("card_path", card_path),
        ("diagram_source", diagram_source),
        ("diagram_artifact", diagram_artifact),
    ):
        if not isinstance(value, str) or not value:
            add_error(errors, f"{location}: отсутствует обязательное поле {field}")

    if not isinstance(template_id, str) or not template_id:
        return
    if not isinstance(card_path, str) or not card_path:
        return
    if not isinstance(diagram_source, str) or not diagram_source:
        return
    if not isinstance(diagram_artifact, str) or not diagram_artifact:
        return

    template = templates.get(template_id)
    if template is None:
        add_error(errors, f"{location}: template_id не найден: {template_id}")
    else:
        template_status = template.get("status")
        selection_status = template.get("selection_status")
        if template_status in {"candidate", "superseded"}:
            add_error(errors, f"{location}: active-запись связана с шаблоном {template_status}: {template_id}")
        if selection_status == "not_selectable":
            add_error(errors, f"{location}: active-запись связана с not_selectable шаблоном: {template_id}")
        template_pattern_id = template.get("pattern_id")
        if template_pattern_id and template_pattern_id != pattern_id:
            add_error(errors, f"{location}: pattern_id не совпадает с application template")

    paths = {
        "card_path": root / card_path,
        "diagram_source": root / diagram_source,
        "diagram_artifact": root / diagram_artifact,
    }
    for field, path in paths.items():
        if not path.is_file():
            add_error(errors, f"{location}: файл не найден ({field}): {path}")

    card = paths["card_path"]
    source = paths["diagram_source"]
    if card.is_file():
        card_text = card.read_text(encoding="utf-8")
        artifact_name = Path(diagram_artifact).name
        if f"]({artifact_name})" not in card_text and diagram_artifact not in card_text:
            add_error(errors, f"{location}: карточка не ссылается на PNG: {diagram_artifact}")
    if source.is_file():
        source_text = source.read_text(encoding="utf-8")
        if "@startuml" not in source_text or "@enduml" not in source_text:
            add_error(errors, f"{location}: некорректная PlantUML-обёртка: {diagram_source}")


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    errors: list[str] = []

    try:
        catalog = load_yaml(root / "pattern-catalog.yml")
        applications = load_yaml(root / "ui-pattern-application-templates.yml")
    except RuntimeError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    catalog_version = catalog.get("catalog_version")
    if not isinstance(catalog_version, str) or not catalog_version.strip():
        add_error(errors, "public catalog has no catalog_version")
        catalog_version = ""
    readme_path = root / "README.md"
    try:
        readme = readme_path.read_text(encoding="utf-8")
    except OSError as exc:
        add_error(errors, f"public README cannot be read: {exc}")
    else:
        if f"Версия набора шаблонов: `{catalog_version}`" not in readme:
            add_error(errors, "README package version does not match catalog_version")

    template_items = applications.get("templates", [])
    templates: dict[str, dict[str, Any]] = {}
    if isinstance(template_items, list):
        for raw_item in template_items:
            if not isinstance(raw_item, dict):
                continue
            item = cast(dict[str, Any], raw_item)
            template_id = item.get("template_id")
            if isinstance(template_id, str) and template_id:
                templates[template_id] = item

    records: list[tuple[str, dict[str, Any]]] = []
    for key in ("entries",):
        value = catalog.get(key, [])
        if isinstance(value, list):
            records.extend(
                (f"{key}[{index}]", cast(dict[str, Any], item))
                for index, item in enumerate(value)
                if isinstance(item, dict)
            )
    extended = catalog.get("extended_templates", {})
    if isinstance(extended, dict) and isinstance(extended.get("entries"), list):
        records.extend(
            (f"extended_templates.entries[{index}]", cast(dict[str, Any], item))
            for index, item in enumerate(extended["entries"])
            if isinstance(item, dict)
        )

    identifiers: set[str] = set()
    active_count = 0
    for location, record in records:
        identifier = record.get("pattern_id") or record.get("id")
        if isinstance(identifier, str):
            if identifier in identifiers:
                add_error(errors, f"{location}: дублирующийся идентификатор: {identifier}")
            identifiers.add(identifier)
        if record.get("status") == "active":
            active_count += 1
        check_record(root, record, location, templates, errors)

    if active_count == 0:
        add_error(errors, "В публичном каталоге нет active-записей")

    active_pattern_ids = {
        str(record.get("pattern_id") or record.get("id"))
        for _, record in records
        if record.get("status") == "active" and (record.get("pattern_id") or record.get("id"))
    }
    check_screen_templates(root, active_pattern_ids, templates, catalog_version, errors)
    check_project_structure(root, errors)
    if args.screen_pool:
        pool_path = args.screen_pool
        if not pool_path.is_absolute():
            pool_path = root / pool_path
        check_screen_pool(
            root,
            pool_path,
            active_pattern_ids,
            catalog_version,
            errors,
            require_confirmed=args.require_confirmed_screen_pool,
        )

    if errors:
        for error in errors:
            print(f"[ERROR] {error}")
        print(f"PUBLIC_CATALOG_CHECK: FAIL ({len(errors)} ошибок)")
        return 1

    suffix = "; screen pool checked" if args.screen_pool else ""
    print(f"PUBLIC_CATALOG_CHECK: PASS ({active_count} active-записей{suffix})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
