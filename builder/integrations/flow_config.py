# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path

from builder.integrations.flow_client import FlowCredentials


def load_flow_credentials() -> FlowCredentials:
    """
    Priority:
      1) Environment variables:
         FLOW_URL, FLOW_SCRIPT_NAME, FLOW_SCRIPT_KEY, FLOW_PROJECT_ID
      2) JSON file: flow_config.json in repo root (next to main.py)
    """
    env_url = os.getenv("FLOW_URL")
    env_script = os.getenv("FLOW_SCRIPT_NAME")
    env_key = os.getenv("FLOW_SCRIPT_KEY")
    env_pid = os.getenv("FLOW_PROJECT_ID")

    if env_url and env_script and env_key and env_pid:
        return FlowCredentials(
            url=env_url.strip(),
            script_name=env_script.strip(),
            script_key=env_key.strip(),
            project_id=int(env_pid),
        )

    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "flow_config.json"
    if not path.exists():
        raise ValueError(
            "Missing Flow/PT credentials. Set env vars (FLOW_URL, FLOW_SCRIPT_NAME, FLOW_SCRIPT_KEY, FLOW_PROJECT_ID) "
            "or create flow_config.json in the repo root."
        )

    obj = json.loads(path.read_text(encoding="utf-8"))
    return FlowCredentials(
        url=str(obj["url"]).strip(),
        script_name=str(obj["script_name"]).strip(),
        script_key=str(obj["script_key"]).strip(),
        project_id=int(obj["project_id"]),
    )
