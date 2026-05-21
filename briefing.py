import os, json, datetime, socket

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
BRIEFING_LOG = os.path.join(SCRIPT_DIR, "data", "briefing_log.json")
os.makedirs(os.path.join(SCRIPT_DIR, "data"), exist_ok=True)

def _today():
    return datetime.date.today().isoformat()

def _already_sent_today():
    if not os.path.exists(BRIEFING_LOG):
        return False
    try:
        with open(BRIEFING_LOG) as f:
            data = json.load(f)
        return data.get("last_date") == _today()
    except Exception:
        return False

def _mark_sent():
    with open(BRIEFING_LOG, "w") as f:
        json.dump({"last_date": _today()}, f)

def _get_weather():
    try:
        import urllib.request
        result = urllib.request.urlopen("https://wttr.in/?format=3", timeout=4).read().decode()
        return result.strip()
    except Exception:
        return None

def _get_system_stats():
    try:
        import psutil
        cpu  = psutil.cpu_percent(interval=0.5)
        ram  = psutil.virtual_memory()
        disk = psutil.disk_usage("C:\\")
        bat  = psutil.sensors_battery()
        parts = [
            f"CPU {cpu:.0f}%",
            f"RAM {ram.percent:.0f}%",
            f"Disk {disk.percent:.0f}% used",
        ]
        if bat:
            plug = "charging" if bat.power_plugged else "on battery"
            parts.append(f"Battery {bat.percent:.0f}% ({plug})")
        return " | ".join(parts)
    except Exception:
        return None

def _get_pending_schedules():
    try:
        sched_file = os.path.join(SCRIPT_DIR, "data", "schedules.json")
        if not os.path.exists(sched_file):
            return []
        with open(sched_file) as f:
            data = json.load(f)
        now = datetime.datetime.now()
        pending = []
        for s in data:
            try:
                t = datetime.datetime.fromisoformat(s.get("next_run", ""))
                if t > now and (t - now).total_seconds() < 86400:
                    pending.append(f"• {s.get('name','Task')} at {t.strftime('%H:%M')}")
            except Exception:
                continue
        return pending
    except Exception:
        return []

def _get_screen_time_yesterday():
    try:
        from tracker import get_yesterday_summary
        return get_yesterday_summary()
    except Exception:
        return None

def _get_uptime():
    try:
        import psutil
        boot   = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.datetime.now() - boot
        h = uptime.seconds // 3600
        m = (uptime.seconds % 3600) // 60
        if uptime.days > 0:
            return f"{uptime.days}d {h}h {m}m"
        return f"{h}h {m}m"
    except Exception:
        return None

def get_briefing(force=False):
    if not force and _already_sent_today():
        return None
    now  = datetime.datetime.now()
    hour = now.hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    day_str = now.strftime("%A, %d %B %Y")
    parts = [f"{greeting}, Vineeth! Here's your briefing for {day_str}:\n"]
    weather = _get_weather()
    if weather:
        parts.append(f"🌤  Weather: {weather}")
    stats = _get_system_stats()
    if stats:
        parts.append(f"💻  System: {stats}")
    uptime = _get_uptime()
    if uptime:
        parts.append(f"⏱  Uptime: {uptime}")
    schedules = _get_pending_schedules()
    if schedules:
        parts.append(f"📅  Today's reminders:")
        parts.extend(f"    {s}" for s in schedules[:5])
    screen_time = _get_screen_time_yesterday()
    if screen_time:
        parts.append(f"📊  Yesterday: {screen_time}")
    parts.append("\nWhat would you like to do today?")
    _mark_sent()
    return "\n".join(parts)

def should_show_briefing():
    if _already_sent_today():
        return False
    now = datetime.datetime.now()
    return 5 <= now.hour <= 11

def get_proactive_suggestions(memory=None):
    suggestions = []
    try:
        import psutil
        disk = psutil.disk_usage("C:\\")
        if disk.percent >= 85:
            suggestions.append(f"⚠️  Your C: drive is {disk.percent:.0f}% full. Want me to clear temp files?")
        bat = psutil.sensors_battery()
        if bat and bat.percent <= 20 and not bat.power_plugged:
            suggestions.append(f"🔋  Battery at {bat.percent:.0f}% — plug in soon!")
        boot   = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime = (datetime.datetime.now() - boot).days
        if uptime >= 7:
            suggestions.append(f"💡  Your PC has been on for {uptime} days. A restart might help performance.")
    except Exception:
        pass
    return suggestions
