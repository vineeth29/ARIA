"""
ARIA Mood System — Rage Detector + Mood Journal
=================================================
Detects emotional state from typing patterns.
Logs moods over time for pattern analysis.
"""

import json, os, datetime, time, re

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
MOODS_FILE = os.path.join(DATA_DIR, "moods.json")

# ════════════════════════════════════════════════════════════════
# RAGE DETECTOR
# ════════════════════════════════════════════════════════════════

_last_message_time = 0
_rapid_count = 0

# Profanity/frustration words (mild detection)
_frustration_words = {
    "ugh", "wtf", "damn", "hell", "crap", "stupid", "hate", "angry",
    "frustrated", "annoying", "broken", "useless", "trash", "garbage",
    "terrible", "worst", "sucks", "dumb", "idiotic", "ridiculous",
    "fml", "smh", "bruh", "omg"
}

def detect_rage(text):
    """
    Analyze text for emotional signals.
    Returns: (rage_level, response_message)
    rage_level: 0=none, 1=mild, 2=medium, 3=high
    """
    global _last_message_time, _rapid_count

    score = 0
    now = time.time()

    # Check for ALL CAPS (3+ words in caps)
    words = text.split()
    caps_words = sum(1 for w in words if w.isupper() and len(w) > 1)
    if caps_words >= 3 or (len(text) > 10 and text.isupper()):
        score += 3

    # Check for excessive punctuation
    if text.count("!") >= 3:
        score += 2
    if text.count("?") >= 3:
        score += 1

    # Check for rapid successive messages (< 3 sec apart)
    if now - _last_message_time < 3 and _last_message_time > 0:
        _rapid_count += 1
        if _rapid_count >= 2:
            score += 2
    else:
        _rapid_count = 0
    _last_message_time = now

    # Check for frustration words
    text_lower = text.lower()
    frustration_hits = sum(1 for w in _frustration_words if w in text_lower.split())
    score += frustration_hits * 1.5

    # Check for very short angry bursts
    if len(text.split()) <= 3 and any(c in text for c in "!?"):
        score += 1

    # Determine rage level
    if score >= 6:
        level = 3
        responses = [
            "Bro take a deep breath. I got this, let me handle it. 🧘",
            "Yo Vineeth, CHILL. I'm literally here to help you. Relax. 😤",
            "Easy there king. Whatever broke, I'll fix it. Just breathe. 💆",
        ]
    elif score >= 3:
        level = 2
        responses = [
            "I can feel the energy through the screen 😂 Don't worry, I got you.",
            "Alright alright, I'm on it. No need to stress 💪",
            "I hear you. Let me sort this out real quick.",
        ]
    elif score >= 1.5:
        level = 1
        responses = [
            "I got you, don't worry about it 👍",
            "On it. No stress.",
            "Say less, handling it now.",
        ]
    else:
        return 0, None

    import random
    return level, random.choice(responses)


# ════════════════════════════════════════════════════════════════
# MOOD JOURNAL
# ════════════════════════════════════════════════════════════════

_mood_keywords = {
    "happy": ["happy", "glad", "great", "awesome", "amazing", "excited", "joy", "wonderful", "fantastic", "love it", "yay", "woohoo"],
    "sad": ["sad", "depressed", "down", "unhappy", "miserable", "lonely", "heartbroken", "crying", "tears"],
    "stressed": ["stressed", "anxious", "worried", "overwhelmed", "pressure", "tense", "nervous", "panic"],
    "angry": ["angry", "furious", "pissed", "mad", "rage", "irritated", "annoyed"],
    "tired": ["tired", "exhausted", "sleepy", "drained", "fatigued", "burnt out", "burnout"],
    "bored": ["bored", "boring", "nothing to do", "meh"],
    "motivated": ["motivated", "pumped", "inspired", "productive", "energized", "focused", "determined"],
    "calm": ["calm", "peaceful", "relaxed", "chill", "serene", "content"],
    "confused": ["confused", "lost", "don't understand", "wtf", "what the"],
}

def detect_mood(text):
    """Detect mood from text. Returns mood string or None."""
    text_lower = text.lower()

    # Check if this looks like a mood expression
    mood_indicators = ["i feel", "i'm feeling", "feeling", "i am", "i'm so", "so "]
    is_mood_expression = any(ind in text_lower for ind in mood_indicators)

    for mood, keywords in _mood_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                return mood

    return None

def log_mood(mood, context=""):
    """Log a mood entry."""
    moods = _load_moods()
    entry = {
        "mood": mood,
        "context": context[:200],
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "day": datetime.datetime.now().strftime("%A"),
        "hour": datetime.datetime.now().hour,
    }
    moods.append(entry)
    # Keep last 500 entries
    if len(moods) > 500:
        moods = moods[-500:]
    _save_moods(moods)
    return entry

def get_mood_history(days=7):
    """Get mood entries from the last N days."""
    moods = _load_moods()
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    cutoff_str = cutoff.strftime("%Y-%m-%d")
    return [m for m in moods if m["timestamp"][:10] >= cutoff_str]

def get_mood_insights():
    """Analyze mood patterns and return insights."""
    moods = _load_moods()
    if len(moods) < 5:
        return "Not enough mood data yet. Keep logging how you feel!"

    # Count moods
    mood_counts = {}
    day_moods = {}
    hour_moods = {}

    for m in moods:
        mood = m["mood"]
        mood_counts[mood] = mood_counts.get(mood, 0) + 1
        day = m.get("day", "Unknown")
        day_moods.setdefault(day, []).append(mood)
        hour = m.get("hour", 12)
        period = "morning" if 5 <= hour < 12 else "afternoon" if 12 <= hour < 17 else "evening" if 17 <= hour < 21 else "night"
        hour_moods.setdefault(period, []).append(mood)

    lines = [f"  Mood Insights ({len(moods)} entries):"]

    # Most common mood
    top_mood = max(mood_counts, key=mood_counts.get)
    lines.append(f"    Most frequent mood: {top_mood} ({mood_counts[top_mood]} times)")

    # Mood by day pattern
    for day, day_mood_list in day_moods.items():
        neg = sum(1 for m in day_mood_list if m in ["stressed", "sad", "angry", "tired"])
        if neg > len(day_mood_list) * 0.5 and len(day_mood_list) >= 2:
            lines.append(f"    ⚠ You tend to feel down on {day}s")

    # Mood by time pattern
    for period, period_moods in hour_moods.items():
        neg = sum(1 for m in period_moods if m in ["stressed", "sad", "angry", "tired"])
        if neg > len(period_moods) * 0.5 and len(period_moods) >= 3:
            lines.append(f"    ⚠ You often feel stressed in the {period}")

    return "\n".join(lines)

def format_mood_history(entries):
    """Format mood entries for display."""
    if not entries:
        return "  No mood entries found."
    emoji_map = {
        "happy": "😊", "sad": "😢", "stressed": "😰", "angry": "😡",
        "tired": "😴", "bored": "😐", "motivated": "🔥", "calm": "😌",
        "confused": "🤔"
    }
    lines = []
    for m in entries[-15:]:  # show last 15
        emoji = emoji_map.get(m["mood"], "🔵")
        ctx = f" — {m['context']}" if m.get("context") else ""
        lines.append(f"    {emoji} {m['mood']} [{m['timestamp']}]{ctx}")
    return "\n".join(lines)

def get_mood_context():
    """Get recent mood as context for AI."""
    moods = _load_moods()
    if not moods:
        return ""
    recent = moods[-3:]
    items = [f"- Feeling {m['mood']} at {m['timestamp']}" for m in recent]
    return "\n[User's recent moods]:\n" + "\n".join(items)

def _load_moods():
    if os.path.exists(MOODS_FILE):
        try:
            with open(MOODS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return []

def _save_moods(moods):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(MOODS_FILE, "w", encoding="utf-8") as f:
        json.dump(moods, f, indent=2, ensure_ascii=False)
