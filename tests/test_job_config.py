import json
from pathlib import Path

from builder.core.job_config import make_job_config, write_job_config, read_job_config


def test_job_config_roundtrip_shots(tmp_path: Path):
    cfg = make_job_config(
        root=tmp_path,
        project="MyShow",
        template_id="vfx_default",
        mode="shots",
        overwrite=False,
        sequences={"SQ010": ["SH010", "SH020"]},
        assets=None,
    )

    path = tmp_path / "job_config.json"
    write_job_config(path, cfg)
    loaded = read_job_config(path)

    assert loaded.mode == "shots"
    assert loaded.sequences is not None
    assert loaded.sequences["SQ010"] == ["SH010", "SH020"]


def test_job_config_roundtrip_assets(tmp_path: Path):
    cfg = make_job_config(
        root=tmp_path,
        project="MyGame",
        template_id="game_default",
        mode="assets",
        overwrite=True,
        sequences=None,
        assets={"characters": ["Hero"], "props": ["Sword"]},
    )

    path = tmp_path / "job_config_assets.json"
    write_job_config(path, cfg)
    loaded = read_job_config(path)

    assert loaded.mode == "assets"
    assert loaded.assets is not None
    assert loaded.assets["characters"] == ["Hero"]


def test_job_config_missing_required_key(tmp_path: Path):
    bad = {
        "tool": "Studio Folder Builder",
        "version": "0.8.0",
        "timestamp": "2026-01-01T00:00:00Z",
        # missing root
        "project": "MyShow",
        "template_id": "vfx_default",
        "mode": "shots",
        "overwrite": False,
        "sequences": {"SQ010": ["SH010"]},
        "assets": None,
    }

    path = tmp_path / "bad.json"
    path.write_text(json.dumps(bad, indent=2), encoding="utf-8")

    try:
        read_job_config(path)
        assert False, "Should have raised ValueError"
    except ValueError:
        assert True
