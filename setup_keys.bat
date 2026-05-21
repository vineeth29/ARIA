@echo off
title ARIA Beast Mode — API Key Setup
color 0B
echo.
echo ============================================
echo   ARIA v5.0 BEAST MODE — API KEY SETUP
echo ============================================
echo.
echo   This will set up your FREE API keys.
echo   Each provider takes 30 seconds to sign up.
echo   No credit card needed for any of them.
echo.
echo ============================================
echo.

cd /d "%~dp0"

:: Check if Python is available
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found. Please install Python first.
    pause
    exit /b 1
)

:: Run the Python key setup
python -c "
import json, os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath('.')), 'config.json')
config_path = 'config.json'

# Load existing config
config = {}
if os.path.exists(config_path):
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except:
        pass

print()
print('  [1/3] GROQ — Ultra-fast AI (llama-3.3-70b)')
print('  Sign up free: https://console.groq.com')
print('  Go to API Keys, create one, paste below.')
print()
key = input('  Groq API Key (or press Enter to skip): ').strip()
if key:
    config['groq_api_key'] = key
    print('  [OK] Groq key saved!')
else:
    print('  [SKIPPED] You can add it later.')

print()
print('  [2/3] CEREBRAS — Wafer-scale engine (llama-3.3-70b)')
print('  Sign up free: https://cloud.cerebras.ai')
print('  Go to API Keys, create one, paste below.')
print()
key = input('  Cerebras API Key (or press Enter to skip): ').strip()
if key:
    config['cerebras_api_key'] = key
    print('  [OK] Cerebras key saved!')
else:
    print('  [SKIPPED] You can add it later.')

print()
print('  [3/3] GOOGLE GEMINI — Gemini 2.0 Flash')
print('  Get key free: https://aistudio.google.com/apikey')
print('  Click Create API Key, paste below.')
print()
key = input('  Gemini API Key (or press Enter to skip): ').strip()
if key:
    config['gemini_api_key'] = key
    print('  [OK] Gemini key saved!')
else:
    print('  [SKIPPED] You can add it later.')

# Ensure defaults
config.setdefault('ollama_model', 'aria')
config.setdefault('ollama_url', 'http://localhost:11434')
config.setdefault('preferred_provider', 'auto')

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

# Count configured providers
count = sum(1 for k in ['groq_api_key', 'cerebras_api_key', 'gemini_api_key'] if config.get(k))

print()
print('  ============================================')
print(f'  DONE! {count}/3 cloud providers configured.')
if count > 0:
    print('  Run: python aria.py  (or double-click run_aria.bat)')
else:
    print('  [WARNING] No keys added. ARIA will only work')
    print('  with local Ollama (if downloaded).')
    print('  Re-run this script anytime to add keys.')
print('  ============================================')
print()
"

pause
