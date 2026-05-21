"""
ARIA Focus Mode
=================
Block distracting sites and track productive time.
Uses Pomodoro-style timers with Windows hosts file blocking.
"""

import os, time, threading, datetime, json

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
FOCUS_FILE = os.path.join(DATA_DIR, "focus.json")
HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"

# Default sites to block
DEFAULT_BLOCKED = [
    "youtube.com", "www.youtube.com",
    "instagram.com", "www.instagram.com",
    "reddit.com", "www.reddit.com",
    "twitter.com", "www.twitter.com", "x.com", "www.x.com",
    "facebook.com", "www.facebook.com",
    "tiktok.com", "www.tiktok.com",
]

_FOCUS_MARKER = "# ARIA-FOCUS-BLOCK"

_active = False
_end_time = None
_timer_thread = None
_lock = threading.Lock()

# ════════════════════════════════════════════════════════════════
# STORAGE
# ════════════════════════════════════════════════════════════════

def _load():
    if os.path.exists(FOCUS_FILE):
        try:
            with open(FOCUS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"blocked_sites": list(DEFAULT_BLOCKED), "sessions": [], "total_focus_minutes": 0}

def _save(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(FOCUS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ════════════════════════════════════════════════════════════════
# HOSTS FILE MANAGEMENT
# ════════════════════════════════════════════════════════════════

def _block_sites(sites):
    """Add blocking entries to hosts file."""
    try:
        with open(HOSTS_PATH, "r") as f:
            content = f.read()
        # Remove old ARIA blocks
        lines = [l for l in content.split("\n") if _FOCUS_MARKER not in l]
        # Add new blocks
        for site in sites:
            lines.append(f"127.0.0.1 {site} {_FOCUS_MARKER}")
        with open(HOSTS_PATH, "w") as f:
            f.write("\n".join(lines))
        return True
    except PermissionError:
        return False  # Need admin rights
    except Exception:
        return False

def _unblock_sites():
    """Remove all ARIA blocking entries from hosts file."""
    try:
        with open(HOSTS_PATH, "r") as f:
            content = f.read()
        lines = [l for l in content.split("\n") if _FOCUS_MARKER not in l]
        with open(HOSTS_PATH, "w") as f:
            f.write("\n".join(lines))
        return True
    except Exception:
        return False

# ════════════════════════════════════════════════════════════════
# FOCUS SESSION MANAGEMENT
# ════════════════════════════════════════════════════════════════

def start_focus(minutes=60):
    """Start a focus session."""
    global _active, _end_time, _timer_thread
    
    with _lock:
        if _active:
            remaining = max(0, int((_end_time - time.time()) / 60))
            return False, f"Focus mode already active! {remaining} min remaining."
        
        _active = True
        _end_time = time.time() + (minutes * 60)
    
    # Try to block sites (may fail without admin)
    data = _load()
    blocked = _block_sites(data["blocked_sites"])
    
    # Start timer thread
    def _timer():
        global _active, _end_time
        while _active and time.time() < _end_time:
            time.sleep(30)
        if _active:
            end_focus()
            # Play sound to notify
            try:
                import sounds
                sounds.focus_end()
            except Exception:
                pass
    
    _timer_thread = threading.Thread(target=_timer, daemon=True)
    _timer_thread.start()
    
    # Log session start
    data["sessions"].append({
        "start": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "planned_minutes": minutes,
        "completed": False,
    })
    _save(data)
    
    block_msg = " Sites blocked!" if blocked else " (Run as admin to block sites)"
    return True, f"🧘 Focus mode ON — {minutes} min.{block_msg}"

def end_focus():
    """End the current focus session."""
    global _active, _end_time
    
    with _lock:
        if not _active:
            return False, "Focus mode is not active."
        
        elapsed = time.time() - (_end_time - 0)  # will be recalculated
        _active = False
        _end_time = None
    
    _unblock_sites()
    
    # Update the last session
    data = _load()
    if data["sessions"]:
        last = data["sessions"][-1]
        start_str = last.get("start", "")
        try:
            start_time = datetime.datetime.strptime(start_str, "%Y-%m-%d %H:%M")
            actual_minutes = int((datetime.datetime.now() - start_time).total_seconds() / 60)
            last["actual_minutes"] = actual_minutes
            last["completed"] = True
            data["total_focus_minutes"] = data.get("total_focus_minutes", 0) + actual_minutes
        except Exception:
            last["completed"] = True
    _save(data)
    
    return True, "🧘 Focus mode OFF. Sites unblocked. Good work! 💪"

def is_active():
    """Check if focus mode is currently active."""
    return _active

def get_remaining():
    """Get remaining focus time in minutes."""
    if not _active or not _end_time:
        return 0
    return max(0, int((_end_time - time.time()) / 60))

def add_blocked_site(site):
    """Add a site to the block list."""
    data = _load()
    site = site.lower().strip()
    if site not in data["blocked_sites"]:
        data["blocked_sites"].append(site)
        # Also add www variant
        if not site.startswith("www."):
            www = f"www.{site}"
            if www not in data["blocked_sites"]:
                data["blocked_sites"].append(www)
        _save(data)
        return True
    return False

def remove_blocked_site(site):
    """Remove a site from the block list."""
    data = _load()
    site = site.lower().strip()
    removed = False
    for s in [site, f"www.{site}"]:
        if s in data["blocked_sites"]:
            data["blocked_sites"].remove(s)
            removed = True
    if removed:
        _save(data)
    return removed

def get_stats():
    """Get focus stats."""
    data = _load()
    total = data.get("total_focus_minutes", 0)
    sessions = data.get("sessions", [])
    completed = sum(1 for s in sessions if s.get("completed"))
    
    # Today's focus
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    today_mins = sum(
        s.get("actual_minutes", 0) for s in sessions
        if s.get("start", "")[:10] == today and s.get("completed")
    )
    
    lines = ["  Focus Stats:"]
    lines.append(f"    📊 Total focus time: {total // 60}h {total % 60}m")
    lines.append(f"    📊 Sessions completed: {completed}")
    lines.append(f"    📊 Today: {today_mins}m focused")
    
    if _active:
        remaining = get_remaining()
        lines.append(f"    🟢 ACTIVE — {remaining} min remaining")
    
    return "\n".join(lines)

def list_blocked():
    """List all blocked sites."""
    data = _load()
    sites = data.get("blocked_sites", [])
    if not sites:
        return "  No sites in block list."
    # Deduplicate for display (show without www)
    unique = sorted(set(s.replace("www.", "") for s in sites))
    lines = ["  Blocked sites (during focus):"]
    for s in unique:
        lines.append(f"    🚫 {s}")
    return "\n".join(lines)
