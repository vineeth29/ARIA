"""
ARIA Smart Clipboard History
==============================
Watches clipboard, builds searchable history.
Background thread monitors every 2 seconds, fully local.
"""

import json, os, datetime, time, threading

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CLIPBOARD_FILE = os.path.join(DATA_DIR, "clipboard.json")

_running = False
_lock = threading.Lock()
_MAX_ENTRIES = 500

# ════════════════════════════════════════════════════════════════
# STORAGE
# ════════════════════════════════════════════════════════════════

def _load():
    if os.path.exists(CLIPBOARD_FILE):
        try:
            with open(CLIPBOARD_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return []

def _save(entries):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CLIPBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

# ════════════════════════════════════════════════════════════════
# CLIPBOARD MONITOR
# ════════════════════════════════════════════════════════════════

def _get_clipboard_text():
    """Get current clipboard text using multiple methods."""
    # Try pyperclip first
    try:
        import pyperclip
        return pyperclip.paste()
    except Exception:
        pass
    # Fallback: use ctypes on Windows
    try:
        import ctypes
        CF_TEXT = 1
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        user32.OpenClipboard(0)
        try:
            if user32.IsClipboardFormatAvailable(13):  # CF_UNICODETEXT
                data = user32.GetClipboardData(13)
                text = ctypes.c_wchar_p(data).value
                return text or ""
        finally:
            user32.CloseClipboard()
    except Exception:
        pass
    return ""

def start_monitor():
    """Start background clipboard monitoring thread."""
    global _running
    if _running:
        return
    _running = True

    def _monitor_loop():
        last_text = ""
        while _running:
            try:
                current = _get_clipboard_text()
                if current and current != last_text and len(current.strip()) > 0:
                    last_text = current
                    _add_entry(current.strip())
            except Exception:
                pass
            time.sleep(2)

    t = threading.Thread(target=_monitor_loop, daemon=True)
    t.start()

def stop_monitor():
    global _running
    _running = False

def _add_entry(text):
    """Add a clipboard entry (deduplicated)."""
    with _lock:
        entries = _load()
        # Don't add duplicates of the most recent entry
        if entries and entries[-1].get("text") == text:
            return
        entry = {
            "text": text[:2000],  # cap at 2000 chars
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": _detect_type(text),
        }
        entries.append(entry)
        # Keep only last N entries
        if len(entries) > _MAX_ENTRIES:
            entries = entries[-_MAX_ENTRIES:]
        _save(entries)

def _detect_type(text):
    """Detect content type of clipboard text."""
    text_lower = text.lower().strip()
    if text_lower.startswith(("http://", "https://", "www.")):
        return "link"
    if "@" in text and "." in text:
        return "email"
    if text.replace("-", "").replace("+", "").replace(" ", "").isdigit() and len(text) >= 7:
        return "phone"
    if len(text) > 200:
        return "text_block"
    return "text"

# ════════════════════════════════════════════════════════════════
# QUERY FUNCTIONS
# ════════════════════════════════════════════════════════════════

def get_recent(limit=10):
    """Get recent clipboard entries."""
    entries = _load()
    return entries[-limit:]

def search(query):
    """Search clipboard history."""
    entries = _load()
    query_lower = query.lower()
    return [e for e in entries if query_lower in e["text"].lower()]

def get_links():
    """Get all copied links."""
    entries = _load()
    return [e for e in entries if e.get("type") == "link"]

def get_by_time(minutes_ago):
    """Get entries from the last N minutes."""
    entries = _load()
    cutoff = datetime.datetime.now() - datetime.timedelta(minutes=minutes_ago)
    cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")
    return [e for e in entries if e["timestamp"] >= cutoff_str]

def format_entries(entries_list):
    """Format clipboard entries for display."""
    if not entries_list:
        return "  No clipboard entries found."
    lines = []
    for e in entries_list:
        icon = {"link": "🔗", "email": "📧", "phone": "📞", "text_block": "📄"}.get(e.get("type"), "📋")
        text_preview = e["text"][:80] + ("..." if len(e["text"]) > 80 else "")
        lines.append(f"    {icon} [{e['timestamp'][11:]}] {text_preview}")
    return "\n".join(lines)

def get_clipboard_context():
    """Get recent clipboard as context for AI."""
    entries = _load()
    if not entries:
        return ""
    recent = entries[-5:]
    items = [f"- [{e['timestamp'][11:]}] {e['text'][:100]}" for e in recent]
    return "\n[Recent clipboard]:\n" + "\n".join(items)

def clear_history():
    """Clear all clipboard history."""
    _save([])
    return True
