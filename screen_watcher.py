import os, time, threading, datetime, json, hashlib, queue

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_DIR    = os.path.join(SCRIPT_DIR, "data")
STATE_FILE  = os.path.join(DATA_DIR, "screen_watcher_state.json")
os.makedirs(DATA_DIR, exist_ok=True)

_running      = False
_thread       = None
_alert_queue  = queue.Queue()
_last_hash    = None
_last_screen  = None
_interval     = 30
_vision_mod   = None
_config       = {}
_last_alert_time = {}
_ALERT_COOLDOWN  = 120

WATCH_PATTERNS = {
    "error": {
        "keywords": ["error", "exception", "failed", "crash", "not responding",
                     "access denied", "blue screen", "critical", "fatal", "traceback"],
        "action":   "auto_fix",
        "message":  "Error detected on screen",
        "cooldown": 60,
    },
    "battery_low": {
        "keywords": ["battery low", "battery critical", "plug in", "10% battery",
                     "15% battery", "20% battery"],
        "action":   "notify",
        "message":  "Low battery warning on screen",
        "cooldown": 300,
    },
    "download_done": {
        "keywords": ["download complete", "download finished", "saved to",
                     "successfully downloaded"],
        "action":   "notify",
        "message":  "Download completed",
        "cooldown": 30,
    },
    "update_available": {
        "keywords": ["update available", "new version", "restart to update",
                     "update now"],
        "action":   "notify",
        "message":  "Software update available",
        "cooldown": 600,
    },
    "meeting": {
        "keywords": ["join now", "meeting starts", "call starting",
                     "zoom meeting", "teams meeting"],
        "action":   "notify",
        "message":  "Meeting notification detected",
        "cooldown": 120,
    },
}

def _take_screenshot():
    try:
        import pyautogui
        from PIL import Image
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.close()
        pyautogui.screenshot().save(tmp.name)
        return tmp.name
    except Exception:
        return None

def _screenshot_hash(path):
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read(8192)).hexdigest()
    except Exception:
        return None

def _screen_changed(path):
    global _last_hash
    h = _screenshot_hash(path)
    if h and h != _last_hash:
        _last_hash = h
        return True
    return False

def _analyse_screenshot(path, question="What is on this screen? Any errors, warnings, or important notifications?"):
    if not _vision_mod or not _config:
        return None
    try:
        reply, _ = _vision_mod.analyze_image(question, path, _config)
        return reply
    except Exception:
        return None

def _check_patterns(text):
    if not text:
        return []
    text_lower = text.lower()
    detected   = []
    now        = time.time()
    for pattern_name, pattern in WATCH_PATTERNS.items():
        if any(kw in text_lower for kw in pattern["keywords"]):
            last = _last_alert_time.get(pattern_name, 0)
            if now - last >= pattern.get("cooldown", _ALERT_COOLDOWN):
                detected.append((pattern_name, pattern))
                _last_alert_time[pattern_name] = now
    return detected

def _load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"enabled": False, "alerts_sent": 0, "last_run": None}

def _save_state(state):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass

def _watcher_loop():
    global _running, _last_screen
    state = _load_state()
    state["enabled"] = True
    _save_state(state)
    while _running:
        try:
            path = _take_screenshot()
            if not path:
                time.sleep(_interval)
                continue
            if _screen_changed(path):
                analysis = _analyse_screenshot(path)
                if analysis:
                    detected = _check_patterns(analysis)
                    for pattern_name, pattern in detected:
                        alert = {
                            "type":      pattern_name,
                            "message":   pattern["message"],
                            "analysis":  analysis[:300],
                            "action":    pattern["action"],
                            "time":      datetime.datetime.now().isoformat(),
                        }
                        _alert_queue.put(alert)
                        state["alerts_sent"] = state.get("alerts_sent", 0) + 1
                _last_screen = analysis
            try:
                os.unlink(path)
            except Exception:
                pass
            state["last_run"] = datetime.datetime.now().isoformat()
            _save_state(state)
        except Exception:
            pass
        time.sleep(_interval)
    state["enabled"] = False
    _save_state(state)

def start(vision_mod=None, config=None, interval=30):
    global _running, _thread, _vision_mod, _config, _interval
    if _running:
        return False, "Screen watcher already running"
    _vision_mod = vision_mod
    _config     = config or {}
    _interval   = max(10, interval)
    _running    = True
    _thread     = threading.Thread(target=_watcher_loop, daemon=True)
    _thread.start()
    return True, f"Screen watcher started (checking every {_interval}s)"

def stop():
    global _running
    _running = False
    return True, "Screen watcher stopped"

def is_running():
    return _running

def get_pending_alerts():
    alerts = []
    while not _alert_queue.empty():
        try:
            alerts.append(_alert_queue.get_nowait())
        except queue.Empty:
            break
    return alerts

def get_last_screen_content():
    return _last_screen

def get_status():
    state = _load_state()
    lines = [
        f"Screen watcher : {'RUNNING' if _running else 'STOPPED'}",
        f"Check interval : every {_interval}s",
        f"Alerts sent    : {state.get('alerts_sent', 0)}",
        f"Last checked   : {state.get('last_run', 'never')[:16] if state.get('last_run') else 'never'}",
        f"Watching for   : {', '.join(WATCH_PATTERNS.keys())}",
    ]
    return "\n".join(lines)

def read_screen_now(vision_mod, config, question=None):
    path = _take_screenshot()
    if not path:
        return "Could not take screenshot"
    q      = question or "Describe what is on this screen in detail. Note any errors, text, or important elements."
    result = None
    try:
        reply, _ = vision_mod.analyze_image(q, path, config)
        result   = reply
    except Exception as e:
        result = f"Could not analyse: {e}"
    try:
        os.unlink(path)
    except Exception:
        pass
    return result
