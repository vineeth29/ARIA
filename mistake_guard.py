import os, re, time, threading, datetime, json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(SCRIPT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

_clipboard_timer = None
_clipboard_lock  = threading.Lock()

DANGEROUS_PATTERNS = [
    (r'\bdelete\b.*\b(all|everything|folder|directory)\b', "delete_all",
     "This will delete everything in that location. Are you sure?"),
    (r'\bformat\b.*\b(drive|disk|partition|c:)\b', "format_drive",
     "Formatting will ERASE ALL DATA on that drive. Are you absolutely sure?"),
    (r'\bshutdown\b|\bturn off\b|\bpower off\b', "shutdown",
     "About to shutdown. Any unsaved work will be lost. Continue?"),
    (r'\bkill\b.*\b(all|every)\b', "kill_all",
     "This will kill all matching processes. Continue?"),
    (r'\brm\s+-rf\b|\bdel\s+/[sq]\b', "force_delete",
     "This is a force-delete command. Cannot be undone. Sure?"),
    (r'\bsend\b.*\b(everyone|all|broadcast)\b', "mass_send",
     "About to send to multiple people. Double-check recipients?"),
]

TONE_PATTERNS = [
    (r'\b(hate|stupid|idiot|dumb|useless|worst)\b', "aggressive",
     "This message sounds harsh. Want me to soften it first?"),
    (r'!!{2,}|[A-Z]{5,}', "aggressive_caps",
     "Message has all-caps or multiple exclamation marks — sounds angry. Send anyway?"),
    (r'\bsorry\b.*\bsorry\b', "over_apologetic",
     "You're apologising twice. You might not need to apologise at all. Review?"),
    (r'\basap\b|urgently|immediately', "pressure",
     "This message creates urgency. Is that the tone you want?"),
]

def check_command_safety(text):
    tl = text.lower()
    for pattern, category, warning in DANGEROUS_PATTERNS:
        if re.search(pattern, tl):
            return True, warning, category
    return False, None, None

def check_message_tone(text):
    warnings = []
    for pattern, category, warning in TONE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(warning)
    return warnings

def start_clipboard_guard(clear_after_seconds=60):
    def _watch():
        try:
            import pyperclip
            initial = pyperclip.paste()
            time.sleep(clear_after_seconds)
            current = pyperclip.paste()
            if current == initial and _looks_like_password(current):
                pyperclip.copy("")
                print(f"\n  [GUARD] Clipboard cleared — sensitive content removed after {clear_after_seconds}s")
        except Exception:
            pass
    with _clipboard_lock:
        t = threading.Thread(target=_watch, daemon=True)
        t.start()

def _looks_like_password(text):
    if not text or len(text) > 200 or len(text) < 6:
        return False
    has_upper  = any(c.isupper() for c in text)
    has_lower  = any(c.islower() for c in text)
    has_digit  = any(c.isdigit() for c in text)
    has_symbol = any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in text)
    no_spaces  = " " not in text
    score = sum([has_upper, has_lower, has_digit, has_symbol, no_spaces])
    return score >= 3

def check_file_delete(path):
    if not os.path.exists(path):
        return None
    if os.path.isdir(path):
        count = sum(len(files) for _, _, files in os.walk(path))
        size  = sum(
            os.path.getsize(os.path.join(r, f))
            for r, _, files in os.walk(path)
            for f in files
        ) / (1024 * 1024)
        if count > 10 or size > 50:
            return f"That folder has {count} files ({size:.0f}MB). Delete all of it?"
        return f"Delete folder '{os.path.basename(path)}' with {count} files?"
    size = os.path.getsize(path) / (1024 * 1024)
    return f"Delete '{os.path.basename(path)}' ({size:.1f}MB)? This can't be undone."

def is_dangerous_request(text):
    is_dangerous, warning, _ = check_command_safety(text)
    return is_dangerous, warning

def check_email_before_send(email_text):
    warnings = check_message_tone(email_text)
    word_count = len(email_text.split())
    if word_count > 500:
        warnings.append(f"Email is {word_count} words — quite long. Consider shortening?")
    return warnings
