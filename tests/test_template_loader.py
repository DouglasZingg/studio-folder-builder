from pathlib import Path
import json

from builder.core.template_loader import TemplateLoader


def write_json(p: Path, obj) -> None:
    p.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def test_load_valid_template(tmp_path: Path):
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    write_json(
        templates_dir / "vfx.json",
        {
            "name": "VFX Default",
            "version": "1.0",
            "project_folders": ["assets", "sequences"],
            "shot_tree": {"docs": ["notes.md"]},
            "asset_tree": {"characters": ["work", "publish"]},
        },
    )

    loader = TemplateLoader(templates_dir)
    result = loader.load_all()

    assert len(result.templates) == 1
    assert result.templates[0].name == "VFX Default"
    assert result.problems == {}


def test_skip_invalid_template_missing_keys(tmp_path: Path):
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    write_json(templates_dir / "bad.json", {"name": "Bad", "version": "1.0"})

    loader = TemplateLoader(templates_dir)
    result = loader.load_all()

    assert len(result.templates) == 0
    assert "bad.json" in result.problems
    # at least one issue
    assert len(result.problems["bad.json"]) >= 1


def test_skip_invalid_json(tmp_path: Path):
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    (templates_dir / "broken.json").write_text("{ this is not json", encoding="utf-8")

    loader = TemplateLoader(templates_dir)
    result = loader.load_all()

    assert len(result.templates) == 0
    assert "broken.json" in result.problems
