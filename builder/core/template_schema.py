from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TemplateIssue:
    code: str
    message: str
    path: str | None = None  # json path like "shot_tree.docs[0]"

    def pretty(self) -> str:
        where = f" ({self.path})" if self.path else ""
        return f"[{self.code}]{where} {self.message}"


def is_starter_file(name: str) -> bool:
    lowered = name.lower()
    return lowered.endswith(".md") or lowered.endswith(".json") or lowered.endswith(".txt")


def validate_template(data: dict[str, Any]) -> list[TemplateIssue]:
    issues: list[TemplateIssue] = []

    # ---- Required keys
    required = ("name", "version", "project_folders", "shot_tree", "asset_tree")
    for k in required:
        if k not in data:
            issues.append(TemplateIssue("MISSING_KEY", f"Missing required key '{k}'", k))

    if issues:
        return issues  # stop early; rest relies on keys

    # ---- Basic types
    if not isinstance(data["name"], str) or not data["name"].strip():
        issues.append(TemplateIssue("BAD_TYPE", "'name' must be a non-empty string", "name"))

    if not isinstance(data["version"], str) or not data["version"].strip():
        issues.append(TemplateIssue("BAD_TYPE", "'version' must be a non-empty string", "version"))

    if not isinstance(data["project_folders"], list):
        issues.append(TemplateIssue("BAD_TYPE", "'project_folders' must be a list", "project_folders"))
    else:
        for i, item in enumerate(data["project_folders"]):
            if not isinstance(item, str) or not item.strip():
                issues.append(TemplateIssue("BAD_ITEM", "project_folders items must be non-empty strings", f"project_folders[{i}]"))
            elif is_starter_file(item):
                issues.append(TemplateIssue("BAD_ITEM", "project_folders cannot contain starter files (e.g. .md/.json)", f"project_folders[{i}]"))

    if not isinstance(data["shot_tree"], dict):
        issues.append(TemplateIssue("BAD_TYPE", "'shot_tree' must be an object/dict", "shot_tree"))
    else:
        issues.extend(_validate_tree_dict(data["shot_tree"], "shot_tree"))

    if not isinstance(data["asset_tree"], dict):
        issues.append(TemplateIssue("BAD_TYPE", "'asset_tree' must be an object/dict", "asset_tree"))
    else:
        # asset_tree values can be list[str] or nested dict[str, list[str]]
        issues.extend(_validate_asset_tree(data["asset_tree"], "asset_tree"))

    return issues


def _validate_tree_dict(tree: dict[str, Any], base: str) -> list[TemplateIssue]:
    issues: list[TemplateIssue] = []
    for k, v in tree.items():
        if not isinstance(k, str) or not k.strip():
            issues.append(TemplateIssue("BAD_KEY", "Tree keys must be non-empty strings", base))
            continue

        if not isinstance(v, list):
            issues.append(TemplateIssue("BAD_TYPE", "Tree values must be lists", f"{base}.{k}"))
            continue

        for i, item in enumerate(v):
            if not isinstance(item, str) or not item.strip():
                issues.append(TemplateIssue("BAD_ITEM", "Tree list items must be non-empty strings", f"{base}.{k}[{i}]"))
            # starter files are allowed only as leaf items; fine here (e.g. docs: ["notes.md"])
    return issues


def _validate_asset_tree(tree: dict[str, Any], base: str) -> list[TemplateIssue]:
    issues: list[TemplateIssue] = []
    for k, v in tree.items():
        if not isinstance(k, str) or not k.strip():
            issues.append(TemplateIssue("BAD_KEY", "asset_tree keys must be non-empty strings", base))
            continue

        if isinstance(v, list):
            for i, item in enumerate(v):
                if not isinstance(item, str) or not item.strip():
                    issues.append(TemplateIssue("BAD_ITEM", "asset_tree list items must be non-empty strings", f"{base}.{k}[{i}]"))
        elif isinstance(v, dict):
            # nested categories e.g. characters: { work: [...], publish: [...] }
            issues.extend(_validate_tree_dict(v, f"{base}.{k}"))
        else:
            issues.append(TemplateIssue("BAD_TYPE", "asset_tree values must be a list or dict", f"{base}.{k}"))
    return issues
