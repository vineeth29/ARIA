"""
ARIA Smart DJ
===============
Music recommendations based on time of day, mood, and context.
Opens YouTube in Zen browser with curated searches.
"""

import datetime

# Curated playlists by mood/context
PLAYLISTS = {
    "morning": [
        "upbeat morning playlist 2024",
        "feel good morning songs",
        "morning motivation music",
    ],
    "focus": [
        "lofi hip hop beats to study",
        "deep focus music for concentration",
        "instrumental study music",
    ],
    "night": [
        "chill night vibes playlist",
        "late night lofi beats",
        "ambient sleep music",
    ],
    "stressed": [
        "calming music for anxiety relief",
        "relaxing nature sounds",
        "peaceful piano music stress relief",
    ],
    "happy": [
        "feel good hits playlist",
        "happy pop songs 2024",
        "best party music mix",
    ],
    "sad": [
        "comforting music when sad",
        "emotional piano music",
        "chill sad songs playlist",
    ],
    "workout": [
        "gym motivation music 2024",
        "workout beast mode playlist",
        "high energy workout music",
    ],
    "chill": [
        "chill vibes playlist",
        "lo-fi chill beats",
        "indie chill songs 2024",
    ],
    "rain": [
        "rain sounds for sleeping 10 hours",
        "thunderstorm sounds relaxing",
        "rain on window sleep sounds",
    ],
}

def _get_time_context():
    hour = datetime.datetime.now().hour
    if 5 <= hour < 10:
        return "morning"
    elif 10 <= hour < 17:
        return "focus"
    elif 17 <= hour < 21:
        return "chill"
    else:
        return "night"

def pick_music(mood=None, genre=None):
    """
    Pick music based on mood, genre, or time of day.
    Returns (search_query, category).
    """
    import random

    category = None
    if genre and genre.lower() in PLAYLISTS:
        category = genre.lower()
    elif mood and mood.lower() in PLAYLISTS:
        category = mood.lower()
    else:
        category = _get_time_context()

    queries = PLAYLISTS.get(category, PLAYLISTS["chill"])
    query = random.choice(queries)
    return query, category

def get_music_url(mood=None, genre=None):
    """Get a YouTube search URL for music."""
    query, category = pick_music(mood, genre)
    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    return url, query, category

def get_recommendation_text(mood=None):
    """Get a human-readable music recommendation."""
    _, query, category = get_music_url(mood)
    emoji_map = {
        "morning": "☀️", "focus": "🎧", "night": "🌙",
        "stressed": "🧘", "happy": "🎉", "sad": "💙",
        "workout": "💪", "chill": "😎", "rain": "🌧",
    }
    emoji = emoji_map.get(category, "🎵")
    return f"{emoji} Playing: {query} ({category} vibes)"

def list_genres():
    lines = ["  Available music moods:"]
    emoji_map = {
        "morning": "☀️", "focus": "🎧", "night": "🌙",
        "stressed": "🧘", "happy": "🎉", "sad": "💙",
        "workout": "💪", "chill": "😎", "rain": "🌧",
    }
    for genre in PLAYLISTS:
        emoji = emoji_map.get(genre, "🎵")
        lines.append(f"    {emoji} /music {genre}")
    return "\n".join(lines)
