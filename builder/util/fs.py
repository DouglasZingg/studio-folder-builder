from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def open_in_file_explorer(path: Path) -> None:
    """
    Opens a folder in the OS file explorer.
    Works on Windows, macOS, Linux.
    """
    path = path.resolve()

    if not path.exists():
        raise FileNotFoundError(str(path))

    if sys.platform.startswith("win"):
        os.startfile(str(path))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)
