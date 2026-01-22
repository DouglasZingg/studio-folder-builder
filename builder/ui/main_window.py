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
from builder.core.planner import plan_shot_build, plan_asset_build
from builder.core.builder import PlanBuilder
from builder.core.reporting import format_build_summary
from builder.core.manifest import build_manifest, write_manifest
from builder.core.template_preview import format_template_preview
from builder.util.parse_input import parse_sequences_and_shots
from builder.util.parse_assets import parse_assets
from builder.util.fs import open_in_file_explorer
from builder.models import PlanAction
from PySide6.QtWidgets import QDialog
from builder.core.job_config import (
    make_job_config,
    write_job_config,
    read_job_config,
    config_to_text_for_ui,
)
from PySide6.QtCore import QObject, QThread, Signal
from builder.integrations.flow_client import FlowClient, format_seq_shots_text
from builder.integrations.flow_config import load_flow_credentials

@dataclass
class UiState:
    root_dir: Path | None = None
    project_name: str = ""
    template: TemplateInfo | None = None
    mode: str = "shots"  # "shots" | "assets"

class FlowWorker(QObject):
    finished = Signal(dict)      # sequences dict
    failed = Signal(str)

    def run(self) -> None:
        try:
            creds = load_flow_credentials()
            client = FlowClient(creds)
            data = client.fetch_sequences_and_shots()
            self.finished.emit(data)
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Studio Folder Builder")
        self.resize(1180, 880)

        self._state = UiState()
        self._templates: list[TemplateInfo] = []
        self._last_load: TemplateLoadResult | None = None

        self._last_plan: list[PlanAction] = []
        self._last_sequences: dict[str, list[str]] | None = None
        self._last_assets: dict[str, list[str]] | None = None

        self._templates_dir = Path(__file__).resolve().parents[2] / "templates"
        self._loader = TemplateLoader(self._templates_dir)

        self._build_ui()
        self._wire_signals()
        self._reload_templates()
        self._apply_mode_visibility()

    # ---------------- UI ----------------

    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)

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
        self.reload_templates_btn = QPushButton("Reload Templates")
        template_row.addWidget(self.template_combo, 1)
        template_row.addWidget(self.reload_templates_btn)
        inputs_layout.addRow("Template:", template_row)

        # Mode row
        mode_row = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Shots Mode (Sequences/Shots)", "shots")
        self.mode_combo.addItem("Assets Mode (Categories/Assets)", "assets")
        mode_row.addWidget(self.mode_combo, 1)
        inputs_layout.addRow("Mode:", mode_row)

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

        # Project row + open folder
        proj_row = QHBoxLayout()
        self.project_edit = QLineEdit()
        self.project_edit.setPlaceholderText("MyShow")
        self.open_project_btn = QPushButton("Open Project Folder")
        self.open_project_btn.setEnabled(False)
        proj_row.addWidget(self.project_edit, 1)
        proj_row.addWidget(self.open_project_btn)
        inputs_layout.addRow("Project:", proj_row)

        # Shots input
        shots_row = QHBoxLayout()
        self.seq_shot_edit = QTextEdit()
        self.seq_shot_edit.setMinimumHeight(130)
        self.seq_shot_edit.setPlaceholderText("SQ010: SH010, SH020\nSQ020: SH010\n")
        self.fill_shots_example_btn = QPushButton("Fill Example")
        shots_row.addWidget(self.seq_shot_edit, 1)
        shots_row.addWidget(self.fill_shots_example_btn)
        self.shots_row_widget = QWidget()
        self.shots_row_widget.setLayout(shots_row)
        inputs_layout.addRow("Seq/Shots:", self.shots_row_widget)

        # Assets input
        assets_row = QHBoxLayout()
        self.assets_edit = QTextEdit()
        self.assets_edit.setMinimumHeight(130)
        self.assets_edit.setPlaceholderText("characters: Hero, Villain\nprops: Sword, Shield\n")
        self.fill_assets_example_btn = QPushButton("Fill Example")
        assets_row.addWidget(self.assets_edit, 1)
        assets_row.addWidget(self.fill_assets_example_btn)
        self.assets_row_widget = QWidget()
        self.assets_row_widget.setLayout(assets_row)
        inputs_layout.addRow("Assets:", self.assets_row_widget)

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
        flow_row = QHBoxLayout()
        self.load_flow_btn = QPushButton("Load Seq/Shots from Flow/PT")
        flow_row.addWidget(self.load_flow_btn)
        flow_row.addStretch(1)
        root_layout.addLayout(flow_row)


        # Config buttons
        cfg_row = QHBoxLayout()
        self.save_config_btn = QPushButton("Save Config...")
        self.load_config_btn = QPushButton("Load Config...")
        cfg_row.addWidget(self.save_config_btn)
        cfg_row.addWidget(self.load_config_btn)
        cfg_row.addStretch(1)
        root_layout.addLayout(cfg_row)

        # Template preview
        root_layout.addWidget(QLabel("Template Preview"))
        self.template_preview = QTextEdit()
        self.template_preview.setReadOnly(True)
        self.template_preview.setMinimumHeight(170)
        root_layout.addWidget(self.template_preview)

        # Output
        root_layout.addWidget(QLabel("Output"))
        self.output = QTextEdit()
        self.output.setReadOnly(True)
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

        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        self.fill_shots_example_btn.clicked.connect(self._fill_shots_example)
        self.fill_assets_example_btn.clicked.connect(self._fill_assets_example)

        self.save_config_btn.clicked.connect(self._on_save_config)
        self.load_config_btn.clicked.connect(self._on_load_config)

        self.load_flow_btn.clicked.connect(self._on_load_flow_clicked)

    # ---------------- Mode ----------------

    def _on_mode_changed(self) -> None:
        self._state.mode = str(self.mode_combo.currentData())
        self._apply_mode_visibility()
        self._invalidate_plan()
        self._log(f"Mode set to: {self._state.mode}")

    def _apply_mode_visibility(self) -> None:
        is_shots = self._state.mode == "shots"
        self.shots_row_widget.setVisible(is_shots)
        self.assets_row_widget.setVisible(not is_shots)
        self.load_flow_btn.setEnabled(self._state.mode == "shots")

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
                self.template_combo.addItem(f"{t.name} (v{t.version})", t.template_id)
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

        self._invalidate_plan()
        self._log(f"Loaded {len(self._templates)} valid template(s). Skipped {problem_count} file(s).")

    def _refresh_template_preview(self) -> None:
        t = self._state.template
        self.template_preview.setPlainText(format_template_preview(t.raw) if t else "")

    def _show_template_errors_dialog(self) -> None:
        if not self._last_load:
            return
        problems = self._last_load.problems
        if not problems:
            QMessageBox.information(self, "Template Errors", "No template errors.")
            return

        lines: list[str] = []
        for filename, issues in problems.items():
            lines.append(filename)
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
            self._invalidate_plan()
            return
        template_id = self.template_combo.itemData(idx)
        self._state.template = next((t for t in self._templates if t.template_id == template_id), None)
        self._refresh_template_preview()
        self._invalidate_plan()

    # ---------------- State ----------------

    def _pick_root_dir(self) -> None:
        start_dir = str(self._state.root_dir) if self._state.root_dir else str(Path.home())
        picked = QFileDialog.getExistingDirectory(self, "Choose Root Directory", start_dir)
        if not picked:
            return
        self._state.root_dir = Path(picked)
        self.root_path_edit.setText(picked)
        self._invalidate_plan()

    def _on_project_changed(self, text: str) -> None:
        self._state.project_name = text.strip()
        self._invalidate_plan()

    def _invalidate_plan(self) -> None:
        self._last_plan = []
        self._last_sequences = None
        self._last_assets = None
        self.build_btn.setEnabled(False)
        self.open_project_btn.setEnabled(False)

    def _fill_shots_example(self) -> None:
        self.seq_shot_edit.setPlainText("SQ010: SH010, SH020\nSQ020: SH010\n")

    def _fill_assets_example(self) -> None:
        self.assets_edit.setPlainText("characters: Hero, Villain\nprops: Sword, Shield\nenvironments: City\n")

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

        t = self._state.template
        if errors:
            self._log("Cannot preview - fix the following:")
            for e in errors:
                self._log(f"  - {e}")
            self._invalidate_plan()
            return

        assert t is not None
        assert root_dir is not None

        project_root = root_dir / self._state.project_name

        if self._state.mode == "shots":
            parsed = parse_sequences_and_shots(self.seq_shot_edit.toPlainText())
            if not parsed.sequences:
                self._log("Seq/Shots input is required (at least one sequence with shots).")
                self._invalidate_plan()
                return

            plan = plan_shot_build(root_dir, self._state.project_name, t.raw, parsed.sequences)
            self._last_sequences = parsed.sequences
            self._last_assets = None

            self._log("Preview Plan (Shots Mode)")
            self._log(f"Project path: {project_root.as_posix()}")
            self._log(f"Sequences: {len(parsed.sequences)} | Shots: {sum(len(v) for v in parsed.sequences.values())}")

        else:
            parsed = parse_assets(self.assets_edit.toPlainText())
            if not parsed.assets:
                self._log("Assets input is required (at least one category with assets).")
                self._invalidate_plan()
                return

            plan = plan_asset_build(root_dir, self._state.project_name, t.raw, parsed.assets)
            self._last_assets = parsed.assets
            self._last_sequences = None

            self._log("Preview Plan (Assets Mode)")
            self._log(f"Project path: {project_root.as_posix()}")
            self._log(f"Categories: {len(parsed.assets)} | Assets: {sum(len(v) for v in parsed.assets.values())}")

        self._last_plan = plan
        self.build_btn.setEnabled(True)
        self.open_project_btn.setEnabled(True)

        self._log(f"Template: {t.name} (v{t.version})")
        self._log("")
        for action in plan:
            self._log(action.pretty())
        self._log("")
        self._log(f"Plan totals - folders/files: {len(plan)} (deduped).")

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
                mode=self._state.mode,
                sequences=self._last_sequences,
                assets=self._last_assets,
                result=result,
            )
            manifest_path = write_manifest(rec)
            self._log(f"Manifest written: {manifest_path.as_posix()}")

        self._log("Build finished.")

    def _open_project_folder(self) -> None:
        root_text = self.root_path_edit.text().strip()
        project = self.project_edit.text().strip()
        if not root_text or not project:
            return
        project_root = Path(root_text) / project
        try:
            project_root.mkdir(parents=True, exist_ok=True)
            open_in_file_explorer(project_root)
        except Exception as exc:
            QMessageBox.warning(self, "Open Folder Failed", str(exc))

    # ---------------- Logging ----------------

    def _log(self, msg: str) -> None:
        self.output.append(msg)

    def _on_save_config(self) -> None:
        root_text = self.root_path_edit.text().strip()
        project = self.project_edit.text().strip()
        t = self._state.template

        if not root_text or not project or not t:
            QMessageBox.warning(self, "Save Config", "Root, Project, and Template must be set before saving.")
            return

        root_dir = Path(root_text)
        overwrite = self.overwrite_checkbox.isChecked()

        # Determine payload based on mode
        sequences = self._last_sequences if self._state.mode == "shots" else None
        assets = self._last_assets if self._state.mode == "assets" else None

        # If user hasn't previewed yet, parse directly from UI so save still works
        if self._state.mode == "shots" and not sequences:
            parsed = parse_sequences_and_shots(self.seq_shot_edit.toPlainText())
            sequences = parsed.sequences if parsed.sequences else None

        if self._state.mode == "assets" and not assets:
            parsed = parse_assets(self.assets_edit.toPlainText())
            assets = parsed.assets if parsed.assets else None

        if self._state.mode == "shots" and not sequences:
            QMessageBox.warning(self, "Save Config", "Shots mode requires at least one sequence with shots.")
            return

        if self._state.mode == "assets" and not assets:
            QMessageBox.warning(self, "Save Config", "Assets mode requires at least one category with assets.")
            return

        cfg = make_job_config(
            root=root_dir,
            project=project,
            template_id=t.template_id,
            mode=self._state.mode,
            overwrite=overwrite,
            sequences=sequences,
            assets=assets,
        )

        default_path = (root_dir / project / "production" / "job_config.json").as_posix()
        path_str, _ = QFileDialog.getSaveFileName(self, "Save Job Config", default_path, "JSON Files (*.json)")
        if not path_str:
            return

        try:
            out_path = write_job_config(Path(path_str), cfg)
            self._log(f"Config saved: {out_path.as_posix()}")
        except Exception as exc:
            QMessageBox.warning(self, "Save Config Failed", str(exc))


    def _on_load_config(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(self, "Load Job Config", "", "JSON Files (*.json)")
        if not path_str:
            return

        try:
            cfg = read_job_config(Path(path_str))
        except Exception as exc:
            QMessageBox.warning(self, "Load Config Failed", str(exc))
            return

        # Apply basic fields
        self.root_path_edit.setText(cfg.root)
        self.project_edit.setText(cfg.project)
        self.overwrite_checkbox.setChecked(cfg.overwrite)

        # Apply mode
        self._state.mode = cfg.mode
        idx = self.mode_combo.findData(cfg.mode)
        if idx >= 0:
            self.mode_combo.setCurrentIndex(idx)
        self._apply_mode_visibility()

        # Select template by template_id
        if self._templates:
            match_idx = None
            for i, t in enumerate(self._templates):
                if t.template_id == cfg.template_id:
                    match_idx = i
                    break
            if match_idx is not None:
                self.template_combo.setCurrentIndex(match_idx)

        # Fill the correct multiline input
        text = config_to_text_for_ui(cfg)
        if cfg.mode == "shots":
            self.seq_shot_edit.setPlainText(text)
            self._last_sequences = cfg.sequences
            self._last_assets = None
        else:
            self.assets_edit.setPlainText(text)
            self._last_assets = cfg.assets
            self._last_sequences = None

        # Plan invalidated until preview is clicked
        self._invalidate_plan()
        self._log(f"Config loaded: {path_str}")
        self._log("Click Preview Plan to regenerate the plan from the loaded config.")

    def _on_load_flow_clicked(self) -> None:
        if self._state.mode != "shots":
            QMessageBox.information(self, "Flow/PT", "Switch to Shots Mode to load sequences/shots from Flow/PT.")
            return

        # UI hint
        self._log("Loading sequences/shots from Flow/PT...")

        # Thread setup
        self._flow_thread = QThread(self)  # keep refs on self to avoid GC
        self._flow_worker = FlowWorker()
        self._flow_worker.moveToThread(self._flow_thread)

        self._flow_thread.started.connect(self._flow_worker.run)
        self._flow_worker.finished.connect(self._on_flow_loaded)
        self._flow_worker.failed.connect(self._on_flow_failed)

        # Ensure cleanup
        self._flow_worker.finished.connect(self._flow_thread.quit)
        self._flow_worker.failed.connect(self._flow_thread.quit)
        self._flow_thread.finished.connect(self._flow_worker.deleteLater)
        self._flow_thread.finished.connect(self._flow_thread.deleteLater)

        self._load_flow_btn_state(True)
        self._flow_thread.start()


    def _load_flow_btn_state(self, busy: bool) -> None:
        self.load_flow_btn.setEnabled(not busy)
        self.load_flow_btn.setText("Loading..." if busy else "Load Seq/Shots from Flow/PT")


    def _on_flow_loaded(self, data: dict) -> None:
        self._load_flow_btn_state(False)

        if not data:
            self._log("Flow/PT returned no sequences/shots (check project_id or permissions).")
            return

        # Fill the text box with formatted output
        text = format_seq_shots_text(data)
        self.seq_shot_edit.setPlainText(text)

        # Invalidate plan; user should preview again
        self._invalidate_plan()
        self._log(f"Loaded from Flow/PT: {len(data)} sequence(s). Click Preview Plan.")


    def _on_flow_failed(self, msg: str) -> None:
        self._load_flow_btn_state(False)
        QMessageBox.warning(self, "Flow/PT Load Failed", msg)
        self._log(f"Flow/PT load failed: {msg}")
