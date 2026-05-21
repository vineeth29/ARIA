import os, json, urllib.request, zipfile, shutil, datetime, sys, re

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
VERSION_FILE = os.path.join(SCRIPT_DIR, "data", "version.json")
BACKUP_DIR   = os.path.join(SCRIPT_DIR, "data", "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(os.path.join(SCRIPT_DIR, "data"), exist_ok=True)

CURRENT_VERSION = "16.0"
GITHUB_REPO     = "yourusername/aria"
GITHUB_API      = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_RAW      = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main"

HEADERS = {
    "User-Agent": "ARIA-Agent/1.0",
    "Accept":     "application/json",
}

def get_current_version():
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE) as f:
                return json.load(f).get("version", CURRENT_VERSION)
        except Exception:
            pass
    return CURRENT_VERSION

def save_version(version):
    with open(VERSION_FILE, "w") as f:
        json.dump({
            "version":    version,
            "updated_at": datetime.datetime.now().isoformat(),
        }, f, indent=2)

def check_for_updates(status_cb=None):
    try:
        req = urllib.request.Request(GITHUB_API, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8) as r:
            data       = json.loads(r.read().decode())
            latest_tag = data.get("tag_name", "").lstrip("v")
            current    = get_current_version()
            changelog  = data.get("body", "No changelog available.")[:500]
            if latest_tag and latest_tag != current:
                return True, latest_tag, changelog
            return False, current, "You're on the latest version."
    except Exception as e:
        return None, None, f"Could not check for updates: {e}"

def backup_current(status_cb=None):
    ts          = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    backup_path = os.path.join(BACKUP_DIR, f"aria_backup_{ts}.zip")
    if status_cb:
        status_cb(f"Backing up current version to {backup_path}...")
    try:
        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in os.listdir(SCRIPT_DIR):
                if f.endswith(".py") or f.endswith(".txt") or f == "config.json":
                    zf.write(os.path.join(SCRIPT_DIR, f), f)
        old_backups = sorted(
            [f for f in os.listdir(BACKUP_DIR) if f.endswith(".zip")]
        )
        for old in old_backups[:-5]:
            os.remove(os.path.join(BACKUP_DIR, old))
        return backup_path
    except Exception as e:
        return None

def download_update(version, download_url, status_cb=None):
    tmp_zip = os.path.join(SCRIPT_DIR, "data", "aria_update.zip")
    try:
        if status_cb:
            status_cb(f"Downloading v{version}...")
        req = urllib.request.Request(download_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as r:
            with open(tmp_zip, "wb") as f:
                f.write(r.read())
        return tmp_zip
    except Exception as e:
        return None

def apply_update(zip_path, status_cb=None):
    try:
        if status_cb:
            status_cb("Applying update...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            for name in zf.namelist():
                if name.endswith(".py") and "/" not in name:
                    if name == "config.json":
                        continue
                    zf.extract(name, SCRIPT_DIR)
                    if status_cb:
                        status_cb(f"Updated: {name}")
        os.remove(zip_path)
        return True
    except Exception as e:
        return False

def update_aria(status_cb=None):
    if status_cb:
        status_cb("Checking for updates...")
    has_update, version, changelog = check_for_updates(status_cb)
    if has_update is None:
        return False, changelog
    if not has_update:
        return False, f"Already on latest version ({version})."
    backup_path = backup_current(status_cb)
    if not backup_path:
        return False, "Could not create backup. Update cancelled."
    if status_cb:
        status_cb(f"New version {version} available!")
        status_cb(f"Changelog: {changelog[:200]}")
    return True, (
        f"Update available: v{version}\n"
        f"Backup saved to: {backup_path}\n\n"
        f"Changelog:\n{changelog}\n\n"
        f"To apply: the update will be downloaded from GitHub.\n"
        f"Set your GitHub repo URL in updater.py → GITHUB_REPO first."
    )

def rollback(status_cb=None):
    backups = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.endswith(".zip")],
        reverse=True
    )
    if not backups:
        return False, "No backups found."
    latest = os.path.join(BACKUP_DIR, backups[0])
    if status_cb:
        status_cb(f"Rolling back to: {backups[0]}")
    try:
        with zipfile.ZipFile(latest, "r") as zf:
            for name in zf.namelist():
                if name.endswith(".py") and name != "config.json":
                    zf.extract(name, SCRIPT_DIR)
        return True, f"Rolled back to {backups[0]}. Restart ARIA."
    except Exception as e:
        return False, f"Rollback failed: {e}"

def get_version_info():
    current = get_current_version()
    backups = [f for f in os.listdir(BACKUP_DIR) if f.endswith(".zip")]
    return (
        f"ARIA Version : v{current}\n"
        f"Backups      : {len(backups)} saved\n"
        f"Script dir   : {SCRIPT_DIR}"
    )
