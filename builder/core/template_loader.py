from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from builder.core.template_schema import TemplateIssue, validate_template


@dataclass(frozen=True)
class TemplateInfo:
    template_id: str          # filename without extension
    name: str                 # display name from JSON
    version: str              # version from JSON
    path: Path                # full path to json
    raw: dict[str, Any]       # full loaded json


@dataclass(frozen=True)
class TemplateLoadResult:
    templates: list[TemplateInfo]
    problems: dict[str, list[TemplateIssue]]  # filename -> issues


class TemplateLoader:
    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir

    def discover(self) -> list[Path]:
        if not self.templates_dir.exists():
            return []
        return sorted(self.templates_dir.glob("*.json"))

    def load_all(self) -> TemplateLoadResult:
        templates: list[TemplateInfo] = []
        problems: dict[str, list[TemplateIssue]] = {}

        for path in self.discover():
            file_key = path.name
            try:
                data = self._read_json(path)
            except Exception as exc:
                problems[file_key] = [TemplateIssue("LOAD_FAIL", str(exc))]
                continue

            issues = validate_template(data)
            if issues:
                problems[file_key] = issues
                continue

            template_id = path.stem
            templates.append(
                TemplateInfo(
                    template_id=template_id,
                    name=str(data["name"]),
                    version=str(data["version"]),
                    path=path,
                    raw=data,
                )
            )

        # Sort templates by display name for nicer UX
        templates.sort(key=lambda t: (t.name.lower(), t.template_id.lower()))
        return TemplateLoadResult(templates=templates, problems=problems)

    def _read_json(self, path: Path) -> dict[str, Any]:
        text = path.read_text(encoding="utf-8")
        try:
            obj = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON (line {e.lineno}, col {e.colno})") from e

        if not isinstance(obj, dict):
            raise ValueError("Template root must be a JSON object")
        return obj
