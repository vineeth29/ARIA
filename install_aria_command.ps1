$AriaDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AriaScript = Join-Path $AriaDir "aria.py"
$LauncherDir = "$env:USERPROFILE\AppData\Local\Microsoft\WindowsApps"
$LauncherPath = Join-Path $LauncherDir "aria.bat"

Write-Host ""
Write-Host " Installing ARIA as a global command..." -ForegroundColor Cyan

$content = "@echo off`r`ncd /d `"$AriaDir`"`r`npython `"$AriaScript`" %*"
Set-Content -Path $LauncherPath -Value $content -Encoding ASCII

Write-Host " Done! ARIA is now a global command." -ForegroundColor Green
Write-Host ""
Write-Host " Open any new terminal and type: aria" -ForegroundColor Yellow
Write-Host ""
Read-Host " Press Enter to exit"
