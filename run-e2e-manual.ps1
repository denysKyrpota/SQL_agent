# PowerShell script to run E2E tests against already-running servers
# Usage: First start servers manually, then run: .\run-e2e-manual.ps1

Write-Host "Running E2E tests against existing servers..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Ensure these servers are running:" -ForegroundColor Yellow
Write-Host "  1. Frontend: http://localhost:5173 (npm run dev in frontend/)" -ForegroundColor Gray
Write-Host "  2. Backend:  http://localhost:8000 (python -m backend.app.main)" -ForegroundColor Gray
Write-Host ""

$response = Read-Host "Are both servers running? (y/n)"

if ($response -eq "y" -or $response -eq "Y") {
    Write-Host ""
    Write-Host "Running Playwright tests..." -ForegroundColor Green

    # Set environment variable to reuse existing servers
    $env:CI = "false"
    npm run test:e2e

    Write-Host ""
    Write-Host "E2E tests completed!" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "Please start the servers first:" -ForegroundColor Red
    Write-Host ""
    Write-Host "Terminal 1 (Backend):" -ForegroundColor Yellow
    Write-Host "  .\venv_win\Scripts\Activate.ps1" -ForegroundColor Gray
    Write-Host "  python -m backend.app.main" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Terminal 2 (Frontend):" -ForegroundColor Yellow
    Write-Host "  cd frontend" -ForegroundColor Gray
    Write-Host "  npm run dev" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Terminal 3 (E2E Tests):" -ForegroundColor Yellow
    Write-Host "  .\run-e2e-manual.ps1" -ForegroundColor Gray
}
