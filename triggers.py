"""
ARIA Trigger Phrases
======================
Custom trigger words that chain multiple automations.
"""

import json, os, re

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
TRIGGERS_FILE = os.path.join(DATA_DIR, "triggers.json")

BUILTIN_TRIGGERS = {
    "goodnight": {
        "name": "Goodnight Routine", "emoji": "🌙",
        "actions": [{"action": "open_url", "kwargs": {"url": "https://www.youtube.com/results?search_query=rain+sounds+for+sleeping", "browser": "zen"}}],
        "response": "Goodnight Vineeth! 🌙 Rain sounds playing. Sweet dreams! 💤"
    },
    "good morning": {
        "name": "Good Morning Routine", "emoji": "☀️",
        "actions": [
            {"action": "open_url", "kwargs": {"url": "https://mail.google.com", "browser": "zen"}},
            {"action": "open_url", "kwargs": {"url": "https://www.youtube.com/results?search_query=upbeat+morning+music", "browser": "zen"}},
        ],
        "response": "Good morning Vineeth! ☀️ Email + music ready. Let's crush today! 💪"
    },
    "study mode": {
        "name": "Study Mode", "emoji": "📚",
        "actions": [{"action": "open_url", "kwargs": {"url": "https://www.youtube.com/results?search_query=lofi+study+music", "browser": "zen"}}],
        "response": "Study mode activated! 📚 Lo-fi music playing. Focus up! 🧠"
    },
    "break time": {
        "name": "Break Time", "emoji": "☕",
        "actions": [{"action": "open_url", "kwargs": {"url": "https://www.youtube.com", "browser": "zen"}}],
        "response": "Break time! ☕ YouTube is open. Relax! 😌"
    },
    "chill mode": {
        "name": "Chill Mode", "emoji": "🎵",
        "actions": [{"action": "open_url", "kwargs": {"url": "https://www.youtube.com/results?search_query=chill+vibes+playlist", "browser": "zen"}}],
        "response": "Chill mode on 🎵 Vibes set. Relax 😎"
    },
}

def _load_custom():
    if os.path.exists(TRIGGERS_FILE):
        try:
            with open(TRIGGERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}

def _save_custom(triggers):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(TRIGGERS_FILE, "w", encoding="utf-8") as f:
        json.dump(triggers, f, indent=2, ensure_ascii=False)

def add_trigger(phrase, actions_str, response=""):
    custom = _load_custom()
    actions = []
    pattern = r'(\w+)\(([^)]*)\)'
    for match in re.finditer(pattern, actions_str):
        func = match.group(1)
        kwargs = {}
        for kv in re.finditer(r'(\w+)\s*=\s*["\']([^"\']*)["\']', match.group(2)):
            kwargs[kv.group(1)] = kv.group(2)
        actions.append({"action": func, "kwargs": kwargs})
    if not actions:
        return False
    custom[phrase.lower()] = {"name": phrase.title(), "emoji": "⚡", "actions": actions, "response": response or f"Triggered: {phrase}", "custom": True}
    _save_custom(custom)
    return True

def remove_trigger(phrase):
    custom = _load_custom()
    if phrase.lower() in custom:
        del custom[phrase.lower()]
        _save_custom(custom)
        return True
    return False

def get_all_triggers():
    all_t = dict(BUILTIN_TRIGGERS)
    all_t.update(_load_custom())
    return all_t

def check_trigger(text):
    text_lower = text.lower().strip()
    for phrase, data in get_all_triggers().items():
        if phrase in text_lower:
            return data, phrase
    return None, None

def list_triggers():
    all_t = get_all_triggers()
    if not all_t:
        return "  No triggers configured."
    lines = ["  Trigger Phrases:"]
    for phrase, data in all_t.items():
        tag = " (custom)" if data.get("custom") else ""
        lines.append(f"    {data['emoji']} \"{phrase}\"{tag} -> {data['name']}")
    return "\n".join(lines)

def execute_trigger(trigger_data):
    from automation import execute_action
    results = []
    for item in trigger_data.get("actions", []):
        try:
            execute_action(item["action"], **item.get("kwargs", {}))
            results.append(f"OK {item['action']}")
        except Exception as e:
            results.append(f"FAIL {item['action']}: {str(e)[:80]}")
    return results
