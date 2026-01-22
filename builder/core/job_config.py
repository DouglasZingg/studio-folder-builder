# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class JobConfig:
    tool: str
    version: str
    timestamp: str

    root: str
    project: str
    template_id: str
    mode: str  # "shots" | "assets"
    overwrite: bool

    sequences: dict[str, list[str]] | None
    assets: dict[str, list[str]] | None


def make_job_config(
    root: Path,
    project: str,
    template_id: str,
    mode: str,
    overwrite: bool,
    sequences: dict[str, list[str]] | None,
    assets: dict[str, list[str]] | None,
    version: str = "0.8.0",
) -> JobConfig:
    return JobConfig(
        tool="Studio Folder Builder",
        version=version,
        timestamp=utc_iso_now(),
        root=root.as_posix(),
        project=project,
        template_id=template_id,
        mode=mode,
        overwrite=overwrite,
        sequences=sequences,
        assets=assets,
    )


def write_job_config(path: Path, config: JobConfig) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(config)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def read_job_config(path: Path) -> JobConfig:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("Config must be a JSON object.")

    # minimal validation
    for k in ("tool", "version", "timestamp", "root", "project", "template_id", "mode", "overwrite"):
        if k not in obj:
            raise ValueError(f"Missing required key: {k}")

    mode = str(obj["mode"])
    sequences = obj.get("sequences")
    assets = obj.get("assets")

    # Enforce mode consistency
    if mode == "shots" and not sequences:
        raise ValueError("Config mode is 'shots' but sequences are missing/empty.")
    if mode == "assets" and not assets:
        raise ValueError("Config mode is 'assets' but assets are missing/empty.")

    return JobConfig(
        tool=str(obj["tool"]),
        version=str(obj["version"]),
        timestamp=str(obj["timestamp"]),
        root=str(obj["root"]),
        project=str(obj["project"]),
        template_id=str(obj["template_id"]),
        mode=mode,
        overwrite=bool(obj["overwrite"]),
        sequences=sequences if isinstance(sequences, dict) else None,
        assets=assets if isinstance(assets, dict) else None,
    )


def config_to_text_for_ui(cfg: JobConfig) -> str:
    """
    Convert config content back into multiline format for the UI text boxes.
    """
    if cfg.mode == "shots" and cfg.sequences:
        lines: list[str] = []
        for seq, shots in cfg.sequences.items():
            lines.append(f"{seq}: {', '.join(shots)}")
        return "\n".join(lines).strip()
    if cfg.mode == "assets" and cfg.assets:
        lines = []
        for cat, items in cfg.assets.items():
            lines.append(f"{cat}: {', '.join(items)}")
        return "\n".join(lines).strip()
    return ""
