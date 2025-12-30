# PolicyLedger - Start Backend and Frontend

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "🚀 PolicyLedger - Starting Backend and Frontend" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Check if virtual environment exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "✅ Activating virtual environment..." -ForegroundColor Green
    & .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "⚠️  Virtual environment not found. Make sure you're in the correct directory." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "📊 Starting Backend (FastAPI on port 8000)" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Start backend in a new window
$backendDir = Join-Path $scriptDir "backend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptDir'; .\.venv\Scripts\Activate.ps1; cd backend; Write-Host '🔧 Backend Server Starting...' -ForegroundColor Green; python main.py"

Write-Host "✅ Backend starting in new window..." -ForegroundColor Green
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host ""

# Wait a bit for backend to start
Start-Sleep -Seconds 2

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "🎨 Starting Frontend (Vite on port 5173)" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if node_modules exists in frontend
$frontendDir = Join-Path $scriptDir "frontend\policy-ledger-insights"
if (Test-Path $frontendDir) {
    if (-not (Test-Path "$frontendDir\node_modules")) {
        Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Yellow
        Set-Location $frontendDir
        npm install
        Set-Location $scriptDir
    }
    
    Write-Host "✅ Starting frontend in new window..." -ForegroundColor Green
    Write-Host "   URL: http://localhost:5173" -ForegroundColor Gray
    Write-Host ""
    
    # Start frontend in a new window
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendDir'; Write-Host '🎨 Frontend Starting...' -ForegroundColor Green; npm run dev"
    
} else {
    Write-Host "⚠️  Frontend directory not found at: $frontendDir" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "✅ PolicyLedger is starting!" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔗 Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "📚 API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "🎨 Frontend: http://localhost:5173" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C in each window to stop the servers" -ForegroundColor Gray
Write-Host ""
