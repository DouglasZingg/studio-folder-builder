from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from builder.models import PlanAction, PlanActionType


@dataclass
class BuildResult:
    created_dirs: int = 0
    created_files: int = 0
    skipped: int = 0
    errors: int = 0
    created: list[PlanAction] = None
    skipped_items: list[PlanAction] = None
    error_items: list[tuple[PlanAction, str]] = None

    def __post_init__(self) -> None:
        if self.created is None:
            self.created = []
        if self.skipped_items is None:
            self.skipped_items = []
        if self.error_items is None:
            self.error_items = []


class PlanBuilder:
    def __init__(self, overwrite: bool = False):
        self.overwrite = overwrite

    def execute(self, plan: Iterable[PlanAction]) -> BuildResult:
        result = BuildResult()

        # Ensure dirs are processed before files
        dirs = [a for a in plan if a.type == PlanActionType.DIR]
        files = [a for a in plan if a.type == PlanActionType.FILE]

        for action in dirs + files:
            try:
                if action.type == PlanActionType.DIR:
                    self._make_dir(action.path)
                    result.created_dirs += 1
                    result.created.append(action)
                else:
                    created = self._make_file(action.path)
                    if created:
                        result.created_files += 1
                        result.created.append(action)
                    else:
                        result.skipped += 1
                        result.skipped_items.append(action)
            except Exception as exc:
                result.errors += 1
                result.error_items.append((action, str(exc)))

        return result

    def _make_dir(self, path: Path) -> None:
        # mkdir with exist_ok=True doesn't "overwrite" content; it just ensures existence.
        path.mkdir(parents=True, exist_ok=True)

    def _make_file(self, path: Path) -> bool:
        """
        Returns True if created/written, False if skipped.
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.exists() and not self.overwrite:
            return False

        # Very simple starter-file content for now (Day 5 adds manifest + richer reporting)
        suffix = path.suffix.lower()
        if suffix == ".md":
            content = f"# Notes\n\nCreated by Studio Folder Builder.\n"
        elif suffix == ".json":
            content = "{\n  \n}\n"
        else:
            content = ""

        path.write_text(content, encoding="utf-8")
        return True
