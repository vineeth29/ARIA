"""
ARIA App Time Tracker + Time Machine
======================================
Silently tracks active windows and provides activity history.
Background thread polls every 10 seconds.
"""

import json, os, datetime, time, threading, re

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
TRACKER_FILE = os.path.join(DATA_DIR, "tracker.json")

_running = False
_lock = threading.Lock()

# ════════════════════════════════════════════════════════════════
# STORAGE
# ════════════════════════════════════════════════════════════════

def _load():
    if os.path.exists(TRACKER_FILE):
        try:
            with open(TRACKER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"sessions": []}

def _save(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(TRACKER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ════════════════════════════════════════════════════════════════
# WINDOW DETECTION
# ════════════════════════════════════════════════════════════════

def _get_active_window():
    """Get the currently active window title and app name."""
    try:
        import ctypes
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value

        if not title:
            return None, None

        # Extract app name from title
        app = _title_to_app(title)
        return app, title
    except Exception:
        return None, None

def _title_to_app(title):
    """Convert window title to app name."""
    title_lower = title.lower()

    app_patterns = {
        "chrome": ["google chrome"],
        "firefox": ["mozilla firefox"],
        "edge": ["microsoft edge"],
        "zen browser": ["zen browser", "zen"],
        "vs code": ["visual studio code"],
        "notepad": ["notepad"],
        "file explorer": ["file explorer"],
        "cmd": ["command prompt", "cmd.exe", "administrator: command"],
        "powershell": ["powershell", "windows powershell"],
        "terminal": ["windows terminal"],
        "discord": ["discord"],
        "whatsapp": ["whatsapp"],
        "telegram": ["telegram"],
        "spotify": ["spotify"],
        "youtube": ["youtube"],
        "vlc": ["vlc media player"],
        "word": ["microsoft word", "word"],
        "excel": ["microsoft excel", "excel"],
        "powerpoint": ["microsoft powerpoint", "powerpoint"],
    }

    for app, patterns in app_patterns.items():
        for pattern in patterns:
            if pattern in title_lower:
                return app
    
    # Fallback: extract from title (usually "Document - App Name")
    parts = title.split(" - ")
    if len(parts) > 1:
        return parts[-1].strip()[:30]
    return title[:30]

# ════════════════════════════════════════════════════════════════
# BACKGROUND TRACKER
# ════════════════════════════════════════════════════════════════

def start_monitor():
    """Start background window tracking thread."""
    global _running
    if _running:
        return
    _running = True

    def _track_loop():
        last_app = None
        last_switch_time = time.time()

        while _running:
            try:
                app, title = _get_active_window()
                now = time.time()

                if app and app != last_app:
                    # Log the previous session
                    if last_app:
                        duration = int(now - last_switch_time)
                        if duration >= 5:  # ignore <5 sec sessions
                            _log_session(last_app, duration)
                    last_app = app
                    last_switch_time = now

            except Exception:
                pass
            time.sleep(10)

    t = threading.Thread(target=_track_loop, daemon=True)
    t.start()

def stop_monitor():
    global _running
    _running = False

def _log_session(app, duration_seconds):
    """Log an app usage session."""
    with _lock:
        data = _load()
        entry = {
            "app": app,
            "duration": duration_seconds,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        }
        data["sessions"].append(entry)

        # Keep only last 30 days of data
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        data["sessions"] = [s for s in data["sessions"] if s.get("date", "") >= cutoff]

        _save(data)

# ════════════════════════════════════════════════════════════════
# QUERY FUNCTIONS
# ════════════════════════════════════════════════════════════════

def get_today_summary():
    """Get today's screen time summary."""
    data = _load()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    today_sessions = [s for s in data["sessions"] if s.get("date") == today]

    if not today_sessions:
        return "  No activity tracked today yet."

    # Aggregate by app
    app_time = {}
    for s in today_sessions:
        app = s["app"]
        app_time[app] = app_time.get(app, 0) + s["duration"]

    # Sort by time descending
    sorted_apps = sorted(app_time.items(), key=lambda x: x[1], reverse=True)

    total_secs = sum(app_time.values())
    lines = [f"  Screen Time Today ({_format_duration(total_secs)} total):"]
    for app, secs in sorted_apps[:10]:
        pct = int(secs / total_secs * 100) if total_secs > 0 else 0
        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
        lines.append(f"    {app:20s} {_format_duration(secs):>8s}  {bar} {pct}%")

    return "\n".join(lines)

def get_app_time(app_name, days=1):
    """Get time spent on a specific app."""
    data = _load()
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    sessions = [s for s in data["sessions"] if s.get("date", "") >= cutoff and app_name.lower() in s["app"].lower()]

    total = sum(s["duration"] for s in sessions)
    return total

def get_activity_at(target_time_str):
    """Get what was active at a specific time (for Time Machine)."""
    data = _load()
    # Find the session closest to the target time
    closest = None
    for s in data["sessions"]:
        if target_time_str[:10] in s.get("timestamp", ""):
            closest = s
    return closest

def get_timeline(date_str=None):
    """Get activity timeline for a specific date."""
    data = _load()
    if not date_str:
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    day_sessions = [s for s in data["sessions"] if s.get("date") == date_str]
    if not day_sessions:
        return f"  No activity data for {date_str}."

    lines = [f"  Activity Timeline — {date_str}:"]
    for s in day_sessions:
        dur = _format_duration(s["duration"])
        lines.append(f"    {s.get('timestamp', '')[11:]} — {s['app']} ({dur})")

    return "\n".join(lines)

def _format_duration(seconds):
    """Format seconds into human readable duration."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    else:
        hours = seconds // 3600
        mins = (seconds % 3600) // 60
        return f"{hours}h {mins}m"

def get_tracker_context():
    """Get screen time context for AI."""
    data = _load()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    today_sessions = [s for s in data["sessions"] if s.get("date") == today]

    if not today_sessions:
        return ""

    app_time = {}
    for s in today_sessions:
        app_time[s["app"]] = app_time.get(s["app"], 0) + s["duration"]

    sorted_apps = sorted(app_time.items(), key=lambda x: x[1], reverse=True)[:5]
    items = [f"- {app}: {_format_duration(secs)}" for app, secs in sorted_apps]
    return "\n[Today's screen time]:\n" + "\n".join(items)
