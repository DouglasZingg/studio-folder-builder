param(
  [string]$Python = "python",
  [switch]$Flow
)

$ErrorActionPreference = "Stop"

Write-Host "== Studio Folder Builder setup =="

& $Python -c "import sys; print('Python', sys.version)"
& $Python -m venv .venv

Write-Host "Activating venv..."
. .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt

if ($Flow) {
  pip install -r requirements-flow.txt
  Write-Host "Flow/PT extras installed."
} else {
  Write-Host "Flow/PT extras skipped. Run with -Flow to install."
}

Write-Host "Running tests..."
python -m pytest -q

Write-Host ""
Write-Host "Done! Run the app with:  python main.py"
