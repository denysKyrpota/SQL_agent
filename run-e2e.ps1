# PowerShell script to run E2E tests with proper environment
# Usage: .\run-e2e.ps1

Write-Host "Starting SQL AI Agent E2E Tests..." -ForegroundColor Cyan
Write-Host ""

# Check if venv is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & ".\venv_win\Scripts\Activate.ps1"
}

# Check if database exists
if (-not (Test-Path "sqlite.db")) {
    Write-Host "Database not found. Initializing..." -ForegroundColor Yellow
    & python scripts/init_db.py
}

Write-Host ""
Write-Host "Running Playwright E2E tests..." -ForegroundColor Green
Write-Host "Playwright will automatically start:"
Write-Host "  - Frontend dev server (http://localhost:5173)" -ForegroundColor Gray
Write-Host "  - Backend API server (http://localhost:8000)" -ForegroundColor Gray
Write-Host ""

# Run Playwright tests
npm run test:e2e

Write-Host ""
Write-Host "E2E tests completed!" -ForegroundColor Cyan
