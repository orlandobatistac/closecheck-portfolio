$repoRoot = Split-Path -Parent $PSScriptRoot
$backendPath = Join-Path $repoRoot "backend"
$frontendPath = Join-Path $repoRoot "frontend"

# Start backend and frontend in separate PowerShell windows.
$backendCommand = "Set-Location '$backendPath'; python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
$frontendCommand = "Set-Location '$frontendPath'; npm run dev -- --host 127.0.0.1 --port 5173"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand

# Open only the frontend URL in the default browser.
Start-Process "http://127.0.0.1:5173"
