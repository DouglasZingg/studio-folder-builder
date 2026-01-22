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
from builder.util.parse_input import parse_sequences_and_shots


@dataclass
class UiState:
    root_dir: Path | None = None
    project_name: str = ""
    template: TemplateInfo | None = None


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Studio Folder Builder")
        self.resize(1020, 760)

        self._state = UiState()
        self._templates: list[TemplateInfo] = []
        self._last_load: TemplateLoadResult | None = None

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

        # Project name
        self.project_edit = QLineEdit()
        self.project_edit.setPlaceholderText("MyShow")
        inputs_layout.addRow("Project:", self.project_edit)

        # Sequences/Shots input
        self.seq_shot_edit = QTextEdit()
        self.seq_shot_edit.setPlaceholderText(
            "Sequences/Shots (examples):\n"
            "SQ010: SH010, SH020, SH030\n"
            "SQ020: SH010\n\n"
            "OR:\n"
            "SQ010\n"
            "  SH010\n"
            "  SH020\n"
        )
        self.seq_shot_edit.setMinimumHeight(140)
        inputs_layout.addRow("Seq/Shots:", self.seq_shot_edit)

        # Options (overwrite later used on Day 4 builder)
        flags_row = QHBoxLayout()
        self.overwrite_checkbox = QCheckBox("Allow overwrite (unsafe)")
        self.overwrite_checkbox.setChecked(False)
        flags_row.addWidget(self.overwrite_checkbox)
        flags_row.addStretch(1)
        inputs_layout.addRow("Options:", flags_row)

        # Buttons
        btn_row = QHBoxLayout()
        self.preview_btn = QPushButton("Preview Plan")
        self.build_btn = QPushButton("Build (Day 4)")
        self.build_btn.setEnabled(False)  # still disabled; Day 4
        btn_row.addWidget(self.preview_btn)
        btn_row.addWidget(self.build_btn)
        btn_row.addStretch(1)
        root_layout.addLayout(btn_row)

        # Output
        root_layout.addWidget(QLabel("Output"))
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("Logs and preview output will appear here...")
        root_layout.addWidget(self.output, 1)

    def _wire_signals(self) -> None:
        self.root_browse_btn.clicked.connect(self._pick_root_dir)
        self.preview_btn.clicked.connect(self._on_preview_clicked)
        self.project_edit.textChanged.connect(self._on_project_changed)
        self.template_combo.currentIndexChanged.connect(self._on_template_changed)
        self.reload_templates_btn.clicked.connect(self._reload_templates)
        self.show_template_errors_btn.clicked.connect(self._show_template_errors_dialog)

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
        else:
            for t in self._templates:
                label = f"{t.name}  (v{t.version})"
                self.template_combo.addItem(label, t.template_id)
            self.template_combo.setCurrentIndex(0)
            self._state.template = self._templates[0]

        if problem_count > 0:
            self.template_warning_label.setText(f"{problem_count} template file(s) have errors and were skipped.")
            self.show_template_errors_btn.setEnabled(True)
        else:
            self.template_warning_label.setText("All templates loaded successfully.")
            self.show_template_errors_btn.setEnabled(False)

        self.template_combo.blockSignals(False)

        self._log(f"Templates dir: {self._templates_dir}")
        self._log(f"Loaded {len(self._templates)} valid template(s). Skipped {problem_count} file(s).")
        if self._state.template:
            self._log(f"Selected template: {self._state.template.name} (v{self._state.template.version})")

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
            return
        template_id = self.template_combo.itemData(idx)
        match = next((t for t in self._templates if t.template_id == template_id), None)
        self._state.template = match
        if match:
            self._log(f"Selected template: {match.name} (v{match.version})")

    # ---------------- State ----------------

    def _pick_root_dir(self) -> None:
        start_dir = str(self._state.root_dir) if self._state.root_dir else str(Path.home())
        picked = QFileDialog.getExistingDirectory(self, "Choose Root Directory", start_dir)
        if not picked:
            return
        self._state.root_dir = Path(picked)
        self.root_path_edit.setText(picked)
        self._log(f"Root set to: {picked}")

    def _on_project_changed(self, text: str) -> None:
        self._state.project_name = text.strip()

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
            self._log("X Cannot preview - fix the following:")
            for e in errors:
                self._log(f"  - {e}")
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

        self._log("Preview Plan (Day 3)")
        self._log(f"Project path: {(root_dir / self._state.project_name).as_posix()}")
        self._log(f"Template: {t.name} (v{t.version})")
        self._log(f"Sequences: {len(parsed.sequences)} | Shots: {sum(len(v) for v in parsed.sequences.values())}")
        self._log("")

        for action in plan:
            self._log(action.pretty())

        self._log("")
        self._log(f"Plan totals - folders/files: {len(plan)} (deduped).")
        self._log("Day 4 will execute this plan on disk (safe mode + overwrite option).")

    # ---------------- Logging ----------------

    def _log(self, msg: str) -> None:
        self.output.append(msg)
