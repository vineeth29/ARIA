import os, json, datetime, sys, time, re, threading

MEMORY_FILE = os.path.expanduser("~/aria_memory.json")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAX_HISTORY = 20

try:
    from automation import action_requires_confirmation
except Exception:
    def action_requires_confirmation(action_name):
        return False


def _safe_prompt(ui, message):
    try:
        return ui.get_input(message)
    except Exception:
        return ""


AUTOMATION_BLOCK = """
## HOW TO EXECUTE TASKS — READ THIS CAREFULLY

When the user asks you to DO anything on the computer, you MUST write an ACTION block.
Do NOT just say "Opening YouTube" — actually open it with an ACTION.
Do NOT describe what you will do — DO IT with an ACTION block.

ACTION SYNTAX (copy exactly):
[ACTION: function_name(key="value")]

COMMON EXAMPLES — memorise these:

User: open youtube / open yt
You write: [ACTION: open_youtube()]

User: open youtube and search lofi
You write: [ACTION: open_youtube(query="lofi music")]

User: open chrome / open browser
You write: [ACTION: open_app(name="chrome")]

User: open spotify
You write: [ACTION: open_app(name="spotify")]

User: open google / go to google.com
You write: [ACTION: open_url(url="https://www.google.com")]

User: search for python tutorials
You write: [ACTION: search_google(query="python tutorials")]

User: take a screenshot
You write: [ACTION: screenshot(filename="screenshot.png")]

User: set volume to 50
You write: [ACTION: set_volume(level="50")]

User: lock the screen
You write: [ACTION: lock_screen()]

User: clear temp files
You write: [ACTION: clear_temp()]

User: what processes are running / what's eating my RAM
You write: [ACTION: run_command(cmd="tasklist /FO TABLE /NH")]

User: check my CPU
You write: [ACTION: run_command(cmd="wmic cpu get loadpercentage")]

User: send whatsapp to John saying hi
You write: [ACTION: send_whatsapp(contact="John" message="hi")]

User: open notepad
You write: [ACTION: open_app(name="notepad")]

User: shutdown my pc
You write: [ACTION: shutdown(delay="0")]

User: check internet
You write: [ACTION: check_internet()]

User: get my wifi password
You write: [ACTION: wifi_password()]

ALL AVAILABLE ACTIONS:
open_url, open_browser, open_youtube, open_app, open_gmail, open_calendar,
search_google, send_whatsapp, browser_click, browser_type, browser_press,
browser_wait, browser_text, close_browser, type_text, press_key, hotkey,
mouse_click, mouse_move, mouse_scroll, screenshot, run_command, wait,
set_volume, mute, lock_screen, sleep_pc, shutdown, restart, cancel_shutdown,
empty_recycle_bin, clear_temp, kill_process, wifi_password, check_internet,
public_ip, local_ip, flush_dns, reset_network, ping, scan_ports,
create_folder, delete_file, rename_file, copy_file, zip_folder, find_files,
read_file, write_file, append_file, disk_usage, battery_status, top_processes,
set_wallpaper, notify, speak, set_reminder, download_file, get_clipboard,
set_clipboard, translate, weather, run_python, generate_password, system_info,
dark_mode, light_mode, startup_programs, install_package, focus_window,
close_window, minimize_all, maximize_window, git_status, git_commit, git_push,
create_shortcut.

STRICT RULES:
1. ALWAYS use [ACTION:] when user asks to open, run, search, control anything.
2. Never say "Opening X" without an ACTION block. That does nothing.
3. Keep your text reply SHORT — 1-3 lines max. Just confirm what you did.
4. After the action, say: Done. Is this what you wanted?
5. Never invent system data. Use run_command to get real values.
"""


def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_memory(mem):
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(mem, f, indent=2)
    except IOError:
        pass


def get_real_system_status():
    parts = []
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.3)
        ram = psutil.virtual_memory()
        bat = psutil.sensors_battery()
        free = ram.available / (1024**3)
        tot = ram.total / (1024**3)
        parts.append(f"CPU {cpu:.0f}%")
        parts.append(f"RAM {free:.1f}/{tot:.1f}GB")
        if bat:
            parts.append(f"Battery {int(bat.percent)}%")
    except Exception:
        pass
    return "  ".join(parts) if parts else "System status unavailable"


def trim_history(history):
    if len(history) > MAX_HISTORY:
        return history[-MAX_HISTORY:]
    return history


def parse_and_execute_actions(text, ui):
    try:
        from automation import execute_action
    except ImportError:
        return False

    pattern = r'\[ACTION:\s*(\w+)\(([^)]*)\)\]'
    matches = list(re.finditer(pattern, text))
    if not matches:
        return False

    for match in matches:
        func_name = match.group(1)
        args_str = match.group(2).strip()
        kwargs = {}
        if args_str:
            for k, v in re.findall(r'(\w+)\s*=\s*"([^"]*)"', args_str):
                try:
                    kwargs[k] = int(v)
                except ValueError:
                    try:
                        kwargs[k] = float(v)
                    except ValueError:
                        kwargs[k] = v
            if not kwargs:
                val = args_str.strip('"').strip("'")
                param_map = {
                    "open_browser": "url", "open_url": "url", "browser_wait": "seconds",
                    "browser_click": "text", "browser_type": "text", "browser_press": "key",
                    "send_whatsapp": "contact", "search_google": "query", "open_youtube": "query",
                    "open_app": "name", "type_text": "text", "press_key": "key",
                    "screenshot": "filename", "run_command": "cmd", "wait": "seconds",
                }
                p = param_map.get(func_name, "text")
                try:
                    kwargs[p] = int(val)
                except ValueError:
                    kwargs[p] = val

        if action_requires_confirmation(func_name):
            if "confirm" not in kwargs:
                confirm = _safe_prompt(ui, f"This action is destructive: {func_name}. Type 'yes' to continue: ")
                if str(confirm).lower() not in {"yes", "y", "confirm", "ok", "sure"}:
                    ui.print_system(f"Cancelled destructive action: {func_name}", "warn")
                    continue
                kwargs["confirm"] = True

        try:
            execute_action(func_name, **kwargs)
        except Exception as e:
            ui.print_system(f"Action failed: {func_name} — {str(e)[:60]}", "error")

    return True
