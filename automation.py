import os, time, subprocess, inspect, shutil, socket, urllib.request, json, datetime, zipfile, re, ctypes

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_FILE = os.path.join(_SCRIPT_DIR, "config.json")

def _get_default_browser():
    try:
        with open(_CONFIG_FILE) as f:
            c = json.load(f)
        return c.get("default_browser", "").lower().strip()
    except Exception:
        return ""

def _set_default_browser(name, path):
    try:
        with open(_CONFIG_FILE) as f:
            c = json.load(f)
        c["default_browser"]      = name.lower().strip()
        c["default_browser_path"] = path
        with open(_CONFIG_FILE, "w") as f:
            json.dump(c, f, indent=2)
    except Exception:
        pass

def _get_default_browser_path():
    try:
        with open(_CONFIG_FILE) as f:
            c = json.load(f)
        return c.get("default_browser_path", "")
    except Exception:
        return ""

BROWSER_ALIASES = {
    "zen":            "zen",
    "zen browser":    "zen",
    "edge":           "edge",
    "msedge":         "edge",
    "microsoft edge": "edge",
    "chrome":         "chrome",
    "google chrome":  "chrome",
    "firefox":        "firefox",
    "mozilla":        "firefox",
    "brave":          "brave",
    "opera":          "opera",
    "vivaldi":        "vivaldi",
}

BROWSER_EXE_NAMES = {
    "zen":     "zen.exe",
    "edge":    "msedge.exe",
    "chrome":  "chrome.exe",
    "firefox": "firefox.exe",
    "brave":   "brave.exe",
    "opera":   "opera.exe",
    "vivaldi": "vivaldi.exe",
}

def set_browser(name):
    canonical = BROWSER_ALIASES.get(name.lower().strip(), name.lower().strip())
    for path in KNOWN_BROWSER_PATHS.get(canonical, []):
        if os.path.exists(path):
            _set_default_browser(canonical, path)
            print(f"  Browser set to: {canonical}")
            return True, path
    _set_default_browser(canonical, "")
    print(f"  Saved {canonical} as browser. Will try to find it when needed.")
    return True, None

KNOWN_BROWSER_PATHS = {
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
    ],
    "edge": [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\Application\msedge.exe"),
    ],
    "firefox": [
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
    ],
    "brave": [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        os.path.expanduser(r"~\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe"),
    ],
    "zen": [
        r"C:\Program Files\Zen Browser\zen.exe",
        os.path.expanduser(r"~\AppData\Local\Zen Browser\zen.exe"),
        os.path.expanduser(r"~\AppData\Roaming\Zen Browser\zen.exe"),
    ],
    "opera": [
        os.path.expanduser(r"~\AppData\Local\Programs\Opera\opera.exe"),
    ],
    "vivaldi": [
        os.path.expanduser(r"~\AppData\Local\Vivaldi\Application\vivaldi.exe"),
    ],
}

def _find_browser_exe(name):
    for path in KNOWN_BROWSER_PATHS.get(name.lower(), []):
        if os.path.exists(path):
            return path
    return None

def _launch_url(url):
    path = _get_default_browser_path()
    name = _get_default_browser()
    if path and os.path.exists(path):
        subprocess.Popen([path, url])
        return True
    if name:
        found = _find_browser_exe(name)
        if found:
            _set_default_browser(name, found)
            subprocess.Popen([found, url])
            return True
    try:
        os.startfile(url)
        return True
    except Exception:
        pass
    return False

_browser = None

def get_browser():
    global _browser
    if _browser is not None:
        try:
            _ = _browser.title
            return _browser
        except Exception:
            _browser = None
    from selenium import webdriver
    from selenium.webdriver.edge.service import Service
    from webdriver_manager.microsoft import EdgeChromiumDriverManager
    service = Service(EdgeChromiumDriverManager().install())
    options = webdriver.EdgeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    user_data = os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data")
    options.add_argument(f"--user-data-dir={user_data}")
    options.add_argument("--profile-directory=Default")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    _browser = webdriver.Edge(service=service, options=options)
    return _browser

def open_url(url, browser=None):
    if not url.startswith("http"):
        url = "https://" + url
    opened = _launch_url(url)
    if opened:
        time.sleep(1)
        return True
    print(f"  No browser set. Tell ARIA: use chrome / use firefox / use edge")
    return False

def open_browser(url, browser=None):
    return open_url(url)

def browser_wait(seconds=3):
    time.sleep(int(seconds))
    return True

def browser_find_and_click(text=None, css=None, xpath=None, wait=10):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    b = get_browser()
    try:
        if xpath:
            el = WebDriverWait(b, wait).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        elif css:
            el = WebDriverWait(b, wait).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css)))
        elif text:
            for by, val in [
                (By.XPATH, f"//*[contains(text(), '{text}')]"),
                (By.XPATH, f"//button[contains(., '{text}')]"),
                (By.XPATH, f"//a[contains(., '{text}')]"),
                (By.XPATH, f"//*[@aria-label='{text}']"),
                (By.XPATH, f"//*[@title='{text}']"),
            ]:
                try:
                    el = WebDriverWait(b, 3).until(EC.element_to_be_clickable((by, val)))
                    break
                except Exception:
                    continue
            else:
                return False
        else:
            return False
        el.click()
        time.sleep(0.5)
        return True
    except Exception:
        return False

def browser_type(text, css=None, xpath=None, clear=True, press_enter=False):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    b = get_browser()
    try:
        if xpath:
            el = WebDriverWait(b, 10).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        elif css:
            el = WebDriverWait(b, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css)))
        else:
            el = b.switch_to.active_element
        if clear:
            el.clear()
        el.send_keys(text)
        if press_enter:
            time.sleep(0.3)
            el.send_keys(Keys.ENTER)
        time.sleep(0.5)
        return True
    except Exception:
        return False

def browser_press_key(key):
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
    b = get_browser()
    key_map = {
        "enter": Keys.ENTER, "tab": Keys.TAB, "escape": Keys.ESCAPE,
        "backspace": Keys.BACKSPACE, "delete": Keys.DELETE,
        "up": Keys.ARROW_UP, "down": Keys.ARROW_DOWN,
        "left": Keys.ARROW_LEFT, "right": Keys.ARROW_RIGHT,
        "space": Keys.SPACE,
    }
    k = key_map.get(key.lower(), key)
    ActionChains(b).send_keys(k).perform()
    time.sleep(0.5)
    return True

def browser_get_text(css=None, xpath=None):
    from selenium.webdriver.common.by import By
    b = get_browser()
    try:
        if xpath:
            return b.find_element(By.XPATH, xpath).text
        elif css:
            return b.find_element(By.CSS_SELECTOR, css).text
        return b.title
    except Exception:
        return ""

def close_browser():
    global _browser
    if _browser:
        _browser.quit()
        _browser = None
    return True

def send_whatsapp(contact, message):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    b = get_browser()
    if "web.whatsapp.com" not in b.current_url:
        b.get("https://web.whatsapp.com")
        try:
            WebDriverWait(b, 30).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true" and @data-tab="3"]'))
            )
        except Exception:
            return False
    time.sleep(1)
    try:
        sb = WebDriverWait(b, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@contenteditable="true" and @data-tab="3"]'))
        )
        sb.click()
        time.sleep(0.5)
        sb.send_keys(contact)
        time.sleep(2)
        contact_el = WebDriverWait(b, 10).until(
            EC.element_to_be_clickable((By.XPATH, f'//span[@title="{contact}" or contains(@title, "{contact}")]'))
        )
        contact_el.click()
        time.sleep(1)
        msg_box = WebDriverWait(b, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@contenteditable="true" and @data-tab="10"]'))
        )
        msg_box.click()
        time.sleep(0.3)
        msg_box.send_keys(message)
        time.sleep(0.5)
        msg_box.send_keys(Keys.ENTER)
        time.sleep(1)
        return True
    except Exception:
        return False

def search_google(query):
    import urllib.parse
    url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
    return open_url(url, browser="zen")

def open_youtube(query=None):
    if query:
        import urllib.parse
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"
    else:
        url = "https://www.youtube.com"
    return open_url(url, browser="zen")

def open_app(name):
    import pyautogui
    app_map = {
        "notepad":        "notepad.exe",
        "calculator":     "calc.exe",
        "paint":          "mspaint.exe",
        "cmd":            "cmd.exe",
        "powershell":     "powershell.exe",
        "explorer":       "explorer.exe",
        "task manager":   "taskmgr.exe",
        "control panel":  "control.exe",
        "settings":       "ms-settings:",
        "vscode":         "code",
        "vs code":        "code",
        "chrome":         "chrome.exe",
        "firefox":        "firefox.exe",
        "edge":           "msedge.exe",
        "zen":            r"C:\Program Files\Zen Browser\zen.exe",
        "zen browser":    r"C:\Program Files\Zen Browser\zen.exe",
        "spotify":        "spotify.exe",
        "discord":        "discord.exe",
        "vlc":            "vlc.exe",
        "word":           "winword.exe",
        "excel":          "excel.exe",
        "powerpoint":     "powerpnt.exe",
        "obs":            "obs64.exe",
        "steam":          "steam.exe",
        "telegram":       "telegram.exe",
        "zoom":           "zoom.exe",
        "teams":          "teams.exe",
        "slack":          "slack.exe",
        "snipping tool":  "snippingtool.exe",
        "device manager": "devmgmt.msc",
        "registry editor":"regedit.exe",
    }
    exe = app_map.get(name.lower().strip(), name)
    try:
        if exe.startswith("ms-"):
            os.startfile(exe)
        elif exe.endswith(".msc"):
            subprocess.Popen(["mmc", exe], shell=True)
        else:
            subprocess.Popen(exe, shell=True)
        time.sleep(2)
        return True
    except Exception:
        pyautogui.hotkey("win")
        time.sleep(1)
        pyautogui.typewrite(name, interval=0.05)
        time.sleep(1.5)
        pyautogui.press("enter")
        time.sleep(2)
        return True

def type_text(text):
    import pyautogui
    if text.isascii():
        pyautogui.typewrite(text, interval=0.02)
    else:
        pyautogui.write(text)
    return True

def press_key(key):
    import pyautogui
    pyautogui.press(key)
    return True

def hotkey(keys):
    import pyautogui
    parts = [k.strip() for k in keys.split("+")]
    pyautogui.hotkey(*parts)
    return True

def mouse_click(x, y):
    import pyautogui
    pyautogui.click(int(x), int(y))
    return True

def mouse_move(x, y):
    import pyautogui
    pyautogui.moveTo(int(x), int(y), duration=0.3)
    return True

def mouse_scroll(direction="down", amount=3):
    import pyautogui
    amt = int(amount)
    pyautogui.scroll(-amt if direction == "down" else amt)
    return True

def take_screenshot(filename="screenshot.png"):
    import pyautogui
    path = os.path.join(os.path.expanduser("~"), "Desktop", filename)
    pyautogui.screenshot().save(path)
    print(f"  Screenshot saved: {path}")
    return path

def run_system_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout.strip() or result.stderr.strip()
        if output:
            print(output)
        return output
    except subprocess.TimeoutExpired:
        return "Command timed out"
    except Exception as e:
        return str(e)

def wait(seconds):
    time.sleep(float(seconds))
    return True

def set_volume(level):
    level = int(level)
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(level / 100, None)
    except Exception:
        run_system_command(f'powershell -c "$wsh = New-Object -ComObject WScript.Shell; '
                           f'1..{max(1,level//2)} | %{{ $wsh.SendKeys([char]175) }}"')
    return True

def mute_volume():
    run_system_command('powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"')
    return True

def lock_screen():
    ctypes.windll.user32.LockWorkStation()
    return True

def sleep_pc():
    run_system_command("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    return True

def shutdown_pc(delay=0):
    run_system_command(f"shutdown /s /t {int(delay)}")
    return True

def restart_pc(delay=0):
    run_system_command(f"shutdown /r /t {int(delay)}")
    return True

def cancel_shutdown():
    run_system_command("shutdown /a")
    return True

def empty_recycle_bin():
    try:
        import winshell
        winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
    except Exception:
        run_system_command('powershell -c "Clear-RecycleBin -Force"')
    print("  Recycle Bin emptied.")
    return True

def clear_temp_files():
    paths = [
        os.environ.get("TEMP", ""),
        os.environ.get("TMP", ""),
        r"C:\Windows\Temp",
    ]
    freed = 0
    for p in paths:
        if not p or not os.path.exists(p):
            continue
        for item in os.listdir(p):
            item_path = os.path.join(p, item)
            try:
                if os.path.isfile(item_path):
                    freed += os.path.getsize(item_path)
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
            except Exception:
                continue
    print(f"  Cleared {freed / (1024*1024):.1f} MB of temp files.")
    return True

def kill_process(name):
    run_system_command(f"taskkill /F /IM {name} /T")
    print(f"  Killed: {name}")
    return True

def get_wifi_password(ssid=None):
    if ssid:
        out = run_system_command(f'netsh wlan show profile name="{ssid}" key=clear')
        m = re.search(r"Key Content\s+:\s+(.+)", out)
        print(f"  Password: {m.group(1).strip()}" if m else "  No password found.")
    else:
        out = run_system_command("netsh wlan show profiles")
        profiles = re.findall(r"All User Profile\s+:\s+(.+)", out)
        for p in profiles:
            p = p.strip()
            detail = run_system_command(f'netsh wlan show profile name="{p}" key=clear')
            m = re.search(r"Key Content\s+:\s+(.+)", detail)
            pw = m.group(1).strip() if m else "open"
            print(f"  {p}: {pw}")
    return True

def check_internet():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        print("  Internet: Connected")
        return True
    except OSError:
        print("  Internet: Not connected")
        return False

def get_public_ip():
    try:
        ip = urllib.request.urlopen("https://api.ipify.org", timeout=5).read().decode()
        print(f"  Public IP: {ip}")
        return ip
    except Exception:
        print("  Could not fetch public IP.")
        return None

def flush_dns():
    run_system_command("ipconfig /flushdns")
    print("  DNS cache flushed.")
    return True

def reset_network():
    for cmd in ["netsh int ip reset", "netsh winsock reset",
                "ipconfig /flushdns", "ipconfig /release", "ipconfig /renew"]:
        run_system_command(cmd)
    print("  Network stack reset. Restart recommended.")
    return True

def ping_host(host="8.8.8.8"):
    out = run_system_command(f"ping -n 4 {host}")
    print(out)
    return True

def create_folder(path):
    os.makedirs(path, exist_ok=True)
    print(f"  Created: {path}")
    return True

def delete_file(path):
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        print(f"  Deleted: {path}")
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False

def rename_file(src, dst):
    try:
        os.rename(src, dst)
        print(f"  Renamed: {src} -> {dst}")
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False

def copy_file(src, dst):
    try:
        shutil.copy2(src, dst)
        print(f"  Copied: {src} -> {dst}")
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False

def zip_folder(folder_path, output_zip=None):
    if not output_zip:
        output_zip = folder_path.rstrip("/\\") + "_backup.zip"
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                fp = os.path.join(root, file)
                zf.write(fp, os.path.relpath(fp, folder_path))
    print(f"  Zipped to: {output_zip}")
    return output_zip

def find_files(pattern, search_dir=None):
    if not search_dir:
        search_dir = os.path.expanduser("~")
    results = []
    for root, dirs, files in os.walk(search_dir):
        dirs[:] = [d for d in dirs if d not in ["$Recycle.Bin", "Windows", "node_modules"]]
        for f in files:
            if re.search(pattern, f, re.IGNORECASE):
                results.append(os.path.join(root, f))
    for r in results[:20]:
        print(f"  {r}")
    print(f"  Found {len(results)} file(s).")
    return results

def open_file_location(path):
    subprocess.Popen(f'explorer /select,"{path}"')
    return True

def read_file(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        print(content[:2000])
        return content
    except Exception as e:
        print(f"  Error: {e}")
        return None

def write_file(path, content):
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  Written: {path}")
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False

def append_file(path, content):
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(content + "\n")
        print(f"  Appended to: {path}")
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False

def disk_usage(drive="C:"):
    total, used, free = shutil.disk_usage(drive)
    gb = 1024 ** 3
    print(f"  {drive} — Total: {total/gb:.1f}GB | Used: {used/gb:.1f}GB | Free: {free/gb:.1f}GB")
    return True

def battery_status():
    try:
        import psutil
        bat = psutil.sensors_battery()
        if bat:
            plug = "plugged in" if bat.power_plugged else "on battery"
            mins = int(bat.secsleft / 60) if bat.secsleft > 0 else "?"
            print(f"  Battery: {int(bat.percent)}% — {plug} — {mins} min remaining")
        else:
            print("  No battery (desktop?)")
    except Exception:
        run_system_command("WMIC Path Win32_Battery Get EstimatedChargeRemaining")
    return True

def top_processes(count=10):
    try:
        import psutil
        procs = []
        for p in psutil.process_iter(["name", "cpu_percent", "memory_info"]):
            try:
                procs.append((p.info["name"], p.info["cpu_percent"], p.info["memory_info"].rss))
            except Exception:
                continue
        procs.sort(key=lambda x: x[2], reverse=True)
        print(f"  {'Process':<35} {'CPU%':>6} {'RAM MB':>8}")
        print("  " + "-" * 52)
        for name, cpu, mem in procs[:int(count)]:
            print(f"  {name:<35} {cpu:>6.1f} {mem/1024/1024:>8.1f}")
    except Exception:
        run_system_command("tasklist /FO TABLE /NH")
    return True

def set_wallpaper(path):
    ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)
    print(f"  Wallpaper set: {path}")
    return True

def notify(title, message, duration=5):
    try:
        from win10toast import ToastNotifier
        ToastNotifier().show_toast(title, message, duration=int(duration), threaded=True)
    except Exception:
        run_system_command(f"powershell -c \"New-BurntToastNotification -Text '{title}', '{message}'\"")
    return True

def speak(text):
    run_system_command(
        f"powershell -c \"Add-Type -AssemblyName System.Speech; "
        f"$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Speak('{text}')\""
    )
    return True

def set_reminder(message, minutes):
    import threading
    def _remind():
        time.sleep(int(minutes) * 60)
        notify("ARIA Reminder", message)
        speak(message)
    threading.Thread(target=_remind, daemon=True).start()
    print(f"  Reminder set for {minutes} minute(s): {message}")
    return True

def download_file(url, save_path=None):
    if not save_path:
        filename = url.split("/")[-1].split("?")[0] or "download"
        save_path = os.path.join(os.path.expanduser("~"), "Downloads", filename)
    try:
        import requests
        r = requests.get(url, stream=True, timeout=30)
        with open(save_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    except Exception:
        urllib.request.urlretrieve(url, save_path)
    print(f"  Downloaded: {save_path}")
    return save_path

def get_clipboard():
    try:
        import pyperclip
        content = pyperclip.paste()
        print(f"  Clipboard: {content[:200]}")
        return content
    except Exception:
        return ""

def set_clipboard(text):
    try:
        import pyperclip
        pyperclip.copy(text)
        print("  Copied to clipboard.")
        return True
    except Exception:
        return False

def open_calendar(date=None):
    if date:
        open_url(f"https://calendar.google.com/calendar/r/day/{date.replace('-', '/')}", browser="zen")
    else:
        open_url("https://calendar.google.com", browser="zen")
    return True

def open_gmail():
    open_url("https://mail.google.com", browser="zen")
    return True

def translate_text(text, target_lang="en"):
    import urllib.parse
    open_url(f"https://translate.google.com/?sl=auto&tl={target_lang}&text={urllib.parse.quote(text)}", browser="zen")
    return True

def check_weather(city=""):
    open_url(f"https://wttr.in/{city}", browser="zen")
    return True

def run_python(code):
    try:
        exec(code, {})
        return True
    except Exception as e:
        print(f"  Python error: {e}")
        return False

def generate_password(length=16):
    import secrets, string
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    pwd = "".join(secrets.choice(chars) for _ in range(int(length)))
    print(f"  Generated: {pwd}")
    set_clipboard(pwd)
    return pwd

def get_system_info():
    run_system_command('systeminfo | findstr /C:"OS" /C:"RAM" /C:"Processor"')
    return True

def enable_dark_mode():
    run_system_command(
        "reg add HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize "
        "/v AppsUseLightTheme /t REG_DWORD /d 0 /f"
    )
    print("  Dark mode enabled.")
    return True

def enable_light_mode():
    run_system_command(
        "reg add HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize "
        "/v AppsUseLightTheme /t REG_DWORD /d 1 /f"
    )
    print("  Light mode enabled.")
    return True

def check_startup_programs():
    run_system_command("reg query HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run")
    return True

def install_package(package, manager="pip"):
    cmds = {
        "pip":    f"pip install {package} --quiet",
        "npm":    f"npm install -g {package}",
        "winget": f"winget install {package}",
        "choco":  f"choco install {package} -y",
    }
    run_system_command(cmds.get(manager, cmds["pip"]))
    print(f"  Installed: {package} via {manager}")
    return True

def open_hosts_file():
    subprocess.Popen(["notepad", r"C:\Windows\System32\drivers\etc\hosts"])
    return True

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        print(f"  Local IP: {ip}")
        return ip
    except Exception:
        run_system_command("ipconfig | findstr IPv4")
        return None

def scan_ports(host="localhost", start=1, end=1024):
    print(f"  Scanning {host} ports {start}-{end}...")
    open_ports = []
    for port in range(int(start), int(end) + 1):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.1)
        if s.connect_ex((host, port)) == 0:
            open_ports.append(port)
            print(f"  Open: {port}")
        s.close()
    print(f"  Scan complete. {len(open_ports)} open port(s).")
    return open_ports

def focus_window(title_contains):
    import ctypes
    found = []
    def callback(hwnd, _):
        if ctypes.windll.user32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(256)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, 256)
            if title_contains.lower() in buf.value.lower() and buf.value:
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                found.append(buf.value)
        return True
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
    ctypes.windll.user32.EnumWindows(WNDENUMPROC(callback), 0)
    if found:
        print(f"  Focused: {found[0]}")
    return bool(found)

def close_window(title_contains):
    run_system_command(f'taskkill /FI "WINDOWTITLE eq *{title_contains}*" /F')
    return True

def minimize_all():
    import pyautogui
    pyautogui.hotkey("win", "d")
    return True

def maximize_window():
    import pyautogui
    pyautogui.hotkey("win", "up")
    return True

def git_status(repo_path="."):
    return run_system_command(f'cd /d "{repo_path}" && git status')

def git_commit(message, repo_path="."):
    run_system_command(f'cd /d "{repo_path}" && git add -A && git commit -m "{message}"')
    return True

def git_push(repo_path="."):
    run_system_command(f'cd /d "{repo_path}" && git push')
    return True

def create_shortcut(target, shortcut_name=None, location="Desktop"):
    try:
        import winshell
        from win32com.client import Dispatch
        loc = winshell.desktop() if location == "Desktop" else location
        name = shortcut_name or os.path.basename(target).replace(".exe", "")
        path = os.path.join(loc, f"{name}.lnk")
        sc = Dispatch("WScript.Shell").CreateShortCut(path)
        sc.Targetpath = target
        sc.save()
        print(f"  Shortcut created: {path}")
        return True
    except Exception as e:
        print(f"  Shortcut error: {e}")
        return False


ACTIONS = {
    "open_browser":       open_browser,
    "open_url":           open_url,
    "browser_wait":       browser_wait,
    "browser_click":      browser_find_and_click,
    "browser_type":       browser_type,
    "browser_press":      browser_press_key,
    "browser_text":       browser_get_text,
    "close_browser":      close_browser,
    "send_whatsapp":      send_whatsapp,
    "search_google":      search_google,
    "open_youtube":       open_youtube,
    "open_app":           open_app,
    "type_text":          type_text,
    "press_key":          press_key,
    "hotkey":             hotkey,
    "mouse_click":        mouse_click,
    "mouse_move":         mouse_move,
    "mouse_scroll":       mouse_scroll,
    "screenshot":         take_screenshot,
    "run_command":        run_system_command,
    "wait":               wait,
    "set_volume":         set_volume,
    "mute":               mute_volume,
    "lock_screen":        lock_screen,
    "sleep_pc":           sleep_pc,
    "shutdown":           shutdown_pc,
    "restart":            restart_pc,
    "cancel_shutdown":    cancel_shutdown,
    "empty_recycle_bin":  empty_recycle_bin,
    "clear_temp":         clear_temp_files,
    "kill_process":       kill_process,
    "wifi_password":      get_wifi_password,
    "check_internet":     check_internet,
    "public_ip":          get_public_ip,
    "local_ip":           get_local_ip,
    "flush_dns":          flush_dns,
    "reset_network":      reset_network,
    "ping":               ping_host,
    "scan_ports":         scan_ports,
    "create_folder":      create_folder,
    "delete_file":        delete_file,
    "rename_file":        rename_file,
    "copy_file":          copy_file,
    "zip_folder":         zip_folder,
    "find_files":         find_files,
    "open_file_location": open_file_location,
    "read_file":          read_file,
    "write_file":         write_file,
    "append_file":        append_file,
    "disk_usage":         disk_usage,
    "battery_status":     battery_status,
    "top_processes":      top_processes,
    "set_wallpaper":      set_wallpaper,
    "notify":             notify,
    "speak":              speak,
    "set_reminder":       set_reminder,
    "download_file":      download_file,
    "get_clipboard":      get_clipboard,
    "set_clipboard":      set_clipboard,
    "open_calendar":      open_calendar,
    "open_gmail":         open_gmail,
    "translate":          translate_text,
    "weather":            check_weather,
    "run_python":         run_python,
    "generate_password":  generate_password,
    "system_info":        get_system_info,
    "dark_mode":          enable_dark_mode,
    "light_mode":         enable_light_mode,
    "startup_programs":   check_startup_programs,
    "install_package":    install_package,
    "open_hosts":         open_hosts_file,
    "focus_window":       focus_window,
    "close_window":       close_window,
    "minimize_all":       minimize_all,
    "maximize_window":    maximize_window,
    "git_status":         git_status,
    "git_commit":         git_commit,
    "git_push":           git_push,
    "create_shortcut":    create_shortcut,
    "set_browser":        set_browser,
}

def execute_action(action_name, **kwargs):
    func = ACTIONS.get(action_name)
    if not func:
        return False
    try:
        sig = inspect.signature(func)
        valid = set(sig.parameters.keys())
        has_var = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
        filtered = kwargs if has_var else {k: v for k, v in kwargs.items() if k in valid}
        return func(**filtered)
    except Exception as e:
        print(f"  Action error ({action_name}): {e}")
        return False
