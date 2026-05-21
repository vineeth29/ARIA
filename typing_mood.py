import time, threading, collections, datetime, json, os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE  = os.path.join(SCRIPT_DIR, "data", "typing_mood.json")
os.makedirs(os.path.join(SCRIPT_DIR, "data"), exist_ok=True)

_session = {
    "keystrokes":    [],
    "backspaces":    0,
    "pauses":        [],
    "last_key_time": None,
    "start_time":    time.time(),
}
_lock = threading.Lock()

def record_input(text, elapsed_seconds):
    with _lock:
        words      = len(text.split())
        backspaces = max(0, len(text) * 2 - len(text))
        chars      = len(text)
        _session["keystrokes"].append({
            "chars":   chars,
            "words":   words,
            "elapsed": elapsed_seconds,
            "time":    datetime.datetime.now().isoformat(),
        })
        if elapsed_seconds > 10:
            _session["pauses"].append(elapsed_seconds)

def analyse_mood():
    with _lock:
        recent = _session["keystrokes"][-10:]
    if not recent:
        return "neutral", 5
    total_chars   = sum(k["chars"] for k in recent)
    total_elapsed = sum(k["elapsed"] for k in recent) or 1
    chars_per_sec  = total_chars / total_elapsed
    long_pauses    = sum(1 for k in recent if k["elapsed"] > 15)
    avg_msg_len    = total_chars / len(recent)
    if chars_per_sec > 8 and avg_msg_len < 30:
        return "stressed", 8
    elif chars_per_sec > 6 and avg_msg_len > 50:
        return "focused", 7
    elif long_pauses >= 3 and chars_per_sec < 2:
        return "stuck", 6
    elif chars_per_sec < 1.5 and avg_msg_len < 20:
        return "tired", 4
    elif chars_per_sec > 4 and avg_msg_len > 40:
        return "engaged", 7
    return "neutral", 5

def get_mood_adjustment(mood):
    adjustments = {
        "stressed": (
            "The user seems stressed right now — short fast typing. "
            "Be extra calm, concise, and reassuring. No long explanations."
        ),
        "stuck": (
            "The user seems stuck — long pauses, slow typing. "
            "Be extra clear and step-by-step. Ask if they need help breaking the problem down."
        ),
        "tired": (
            "The user seems tired — very slow, short messages. "
            "Keep responses short and simple. Offer to summarise things."
        ),
        "focused": (
            "The user is in focused mode — detailed messages, steady pace. "
            "Match their depth. Give thorough answers."
        ),
        "engaged": (
            "The user is engaged and active. Match their energy. Be dynamic."
        ),
        "neutral": "",
    }
    return adjustments.get(mood, "")

def get_context_injection():
    mood, intensity = analyse_mood()
    adjustment = get_mood_adjustment(mood)
    if not adjustment:
        return ""
    return f"\n[TYPING MOOD DETECTED: {mood} (intensity {intensity}/10)]\n{adjustment}"

def save_mood_log():
    mood, intensity = analyse_mood()
    try:
        log = []
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE) as f:
                log = json.load(f)
        log.append({
            "time":      datetime.datetime.now().isoformat(),
            "mood":      mood,
            "intensity": intensity,
            "messages":  len(_session["keystrokes"]),
        })
        log = log[-500:]
        with open(DATA_FILE, "w") as f:
            json.dump(log, f, indent=2)
    except Exception:
        pass

def get_mood_history():
    try:
        with open(DATA_FILE) as f:
            log = json.load(f)
        recent = log[-20:]
        mood_counts = collections.Counter(e["mood"] for e in recent)
        lines = ["Typing mood history (last 20 sessions):"]
        for mood, count in mood_counts.most_common():
            bar = "█" * count
            lines.append(f"  {mood:<10} {bar} {count}")
        return "\n".join(lines)
    except Exception:
        return "No mood history yet."
