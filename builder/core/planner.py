from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Tuple

from builder.models import PlanAction, PlanActionType
from builder.core.template_schema import is_starter_file


# ---------------- SHOTS MODE ----------------

def plan_shot_build(
    root: Path,
    project: str,
    template_raw: dict[str, Any],
    sequences: dict[str, list[str]],
) -> list[PlanAction]:
    project_root = root / project
    actions: list[PlanAction] = []

    for name in template_raw.get("project_folders", []):
        actions.append(PlanAction(PlanActionType.DIR, project_root / name))

    sequences_root = project_root / "sequences"
    actions.append(PlanAction(PlanActionType.DIR, sequences_root))

    shot_tree = template_raw.get("shot_tree", {})
    for seq, shots in sequences.items():
        seq_root = sequences_root / seq
        actions.append(PlanAction(PlanActionType.DIR, seq_root))

        for shot in shots:
            shot_root = seq_root / shot
            actions.append(PlanAction(PlanActionType.DIR, shot_root))
            actions.extend(_expand_tree(shot_root, shot_tree))

    return _dedupe_sorted(actions)


# ---------------- ASSETS MODE ----------------

def plan_asset_build(
    root: Path,
    project: str,
    template_raw: dict[str, Any],
    assets: dict[str, list[str]],
) -> list[PlanAction]:
    """
    Build plan:
      root/project/assets/<category>/<asset_name>/<asset_tree[category]...>
    If template.asset_tree[category] is a list[str], those are subfolders under asset root.
    If it's a dict, it's treated like shot_tree (folder -> children list).
    """
    project_root = root / project
    actions: list[PlanAction] = []

    for name in template_raw.get("project_folders", []):
        actions.append(PlanAction(PlanActionType.DIR, project_root / name))

    assets_root = project_root / "assets"
    actions.append(PlanAction(PlanActionType.DIR, assets_root))

    asset_tree = template_raw.get("asset_tree", {})

    for cat, names in assets.items():
        cat_root = assets_root / cat
        actions.append(PlanAction(PlanActionType.DIR, cat_root))

        # category spec in template
        spec = asset_tree.get(cat)

        for asset_name in names:
            asset_root = cat_root / asset_name
            actions.append(PlanAction(PlanActionType.DIR, asset_root))

            if isinstance(spec, list):
                # list of folders under asset_root
                for item in spec:
                    if not isinstance(item, str) or not item.strip():
                        continue
                    p = asset_root / item
                    if is_starter_file(item):
                        actions.append(PlanAction(PlanActionType.FILE, p))
                    else:
                        actions.append(PlanAction(PlanActionType.DIR, p))

            elif isinstance(spec, dict):
                # nested dict like shot_tree: { work:[...], publish:[...] }
                actions.extend(_expand_tree(asset_root, spec))

            else:
                # fallback if category not in template: create minimal structure
                actions.append(PlanAction(PlanActionType.DIR, asset_root / "work"))
                actions.append(PlanAction(PlanActionType.DIR, asset_root / "publish"))
                actions.append(PlanAction(PlanActionType.DIR, asset_root / "docs"))
                actions.append(PlanAction(PlanActionType.FILE, asset_root / "docs" / "notes.md"))

    return _dedupe_sorted(actions)


# ---------------- Shared helpers ----------------

def _expand_tree(base: Path, tree: dict[str, Any]) -> list[PlanAction]:
    actions: list[PlanAction] = []

    for folder_name, children in tree.items():
        node_path = base / folder_name
        actions.append(PlanAction(PlanActionType.DIR, node_path))

        if not isinstance(children, list):
            continue

        for item in children:
            if not isinstance(item, str) or not item.strip():
                continue
            item_path = node_path / item
            if is_starter_file(item):
                actions.append(PlanAction(PlanActionType.FILE, item_path))
            else:
                actions.append(PlanAction(PlanActionType.DIR, item_path))

    return actions


def _dedupe_sorted(actions: Iterable[PlanAction]) -> list[PlanAction]:
    seen: set[tuple[str, str]] = set()
    unique: list[PlanAction] = []
    for a in actions:
        key = (a.type.value, str(a.path))
        if key in seen:
            continue
        seen.add(key)
        unique.append(a)

    def sort_key(a: PlanAction) -> Tuple[str, int, str]:
        t = 0 if a.type == PlanActionType.DIR else 1
        return (str(a.path).lower(), t, a.type.value)

    unique.sort(key=sort_key)
    return unique
