# Studio Folder Builder (Template Generator)

A standalone **Python + PySide6** tool that generates **studio-style project folder structures** from configurable templates.  
Supports both **Shots Mode (Sequences/Shots)** and **Assets Mode (Categories/Assets)** with a **preview plan**, safe build rules, and reproducible manifests.

Designed as a production coordination / pipeline utility for VFX and game studios.

---

## Features

Template-driven folder structure generation (JSON templates)  
Preview Plan (see exactly what will be created)  
Safe Build (no overwrites by default) + optional overwrite toggle  
Creates starter files (e.g. `notes.md`, `manifest.json`)  
Writes a project-wide `production/manifest.json` build manifest  
Shots Mode: `sequences/SQ###/SH###/...`  
Assets Mode: `assets/<category>/<asset>/...`  
Save/Load job configs for reproducible builds (`job_config.json`)  
Optional Flow/PT (ShotGrid) integration to load sequences/shots automatically  

---

## Screenshots (add these)

Create a folder: `docs/screenshots/` and add:

- Main Window (Shots Mode)
- Main Window (Assets Mode)
- Preview Plan output
- Manifest JSON example

Then link them here:

```md
![Shots Mode](docs/screenshots/shots_mode.png)
![Assets Mode](docs/screenshots/assets_mode.png)
![Preview Plan](docs/screenshots/preview_plan.png)
![Manifest](docs/screenshots/manifest.png)
```

---

## Install

### 1) Create venv
```bash
python -m venv .venv
```

### 2) Activate venv

**Windows (PowerShell)**
```powershell
.venv\Scripts\Activate.ps1
```

### 3) Install dependencies
```bash
pip install -r requirements.txt
```

---

## Run

```bash
python main.py
```

---

## Usage

### Shots Mode (Sequences/Shots)

1) Choose a root folder (example: `D:/shows`)  
2) Select template (example: **VFX Default**)  
3) Enter project name  
4) Enter sequences/shots:

Example:
```
SQ010: SH010, SH020, SH030
SQ020: SH010
```

5) Click **Preview Plan**  
6) Click **Build**  

Generated output looks like:
```
<root>/<project>/sequences/SQ010/SH010/work/maya
<root>/<project>/sequences/SQ010/SH010/publish/usd
<root>/<project>/sequences/SQ010/SH010/docs/notes.md
```

---

### Assets Mode (Categories/Assets)

Switch to **Assets Mode** and enter:

Example:
```
characters: Hero, Villain
props: Sword, Shield
environments: City
```

Preview → Build generates:
```
<root>/<project>/assets/characters/Hero/...
<root>/<project>/assets/props/Sword/...
```

---

## Output: Manifest

Each build writes a project-wide manifest:

`<root>/<project>/production/manifest.json`

Includes:
- tool name + template + version
- timestamp (UTC)
- build results counts
- per-item action outcomes (created/skipped/error)
- mode + sequences/assets inputs

---

## Save/Load Job Configs

You can save job configs to JSON and reload later:

- Saves root, project, template, mode, overwrite flag, and structure input
- Reload restores UI fields and lets you rebuild consistently

Suggested config location:
`<root>/<project>/production/job_config.json`

---

## Templates

Templates live in `/templates` and define:

- Project-level folders (`project_folders`)
- Shot tree structure (`shot_tree`)
- Asset tree structure (`asset_tree`)
- Starter files (`.md`, `.json`) vs folders

Example template snippet:
```json
{
  "name": "VFX Default",
  "version": "1.0",
  "project_folders": ["assets", "sequences", "tools", "production"],
  "shot_tree": {
    "work": ["maya", "houdini", "nuke"],
    "docs": ["notes.md", "manifest.json"]
  },
  "asset_tree": {
    "characters": ["work", "publish", "textures"]
  }
}
```

**Starter file rule:**  
Any entry ending in `.md` / `.json` is treated as a file instead of a folder.

---

## Optional: Flow/PT (ShotGrid) Integration

This tool can optionally load Sequences/Shots from Flow Production Tracking (ShotGrid).

### Install ShotGrid API
```bash
pip install shotgun_api3
```

### Configure credentials

#### Option A) Environment variables
- `FLOW_URL`
- `FLOW_SCRIPT_NAME`
- `FLOW_SCRIPT_KEY`
- `FLOW_PROJECT_ID`

#### Option B) Config file
Create `flow_config.json` in the repo root (next to `main.py`):

```json
{
  "url": "https://YOURSTUDIO.shotgrid.autodesk.com",
  "script_name": "your_script_name",
  "script_key": "your_script_key",
  "project_id": 123
}
```

> `flow_config.json` should **never** be committed to git (contains secrets).

### Troubleshooting Flow/PT
If Flow/PT returns **no sequences/shots**, verify:
- your `project_id` is correct and visible to the script key
- your script has permission to read Project/Shot/Sequence entities
- your studio may use custom fields (e.g., `sq_sequence` instead of `sg_sequence`)

---

## Run Tests

```bash
python -m pytest -q
```

---

## Repo Structure

```
studio-folder-builder/
├── main.py
├── requirements.txt
├── README.md
├── CHANGELOG.md
├── templates/
│   ├── vfx_default.json
│   ├── game_default.json
│   └── animation_default.json
├── builder/
│   ├── app.py
│   ├── models.py
│   ├── core/
│   ├── ui/
│   ├── util/
│   └── integrations/   (optional Flow/PT)
└── tests/
```

---

## Portfolio Notes

This project demonstrates:
- Template-driven pipeline tooling
- Preview/build workflow (safe operations first)
- Filesystem execution + reporting
- Reproducible manifest tracking
- Optional Flow/PT integration (production tracking driven tooling)


