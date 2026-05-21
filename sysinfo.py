"""
ARIA System Info Gatherer
==========================
Gathers REAL hardware and system info using actual commands.
This data is injected into the AI context so it NEVER makes up specs.
"""

import subprocess, platform, os, json


def _run(cmd, shell=True, timeout=10):
    """Run a command and return stdout, or empty string on failure."""
    try:
        result = subprocess.run(
            cmd, shell=shell, capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip()
    except Exception:
        return ""


def get_cpu_info():
    """Get real CPU name."""
    out = _run('wmic cpu get Name /value')
    for line in out.split('\n'):
        if line.strip().startswith('Name='):
            return line.split('=', 1)[1].strip()
    return platform.processor() or "Unknown"


def get_ram_info():
    """Get real total RAM."""
    try:
        import psutil
        ram = psutil.virtual_memory()
        total_gb = ram.total / (1024**3)
        used_gb = ram.used / (1024**3)
        avail_gb = ram.available / (1024**3)
        return {
            "total_gb": round(total_gb, 1),
            "used_gb": round(used_gb, 1),
            "available_gb": round(avail_gb, 1),
            "percent": ram.percent
        }
    except Exception:
        pass
    # fallback via wmic
    out = _run('wmic memorychip get Capacity /value')
    total = 0
    for line in out.split('\n'):
        if line.strip().startswith('Capacity='):
            try:
                total += int(line.split('=', 1)[1].strip())
            except ValueError:
                pass
    if total:
        return {"total_gb": round(total / (1024**3), 1)}
    return {"total_gb": "Unknown"}


def get_disk_info():
    """Get real disk info for all drives."""
    disks = []
    try:
        import psutil
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append({
                    "drive": part.device,
                    "total_gb": round(usage.total / (1024**3), 1),
                    "used_gb": round(usage.used / (1024**3), 1),
                    "free_gb": round(usage.free / (1024**3), 1),
                    "percent": usage.percent
                })
            except (PermissionError, OSError):
                continue
    except Exception:
        pass
    return disks


def get_gpu_info():
    """Get real GPU name."""
    out = _run('wmic path win32_videocontroller get Name /value')
    gpus = []
    for line in out.split('\n'):
        if line.strip().startswith('Name='):
            name = line.split('=', 1)[1].strip()
            if name:
                gpus.append(name)
    return gpus if gpus else ["Unknown"]


def get_battery_info():
    """Get real battery info."""
    try:
        import psutil
        bat = psutil.sensors_battery()
        if bat:
            return {
                "percent": int(bat.percent),
                "plugged_in": bat.power_plugged
            }
    except Exception:
        pass
    return None


def get_os_info():
    """Get OS version."""
    return platform.platform()


def get_top_processes(n=5):
    """Get top N processes by CPU/memory."""
    try:
        import psutil
        procs = []
        for p in psutil.process_iter(['name', 'cpu_percent', 'memory_info']):
            try:
                mem_mb = p.info['memory_info'].rss / (1024**2)
                procs.append({
                    "name": p.info['name'],
                    "cpu": p.info['cpu_percent'],
                    "ram_mb": round(mem_mb, 1)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        # Sort by RAM usage (more reliable than instant CPU)
        procs.sort(key=lambda x: x['ram_mb'], reverse=True)
        return procs[:n]
    except Exception:
        return []


def get_full_system_snapshot():
    """
    Gather ALL real system info into a single string.
    This gets injected into the AI's context so it has real data.
    """
    lines = []
    lines.append("═══ REAL SYSTEM INFO (gathered from actual hardware) ═══")

    # CPU
    cpu_name = get_cpu_info()
    lines.append(f"CPU: {cpu_name}")
    try:
        import psutil
        cpu_pct = psutil.cpu_percent(interval=1)
        cores = psutil.cpu_count(logical=True)
        lines.append(f"CPU Usage: {cpu_pct}% | Cores: {cores}")
    except Exception:
        pass

    # RAM
    ram = get_ram_info()
    if isinstance(ram.get("total_gb"), float):
        lines.append(f"RAM: {ram.get('used_gb', '?')}GB used / {ram['total_gb']}GB total ({ram.get('percent', '?')}%)")
    else:
        lines.append(f"RAM: {ram.get('total_gb', 'Unknown')}")

    # GPU
    gpus = get_gpu_info()
    lines.append(f"GPU: {', '.join(gpus)}")

    # Disks
    disks = get_disk_info()
    for d in disks:
        lines.append(f"Disk {d['drive']}: {d['used_gb']}GB used / {d['total_gb']}GB total ({d['free_gb']}GB free, {d['percent']}%)")

    # Battery
    bat = get_battery_info()
    if bat:
        plug = "plugged in" if bat['plugged_in'] else "on battery"
        lines.append(f"Battery: {bat['percent']}% ({plug})")

    # OS
    lines.append(f"OS: {get_os_info()}")

    # Top processes
    top = get_top_processes(5)
    if top:
        lines.append("Top processes by RAM:")
        for p in top:
            lines.append(f"  - {p['name']}: {p['ram_mb']}MB RAM, {p['cpu']}% CPU")

    lines.append("═══ END REAL SYSTEM INFO ═══")
    return "\n".join(lines)
