.# IPL Dashboard Launcher
$logo = @"
    _____  ____    __         
   |_   _|/ ___|   \ \       
     | | | |  _     \ \      
     | | | |_| |    / /      
     |_|  \____|   /_/       
    DASHBOARD v1.0   
"@

Clear-Host
Write-Host $logo -ForegroundColor Cyan

Write-Host "`n[" -NoNewline
Write-Host "●" -ForegroundColor Green -NoNewline
Write-Host "] Initializing Dashboard..." -ForegroundColor White

# Activate virtual environment
Write-Host "[" -NoNewline
Write-Host "●" -ForegroundColor Yellow -NoNewline
Write-Host "] Activating environment..." -ForegroundColor White
& "$PSScriptRoot\venv\Scripts\activate.ps1"

# Launch the dashboard
Write-Host "[" -NoNewline
Write-Host "●" -ForegroundColor Magenta -NoNewline
Write-Host "] Starting Streamlit server..." -ForegroundColor White
Write-Host "`nDashboard will open in your browser shortly...`n" -ForegroundColor Cyan
& "$PSScriptRoot\venv\Scripts\streamlit.exe" run "$PSScriptRoot\app.py"