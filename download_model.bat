@echo off
title ARIA Model Download - qwen2.5:7b (Auto-Retry)
color 0B
echo.
echo ============================================
echo   DOWNLOADING qwen2.5:7b (4.7 GB)
echo   Will auto-retry on failure until done!
echo ============================================
echo.

:RETRY
echo [%date% %time%] Starting download attempt...
echo.
ollama pull qwen2.5:7b
if %ERRORLEVEL% EQU 0 goto SUCCESS
echo.
echo [FAILED] Download interrupted. Retrying in 10 seconds...
echo          (Ollama resumes from where it left off)
echo.
timeout /t 10 /nobreak
goto RETRY

:SUCCESS
echo.
echo ============================================
echo   DOWNLOAD COMPLETE! Building custom ARIA model...
echo ============================================
echo.
ollama create aria -f c:\Users\vinee\Desktop\ai\Modelfile
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo   ALL DONE! ARIA offline model is ready!
    echo   You now have full offline fallback.
    echo ============================================
) else (
    echo.
    echo   [WARNING] Model build failed. You can retry with:
    echo   ollama create aria -f c:\Users\vinee\Desktop\ai\Modelfile
)
echo.
pause
