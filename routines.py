import json, os, datetime, threading, time, re

SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
ROUTINES_FILE = os.path.join(SCRIPT_DIR, "data", "routines.json")
os.makedirs(os.path.join(SCRIPT_DIR, "data"), exist_ok=True)

def _load():
    if os.path.exists(ROUTINES_FILE):
        try:
            with open(ROUTINES_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save(data):
    with open(ROUTINES_FILE, "w") as f:
        json.dump(data, f, indent=2)

def save_routine(name, steps, trigger=None, schedule=None):
    routines = _load()
    routines[name.lower()] = {
        "name":     name,
        "steps":    steps,
        "trigger":  trigger,
        "schedule": schedule,
        "created":  datetime.datetime.now().isoformat(),
        "run_count": 0
    }
    _save(routines)
    return True

def delete_routine(name):
    routines = _load()
    if name.lower() in routines:
        del routines[name.lower()]
        _save(routines)
        return True
    return False

def get_routine(name):
    routines = _load()
    return routines.get(name.lower())

def list_routines():
    routines = _load()
    if not routines:
        return "No routines saved yet.\nCreate one: /routine save <name> | step1 | step2 | step3"
    lines = ["Saved routines:"]
    for key, r in routines.items():
        steps = len(r.get("steps", []))
        trigger = r.get("trigger", "manual")
        runs = r.get("run_count", 0)
        lines.append(f"  {r['name']} — {steps} steps, trigger: {trigger}, ran {runs}x")
    return "\n".join(lines)

def run_routine(name, action_executor=None):
    routine = get_routine(name)
    if not routine:
        return False, f"Routine '{name}' not found. Type /routines to see all."
    steps = routine.get("steps", [])
    if not steps:
        return False, "Routine has no steps."
    results = []
    for i, step in enumerate(steps, 1):
        results.append(f"Step {i}: {step}")
        if action_executor:
            try:
                action_executor(step)
            except Exception as e:
                results.append(f"  Error: {e}")
        time.sleep(0.5)
    routines = _load()
    if name.lower() in routines:
        routines[name.lower()]["run_count"] = routines[name.lower()].get("run_count", 0) + 1
        routines[name.lower()]["last_run"] = datetime.datetime.now().isoformat()
        _save(routines)
    return True, "\n".join(results)

def parse_routine_command(text):
    tl = text.lower().strip()
    if tl.startswith("/routine save ") or tl.startswith("/routine create "):
        rest = text[text.lower().index("save ") + 5:].strip() if "save " in tl else \
               text[text.lower().index("create ") + 7:].strip()
        if "|" in rest:
            parts = [p.strip() for p in rest.split("|")]
            name  = parts[0]
            steps = parts[1:]
            return "save", name, steps
        return "save_partial", rest, []
    if tl.startswith("/routine run ") or tl.startswith("run routine "):
        name = text.split(" ", 2)[-1].strip()
        return "run", name, []
    if tl.startswith("/routine delete "):
        name = text[16:].strip()
        return "delete", name, []
    if tl in ("/routines", "/routine list"):
        return "list", "", []
    if tl.startswith("/routine "):
        name = text[9:].strip()
        return "run", name, []
    return None, None, None

BUILTIN_ROUTINES = {
    "morning": [
        "[ACTION: check_internet()]",
        "[ACTION: battery_status()]",
        "[ACTION: clear_temp()]",
        "[ACTION: open_url(url=\"https://wttr.in\")]",
        "[ACTION: open_app(name=\"spotify\")]",
    ],
    "goodnight": [
        "[ACTION: clear_temp()]",
        "[ACTION: empty_recycle_bin()]",
        "[ACTION: screenshot(filename=\"goodnight_screenshot.png\")]",
        "[ACTION: lock_screen()]",
    ],
    "work": [
        "[ACTION: open_app(name=\"vscode\")]",
        "[ACTION: open_url(url=\"https://mail.google.com\")]",
        "[ACTION: open_url(url=\"https://calendar.google.com\")]",
    ],
    "study": [
        "[ACTION: open_app(name=\"notepad\")]",
        "[ACTION: set_volume(level=\"30\")]",
        "[ACTION: open_youtube(query=\"lofi study music\")]",
    ],
    "cleanup": [
        "[ACTION: clear_temp()]",
        "[ACTION: empty_recycle_bin()]",
        "[ACTION: disk_usage(drive=\"C:\")]",
    ],
}

def get_builtin(name):
    return BUILTIN_ROUTINES.get(name.lower())

def ensure_builtins():
    routines = _load()
    for name, steps in BUILTIN_ROUTINES.items():
        if name not in routines:
            save_routine(name, steps, trigger="manual")
