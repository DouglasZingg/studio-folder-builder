from pathlib import Path

from builder.core.builder import PlanBuilder
from builder.models import PlanAction, PlanActionType


def test_builder_creates_dirs_and_files(tmp_path: Path):
    plan = [
        PlanAction(PlanActionType.DIR, tmp_path / "A"),
        PlanAction(PlanActionType.DIR, tmp_path / "A" / "B"),
        PlanAction(PlanActionType.FILE, tmp_path / "A" / "B" / "notes.md"),
        PlanAction(PlanActionType.FILE, tmp_path / "A" / "B" / "manifest.json"),
    ]

    builder = PlanBuilder(overwrite=False)
    result = builder.execute(plan)

    assert (tmp_path / "A").is_dir()
    assert (tmp_path / "A" / "B").is_dir()
    assert (tmp_path / "A" / "B" / "notes.md").is_file()
    assert (tmp_path / "A" / "B" / "manifest.json").is_file()

    assert result.created_dirs >= 2
    assert result.created_files >= 2
    assert result.errors == 0


def test_builder_skips_existing_files_when_no_overwrite(tmp_path: Path):
    file_path = tmp_path / "notes.md"
    file_path.write_text("ORIGINAL", encoding="utf-8")

    plan = [PlanAction(PlanActionType.FILE, file_path)]

    builder = PlanBuilder(overwrite=False)
    result = builder.execute(plan)

    assert file_path.read_text(encoding="utf-8") == "ORIGINAL"
    assert result.created_files == 0
    assert result.skipped == 1
    assert result.errors == 0


def test_builder_overwrites_when_enabled(tmp_path: Path):
    file_path = tmp_path / "notes.md"
    file_path.write_text("ORIGINAL", encoding="utf-8")

    plan = [PlanAction(PlanActionType.FILE, file_path)]

    builder = PlanBuilder(overwrite=True)
    result = builder.execute(plan)

    # builder writes default md starter content
    assert "Created by Studio Folder Builder" in file_path.read_text(encoding="utf-8")
    assert result.created_files == 1
    assert result.skipped == 0
    assert result.errors == 0
