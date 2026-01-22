from __future__ import annotations

from typing import Any


def format_template_preview(template_raw: dict[str, Any]) -> str:
    """
    Produces a human-readable preview of the template contents.
    """
    lines: list[str] = []

    name = template_raw.get("name", "Unnamed Template")
    version = template_raw.get("version", "0.0")
    lines.append(f"{name} (v{version})")
    lines.append("-" * 40)

    pf = template_raw.get("project_folders", [])
    lines.append("Project folders:")
    if pf:
        for item in pf:
            lines.append(f"  - {item}")
    else:
        lines.append("  (none)")
    lines.append("")

    lines.append("Shot tree:")
    st = template_raw.get("shot_tree", {})
    if isinstance(st, dict) and st:
        for k, v in st.items():
            lines.append(f"  {k}/")
            if isinstance(v, list) and v:
                for child in v:
                    lines.append(f"    - {child}")
            else:
                lines.append("    (empty)")
    else:
        lines.append("  (none)")
    lines.append("")

    lines.append("Asset tree:")
    at = template_raw.get("asset_tree", {})
    if isinstance(at, dict) and at:
        for k, v in at.items():
            lines.append(f"  {k}/")
            if isinstance(v, list):
                for child in v:
                    lines.append(f"    - {child}")
            elif isinstance(v, dict):
                for kk, vv in v.items():
                    lines.append(f"    {kk}/")
                    if isinstance(vv, list) and vv:
                        for child in vv:
                            lines.append(f"      - {child}")
                    else:
                        lines.append("      (empty)")
            else:
                lines.append("    (invalid)")
    else:
        lines.append("  (none)")

    return "\n".join(lines).strip()
