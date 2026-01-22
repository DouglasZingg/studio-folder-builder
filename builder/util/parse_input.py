from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ParsedShotInput:
    sequences: Dict[str, List[str]]  # seq -> [shots]


_SEQ_LINE = re.compile(r"^\s*([A-Za-z0-9_\-]+)\s*:\s*(.+?)\s*$")


def parse_sequences_and_shots(text: str) -> ParsedShotInput:
    """
    Parses a multiline sequences/shots input.

    Supported formats:
      1) "SQ010: SH010, SH020"
      2) "SQ010" then indented shot lines below it

    Returns dict with unique, order-preserved shots per sequence.
    """
    sequences: Dict[str, List[str]] = {}
    current_seq: str | None = None

    lines = [ln.rstrip() for ln in (text or "").splitlines() if ln.strip()]

    for line in lines:
        m = _SEQ_LINE.match(line)
        if m:
            seq = m.group(1).strip()
            shots_part = m.group(2).strip()
            shots = _split_tokens(shots_part)
            sequences.setdefault(seq, [])
            _extend_unique(sequences[seq], shots)
            current_seq = seq
            continue

        # If it's not a "SEQ: ..." line, treat it as either a new seq or a shot under current seq
        if current_seq is None:
            # assume this is a sequence line
            seq = line.strip()
            sequences.setdefault(seq, [])
            current_seq = seq
        else:
            # treat as shot line under current_seq
            shot = line.strip()
            _extend_unique(sequences[current_seq], [shot])

    # prune empty
    sequences = {k: v for k, v in sequences.items() if k and v}
    return ParsedShotInput(sequences=sequences)


def _split_tokens(s: str) -> List[str]:
    # Split by comma or whitespace, preserve order, remove empties
    raw = re.split(r"[,\s]+", s.strip())
    return [t for t in (x.strip() for x in raw) if t]


def _extend_unique(dst: List[str], items: List[str]) -> None:
    seen = set(dst)
    for it in items:
        if it not in seen:
            dst.append(it)
            seen.add(it)
