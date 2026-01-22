from pathlib import Path
from builder.core.planner import plan_asset_build


def test_asset_plan_creates_category_and_asset_paths():
    template = {
        "name": "Game Default",
        "version": "1.0",
        "project_folders": ["assets", "tools"],
        "shot_tree": {"docs": ["notes.md"]},
        "asset_tree": {
            "characters": ["work", "publish", "textures"],
            "props": ["work", "publish"],
        },
    }

    root = Path("D:/shows")
    assets = {"characters": ["Hero"], "props": ["Sword"]}

    plan = plan_asset_build(root=root, project="MyGame", template_raw=template, assets=assets)
    paths = {(a.type.value, a.path.as_posix()) for a in plan}

    assert ("dir", "D:/shows/MyGame/assets/characters") in paths
    assert ("dir", "D:/shows/MyGame/assets/characters/Hero/work") in paths
    assert ("dir", "D:/shows/MyGame/assets/props/Sword/publish") in paths
