import json, os, datetime, re

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(SCRIPT_DIR, "data", "negotiator_history.json")
os.makedirs(os.path.join(SCRIPT_DIR, "data"), exist_ok=True)

BAD_PATTERNS = [
    (r"sleep at (\d+)", "sleep_time"),
    (r"sleep by (\d+)", "sleep_time"),
    (r"wake up at (\d+)", "wake_time"),
    (r"study for (\d+)\s*hour", "study_hours"),
    (r"work for (\d+)\s*hour", "work_hours"),
    (r"(\d+)\s*minute break", "break_minutes"),
    (r"exercise (\d+)", "exercise_minutes"),
    (r"finish by (\d+)", "finish_time"),
    (r"done by (\d+)", "finish_time"),
]

def _load():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"promises": [], "outcomes": {}}

def _save(data):
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

def detect_promise(text):
    tl = text.lower()
    for pattern, category in BAD_PATTERNS:
        m = re.search(pattern, tl)
        if m:
            return category, m.group(1), text
    vague_patterns = [
        (r"i'll (sleep|rest|stop) (soon|later|early)", "sleep_vague"),
        (r"just (one more|a few more) (minute|hour|episode|game)", "just_one_more"),
        (r"i'll (start|begin|do it) (tomorrow|later|soon)", "procrastination"),
        (r"i (won't|wont) (eat|drink|have) (junk|fast food|coffee)", "diet_promise"),
    ]
    for pattern, category in vague_patterns:
        if re.search(pattern, tl):
            return category, None, text
    return None, None, None

def log_promise(category, value, original_text):
    data = _load()
    data["promises"].append({
        "category":  category,
        "value":     value,
        "text":      original_text,
        "time":      datetime.datetime.now().isoformat(),
        "kept":      None,
    })
    data["promises"] = data["promises"][-100:]
    _save(data)

def get_past_promises(category, limit=5):
    data = _load()
    return [p for p in data["promises"] if p["category"] == category][-limit:]

def build_negotiation(category, value, original_text):
    past = get_past_promises(category, limit=5)
    if not past:
        log_promise(category, value, original_text)
        return None
    broken_count = sum(1 for p in past if p.get("kept") is False)
    unknown_count = sum(1 for p in past if p.get("kept") is None)
    total = len(past)
    if broken_count == 0 and unknown_count > total * 0.7:
        log_promise(category, value, original_text)
        return None
    messages = {
        "sleep_time": (
            f"Hold on — you've said this {total} time(s) before. "
            f"Based on your history, you usually end up sleeping much later. "
            f"Want to set a firm reminder instead of just a goal?"
        ),
        "just_one_more": (
            f"You've said 'just one more' {total} time(s) recently. "
            f"It usually turns into several more. Want me to set a hard stop timer?"
        ),
        "procrastination": (
            f"You've said you'll do it later {total} time(s) recently. "
            f"Want to break it into one small step you can do right now instead?"
        ),
        "study_hours": (
            f"You've planned {value}-hour study sessions {total} time(s). "
            f"Want me to break it into focused 25-min blocks with breaks instead?"
        ),
        "diet_promise": (
            f"You've made this promise {total} time(s). "
            f"Want me to track it and remind you when you're tempted?"
        ),
    }
    response = messages.get(category, (
        f"You've made a similar commitment {total} time(s) recently. "
        f"Want me to help you actually stick to it this time?"
    ))
    log_promise(category, value, original_text)
    return response

def is_negotiable(text):
    cat, val, orig = detect_promise(text)
    return cat is not None

def check_and_negotiate(text):
    cat, val, orig = detect_promise(text)
    if not cat:
        return None
    return build_negotiation(cat, val, orig)
