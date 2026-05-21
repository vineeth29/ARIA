"""
ARIA Quick Notes System
========================
Instant note-taking. Fully local, stored in data/notes.json.
"""

import json, os, datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
NOTES_FILE = os.path.join(DATA_DIR, "notes.json")

def _load():
    if os.path.exists(NOTES_FILE):
        try:
            with open(NOTES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return []

def _save(notes):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, indent=2, ensure_ascii=False)

def add_note(text):
    """Add a new note."""
    notes = _load()
    note = {
        "id": len(notes) + 1,
        "text": text,
        "created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    notes.append(note)
    _save(notes)
    return note["id"]

def get_notes(limit=20):
    """Get recent notes."""
    notes = _load()
    return notes[-limit:]

def delete_note(note_id):
    """Delete a note by ID."""
    notes = _load()
    original_len = len(notes)
    notes = [n for n in notes if n["id"] != note_id]
    if len(notes) < original_len:
        _save(notes)
        return True
    return False

def search_notes(query):
    """Search notes by keyword."""
    notes = _load()
    query = query.lower()
    return [n for n in notes if query in n["text"].lower()]

def format_notes(notes_list):
    """Format notes for display."""
    if not notes_list:
        return "  No notes found."
    lines = []
    for n in notes_list:
        lines.append(f"    #{n['id']} [{n['created']}] {n['text']}")
    return "\n".join(lines)

def clear_all():
    """Delete all notes."""
    _save([])
    return True

def get_notes_context():
    """Get notes as context string for AI."""
    notes = _load()
    if not notes:
        return ""
    recent = notes[-10:]
    items = [f"- {n['text']} ({n['created']})" for n in recent]
    return "\n[User's recent notes]:\n" + "\n".join(items)
