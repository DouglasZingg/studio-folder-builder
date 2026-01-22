# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from builder.core.builder import BuildResult


@dataclass(frozen=True)
class ManifestRecord:
    tool: str
    template: str
    template_version: str
    timestamp: str
    root: str
    project: str
    overwrite: bool

    mode: str  # "shots" or "assets"
    sequences: dict[str, list[str]] | None
    assets: dict[str, list[str]] | None

    results: dict[str, int]
    actions: list[dict[str, Any]]
    manifest_path: str


def utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def determine_manifest_path(project_root: Path, template_raw: dict[str, Any]) -> Path:
    """
    Project-wide manifest location preference:
      1) project_root/production/manifest.json
      2) project_root/tools/manifest.json
      3) project_root/manifest.json
    """
    prod = project_root / "production"
    tools = project_root / "tools"

    # Prefer production by default (studio-ish). If it doesn't exist yet, we create it when writing.
    return prod / "manifest.json" if True else (tools / "manifest.json" if tools.exists() else project_root / "manifest.json")


def build_manifest(
    project_root: Path,
    template_name: str,
    template_version: str,
    template_raw: dict[str, Any],
    mode: str,
    sequences: dict[str, list[str]] | None,
    assets: dict[str, list[str]] | None,
    result: BuildResult,
) -> ManifestRecord:
    manifest_path = determine_manifest_path(project_root, template_raw)

    actions_out: list[dict[str, Any]] = []
    for oc in result.outcomes:
        actions_out.append(
            {
                "type": oc.action.type.value,
                "path": oc.action.path.as_posix(),
                "status": oc.status,
                "message": oc.message,
            }
        )

    return ManifestRecord(
        tool="Studio Folder Builder",
        template=template_name,
        template_version=template_version,
        timestamp=utc_iso_now(),
        root=project_root.parent.as_posix(),
        project=project_root.name,
        overwrite=result.overwrite,
        mode=mode,
        sequences=sequences,
        assets=assets,
        results={
            "created_dirs": result.created_dirs,
            "created_files": result.created_files,
            "skipped": result.skipped,
            "errors": result.errors,
        },
        actions=actions_out,
        manifest_path=manifest_path.as_posix(),
    )


def write_manifest(rec: ManifestRecord) -> Path:
    path = Path(rec.manifest_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(rec)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
