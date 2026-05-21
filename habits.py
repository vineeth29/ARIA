"""
ARIA Self-Learning Habits Engine
==================================
Learns your patterns and suggests actions proactively.
Logs actions with timestamps, detects repetitions.
"""

import json, os, datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
HABITS_FILE = os.path.join(DATA_DIR, "habits.json")

MIN_REPS = 5  # Minimum repetitions before suggesting

def _load():
    if os.path.exists(HABITS_FILE):
        try:
            with open(HABITS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"actions": [], "patterns": {}}

def _save(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(HABITS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def log_action(action_text):
    """Log a user action for pattern detection."""
    data = _load()
    now = datetime.datetime.now()
    entry = {
        "action": action_text[:200],
        "hour": now.hour,
        "day": now.strftime("%A"),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
    }
    data["actions"].append(entry)
    # Keep last 2000 actions
    if len(data["actions"]) > 2000:
        data["actions"] = data["actions"][-2000:]
    # Update patterns
    _update_patterns(data, entry)
    _save(data)

def _update_patterns(data, entry):
    """Update pattern counts for an action."""
    action = entry["action"].lower().strip()
    hour = entry["hour"]
    day = entry["day"]
    # Pattern key: action at specific hour
    key_hour = f"{action}|hour:{hour}"
    key_day = f"{action}|day:{day}"
    key_combo = f"{action}|{day}|{hour}"
    for key in [key_hour, key_day, key_combo]:
        data["patterns"][key] = data["patterns"].get(key, 0) + 1

def get_suggestions():
    """Get proactive suggestions based on learned patterns."""
    data = _load()
    now = datetime.datetime.now()
    current_hour = now.hour
    current_day = now.strftime("%A")
    suggestions = []
    seen = set()

    for key, count in data["patterns"].items():
        if count < MIN_REPS:
            continue
        parts = key.split("|")
        action = parts[0]
        if action in seen:
            continue
        # Check if matches current time
        matches = False
        for part in parts[1:]:
            if part == f"hour:{current_hour}":
                matches = True
            if part == f"day:{current_day}":
                matches = True
        if matches:
            seen.add(action)
            suggestions.append({"action": action, "confidence": count, "reason": f"You've done this {count} times at this time"})

    # Sort by confidence
    suggestions.sort(key=lambda x: x["confidence"], reverse=True)
    return suggestions[:3]  # Top 3

def get_suggestion_text():
    """Get formatted suggestion text for display."""
    suggestions = get_suggestions()
    if not suggestions:
        return ""
    lines = []
    for s in suggestions:
        lines.append(f"  💡 Maybe: \"{s['action']}\"? ({s['reason']})")
    return "\n".join(lines)

def get_habit_stats():
    """Get habit tracking stats."""
    data = _load()
    total = len(data["actions"])
    patterns = len([k for k, v in data["patterns"].items() if v >= MIN_REPS])
    lines = ["  Habit Stats:"]
    lines.append(f"    📊 Actions logged: {total}")
    lines.append(f"    🧠 Patterns learned: {patterns}")

    # Show top patterns
    top = sorted(data["patterns"].items(), key=lambda x: x[1], reverse=True)[:5]
    if top:
        lines.append("    Top patterns:")
        for key, count in top:
            action = key.split("|")[0]
            lines.append(f"      🔄 {action} ({count}x)")
    return "\n".join(lines)

def clear_habits():
    _save({"actions": [], "patterns": {}})
    return True
