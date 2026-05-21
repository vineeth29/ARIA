"""
ARIA Scheduled Tasks Daemon
=============================
Background scheduler that runs timed automations.
Stores schedules in data/schedules.json, survives restarts.
"""

import json, os, datetime, time, threading, re

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
SCHEDULES_FILE = os.path.join(DATA_DIR, "schedules.json")

_running = False
_lock = threading.Lock()

def _load():
    if os.path.exists(SCHEDULES_FILE):
        try:
            with open(SCHEDULES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return []

def _save(schedules):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SCHEDULES_FILE, "w", encoding="utf-8") as f:
        json.dump(schedules, f, indent=2, ensure_ascii=False)

def add_schedule(description, time_str, repeat="once"):
    """
    Add a scheduled task.
    time_str: "8:00", "14:30", etc (24h format)
    repeat: "once", "daily", "weekdays", "hourly"
    """
    schedules = _load()
    sid = max([s.get("id", 0) for s in schedules], default=0) + 1
    entry = {
        "id": sid,
        "description": description,
        "time": time_str,
        "repeat": repeat,
        "enabled": True,
        "last_run": None,
        "created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    schedules.append(entry)
    _save(schedules)
    return sid

def remove_schedule(sid):
    schedules = _load()
    original = len(schedules)
    schedules = [s for s in schedules if s.get("id") != sid]
    if len(schedules) < original:
        _save(schedules)
        return True
    return False

def list_schedules():
    schedules = _load()
    if not schedules:
        return "  No scheduled tasks."
    lines = ["  Scheduled Tasks:"]
    for s in schedules:
        status = "✅" if s.get("enabled") else "⏸"
        lines.append(f"    {status} #{s['id']} [{s['time']} {s['repeat']}] {s['description']}")
    return "\n".join(lines)

def _should_run(schedule):
    now = datetime.datetime.now()
    current_time = now.strftime("%H:%M")
    today = now.strftime("%Y-%m-%d")
    target_time = schedule.get("time", "")

    if current_time != target_time:
        return False
    if not schedule.get("enabled", True):
        return False

    last_run = schedule.get("last_run", "")
    if last_run and last_run[:10] == today and schedule["repeat"] != "hourly":
        return False

    repeat = schedule.get("repeat", "once")
    if repeat == "weekdays" and now.weekday() >= 5:
        return False

    return True

def _alert_queue():
    """Get pending schedule alerts."""
    return _pending_alerts

_pending_alerts = []
_alerts_lock = threading.Lock()

def get_pending_alerts():
    with _alerts_lock:
        alerts = list(_pending_alerts)
        _pending_alerts.clear()
    return alerts

def start_daemon():
    global _running
    if _running:
        return
    _running = True

    def _daemon_loop():
        while _running:
            try:
                schedules = _load()
                changed = False
                for s in schedules:
                    if _should_run(s):
                        desc = s["description"]
                        with _alerts_lock:
                            _pending_alerts.append(f"⏰ Scheduled: {desc}")
                        s["last_run"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        if s["repeat"] == "once":
                            s["enabled"] = False
                        changed = True
                if changed:
                    _save(schedules)
            except Exception:
                pass
            time.sleep(30)

    t = threading.Thread(target=_daemon_loop, daemon=True)
    t.start()

def stop_daemon():
    global _running
    _running = False
