@echo off
setlocal enabledelayedexpansion

REM == Studio Folder Builder setup ==
REM Usage:
REM   setup.bat          (core + dev deps, runs tests)
REM   setup.bat --flow   (also installs Flow/PT deps)

set PY=python

echo == Studio Folder Builder setup ==
%PY% -c "import sys; print('Python', sys.version)"

if not exist .venv (
  %PY% -m venv .venv
)

call .venv\Scripts\activate

python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt

if "%1"=="--flow" (
  pip install -r requirements-flow.txt
  echo Flow/PT extras installed.
) else (
  echo Flow/PT extras skipped. Run: setup.bat --flow
)

echo Running tests...
python -m pytest -q
if errorlevel 1 (
  echo Tests failed.
  exit /b 1
)

echo.
echo Done! Run the app with: python main.py
pause
