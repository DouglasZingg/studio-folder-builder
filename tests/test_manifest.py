import json
from pathlib import Path

from builder.core.builder import PlanBuilder
from builder.models import PlanAction, PlanActionType
from builder.core.manifest import build_manifest, write_manifest


def test_manifest_written(tmp_path: Path):
    root = tmp_path
    project_root = root / "MyShow"

    plan = [
        PlanAction(PlanActionType.DIR, project_root / "production"),
        PlanAction(PlanActionType.FILE, project_root / "production" / "notes.md"),
    ]

    builder = PlanBuilder(overwrite=False)
    result = builder.execute(plan)

    template = {
        "name": "VFX Default",
        "version": "1.0",
        "project_folders": ["production"],
        "shot_tree": {"docs": ["notes.md", "manifest.json"]},
        "asset_tree": {"characters": ["work"]},
    }

    rec = build_manifest(
        project_root=project_root,
        template_name="VFX Default",
        template_version="1.0",
        template_raw=template,
        mode="shots",
        sequences={"SQ010": ["SH010"]},
        assets=None,
        result=result,
    )


    path = write_manifest(rec)
    assert path.is_file()

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["tool"] == "Studio Folder Builder"
    assert data["template"] == "VFX Default"
    assert "timestamp" in data
    assert data["results"]["errors"] == 0
    assert data["manifest_path"] == path.as_posix()
