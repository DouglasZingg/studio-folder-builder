from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from builder.models import PlanAction, PlanActionType


@dataclass(frozen=True)
class ActionOutcome:
    action: PlanAction
    status: str  # "created" | "skipped" | "error"
    message: str | None = None


@dataclass
class BuildResult:
    overwrite: bool = False
    created_dirs: int = 0
    created_files: int = 0
    skipped: int = 0
    errors: int = 0
    outcomes: list[ActionOutcome] = field(default_factory=list)


class PlanBuilder:
    def __init__(self, overwrite: bool = False):
        self.overwrite = overwrite

    def execute(self, plan: Iterable[PlanAction]) -> BuildResult:
        result = BuildResult(overwrite=self.overwrite)

        dirs = [a for a in plan if a.type == PlanActionType.DIR]
        files = [a for a in plan if a.type == PlanActionType.FILE]

        for action in dirs + files:
            try:
                if action.type == PlanActionType.DIR:
                    created = self._make_dir(action.path)
                    if created:
                        result.created_dirs += 1
                        result.outcomes.append(ActionOutcome(action, "created"))
                    else:
                        result.skipped += 1
                        result.outcomes.append(ActionOutcome(action, "skipped", "Directory already exists"))
                else:
                    created = self._make_file(action.path)
                    if created:
                        result.created_files += 1
                        result.outcomes.append(ActionOutcome(action, "created"))
                    else:
                        result.skipped += 1
                        result.outcomes.append(ActionOutcome(action, "skipped", "File already exists (overwrite OFF)"))
            except Exception as exc:
                result.errors += 1
                result.outcomes.append(ActionOutcome(action, "error", str(exc)))

        return result

    def _make_dir(self, path: Path) -> bool:
        if path.exists():
            return False
        path.mkdir(parents=True, exist_ok=True)
        return True

    def _make_file(self, path: Path) -> bool:
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.exists() and not self.overwrite:
            return False

        suffix = path.suffix.lower()
        if suffix == ".md":
            content = "# Notes\n\nCreated by Studio Folder Builder.\n"
        elif suffix == ".json":
            content = "{\n  \n}\n"
        else:
            content = ""

        path.write_text(content, encoding="utf-8")
        return True
