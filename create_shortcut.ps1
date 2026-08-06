$desktopPath = [System.Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktopPath "IPL Dashboard.lnk"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$targetPath = Join-Path $scriptPath "start.bat"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetPath
$shortcut.WorkingDirectory = $scriptPath
$shortcut.Description = "IPL Data Analysis Dashboard"
$shortcut.IconLocation = "shell32.dll,27"
$shortcut.Save()

Write-Host "Shortcut created successfully on your desktop!"
Write-Host "You can now double-click 'IPL Dashboard' on your desktop to start the application."
pause