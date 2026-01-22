from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, List, Tuple

from builder.models import PlanAction, PlanActionType
from builder.core.template_schema import is_starter_file


def plan_shot_build(
    root: Path,
    project: str,
    template_raw: dict[str, Any],
    sequences: dict[str, list[str]],
) -> list[PlanAction]:
    """
    Builds a flat plan of folders/files for:
      root/project/sequences/<SEQ>/<SHOT>/<shot_tree...>
    plus top-level project_folders.
    """
    project_root = root / project
    actions: list[PlanAction] = []

    # top-level project folders
    for name in template_raw.get("project_folders", []):
        actions.append(PlanAction(PlanActionType.DIR, project_root / name))

    # common containers (optional but typical)
    sequences_root = project_root / "sequences"
    actions.append(PlanAction(PlanActionType.DIR, sequences_root))

    shot_tree = template_raw.get("shot_tree", {})
    # seq/shot paths
    for seq, shots in sequences.items():
        seq_root = sequences_root / seq
        actions.append(PlanAction(PlanActionType.DIR, seq_root))

        for shot in shots:
            shot_root = seq_root / shot
            actions.append(PlanAction(PlanActionType.DIR, shot_root))

            actions.extend(_expand_tree(shot_root, shot_tree))

    return _dedupe_sorted(actions)


def _expand_tree(base: Path, tree: dict[str, Any]) -> list[PlanAction]:
    """
    Expand a dict tree:
      { "work": ["maya","houdini"], "docs":["notes.md"] }
    into plan actions under base.
    """
    actions: list[PlanAction] = []

    for folder_name, children in tree.items():
        node_path = base / folder_name
        actions.append(PlanAction(PlanActionType.DIR, node_path))

        if not isinstance(children, list):
            # Day 3 assumes list children (validated by Day 2)
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
    # Deduplicate by (type, path) but keep deterministic order:
    # sort by path, dirs before files within same path parent.
    seen: set[tuple[str, str]] = set()
    unique: list[PlanAction] = []
    for a in actions:
        key = (a.type.value, str(a.path))
        if key in seen:
            continue
        seen.add(key)
        unique.append(a)

    def sort_key(a: PlanAction) -> Tuple[str, int, str]:
        # dirs first
        t = 0 if a.type == PlanActionType.DIR else 1
        return (str(a.path).lower(), t, a.type.value)

    unique.sort(key=sort_key)
    return unique
