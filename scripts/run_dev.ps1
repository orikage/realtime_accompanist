$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
  python -m venv (Join-Path $Root ".venv")
  & $Python -m pip install -e "$Root[dev]"
}

& $Python -m uvicorn realtime_accompanist.web.app:app --host 127.0.0.1 --port 8000 --reload

