# PolicyLedger Backend Startup Script
# Run this to start the backend server with live training support

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "🚀 PolicyLedger Backend Server" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (Test-Path ".venv") {
    Write-Host "✅ Found virtual environment" -ForegroundColor Green
    & .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "⚠️  No virtual environment found. Creating one..." -ForegroundColor Yellow
    python -m venv .venv
    & .\.venv\Scripts\Activate.ps1
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
}

Write-Host ""
Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan
pip install -q -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "Server Starting..." -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "📡 REST API:     http://localhost:8000" -ForegroundColor White
Write-Host "🔌 WebSocket:    ws://localhost:8000/ws/train/{agent_id}" -ForegroundColor White
Write-Host "📚 API Docs:     http://localhost:8000/docs" -ForegroundColor White
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the server
python start_server.py
