from pathlib import Path

from builder.core.planner import plan_shot_build
from builder.models import PlanActionType


def test_plan_contains_project_folders_and_shot_tree():
    template = {
        "name": "VFX Default",
        "version": "1.0",
        "project_folders": ["assets", "sequences", "tools"],
        "shot_tree": {"docs": ["notes.md", "manifest.json"], "work": ["maya"]},
        "asset_tree": {"characters": ["work"]},
    }

    root = Path("D:/shows")
    sequences = {"SQ010": ["SH010"]}

    plan = plan_shot_build(root=root, project="MyShow", template_raw=template, sequences=sequences)

    # Some expected paths
    paths = {(a.type.value, a.path.as_posix()) for a in plan}

    assert ("dir", "D:/shows/MyShow/assets") in paths
    assert ("dir", "D:/shows/MyShow/sequences") in paths
    assert ("dir", "D:/shows/MyShow/sequences/SQ010/SH010/work/maya") in paths
    assert ("file", "D:/shows/MyShow/sequences/SQ010/SH010/docs/notes.md") in paths
    assert ("file", "D:/shows/MyShow/sequences/SQ010/SH010/docs/manifest.json") in paths

    # Ensure at least one file and one dir exist
    assert any(a.type == PlanActionType.FILE for a in plan)
    assert any(a.type == PlanActionType.DIR for a in plan)


def test_plan_dedupes_repeated_entries():
    template = {
        "name": "Temp",
        "version": "1.0",
        "project_folders": ["sequences", "sequences"],  # duplicate on purpose
        "shot_tree": {"docs": ["notes.md", "notes.md"]},  # duplicate on purpose
        "asset_tree": {"characters": ["work"]},
    }
    root = Path("D:/shows")
    sequences = {"SQ010": ["SH010"]}

    plan = plan_shot_build(root=root, project="MyShow", template_raw=template, sequences=sequences)
    paths = [(a.type.value, a.path.as_posix()) for a in plan]

    assert paths.count(("dir", "D:/shows/MyShow/sequences")) == 1
    assert paths.count(("file", "D:/shows/MyShow/sequences/SQ010/SH010/docs/notes.md")) == 1
