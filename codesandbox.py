import os, sys, subprocess, tempfile, re, json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(os.path.expanduser("~"), "ARIA_Scripts")
os.makedirs(SCRIPTS_DIR, exist_ok=True)

def run_python_code(code, timeout=30):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py",
                                     delete=False, encoding="utf-8") as f:
        f.write(code)
        tmp_path = f.name
    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True, text=True,
            timeout=timeout, encoding="utf-8", errors="replace"
        )
        output = result.stdout.strip()
        errors = result.stderr.strip()
        return {
            "success":   result.returncode == 0,
            "output":    output[:3000] if output else "",
            "error":     errors[:2000] if errors else "",
            "exit_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "", "error": f"Timed out after {timeout}s", "exit_code": -1}
    except Exception as e:
        return {"success": False, "output": "", "error": str(e), "exit_code": -1}
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

def run_powershell(code, timeout=30):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1",
                                     delete=False, encoding="utf-8") as f:
        f.write(code)
        tmp_path = f.name
    try:
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", tmp_path],
            capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace"
        )
        return {
            "success":   result.returncode == 0,
            "output":    result.stdout.strip()[:3000],
            "error":     result.stderr.strip()[:2000],
            "exit_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "", "error": "Timed out", "exit_code": -1}
    except Exception as e:
        return {"success": False, "output": "", "error": str(e), "exit_code": -1}
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

def auto_install_and_run(code, timeout=30):
    result = run_python_code(code, timeout)
    if not result["success"] and "ModuleNotFoundError" in result["error"]:
        m = re.search(r"No module named '([^']+)'", result["error"])
        if m:
            pkg = m.group(1).replace("_", "-")
            print(f"  Installing {pkg}...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg, "--quiet"],
                capture_output=True
            )
            result = run_python_code(code, timeout)
    return result

def save_script(name, code, description=""):
    safe_name = re.sub(r'[^\w\-]', '_', name)
    path = os.path.join(SCRIPTS_DIR, f"{safe_name}.py")
    header = f'# ARIA Script: {name}\n# {description}\n\n' if description else ""
    with open(path, "w", encoding="utf-8") as f:
        f.write(header + code)
    return path

def list_scripts():
    scripts = []
    for f in os.listdir(SCRIPTS_DIR):
        if f.endswith(".py"):
            path = os.path.join(SCRIPTS_DIR, f)
            size = os.path.getsize(path)
            scripts.append(f"  {f} ({size} bytes)")
    if not scripts:
        return "No saved scripts yet."
    return "Saved scripts:\n" + "\n".join(scripts)

def run_saved_script(name):
    safe_name = re.sub(r'[^\w\-]', '_', name)
    path = os.path.join(SCRIPTS_DIR, f"{safe_name}.py")
    if not os.path.exists(path):
        path = os.path.join(SCRIPTS_DIR, name if name.endswith(".py") else name + ".py")
    if not os.path.exists(path):
        return {"success": False, "error": f"Script not found: {name}", "output": ""}
    with open(path, encoding="utf-8") as f:
        code = f.read()
    return auto_install_and_run(code)

def format_result(result):
    if result["success"]:
        out = result.get("output", "")
        return f"✅ Ran successfully.\n{out}" if out else "✅ Ran successfully (no output)."
    else:
        err = result.get("error", "Unknown error")
        return f"❌ Failed:\n{err}"
