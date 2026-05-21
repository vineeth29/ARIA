import json, os, sys, time, shutil, subprocess, re

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")

RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[38;5;39m"
GREEN  = "\033[38;5;120m"
YELLOW = "\033[38;5;228m"
DIM    = "\033[38;5;240m"

def _p(text, color=CYAN):
    print(f"  {color}{text}{RESET}")

def _ask(prompt, default=None, color=YELLOW):
    hint = f" [{default}]" if default else ""
    try:
        val = input(f"  {color}{prompt}{hint}: {RESET}").strip()
        return val if val else (default or "")
    except (EOFError, KeyboardInterrupt):
        return default or ""

def _ask_choice(prompt, choices, default=None):
    opts = " / ".join(f"{CYAN}{c}{RESET}" for c in choices)
    hint = f" (default: {default})" if default else ""
    _p(f"{prompt}{hint}", YELLOW)
    _p(f"Options: {opts}", DIM)
    val = input(f"  > ").strip().lower()
    if not val and default:
        return default
    for c in choices:
        if val in [c.lower(), c[0].lower()]:
            return c
    return val if val else (default or choices[0])

def _find_exe(names):
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    common_paths = [
        r"C:\Program Files",
        r"C:\Program Files (x86)",
        os.path.expanduser(r"~\AppData\Local"),
        os.path.expanduser(r"~\AppData\Roaming"),
    ]
    for base in common_paths:
        if not os.path.exists(base):
            continue
        for root, dirs, files in os.walk(base):
            dirs[:] = dirs[:5]
            for f in files:
                if f.lower() in [n.lower() for n in names]:
                    return os.path.join(root, f)
    return None

KNOWN_BROWSER_PATHS = {
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
    ],
    "edge": [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\Application\msedge.exe"),
    ],
    "firefox": [
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
    ],
    "brave": [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        os.path.expanduser(r"~\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe"),
    ],
    "zen": [
        r"C:\Program Files\Zen Browser\zen.exe",
        os.path.expanduser(r"~\AppData\Local\Zen Browser\zen.exe"),
        os.path.expanduser(r"~\AppData\Roaming\Zen Browser\zen.exe"),
    ],
    "opera": [
        os.path.expanduser(r"~\AppData\Local\Programs\Opera\opera.exe"),
        r"C:\Program Files\Opera\opera.exe",
    ],
    "vivaldi": [
        os.path.expanduser(r"~\AppData\Local\Vivaldi\Application\vivaldi.exe"),
        r"C:\Program Files\Vivaldi\Application\vivaldi.exe",
    ],
}

def _detect_browsers():
    browsers = {}
    for name, paths in KNOWN_BROWSER_PATHS.items():
        for path in paths:
            if os.path.exists(path):
                browsers[name] = path
                break
    return browsers

def _detect_apps():
    apps = {}
    checks = {
        "vscode":   ["code.exe", "Code.exe"],
        "spotify":  ["Spotify.exe"],
        "discord":  ["Discord.exe", "discord.exe"],
        "telegram": ["Telegram.exe"],
        "steam":    ["steam.exe"],
        "vlc":      ["vlc.exe"],
        "obs":      ["obs64.exe", "obs.exe"],
        "notepad+": ["notepad++.exe"],
        "zoom":     ["Zoom.exe"],
        "teams":    ["Teams.exe"],
        "slack":    ["slack.exe"],
        "whatsapp": ["WhatsApp.exe"],
    }
    for name, exes in checks.items():
        path = _find_exe(exes)
        if path:
            apps[name] = path
    return apps

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def is_setup_done():
    cfg = load_config()
    return cfg.get("setup_done", False)

def run_wizard():
    os.system("cls" if os.name == "nt" else "clear")
    print(f"""
  {CYAN}{BOLD}╔══════════════════════════════════════════════════╗
  ║         Welcome to ARIA — First Time Setup       ║
  ║   Let's personalise ARIA for you. Takes ~2 min   ║
  ╚══════════════════════════════════════════════════╝{RESET}
""")
    cfg = load_config()

    print(f"  {BOLD}Step 1 — About you{RESET}")
    print()
    name = _ask("What's your name?", default=cfg.get("user_name", ""))
    cfg["user_name"] = name

    wake = _ask(f"What should ARIA call you?", default=cfg.get("user_nickname", name))
    cfg["user_nickname"] = wake or name

    print()
    print(f"  {BOLD}Step 2 — Your browser{RESET}")
    print()
    detected_browsers = _detect_browsers()
    if detected_browsers:
        _p(f"Found on your PC: {', '.join(detected_browsers.keys())}", GREEN)
    else:
        _p("No browsers auto-detected.", DIM)

    browser_choice = _ask(
        "Which browser should ARIA use?",
        default=cfg.get("default_browser", list(detected_browsers.keys())[0] if detected_browsers else "chrome")
    ).lower().strip()
    cfg["default_browser"] = browser_choice
    if browser_choice in detected_browsers:
        cfg["default_browser_path"] = detected_browsers[browser_choice]
        _p(f"✓ Found at: {detected_browsers[browser_choice]}", GREEN)
    else:
        path = _find_exe([browser_choice + ".exe", browser_choice.replace(" ", "") + ".exe"])
        if path:
            cfg["default_browser_path"] = path
            _p(f"✓ Found at: {path}", GREEN)
        else:
            _p(f"Couldn't find {browser_choice} automatically. You can set it later with: use <browser>", YELLOW)

    print()
    print(f"  {BOLD}Step 3 — Your apps{RESET}")
    print()
    detected_apps = _detect_apps()
    if detected_apps:
        _p(f"Found on your PC: {', '.join(detected_apps.keys())}", GREEN)
    cfg["detected_apps"] = detected_apps

    music_app = _ask(
        "Which music app do you use? (spotify / youtube / none)",
        default=cfg.get("music_app", "spotify" if "spotify" in detected_apps else "youtube")
    ).lower().strip()
    cfg["music_app"] = music_app

    code_editor = _ask(
        "Which code editor do you use? (vscode / notepad++ / none)",
        default=cfg.get("code_editor", "vscode" if "vscode" in detected_apps else "none")
    ).lower().strip()
    cfg["code_editor"] = code_editor

    print()
    print(f"  {BOLD}Step 4 — Your folders{RESET}")
    print()
    _p("ARIA can search your documents and notes.", DIM)
    docs_folder = _ask(
        "Your main documents folder? (press Enter to skip)",
        default=cfg.get("docs_folder", os.path.expanduser("~\\Documents"))
    )
    cfg["docs_folder"] = docs_folder

    notes_folder = _ask(
        "Your notes/study folder? (press Enter to skip)",
        default=cfg.get("notes_folder", "")
    )
    cfg["notes_folder"] = notes_folder

    download_folder = _ask(
        "Your downloads folder?",
        default=cfg.get("download_folder", os.path.expanduser("~\\Downloads"))
    )
    cfg["download_folder"] = download_folder

    print()
    print(f"  {BOLD}Step 5 — Preferences{RESET}")
    print()
    lang = _ask(
        "Preferred language for ARIA replies? (english / tamil / hindi / any)",
        default=cfg.get("reply_language", "english")
    ).lower().strip()
    cfg["reply_language"] = lang

    tone = _ask_choice(
        "How should ARIA talk to you?",
        ["casual", "formal", "savage", "motivator"],
        default=cfg.get("personality_mode", "casual")
    )
    cfg["personality_mode"] = tone

    startup = _ask_choice(
        "Show daily briefing on startup?",
        ["yes", "no"],
        default="yes" if cfg.get("startup_briefing", True) else "no"
    )
    cfg["startup_briefing"] = startup == "yes"

    sounds = _ask_choice(
        "Enable sounds?",
        ["yes", "no"],
        default="yes" if cfg.get("features", {}).get("sounds", True) else "no"
    )
    if "features" not in cfg:
        cfg["features"] = {}
    cfg["features"]["sounds"] = sounds == "yes"

    print()
    print(f"  {BOLD}Step 6 — Quick shortcuts{RESET}")
    print()
    _p("You can teach ARIA custom shortcuts. E.g. 'my project' → opens a folder.", DIM)
    shortcuts = cfg.get("custom_shortcuts", {})
    for i in range(3):
        phrase = _ask(f"Shortcut {i+1} phrase (or Enter to skip)", default="")
        if not phrase:
            break
        action = _ask(f"  What should '{phrase}' do?", default="")
        if action:
            shortcuts[phrase.lower()] = action
    cfg["custom_shortcuts"] = shortcuts

    cfg["setup_done"] = True
    cfg["setup_date"] = time.strftime("%Y-%m-%d %H:%M")
    save_config(cfg)

    print()
    print(f"""  {GREEN}{BOLD}╔══════════════════════════════════════════════════╗
  ║           All done! ARIA is personalised.        ║
  ╚══════════════════════════════════════════════════╝{RESET}

  {DIM}Name     : {RESET}{name}
  {DIM}Called   : {RESET}{cfg['user_nickname']}
  {DIM}Browser  : {RESET}{cfg['default_browser']}
  {DIM}Music    : {RESET}{cfg['music_app']}
  {DIM}Editor   : {RESET}{cfg['code_editor']}
  {DIM}Language : {RESET}{cfg['reply_language']}
  {DIM}Tone     : {RESET}{cfg['personality_mode']}

  {CYAN}ARIA will now remember all of this.
  You can change anything anytime — just tell ARIA.{RESET}
""")
    time.sleep(1)
    return cfg

def get_user_context():
    cfg = load_config()
    parts = []
    if cfg.get("user_nickname"):
        parts.append(f"User's name: {cfg['user_nickname']}")
    if cfg.get("default_browser"):
        parts.append(f"Default browser: {cfg['default_browser']}")
    if cfg.get("music_app"):
        parts.append(f"Music app: {cfg['music_app']}")
    if cfg.get("code_editor"):
        parts.append(f"Code editor: {cfg['code_editor']}")
    if cfg.get("reply_language") and cfg["reply_language"] != "english":
        parts.append(f"Reply in: {cfg['reply_language']}")
    if cfg.get("personality_mode"):
        parts.append(f"Tone: {cfg['personality_mode']}")
    if cfg.get("custom_shortcuts"):
        for phrase, action in cfg["custom_shortcuts"].items():
            parts.append(f"Shortcut '{phrase}' = {action}")
    if cfg.get("docs_folder"):
        parts.append(f"Docs folder: {cfg['docs_folder']}")
    if cfg.get("notes_folder"):
        parts.append(f"Notes folder: {cfg['notes_folder']}")
    detected = cfg.get("detected_apps", {})
    if detected:
        parts.append(f"Installed apps: {', '.join(detected.keys())}")
    return "\n".join(parts)

def handle_settings_change(text, cfg):
    tl = text.lower().strip()
    changed = False

    browser_words = ["use ", "set browser ", "default browser ", "open with "]
    for bw in browser_words:
        if tl.startswith(bw):
            browser_name = tl[len(bw):].strip().split()[0].lower()
            # Look up known paths first
            path = None
            for p in KNOWN_BROWSER_PATHS.get(browser_name, []):
                if os.path.exists(p):
                    path = p
                    break
            cfg["default_browser"] = browser_name
            if path:
                cfg["default_browser_path"] = path
                save_config(cfg)
                return True, f"Got it! Using {browser_name} from now on."
            else:
                # Store name anyway — user said to use it
                cfg["default_browser_path"] = ""
                save_config(cfg)
                return True, f"Set to {browser_name}. I'll try to find it when you open something."

    if "call me " in tl:
        m = re.search(r"call me ([a-zA-Z]+)", tl)
        if m:
            cfg["user_nickname"] = m.group(1).capitalize()
            save_config(cfg)
            return True, f"Sure, I'll call you {cfg['user_nickname']}!"

    if "speak in " in tl or "reply in " in tl or "talk in " in tl:
        m = re.search(r"(?:speak|reply|talk) in ([a-zA-Z]+)", tl)
        if m:
            cfg["reply_language"] = m.group(1).lower()
            save_config(cfg)
            return True, f"I'll reply in {m.group(1)} from now on."

    if "my music app is " in tl or "use " in tl and "music" in tl:
        for app in ["spotify", "youtube", "apple music", "amazon music", "gaana", "jiosaavn"]:
            if app in tl:
                cfg["music_app"] = app
                save_config(cfg)
                return True, f"Got it, I'll use {app} for music."

    if "my editor is " in tl or "use " in tl and ("editor" in tl or "ide" in tl):
        for ed in ["vscode", "vs code", "notepad++", "sublime", "pycharm", "intellij"]:
            if ed in tl:
                cfg["code_editor"] = ed.replace(" ", "")
                save_config(cfg)
                return True, f"Got it, I'll use {ed} as your editor."

    shortcuts = cfg.get("custom_shortcuts", {})
    if "when i say " in tl and " open " in tl:
        m = re.search(r"when i say ['\"]?(.+?)['\"]? (?:open|do|run) (.+)", tl)
        if m:
            phrase  = m.group(1).strip().lower()
            action  = m.group(2).strip()
            shortcuts[phrase] = action
            cfg["custom_shortcuts"] = shortcuts
            save_config(cfg)
            return True, f"Shortcut saved! When you say '{phrase}' I'll {action}."

    return False, None

if __name__ == "__main__":
    run_wizard()
