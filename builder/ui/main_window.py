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
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from builder.core.template_loader import TemplateInfo, TemplateLoader


@dataclass
class UiState:
    root_dir: Path | None = None
    project_name: str = ""
    template: TemplateInfo | None = None


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Studio Folder Builder")
        self.resize(980, 640)

        self._state = UiState()
        self._templates: list[TemplateInfo] = []

        self._templates_dir = Path(__file__).resolve().parents[2] / "templates"
        self._loader = TemplateLoader(self._templates_dir)

        self._build_ui()
        self._wire_signals()
        self._load_templates_into_dropdown()

    # ---------------- UI ----------------

    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)

        # Top: Inputs
        inputs_group = QGroupBox("Job Setup")
        root_layout.addWidget(inputs_group)

        inputs_layout = QFormLayout(inputs_group)
        inputs_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Root picker row
        root_row = QHBoxLayout()
        self.root_path_edit = QLineEdit()
        self.root_path_edit.setPlaceholderText("Choose a root directory (e.g., D:/shows)")
        self.root_browse_btn = QPushButton("Browse...")
        root_row.addWidget(self.root_path_edit, 1)
        root_row.addWidget(self.root_browse_btn)
        inputs_layout.addRow("Root:", root_row)

        # Template dropdown
        self.template_combo = QComboBox()
        self.template_combo.setMinimumWidth(340)
        inputs_layout.addRow("Template:", self.template_combo)

        # Project name
        self.project_edit = QLineEdit()
        self.project_edit.setPlaceholderText("MyShow")
        inputs_layout.addRow("Project:", self.project_edit)

        # Safe mode / overwrite (placeholder behavior for Day 1)
        flags_row = QHBoxLayout()
        self.overwrite_checkbox = QCheckBox("Allow overwrite (unsafe)")
        self.overwrite_checkbox.setChecked(False)
        flags_row.addWidget(self.overwrite_checkbox)
        flags_row.addStretch(1)
        inputs_layout.addRow("Options:", flags_row)

        # Buttons row
        btn_row = QHBoxLayout()
        self.preview_btn = QPushButton("Preview Plan")
        self.build_btn = QPushButton("Build (disabled Day 1)")
        self.build_btn.setEnabled(False)  # Day 1 only
        btn_row.addWidget(self.preview_btn)
        btn_row.addWidget(self.build_btn)
        btn_row.addStretch(1)
        root_layout.addLayout(btn_row)

        # Bottom: Log / Output
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("Preview output will appear here...")
        root_layout.addWidget(QLabel("Output"))
        root_layout.addWidget(self.output, 1)

    def _wire_signals(self) -> None:
        self.root_browse_btn.clicked.connect(self._pick_root_dir)
        self.preview_btn.clicked.connect(self._on_preview_clicked)
        self.project_edit.textChanged.connect(self._on_project_changed)
        self.template_combo.currentIndexChanged.connect(self._on_template_changed)

    # ---------------- Template loading ----------------

    def _load_templates_into_dropdown(self) -> None:
        self.template_combo.clear()
        self._templates, errors = self._loader.load_all()

        if errors:
            self._log("Template load warnings:")
            for e in errors:
                self._log(f"  - {e}")

        if not self._templates:
            self.template_combo.addItem("No templates found (add JSON to /templates)", None)
            self._state.template = None
            self._log(f"No templates discovered in: {self._templates_dir}")
            return

        for t in self._templates:
            label = f"{t.name}  (v{t.version})"
            self.template_combo.addItem(label, t.template_id)

        # select first template by default
        self.template_combo.setCurrentIndex(0)
        self._state.template = self._templates[0]
        self._log(f"Loaded {len(self._templates)} template(s) from {self._templates_dir}")

    def _on_template_changed(self, idx: int) -> None:
        if idx < 0 or not self._templates:
            self._state.template = None
            return

        template_id = self.template_combo.itemData(idx)
        match = next((t for t in self._templates if t.template_id == template_id), None)
        self._state.template = match
        if match:
            self._log(f"Selected template: {match.name} (v{match.version})")

    # ---------------- State changes ----------------

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
        # Day 1: placeholder “plan” — just validates inputs and logs intent.
        root_text = self.root_path_edit.text().strip()
        root_dir = Path(root_text) if root_text else None
        self._state.root_dir = root_dir

        errors: list[str] = []
        if not root_dir:
            errors.append("Root directory is required.")
        if not self._state.project_name:
            errors.append("Project name is required.")
        if not self._state.template:
            errors.append("A template must be selected.")

        if errors:
            self._log("X Cannot preview - fix the following:")
            for e in errors:
                self._log(f"  - {e}")
            return

        t = self._state.template
        assert t is not None

        project_path = root_dir / self._state.project_name
        self._log("Preview (Day 1 placeholder)")
        self._log(f"Root:    {root_dir}")
        self._log(f"Project: {self._state.project_name}")
        self._log(f"Path:    {project_path}")
        self._log(f"Template:{t.name} (v{t.version})")
        self._log("")
        self._log("Next (Day 3) the preview will list every folder/file to be created.")

    # ---------------- Logging ----------------

    def _log(self, msg: str) -> None:
        self.output.append(msg)
