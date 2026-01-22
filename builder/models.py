from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class PlanActionType(str, Enum):
    DIR = "dir"
    FILE = "file"


@dataclass(frozen=True)
class PlanAction:
    type: PlanActionType
    path: Path

    def pretty(self) -> str:
        if self.type == PlanActionType.DIR:
            return f"Create folder: {self.path.as_posix()}"
        return f"Create file:   {self.path.as_posix()}"
