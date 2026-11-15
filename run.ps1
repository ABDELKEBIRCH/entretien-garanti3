$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
if (-not (Test-Path .\.venv\Scripts\python.exe)) {
  python -m venv .venv
}
& .\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
$frontend = Join-Path $root "frontend"
Push-Location $frontend
pnpm install --frozen-lockfile
if ($LASTEXITCODE -ne 0) {
  Pop-Location
  exit $LASTEXITCODE
}
pnpm run build
if ($LASTEXITCODE -ne 0) {
  Pop-Location
  exit $LASTEXITCODE
}
Pop-Location
$env:PYTHONPATH = "$root\backend"
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --app-dir backend --host 127.0.0.1 --port 8000
