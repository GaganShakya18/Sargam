$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$backendVenv = Join-Path $backend ".venv\Scripts\python.exe"

if (-not (Test-Path $backendVenv)) {
    Write-Host "Creating backend virtual environment..."
    python -m venv "$backend\.venv"
}

Write-Host "Installing backend dependencies..."
& "$backend\.venv\Scripts\python.exe" -m pip install -r "$backend\requirements.txt"

Write-Host "Starting backend API..."
$backendCommand = "cd /d `"$backend`"; .\.venv\Scripts\Activate.ps1; python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
Start-Process powershell.exe -ArgumentList '-NoExit', '-Command', $backendCommand

Write-Host "Installing frontend dependencies..."
$frontendInstallCommand = "cd /d `"$frontend`"; npm install"
Start-Process powershell.exe -ArgumentList '-NoExit', '-Command', $frontendInstallCommand

Write-Host "Starting frontend preview..."
$frontendRunCommand = "cd /d `"$frontend`"; npm run dev -- --host 0.0.0.0"
Start-Process powershell.exe -ArgumentList '-NoExit', '-Command', $frontendRunCommand

Write-Host ""
Write-Host "The app should now be available at:"
Write-Host "- Frontend: http://localhost:5173"
Write-Host "- Backend API: http://localhost:8000"
Write-Host ""
Write-Host "If the browser does not open automatically, open http://localhost:5173 manually."
