from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TemplateInfo:
    template_id: str          # filename without extension
    name: str                 # display name from JSON
    version: str              # version from JSON
    path: Path                # full path to json
    raw: dict[str, Any]       # full loaded json


class TemplateError(Exception):
    pass


class TemplateLoader:
    REQUIRED_KEYS = ("name", "version", "project_folders", "shot_tree", "asset_tree")

    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir

    def discover(self) -> list[Path]:
        if not self.templates_dir.exists():
            return []
        return sorted(self.templates_dir.glob("*.json"))

    def load_all(self) -> tuple[list[TemplateInfo], list[str]]:
        templates: list[TemplateInfo] = []
        errors: list[str] = []

        for path in self.discover():
            try:
                info = self.load_one(path)
                templates.append(info)
            except Exception as exc:
                errors.append(f"{path.name}: {exc}")

        return templates, errors

    def load_one(self, path: Path) -> TemplateInfo:
        data = self._read_json(path)
        self._validate(data, path)

        template_id = path.stem
        name = str(data.get("name", template_id))
        version = str(data.get("version", "0.0"))

        return TemplateInfo(
            template_id=template_id,
            name=name,
            version=version,
            path=path,
            raw=data,
        )

    def _read_json(self, path: Path) -> dict[str, Any]:
        try:
            text = path.read_text(encoding="utf-8")
            obj = json.loads(text)
        except json.JSONDecodeError as e:
            raise TemplateError(f"Invalid JSON (line {e.lineno}, col {e.colno})") from e
        except OSError as e:
            raise TemplateError(f"Could not read file: {e}") from e

        if not isinstance(obj, dict):
            raise TemplateError("Template root must be a JSON object")
        return obj

    def _validate(self, data: dict[str, Any], path: Path) -> None:
        missing = [k for k in self.REQUIRED_KEYS if k not in data]
        if missing:
            raise TemplateError(f"Missing required keys: {', '.join(missing)}")

        if not isinstance(data["project_folders"], list):
            raise TemplateError("'project_folders' must be a list")

        if not isinstance(data["shot_tree"], dict):
            raise TemplateError("'shot_tree' must be an object/dict")

        if not isinstance(data["asset_tree"], dict):
            raise TemplateError("'asset_tree' must be an object/dict")
