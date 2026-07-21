# One-shot local dev setup for Windows (PowerShell).
# Run from the project root:  powershell -ExecutionPolicy Bypass -File scripts\setup-windows.ps1
# Downloads: Python venv + all backend deps, frontend node_modules, backend .env.

$ErrorActionPreference = "Stop"

function Assert-Command($name, $hint) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        Write-Host "MISSING: $name — $hint" -ForegroundColor Red
        exit 1
    }
}

Write-Host "== Checking prerequisites ==" -ForegroundColor Cyan
Assert-Command python "Install Python 3.12+ from https://www.python.org/downloads/ (check 'Add to PATH')"
Assert-Command node   "Install Node.js 20+ LTS from https://nodejs.org/"
Assert-Command npm    "Comes with Node.js — reinstall Node if missing"

$pyVersion = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ([version]$pyVersion -lt [version]"3.12") {
    Write-Host "Python $pyVersion found; this project targets 3.12+. Install 3.12 and retry." -ForegroundColor Red
    exit 1
}

Write-Host "== Backend: creating venv + installing dependencies ==" -ForegroundColor Cyan
Set-Location backend
if (-not (Test-Path ".venv")) { python -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -e ".[dev]"

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created backend\.env from example — edit POSTGRES_PASSWORD and (optionally) APP_OPENAI_API_KEY" -ForegroundColor Yellow
}
Set-Location ..

Write-Host "== Frontend: installing node_modules ==" -ForegroundColor Cyan
Set-Location frontend
npm install --no-audit --no-fund
Set-Location ..

Write-Host "== Verifying: running the backend test suite ==" -ForegroundColor Cyan
Set-Location backend
& .\.venv\Scripts\python.exe -m pytest -q
Set-Location ..

Write-Host ""
Write-Host "Done. Next steps:" -ForegroundColor Green
Write-Host "  Full stack (recommended):  docker compose up --build     -> http://localhost:3000"
Write-Host "  Backend only (dev):        cd backend; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload"
Write-Host "  Frontend only (dev):       cd frontend; npm run dev      -> http://localhost:5173"
Write-Host "  (API dev mode needs postgres+redis: docker compose up postgres redis qdrant)"
