from __future__ import annotations

from builder.core.builder import BuildResult


def format_build_summary(result: BuildResult) -> str:
    return (
        f"Build Summary:\n"
        f"  Created dirs:  {result.created_dirs}\n"
        f"  Created files: {result.created_files}\n"
        f"  Skipped:       {result.skipped}\n"
        f"  Errors:        {result.errors}\n"
    )
