import os, sys, subprocess, shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR   = os.path.join(SCRIPT_DIR, "dist")
BUILD_DIR  = os.path.join(SCRIPT_DIR, "build")

SPEC = '''
# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['installer.py'],
    pathex=['{script_dir}'],
    binaries=[],
    datas=[
        ('aria.py',          '.'),
        ('providers.py',     '.'),
        ('automation.py',    '.'),
        ('personalities.py', '.'),
        ('mood.py',          '.'),
        ('notes.py',         '.'),
        ('focus.py',         '.'),
        ('scheduler.py',     '.'),
        ('habits.py',        '.'),
        ('tracker.py',       '.'),
        ('health.py',        '.'),
        ('clipboard_mgr.py', '.'),
        ('smart_dj.py',      '.'),
        ('tiler.py',         '.'),
        ('games.py',         '.'),
        ('sounds.py',        '.'),
        ('triggers.py',      '.'),
        ('sysinfo.py',       '.'),
        ('aria_prompt.txt',  '.'),
        ('config.json',      '.'),
        ('data',             'data'),
    ],
    hiddenimports=[
        'requests','psutil','pyautogui','selenium',
        'webdriver_manager','webdriver_manager.microsoft',
        'pyperclip','win10toast','winshell','win32com',
        'win32com.client','pycaw','comtypes','json',
        'subprocess','threading','datetime','socket',
        'urllib','urllib.request','urllib.parse',
        'zipfile','shutil','ctypes','re','inspect',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
    name='ARIA_Setup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
'''.replace('{script_dir}', SCRIPT_DIR.replace('\\', '\\\\'))


def main():
    print("\n  ARIA EXE Builder")
    print("  ================\n")

    print("  Step 1/3 — Installing PyInstaller...")
    r = subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller", "--quiet"], capture_output=True)
    if r.returncode != 0:
        print("  Failed to install PyInstaller. Run: pip install pyinstaller")
        sys.exit(1)
    print("  PyInstaller ready.\n")

    spec_path = os.path.join(SCRIPT_DIR, "ARIA_Setup.spec")
    with open(spec_path, "w") as f:
        f.write(SPEC)
    print("  Step 2/3 — Building EXE (this takes 1-3 minutes)...")
    r = subprocess.run(
        [sys.executable, "-m", "PyInstaller", spec_path, "--distpath", DIST_DIR,
         "--workpath", BUILD_DIR, "--noconfirm"],
        capture_output=True, text=True, cwd=SCRIPT_DIR
    )
    if r.returncode != 0:
        print("  Build failed. Error output:")
        print(r.stderr[-2000:])
        sys.exit(1)

    exe_path = os.path.join(DIST_DIR, "ARIA_Setup.exe")
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"  Step 3/3 — Done!\n")
        print(f"  EXE created: {exe_path}")
        print(f"  Size: {size_mb:.1f} MB\n")
        print("  Share ARIA_Setup.exe with anyone.")
        print("  When they run it, it will:")
        print("   1. Install all Python packages automatically")
        print("   2. Walk them through getting free API keys")
        print("   3. Test everything works")
        print("   4. Launch ARIA\n")

        # Copy to desktop for convenience
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        dest = os.path.join(desktop, "ARIA_Setup.exe")
        try:
            shutil.copy2(exe_path, dest)
            print(f"  Also copied to Desktop: {dest}")
        except Exception:
            pass
    else:
        print("  Build completed but EXE not found. Check dist/ folder.")

    try:
        shutil.rmtree(BUILD_DIR, ignore_errors=True)
        os.remove(spec_path)
    except Exception:
        pass


if __name__ == "__main__":
    main()
