@echo off
echo.
echo  Installing ARIA global command...
echo.

set ARIA_DIR=%~dp0
set LAUNCHER=%USERPROFILE%\AppData\Local\Microsoft\WindowsApps\aria.bat

echo @echo off > "%LAUNCHER%"
echo cd /d "%ARIA_DIR%" >> "%LAUNCHER%"
echo python "%ARIA_DIR%aria.py" %%* >> "%LAUNCHER%"

echo  Done!
echo.
echo  You can now open ANY terminal and just type:  aria
echo.
pause
