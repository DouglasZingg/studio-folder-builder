# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class FlowCredentials:
    url: str
    script_name: str
    script_key: str
    project_id: int


class FlowClientError(RuntimeError):
    pass


class FlowClient:
    """
    Thin wrapper around the ShotGrid (Flow/PT) Python API.
    """

    def __init__(self, creds: FlowCredentials) -> None:
        self.creds = creds
        try:
            from shotgun_api3 import Shotgun  # type: ignore
        except Exception as exc:
            raise FlowClientError(
                "Flow/PT integration requires 'shotgun_api3'. Install it with: pip install shotgun_api3"
            ) from exc

        self._sg = Shotgun(creds.url, script_name=creds.script_name, api_key=creds.script_key)

    def fetch_sequences_and_shots(self) -> Dict[str, List[str]]:
        project = {"type": "Project", "id": self.creds.project_id}

        # Try to fetch sequences first
        seq_fields = ["id", "code"]
        seq_filters = [["project", "is", project]]
        sequences = self._sg.find("Sequence", seq_filters, seq_fields) or []

        seq_id_to_code: dict[int, str] = {}
        for s in sequences:
            sid = int(s["id"])
            code = str(s.get("code") or "").strip()
            if code:
                seq_id_to_code[sid] = code

        # Always fetch shots (some studios don't use Sequence entity)
        shot_fields = ["id", "code", "sg_sequence"]
        shot_filters = [["project", "is", project]]
        shots = self._sg.find("Shot", shot_filters, shot_fields) or []

        if not shots:
            return {}

        out: Dict[str, List[str]] = {}

        for sh in shots:
            code = str(sh.get("code") or "").strip()
            if not code:
                continue

            seq = sh.get("sg_sequence")
            seq_code = None

            # If sequence link exists and we have sequence codes
            if isinstance(seq, dict) and seq.get("id"):
                sid = int(seq["id"])
                seq_code = seq_id_to_code.get(sid)

            # If no sequence system, group under UNASSIGNED
            if not seq_code:
                seq_code = "UNASSIGNED"

            out.setdefault(seq_code, [])
            if code not in out[seq_code]:
                out[seq_code].append(code)

        for k in out:
            out[k].sort()

        return out

def format_seq_shots_text(data: Dict[str, List[str]]) -> str:
    lines: list[str] = []
    for seq in sorted(data.keys()):
        shots = data[seq]
        if not shots:
            continue
        lines.append(f"{seq}: {', '.join(shots)}")
    return "\n".join(lines).strip()
