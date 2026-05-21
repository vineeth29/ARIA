import os, tempfile, subprocess, sys

def take_screenshot_to_temp():
    import tempfile
    try:
        import pyautogui
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.close()
        pyautogui.screenshot().save(tmp.name)
        return tmp.name
    except Exception as e:
        return None

def read_screen(vision_mod, config, question="What's on my screen?"):
    path = take_screenshot_to_temp()
    if not path:
        return "Couldn't take a screenshot. Make sure pyautogui is installed."
    try:
        reply, provider = vision_mod.analyze_image(question, path, config)
        if reply:
            return reply
        return "Couldn't read the screen. Vision provider unavailable."
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass

def is_screen_request(text):
    phrases = [
        "what's on my screen", "whats on my screen", "what is on my screen",
        "read my screen", "look at my screen", "see my screen",
        "read the error", "read that popup", "what does it say",
        "read the screen", "whats on screen", "describe my screen",
        "what's happening on screen", "help me with this screen",
        "read this window", "what's this error",
    ]
    tl = text.lower()
    return any(p in tl for p in phrases)
