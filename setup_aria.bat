@echo off
title ARIA Setup - One-Click Installer
color 0B
echo.
echo ============================================
echo   ARIA v5.0 - AUTOMATED SETUP SCRIPT
echo ============================================
echo.

:: Step 1 — Check if Ollama is installed
echo [1/5] Checking if Ollama is installed...
where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo       Ollama not found. Installing via winget...
    echo       This downloads ~1.8 GB. Please wait...
    echo.
    winget install Ollama.Ollama --accept-package-agreements --accept-source-agreements
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] winget install failed.
        echo         Please install Ollama manually from: https://ollama.com/download
        echo         Then re-run this script.
        pause
        exit /b 1
    )
    echo.
    echo       Refreshing PATH...
    set "PATH=%PATH%;%USERPROFILE%\AppData\Local\Programs\Ollama"
    set "PATH=%PATH%;C:\Program Files\Ollama"
) else (
    echo       Ollama is already installed. Good.
)
echo.

:: Step 2 — Start Ollama server
echo [2/5] Starting Ollama server...
tasklist /FI "IMAGENAME eq ollama.exe" 2>nul | find /I "ollama.exe" >nul
if %errorlevel% neq 0 (
    start /B ollama serve >nul 2>&1
    echo       Waiting for server to start...
    timeout /t 5 /nobreak >nul
) else (
    echo       Ollama server already running.
)
echo.

:: Step 3 — Pull base model
echo [3/5] Pulling base model (qwen2.5:7b)...
echo       This downloads ~4.4 GB. Please wait...
echo.
ollama pull qwen2.5:7b
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to pull model. Check your internet connection.
    pause
    exit /b 1
)
echo.

:: Step 4 — Build custom ARIA model
echo [4/5] Building custom ARIA model...
cd /d "%~dp0"
ollama create aria -f Modelfile
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to create custom model.
    echo         Make sure the Modelfile exists in: %~dp0
    pause
    exit /b 1
)
echo.

:: Step 5 — Test
echo [5/5] Testing ARIA model...
echo       Sending test prompt...
ollama run aria "Say exactly: ARIA v5.0 is online. Ready, Boss." --nowordwrap
echo.

echo ============================================
echo   SETUP COMPLETE!
echo ============================================
echo.
echo   To start ARIA, run:
echo     cd %~dp0
echo     python aria.py
echo.
echo   Or just double-click: run_aria.bat
echo.
pause
