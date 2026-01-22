from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from builder.core.template_loader import TemplateInfo, TemplateLoader, TemplateLoadResult
from builder.core.planner import plan_shot_build
from builder.core.builder import PlanBuilder
from builder.core.reporting import format_build_summary
from builder.core.manifest import build_manifest, write_manifest
from builder.core.template_preview import format_template_preview
from builder.util.parse_input import parse_sequences_and_shots
from builder.util.fs import open_in_file_explorer
from builder.models import PlanAction


@dataclass
class UiState:
    root_dir: Path | None = None
    project_name: str = ""
    template: TemplateInfo | None = None


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Studio Folder Builder")
        self.resize(1120, 820)

        self._state = UiState()
        self._templates: list[TemplateInfo] = []
        self._last_load: TemplateLoadResult | None = None

        self._last_plan: list[PlanAction] = []
        self._last_sequences: dict[str, list[str]] = {}

        self._templates_dir = Path(__file__).resolve().parents[2] / "templates"
        self._loader = TemplateLoader(self._templates_dir)

        self._build_ui()
        self._wire_signals()
        self._reload_templates()

    # ---------------- UI ----------------

    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)

        # ---- Job setup group
        inputs_group = QGroupBox("Job Setup")
        root_layout.addWidget(inputs_group)

        inputs_layout = QFormLayout(inputs_group)
        inputs_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Root picker
        root_row = QHBoxLayout()
        self.root_path_edit = QLineEdit()
        self.root_path_edit.setPlaceholderText("Choose a root directory (e.g., D:/shows)")
        self.root_browse_btn = QPushButton("Browse...")
        root_row.addWidget(self.root_path_edit, 1)
        root_row.addWidget(self.root_browse_btn)
        inputs_layout.addRow("Root:", root_row)

        # Template row
        template_row = QHBoxLayout()
        self.template_combo = QComboBox()
        self.template_combo.setMinimumWidth(340)
        self.reload_templates_btn = QPushButton("Reload Templates")
        template_row.addWidget(self.template_combo, 1)
        template_row.addWidget(self.reload_templates_btn)
        inputs_layout.addRow("Template:", template_row)

        # Profile quick buttons
        profile_row = QHBoxLayout()
        self.profile_vfx_btn = QPushButton("VFX")
        self.profile_game_btn = QPushButton("Game")
        self.profile_anim_btn = QPushButton("Animation")
        profile_row.addWidget(QLabel("Quick Profiles:"))
        profile_row.addWidget(self.profile_vfx_btn)
        profile_row.addWidget(self.profile_game_btn)
        profile_row.addWidget(self.profile_anim_btn)
        profile_row.addStretch(1)
        inputs_layout.addRow("", profile_row)

        # Template warnings
        warn_row = QHBoxLayout()
        self.template_warning_label = QLabel("")
        self.template_warning_label.setWordWrap(True)
        self.template_warning_label.setStyleSheet("color: #b36b00;")
        self.show_template_errors_btn = QPushButton("Show Template Errors...")
        self.show_template_errors_btn.setEnabled(False)
        warn_row.addWidget(self.template_warning_label, 1)
        warn_row.addWidget(self.show_template_errors_btn)
        inputs_layout.addRow("Templates:", warn_row)

        # Project name + open folder
        proj_row = QHBoxLayout()
        self.project_edit = QLineEdit()
        self.project_edit.setPlaceholderText("MyShow")
        self.open_project_btn = QPushButton("Open Project Folder")
        self.open_project_btn.setEnabled(False)
        proj_row.addWidget(self.project_edit, 1)
        proj_row.addWidget(self.open_project_btn)
        inputs_layout.addRow("Project:", proj_row)

        # Sequences/Shots input + fill example
        seq_row = QHBoxLayout()
        self.seq_shot_edit = QTextEdit()
        self.seq_shot_edit.setPlaceholderText(
            "Sequences/Shots examples:\n"
            "SQ010: SH010, SH020, SH030\n"
            "SQ020: SH010\n"
        )
        self.seq_shot_edit.setMinimumHeight(140)
        self.fill_example_btn = QPushButton("Fill Example")
        seq_row.addWidget(self.seq_shot_edit, 1)
        seq_row.addWidget(self.fill_example_btn)
        inputs_layout.addRow("Seq/Shots:", seq_row)

        # Options
        flags_row = QHBoxLayout()
        self.overwrite_checkbox = QCheckBox("Allow overwrite (unsafe)")
        self.overwrite_checkbox.setChecked(False)
        flags_row.addWidget(self.overwrite_checkbox)
        flags_row.addStretch(1)
        inputs_layout.addRow("Options:", flags_row)

        # Buttons
        btn_row = QHBoxLayout()
        self.preview_btn = QPushButton("Preview Plan")
        self.build_btn = QPushButton("Build")
        self.build_btn.setEnabled(False)
        btn_row.addWidget(self.preview_btn)
        btn_row.addWidget(self.build_btn)
        btn_row.addStretch(1)
        root_layout.addLayout(btn_row)

        # ---- Template preview panel
        root_layout.addWidget(QLabel("Template Preview"))
        self.template_preview = QTextEdit()
        self.template_preview.setReadOnly(True)
        self.template_preview.setMinimumHeight(180)
        root_layout.addWidget(self.template_preview)

        # ---- Output panel
        root_layout.addWidget(QLabel("Output"))
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("Logs and preview output will appear here...")
        root_layout.addWidget(self.output, 1)

    def _wire_signals(self) -> None:
        self.root_browse_btn.clicked.connect(self._pick_root_dir)

        self.preview_btn.clicked.connect(self._on_preview_clicked)
        self.build_btn.clicked.connect(self._on_build_clicked)
        self.open_project_btn.clicked.connect(self._open_project_folder)

        self.project_edit.textChanged.connect(self._on_project_changed)
        self.template_combo.currentIndexChanged.connect(self._on_template_changed)

        self.reload_templates_btn.clicked.connect(self._reload_templates)
        self.show_template_errors_btn.clicked.connect(self._show_template_errors_dialog)

        self.profile_vfx_btn.clicked.connect(lambda: self._select_profile("vfx"))
        self.profile_game_btn.clicked.connect(lambda: self._select_profile("game"))
        self.profile_anim_btn.clicked.connect(lambda: self._select_profile("animation"))

        self.fill_example_btn.clicked.connect(self._fill_example)

    # ---------------- Templates ----------------

    def _reload_templates(self) -> None:
        self.template_combo.blockSignals(True)
        self.template_combo.clear()

        self._last_load = self._loader.load_all()
        self._templates = self._last_load.templates

        problems = self._last_load.problems
        problem_count = len(problems)

        if not self._templates:
            self.template_combo.addItem("No valid templates found", None)
            self._state.template = None
            self.template_preview.setPlainText("")
        else:
            for t in self._templates:
                label = f"{t.name}  (v{t.version})"
                self.template_combo.addItem(label, t.template_id)
            self.template_combo.setCurrentIndex(0)
            self._state.template = self._templates[0]
            self._refresh_template_preview()

        if problem_count > 0:
            self.template_warning_label.setText(f"{problem_count} template file(s) have errors and were skipped.")
            self.show_template_errors_btn.setEnabled(True)
        else:
            self.template_warning_label.setText("All templates loaded successfully.")
            self.show_template_errors_btn.setEnabled(False)

        self.template_combo.blockSignals(False)

        # reset plan/build
        self._last_plan = []
        self._last_sequences = {}
        self.build_btn.setEnabled(False)
        self.open_project_btn.setEnabled(False)

        self._log(f"Templates dir: {self._templates_dir}")
        self._log(f"Loaded {len(self._templates)} valid template(s). Skipped {problem_count} file(s).")
        if self._state.template:
            self._log(f"Selected template: {self._state.template.name} (v{self._state.template.version})")

    def _refresh_template_preview(self) -> None:
        t = self._state.template
        if not t:
            self.template_preview.setPlainText("")
            return
        self.template_preview.setPlainText(format_template_preview(t.raw))

    def _show_template_errors_dialog(self) -> None:
        if not self._last_load:
            return
        problems = self._last_load.problems
        if not problems:
            QMessageBox.information(self, "Template Errors", "No template errors.")
            return

        lines: list[str] = []
        for filename, issues in problems.items():
            lines.append(f"{filename}")
            for issue in issues:
                lines.append(f"  - {issue.pretty()}")
            lines.append("")
        msg = "\n".join(lines).strip()

        box = QMessageBox(self)
        box.setWindowTitle("Template Errors")
        box.setIcon(QMessageBox.Icon.Warning)
        box.setText("Some templates could not be loaded and were skipped.")
        box.setDetailedText(msg)
        box.exec()

    def _on_template_changed(self, idx: int) -> None:
        if idx < 0 or not self._templates:
            self._state.template = None
            self._refresh_template_preview()
            return
        template_id = self.template_combo.itemData(idx)
        match = next((t for t in self._templates if t.template_id == template_id), None)
        self._state.template = match
        if match:
            self._log(f"Selected template: {match.name} (v{match.version})")
        self._refresh_template_preview()

        # changing template invalidates plan
        self._last_plan = []
        self._last_sequences = {}
        self.build_btn.setEnabled(False)

    def _select_profile(self, keyword: str) -> None:
        """
        Selects the first template where either:
          - filename contains keyword, OR
          - name contains keyword
        """
        keyword = keyword.lower().strip()
        if not self._templates:
            return

        best_idx = None
        for i, t in enumerate(self._templates):
            if keyword in t.template_id.lower() or keyword in t.name.lower():
                best_idx = i
                break

        if best_idx is None:
            self._log(f"?No template matched profile '{keyword}'.")
            return

        self.template_combo.setCurrentIndex(best_idx)
        self._log(f"Profile selected: {keyword}")

    # ---------------- State ----------------

    def _pick_root_dir(self) -> None:
        start_dir = str(self._state.root_dir) if self._state.root_dir else str(Path.home())
        picked = QFileDialog.getExistingDirectory(self, "Choose Root Directory", start_dir)
        if not picked:
            return
        self._state.root_dir = Path(picked)
        self.root_path_edit.setText(picked)
        self._log(f"Root set to: {picked}")

        self._invalidate_plan()

    def _on_project_changed(self, text: str) -> None:
        self._state.project_name = text.strip()
        self._invalidate_plan()

    def _invalidate_plan(self) -> None:
        self._last_plan = []
        self._last_sequences = {}
        self.build_btn.setEnabled(False)
        self.open_project_btn.setEnabled(False)

    def _fill_example(self) -> None:
        self.seq_shot_edit.setPlainText(
            "SQ010: SH010, SH020, SH030\n"
            "SQ020: SH010\n"
        )
        self._log("Inserted example Seq/Shots input.")

    # ---------------- Actions ----------------

    def _on_preview_clicked(self) -> None:
        root_text = self.root_path_edit.text().strip()
        root_dir = Path(root_text) if root_text else None
        self._state.root_dir = root_dir

        errors: list[str] = []
        if not root_dir:
            errors.append("Root directory is required.")
        if not self._state.project_name:
            errors.append("Project name is required.")
        if not self._state.template:
            errors.append("A valid template must be selected.")

        parsed = parse_sequences_and_shots(self.seq_shot_edit.toPlainText())
        if not parsed.sequences:
            errors.append("Seq/Shots input is required (at least one sequence with shots).")

        if errors:
            self._log("Cannot preview - fix the following:")
            for e in errors:
                self._log(f"  - {e}")
            self._invalidate_plan()
            return

        t = self._state.template
        assert t is not None
        assert root_dir is not None

        plan = plan_shot_build(
            root=root_dir,
            project=self._state.project_name,
            template_raw=t.raw,
            sequences=parsed.sequences,
        )
        self._last_plan = plan
        self._last_sequences = parsed.sequences

        self.build_btn.setEnabled(True)

        # Open Project Folder button becomes available after preview
        project_root = root_dir / self._state.project_name
        self.open_project_btn.setEnabled(project_root.exists() or True)

        self._log("Preview Plan (Day 6)")
        self._log(f"Project path: {project_root.as_posix()}")
        self._log(f"Template: {t.name} (v{t.version})")
        self._log(f"Sequences: {len(parsed.sequences)} | Shots: {sum(len(v) for v in parsed.sequences.values())}")
        self._log("")

        for action in plan:
            self._log(action.pretty())

        self._log("")
        self._log(f"Plan totals - folders/files: {len(plan)} (deduped).")
        self._log("Click Build to create this structure on disk.")

    def _on_build_clicked(self) -> None:
        if not self._last_plan:
            self._log("No plan available. Click Preview Plan first.")
            self.build_btn.setEnabled(False)
            return

        overwrite = self.overwrite_checkbox.isChecked()
        builder = PlanBuilder(overwrite=overwrite)

        self._log("")
        self._log(f"Building... (overwrite={'ON' if overwrite else 'OFF'})")

        result = builder.execute(self._last_plan)

        self._log("")
        self._log(format_build_summary(result))

        # Manifest
        root_dir = self._state.root_dir
        t = self._state.template
        if root_dir and t:
            project_root = root_dir / self._state.project_name
            rec = build_manifest(
                project_root=project_root,
                template_name=t.name,
                template_version=t.version,
                template_raw=t.raw,
                sequences=self._last_sequences,
                result=result,
            )
            manifest_path = write_manifest(rec)
            self._log(f"Manifest written: {manifest_path.as_posix()}")

        self._log("Build finished.")

    def _open_project_folder(self) -> None:
        root_text = self.root_path_edit.text().strip()
        if not root_text:
            return
        root_dir = Path(root_text)
        project = self.project_edit.text().strip()
        if not project:
            return

        project_root = root_dir / project
        try:
            project_root.mkdir(parents=True, exist_ok=True)
            open_in_file_explorer(project_root)
            self._log(f"Opened: {project_root.as_posix()}")
        except Exception as exc:
            QMessageBox.warning(self, "Open Folder Failed", str(exc))

    # ---------------- Logging ----------------

    def _log(self, msg: str) -> None:
        self.output.append(msg)
