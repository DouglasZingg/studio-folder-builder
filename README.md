# Studio Folder Builder (Template Generator)

A standalone **Python + PySide6** tool that generates **studio-style project folder structures** from configurable templates.

Supports:
- **Shots Mode** (Sequences/Shots) — `sequences/SQ###/SH###/...`
- **Assets Mode** (Categories/Assets) — `assets/<category>/<asset>/...`

Includes a **Preview Plan** (see exactly what will be created), a safe **Build** step (filesystem), and a reproducible **manifest**.

---

## Requirements

- Windows 10/11
- Python **3.10+** (tested on 3.11)
- No admin rights required

---

## Quickstart (Windows — Command Prompt)

### Option A — One-step setup (recommended)
1) Open **Command Prompt** in the repo root (the folder that contains `main.py`)  
2) Run:

```bat
setup.bat
```

This will:
- create `.venv/`
- install dependencies
- run tests (`pytest`)

Then run the app:

```bat
run_app.bat
```

### Option B — Manual setup (Command Prompt)

```bat
python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
pip install -r requirements-dev.txt

python -m pytest -q
python main.py
```

---

## Optional: Flow/PT (ShotGrid) Integration

Flow/PT support is optional. If you don't use it, you can ignore this section.

### Install the optional dependency (Command Prompt)

```bat
.venv\Scripts\activate
pip install -r requirements-flow.txt
```

### Configure credentials (safe)

1) Copy the example config:
- `flow_config.example.json` → `flow_config.json`

2) Fill in values in `flow_config.json`:

```json
{
  "url": "https://YOURSTUDIO.shotgrid.autodesk.com",
  "script_name": "your_script_name",
  "script_key": "your_script_key",
  "project_id": 123
}
```

> Do **not** commit `flow_config.json` (it contains secrets). It is already gitignored.

### Troubleshooting Flow/PT
If Flow/PT returns **no sequences/shots**, verify:
- `project_id` is correct *and visible* to the script key (a wrong ID often returns `Project: None`)
- the script has permission to read **Project**, **Shot**, and **Sequence** entities
- your studio may use custom fields (e.g., `sq_sequence` instead of `sg_sequence`)

---

## How to Use
-Run python main.py in Command Prompt
### 1) Select basics
1) Choose a **Root** directory (example: `D:\shows`)
2) Select a **Template**
3) Enter a **Project** name

### 2) Choose a mode

#### Shots Mode (Sequences/Shots)
Enter sequences/shots like:

```
SQ010: SH010, SH020, SH030
SQ020: SH010
```

Click **Preview Plan** → verify output → click **Build**.

#### Assets Mode (Categories/Assets)
Enter categories/assets like:

```
run_tests.bat
```

Click **Preview Plan** → **Build**.

### 3) Outputs you should expect

#### Manifest
After Build, a project-wide manifest is written to:

`<root>/<project>/production/manifest.json`

It includes:
- template name + version
- timestamp (UTC)
- created/skipped/errors counts
- per-item action outcomes
- mode + sequences/assets used

#### Save/Load job configs
Use **Save Config…** / **Load Config…** to store and restore a job setup for reproducible builds.

Suggested location:

`<root>/<project>/production/job_config.json`

---

## Templates

Templates live in `templates/` and define:
- `project_folders` (top-level folders)
- `shot_tree` (folders/files per shot)
- `asset_tree` (folders/files per asset category)

Starter file rule:
- Any entry ending in `.md` or `.json` is treated as a **file** (starter file), not a folder.

---

## Run Tests (Command Prompt)

```bat
run_tests.bat
```

Or manually:

```bat
.venv\Scripts\activate
python -m pytest -q
```

---

## PowerShell (optional)

If you prefer PowerShell, you can also run:

```powershell
./setup.ps1
python main.py
```

---

## Repo Layout

```
studio-folder-builder/
├── main.py
├── requirements.txt
├── requirements-dev.txt
├── requirements-flow.txt
├── setup.bat
├── run_app.bat
├── run_tests.bat
├── templates/
├── builder/
└── tests/
```
