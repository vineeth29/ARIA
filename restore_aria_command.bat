@echo off
title Restore ARIA global command
color 0B
echo.
echo  Restoring "aria" as a global command...
echo.

set ARIA_DIR=%~dp0
set WIN_APPS=%USERPROFILE%\AppData\Local\Microsoft\WindowsApps

echo @echo off > "%WIN_APPS%\aria.bat"
echo cd /d "%ARIA_DIR%" >> "%WIN_APPS%\aria.bat"
echo python "%ARIA_DIR%aria.py" >> "%WIN_APPS%\aria.bat"

echo  Done!
echo.
echo  Close this window, open any new CMD or PowerShell, and type:
echo.
echo     aria
echo.
pause
