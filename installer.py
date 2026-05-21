import os, sys, json, subprocess, time

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

BANNER = """
  ╔══════════════════════════════════════════════════════╗
  ║         ARIA — Offline AI Agent  Setup               ║
  ║         Advanced Reasoning & Intelligence Agent      ║
  ╚══════════════════════════════════════════════════════╝
"""

STEPS = [
    {
        "key": "groq_api_key",
        "name": "Groq (PRIMARY — fastest, free)",
        "url": "https://console.groq.com/keys",
        "hint": "Sign up free at console.groq.com → API Keys → Create Key",
        "required": True,
        "prefix": "gsk_",
    },
    {
        "key": "cerebras_api_key",
        "name": "Cerebras (SECONDARY — ultra fast, free)",
        "url": "https://cloud.cerebras.ai",
        "hint": "Sign up at cloud.cerebras.ai → API Keys → Create",
        "required": False,
        "prefix": "csk-",
    },
    {
        "key": "gemini_api_key",
        "name": "Gemini (TERTIARY — Google AI, free)",
        "url": "https://aistudio.google.com/app/apikey",
        "hint": "Go to aistudio.google.com → Get API Key → Create",
        "required": False,
        "prefix": "AIza",
    },
]

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def banner():
    clear()
    print(BANNER)

def install_dependencies():
    print("  Installing required packages...\n")
    packages = [
        "requests", "psutil", "pyautogui", "selenium",
        "webdriver-manager", "pyperclip", "win10toast",
        "winshell", "pywin32", "pycaw", "comtypes",
    ]
    for pkg in packages:
        print(f"  Installing {pkg}...", end=" ", flush=True)
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg, "--quiet", "--disable-pip-version-check"],
            capture_output=True
        )
        print("OK" if r.returncode == 0 else "skipped")
    print()

def check_ollama():
    print("  Checking Ollama (local offline model)...")
    try:
        import requests
        r = requests.get("http://localhost:11434/", timeout=3)
        if r.status_code == 200:
            print("  Ollama: Running\n")
            return True
    except Exception:
        pass
    print("  Ollama not detected. It is optional but enables fully offline mode.")
    print("  Download from: https://ollama.com\n")
    return False

def setup_keys():
    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                config = json.load(f)
        except Exception:
            pass

    print("  ARIA uses free AI APIs. You need at least ONE key (Groq recommended).\n")
    print("  All keys are stored ONLY on your machine. Nothing is uploaded.\n")

    for i, step in enumerate(STEPS, 1):
        banner()
        tag = "[REQUIRED]" if step["required"] else "[OPTIONAL — press Enter to skip]"
        print(f"  Step {i} of {len(STEPS)} — {step['name']}  {tag}\n")
        print(f"  Get your key here: {step['url']}")
        print(f"  Hint: {step['hint']}\n")

        existing = config.get(step["key"], "")
        if existing:
            print(f"  Current key: {existing[:8]}...{existing[-4:]}")
            keep = input("  Keep existing key? (Enter = yes / type new key): ").strip()
            if not keep:
                print(f"  Keeping existing key.\n")
                continue
            key = keep
        else:
            key = input(f"  Paste your {step['name'].split()[0]} API key: ").strip()

        if not key and not step["required"]:
            print(f"  Skipped.\n")
            continue

        if not key and step["required"]:
            print("  Groq key is required. Please get one at console.groq.com\n")
            key = input("  Paste Groq API key: ").strip()

        if key:
            config[step["key"]] = key
            print(f"  Saved.\n")
        time.sleep(0.5)

    banner()
    print("  Step 4 of 4 — Offline Model (Ollama)\n")
    print("  ARIA uses Ollama as a fallback when internet is unavailable.")
    print("  Model: llama3.1 (recommended) or any model you have installed.\n")
    model = input("  Ollama model name (press Enter for llama3.1): ").strip()
    config["ollama_model"] = model or "llama3.1"
    config["ollama_url"] = "http://localhost:11434"
    config["preferred_provider"] = "auto"
    config.setdefault("features", {
        "sounds": True, "personalities": True, "notes": True,
        "mood_journal": True, "rage_detector": True, "health_monitor": True,
        "clipboard_history": True, "app_tracker": True, "triggers": True,
        "scheduler": True, "smart_dj": True, "focus_mode": True,
        "window_tiler": True, "habits": True, "games": True,
    })
    config["personality_mode"] = "default"
    config["focus_blocked_sites"] = []

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

    return config

def test_providers(config):
    banner()
    print("  Testing your API keys...\n")
    import requests

    results = {}

    if config.get("groq_api_key"):
        print("  Testing Groq...", end=" ", flush=True)
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {config['groq_api_key']}", "Content-Type": "application/json"},
                json={"model": "llama-3.3-70b-versatile", "messages": [{"role":"user","content":"hi"}], "max_tokens": 5},
                timeout=10
            )
            ok = r.status_code == 200
            print("OK" if ok else f"FAILED ({r.status_code})")
            results["Groq"] = ok
        except Exception as e:
            print(f"FAILED ({str(e)[:40]})")
            results["Groq"] = False

    if config.get("cerebras_api_key"):
        print("  Testing Cerebras...", end=" ", flush=True)
        try:
            r = requests.post(
                "https://api.cerebras.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {config['cerebras_api_key']}", "Content-Type": "application/json"},
                json={"model": "llama3.1-8b", "messages": [{"role":"user","content":"hi"}], "max_tokens": 5},
                timeout=10
            )
            ok = r.status_code == 200
            print("OK" if ok else f"FAILED ({r.status_code})")
            results["Cerebras"] = ok
        except Exception as e:
            print(f"FAILED ({str(e)[:40]})")
            results["Cerebras"] = False

    if config.get("gemini_api_key"):
        print("  Testing Gemini...", end=" ", flush=True)
        try:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={config['gemini_api_key']}",
                json={"contents": [{"parts": [{"text": "hi"}]}]},
                timeout=10
            )
            ok = r.status_code == 200
            print("OK" if ok else f"FAILED ({r.status_code})")
            results["Gemini"] = ok
        except Exception as e:
            print(f"FAILED ({str(e)[:40]})")
            results["Gemini"] = False

    print()
    working = [k for k, v in results.items() if v]
    if working:
        print(f"  Working providers: {', '.join(working)}")
        return True
    else:
        print("  No providers working. Check your API keys.")
        return False

def create_launcher():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bat_path = os.path.join(script_dir, "run_aria.bat")
    with open(bat_path, "w") as f:
        f.write(f'@echo off\ncd /d "{script_dir}"\npython aria.py\npause\n')
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    desktop_bat = os.path.join(desktop, "ARIA.bat")
    try:
        import shutil
        shutil.copy2(bat_path, desktop_bat)
        print(f"  Desktop shortcut created: {desktop_bat}")
    except Exception:
        pass

def main():
    banner()
    print("  Welcome! This installer will set up ARIA on your machine.\n")
    print("  What it does:")
    print("   1. Installs Python packages")
    print("   2. Guides you through getting free API keys (takes ~5 min)")
    print("   3. Tests everything works")
    print("   4. Creates a desktop launcher\n")
    input("  Press Enter to start setup...")

    banner()
    install_dependencies()

    check_ollama()

    config = setup_keys()

    banner()
    print("  Almost done! Testing connections...\n")
    ok = test_providers(config)

    banner()
    create_launcher()

    print()
    if ok:
        print("  Setup complete! ARIA is ready.\n")
        print("  To start ARIA:")
        print("   - Double-click ARIA.bat on your Desktop")
        print("   - Or run: python aria.py\n")
    else:
        print("  Setup done but no API keys verified.")
        print("  Run installer.py again to re-enter your keys.\n")

    input("  Press Enter to launch ARIA now...")
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    os.execv(sys.executable, [sys.executable, "aria.py"])

if __name__ == "__main__":
    main()
