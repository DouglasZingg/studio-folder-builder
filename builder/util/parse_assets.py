from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ParsedAssetInput:
    assets: Dict[str, List[str]]  # category -> [asset_names]


_CAT_LINE = re.compile(r"^\s*([A-Za-z0-9_\-]+)\s*:\s*(.+?)\s*$")


def parse_assets(text: str) -> ParsedAssetInput:
    assets: Dict[str, List[str]] = {}
    current_cat: str | None = None

    lines = [ln.rstrip() for ln in (text or "").splitlines() if ln.strip()]

    for line in lines:
        m = _CAT_LINE.match(line)
        if m:
            cat = m.group(1).strip()
            items = _split_tokens(m.group(2).strip())
            assets.setdefault(cat, [])
            _extend_unique(assets[cat], items)
            current_cat = cat
            continue

        if current_cat is None:
            cat = line.strip()
            assets.setdefault(cat, [])
            current_cat = cat
        else:
            item = line.strip()
            _extend_unique(assets[current_cat], [item])

    assets = {k: v for k, v in assets.items() if k and v}
    return ParsedAssetInput(assets=assets)


def _split_tokens(s: str) -> List[str]:
    raw = re.split(r"[,\s]+", s.strip())
    return [t for t in (x.strip() for x in raw) if t]


def _extend_unique(dst: List[str], items: List[str]) -> None:
    seen = set(dst)
    for it in items:
        if it not in seen:
            dst.append(it)
            seen.add(it)
