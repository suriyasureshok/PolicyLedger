# Quick Start - Backend Only

Write-Host "🚀 Starting PolicyLedger Backend..." -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

if (Test-Path ".venv\Scripts\Activate.ps1") {
    & .\.venv\Scripts\Activate.ps1
}

Write-Host "📊 Backend running on http://localhost:8000" -ForegroundColor Green
Write-Host "📚 API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""

Set-Location backend
python main.py
