import json, os, datetime, subprocess

SCRIPT_DIR      = os.path.dirname(os.path.abspath(__file__))
WORKSPACES_FILE = os.path.join(SCRIPT_DIR, "data", "workspaces.json")
os.makedirs(os.path.join(SCRIPT_DIR, "data"), exist_ok=True)

BUILTIN_WORKSPACES = {
    "work": {
        "name": "Work",
        "apps": ["vscode", "chrome"],
        "urls": ["https://mail.google.com", "https://calendar.google.com"],
        "folders": [],
        "focus_mode": True,
        "volume": 40,
    },
    "study": {
        "name": "Study",
        "apps": ["notepad"],
        "urls": [],
        "folders": [],
        "focus_mode": True,
        "volume": 30,
        "music": "lofi study music",
    },
    "gaming": {
        "name": "Gaming",
        "apps": ["steam"],
        "urls": [],
        "folders": [],
        "focus_mode": False,
        "volume": 80,
    },
    "chill": {
        "name": "Chill",
        "apps": ["spotify"],
        "urls": ["https://youtube.com"],
        "folders": [],
        "focus_mode": False,
        "volume": 60,
    },
}

def _load():
    data = dict(BUILTIN_WORKSPACES)
    if os.path.exists(WORKSPACES_FILE):
        try:
            with open(WORKSPACES_FILE) as f:
                saved = json.load(f)
            data.update(saved)
        except Exception:
            pass
    return data

def _save(data):
    user_only = {k: v for k, v in data.items() if k not in BUILTIN_WORKSPACES}
    with open(WORKSPACES_FILE, "w") as f:
        json.dump(user_only, f, indent=2)

def list_workspaces():
    ws = _load()
    lines = ["Available workspaces:"]
    for key, w in ws.items():
        apps = ", ".join(w.get("apps", [])) or "none"
        focus = "focus on" if w.get("focus_mode") else "focus off"
        lines.append(f"  {w['name']} — apps: {apps} | {focus}")
    lines.append("\nSwitch: /workspace <name>   Save: /workspace save <name>")
    return "\n".join(lines)

def save_workspace(name, apps=None, urls=None, folders=None,
                   focus_mode=False, volume=50, music=None):
    ws = _load()
    ws[name.lower()] = {
        "name":       name,
        "apps":       apps    or [],
        "urls":       urls    or [],
        "folders":    folders or [],
        "focus_mode": focus_mode,
        "volume":     volume,
        "music":      music,
        "saved":      datetime.datetime.now().isoformat(),
    }
    _save(ws)
    return True

def get_workspace_actions(name):
    ws = _load()
    w  = ws.get(name.lower())
    if not w:
        return None, f"Workspace '{name}' not found. Available: {', '.join(ws.keys())}"
    actions = []
    vol = w.get("volume", 50)
    actions.append(f'[ACTION: set_volume(level="{vol}")]')
    for app in w.get("apps", []):
        actions.append(f'[ACTION: open_app(name="{app}")]')
    for url in w.get("urls", []):
        actions.append(f'[ACTION: open_url(url="{url}")]')
    music = w.get("music")
    if music:
        actions.append(f'[ACTION: open_youtube(query="{music}")]')
    for folder in w.get("folders", []):
        actions.append(f'[ACTION: run_command(cmd="explorer \\"{folder}\\"")]')
    return actions, None

def is_workspace_request(text):
    phrases = ["workspace", "work mode", "study mode", "gaming mode",
               "chill mode", "switch to", "switch mode"]
    tl = text.lower()
    return any(p in tl for p in phrases) or tl.startswith("/workspace")

def parse_workspace_command(text):
    tl = text.lower().strip()
    if "/workspace save" in tl:
        name = text.split("save")[-1].strip()
        return "save", name
    if tl.startswith("/workspace "):
        name = text[11:].strip()
        return "switch", name
    for phrase in ["switch to ", "switch mode ", "go to "]:
        if phrase in tl:
            name = tl.split(phrase)[-1].strip().split()[0]
            return "switch", name
    for name in ["work", "study", "gaming", "chill"]:
        if name + " mode" in tl or tl.endswith(name):
            return "switch", name
    if tl == "/workspaces":
        return "list", ""
    return None, None
