import psutil, os, time, threading, datetime

_alerted = {}
_ALERT_COOLDOWN = 1800
_alerts_queue = []
_lock = threading.Lock()

IGNORED_PROCESSES = {
    "system idle process", "idle", "system", "registry",
    "smss.exe", "csrss.exe", "wininit.exe", "services.exe",
    "lsass.exe", "svchost.exe", "dwm.exe", "winlogon.exe",
    "phoneexperiencehost.exe", "runtimebroker.exe", "searchhost.exe",
    "searchindexer.exe", "antimalware service executable", "msmpeng.exe",
    "securityhealthsystray.exe", "securityhealthservice.exe",
    "wmiprvse.exe", "taskhostw.exe", "ctfmon.exe", "sihost.exe",
    "fontdrvhost.exe", "spoolsv.exe", "msiexec.exe", "audiodg.exe",
    "shellexperiencehost.exe", "startmenuexperiencehost.exe",
    "textinputhost.exe", "applicationframehost.exe",
    "widgetsservice.exe", "widgets.exe",
}

def _should_alert(key):
    now = time.time()
    if key in _alerted and now - _alerted[key] < _ALERT_COOLDOWN:
        return False
    _alerted[key] = now
    return True

def _queue_alert(message):
    with _lock:
        _alerts_queue.append(message)

def get_pending_alerts():
    with _lock:
        alerts = list(_alerts_queue)
        _alerts_queue.clear()
    return alerts

def _get_top_process_by_cpu():
    procs = []
    for p in psutil.process_iter(["name", "cpu_percent"]):
        try:
            name = p.info["name"] or ""
            cpu  = p.info["cpu_percent"] or 0.0
            if name.lower() in IGNORED_PROCESSES:
                continue
            if cpu > 0:
                procs.append((name, cpu))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    procs.sort(key=lambda x: x[1], reverse=True)
    return procs[0] if procs else None

def _get_top_process_by_ram():
    procs = []
    for p in psutil.process_iter(["name", "memory_info"]):
        try:
            name   = p.info["name"] or ""
            mem_mb = p.info["memory_info"].rss / (1024 ** 2)
            if name.lower() in IGNORED_PROCESSES:
                continue
            procs.append((name, mem_mb))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    procs.sort(key=lambda x: x[1], reverse=True)
    return procs[0] if procs else None

def check_disk():
    alerts = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            pct   = usage.percent
            free  = usage.free / (1024 ** 3)
            if pct >= 95 and _should_alert(f"disk_{part.device}_95"):
                alerts.append(f"🔴 {part.device} is {pct}% full — only {free:.1f}GB left. Want me to clear temp files?")
            elif pct >= 90 and _should_alert(f"disk_{part.device}_90"):
                alerts.append(f"🟡 {part.device} is {pct}% full ({free:.1f}GB free). Consider cleaning up.")
        except (PermissionError, OSError):
            continue
    return alerts

def check_ram():
    ram = psutil.virtual_memory()
    if ram.percent >= 90 and _should_alert("ram_90"):
        top = _get_top_process_by_ram()
        if top:
            return [f"🟡 RAM at {ram.percent}% — heaviest app: {top[0]} ({top[1]:.0f}MB). Want me to kill it?"]
        return [f"🟡 RAM at {ram.percent}%. Want me to check what's using it?"]
    return []

def check_battery():
    bat = psutil.sensors_battery()
    if not bat:
        return []
    if bat.percent <= 15 and not bat.power_plugged and _should_alert("battery_15"):
        return [f"🔴 Battery at {bat.percent}%! Plug in now!"]
    if bat.percent <= 25 and not bat.power_plugged and _should_alert("battery_25"):
        return [f"🟡 Battery at {bat.percent}% and not charging. Plug in soon."]
    return []

def check_cpu():
    cpu = psutil.cpu_percent(interval=2)
    if cpu < 90:
        return []
    if not _should_alert("cpu_90"):
        return []
    top = _get_top_process_by_cpu()
    if top:
        return [f"🟡 CPU at {cpu:.0f}% — culprit: {top[0]} ({top[1]:.0f}%). Want me to kill it?"]
    return [f"🟡 CPU at {cpu:.0f}%. No single app to blame — may be background Windows tasks."]

def check_uptime():
    boot  = datetime.datetime.fromtimestamp(psutil.boot_time())
    days  = (datetime.datetime.now() - boot).days
    if days >= 10 and _should_alert("uptime_10"):
        return [f"💡 PC has been on for {days} days without a restart. A reboot might help performance."]
    if days >= 7 and _should_alert("uptime_7"):
        return [f"💡 {days} days since last restart. Consider rebooting soon."]
    return []

def run_all_checks():
    alerts = []
    alerts.extend(check_disk())
    alerts.extend(check_ram())
    alerts.extend(check_battery())
    alerts.extend(check_cpu())
    alerts.extend(check_uptime())
    return alerts

def get_health_report():
    lines = ["System Health Report"]
    lines.append("─" * 35)

    cpu = psutil.cpu_percent(interval=1)
    emoji = "🟢" if cpu < 70 else "🟡" if cpu < 90 else "🔴"
    lines.append(f"  {emoji} CPU      : {cpu:.0f}%")

    ram = psutil.virtual_memory()
    emoji = "🟢" if ram.percent < 70 else "🟡" if ram.percent < 85 else "🔴"
    used  = ram.used  / (1024 ** 3)
    total = ram.total / (1024 ** 3)
    lines.append(f"  {emoji} RAM      : {ram.percent:.0f}%  ({used:.1f} / {total:.1f} GB)")

    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            emoji = "🟢" if usage.percent < 80 else "🟡" if usage.percent < 90 else "🔴"
            free  = usage.free / (1024 ** 3)
            lines.append(f"  {emoji} {part.device:<8} : {usage.percent:.0f}% used  ({free:.1f} GB free)")
        except (PermissionError, OSError):
            continue

    bat = psutil.sensors_battery()
    if bat:
        emoji = "🟢" if bat.percent > 50 else "🟡" if bat.percent > 20 else "🔴"
        plug  = "charging" if bat.power_plugged else "on battery"
        lines.append(f"  {emoji} Battery  : {bat.percent:.0f}%  ({plug})")

    boot   = datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.datetime.now() - boot
    h = uptime.seconds // 3600
    m = (uptime.seconds % 3600) // 60
    lines.append(f"  ⏱  Uptime   : {uptime.days}d {h}h {m}m")

    top_cpu = _get_top_process_by_cpu()
    top_ram = _get_top_process_by_ram()
    if top_cpu:
        lines.append(f"  📌 Top CPU  : {top_cpu[0]}  ({top_cpu[1]:.0f}%)")
    if top_ram:
        lines.append(f"  📌 Top RAM  : {top_ram[0]}  ({top_ram[1]:.0f} MB)")

    return "\n".join(lines)

_running = False

def start_monitor():
    global _running
    if _running:
        return
    _running = True

    def _loop():
        time.sleep(30)
        while _running:
            try:
                for alert in run_all_checks():
                    _queue_alert(alert)
            except Exception:
                pass
            time.sleep(60)

    threading.Thread(target=_loop, daemon=True).start()

def stop_monitor():
    global _running
    _running = False
