"""
ARIA Sound Effects Engine
==========================
Audio feedback for actions using winsound (built-in, no install needed).
Generates tones programmatically — no WAV files required.
"""

import winsound
import threading

# Global toggle
_enabled = True

def set_enabled(enabled):
    global _enabled
    _enabled = enabled

def is_enabled():
    return _enabled

def _play_async(func):
    """Play sound in background thread so it doesn't block."""
    if not _enabled:
        return
    threading.Thread(target=func, daemon=True).start()

# ════════════════════════════════════════════════════════════════
# SOUND EFFECTS
# ════════════════════════════════════════════════════════════════

def startup():
    """Startup chime — ascending three-note chord."""
    def _play():
        winsound.Beep(523, 120)   # C5
        winsound.Beep(659, 120)   # E5
        winsound.Beep(784, 200)   # G5
    _play_async(_play)

def success():
    """Task complete — quick happy ding."""
    def _play():
        winsound.Beep(880, 100)   # A5
        winsound.Beep(1108, 180)  # C#6
    _play_async(_play)

def error():
    """Error — low warning buzz."""
    def _play():
        winsound.Beep(220, 200)   # A3
        winsound.Beep(196, 300)   # G3
    _play_async(_play)

def notification():
    """Notification — soft two-tone ping."""
    def _play():
        winsound.Beep(660, 100)
        winsound.Beep(880, 150)
    _play_async(_play)

def reminder():
    """Reminder/alarm — attention-grabbing triple beep."""
    def _play():
        for _ in range(3):
            winsound.Beep(1000, 150)
            winsound.Beep(0, 100)  # silence gap
    _play_async(_play)

def focus_start():
    """Focus mode activated — descending calm tone."""
    def _play():
        winsound.Beep(784, 150)   # G5
        winsound.Beep(659, 150)   # E5
        winsound.Beep(523, 250)   # C5
    _play_async(_play)

def focus_end():
    """Focus mode ended — ascending celebration."""
    def _play():
        winsound.Beep(523, 100)
        winsound.Beep(659, 100)
        winsound.Beep(784, 100)
        winsound.Beep(1047, 250)  # C6
    _play_async(_play)

def message_sent():
    """Message sent — quick whoosh-like sweep."""
    def _play():
        for freq in range(400, 900, 100):
            winsound.Beep(freq, 40)
    _play_async(_play)

def warning():
    """Warning — two slow low beeps."""
    def _play():
        winsound.Beep(330, 300)
        winsound.Beep(330, 300)
    _play_async(_play)

def rage_calm():
    """Calming tone for rage detection — slow descending."""
    def _play():
        winsound.Beep(600, 200)
        winsound.Beep(500, 200)
        winsound.Beep(400, 300)
    _play_async(_play)
