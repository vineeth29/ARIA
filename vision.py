import base64, os, mimetypes, json, re

SUPPORTED = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}

def load_image_base64(path):
    ext = os.path.splitext(path)[1].lower()
    if ext not in SUPPORTED:
        return None, None, f"Unsupported image type: {ext}"
    if not os.path.exists(path):
        return None, None, f"File not found: {path}"
    mime = mimetypes.guess_type(path)[0] or "image/jpeg"
    with open(path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, mime, None

def build_gemini_image_message(text, image_path):
    data, mime, err = load_image_base64(image_path)
    if err:
        return None, err
    return {
        "role": "user",
        "parts": [
            {"inline_data": {"mime_type": mime, "data": data}},
            {"text": text}
        ]
    }, None

def build_groq_image_message(text, image_path):
    data, mime, err = load_image_base64(image_path)
    if err:
        return None, err
    return {
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{data}"}},
            {"type": "text", "text": text}
        ]
    }, None

def ask_gemini_vision(text, image_path, api_key):
    import requests
    msg, err = build_gemini_image_message(text, image_path)
    if err:
        return None, err
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {
        "contents": [msg],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 1024}
    }
    try:
        r = requests.post(url, json=payload, timeout=30)
        if r.status_code != 200:
            return None, f"Gemini error {r.status_code}: {r.text[:100]}"
        cands = r.json().get("candidates", [])
        if not cands:
            return None, "No response from Gemini"
        parts = cands[0].get("content", {}).get("parts", [])
        text_out = "".join(p.get("text", "") for p in parts)
        return text_out.strip(), None
    except Exception as e:
        return None, str(e)

def ask_groq_vision(text, image_path, api_key):
    import requests
    msg, err = build_groq_image_message(text, image_path)
    if err:
        return None, err
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.2-11b-vision-preview",
        "messages": [msg],
        "max_tokens": 1024,
        "temperature": 0.4
    }
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers, json=payload, timeout=30
        )
        if r.status_code != 200:
            return None, f"Groq vision error {r.status_code}: {r.text[:100]}"
        return r.json()["choices"][0]["message"]["content"].strip(), None
    except Exception as e:
        return None, str(e)

def analyze_image(text, image_path, config):
    gemini_key = config.get("gemini_api_key", "")
    groq_key   = config.get("groq_api_key", "")

    if gemini_key:
        result, err = ask_gemini_vision(text, image_path, gemini_key)
        if result:
            return result, "Gemini"
    if groq_key:
        result, err = ask_groq_vision(text, image_path, groq_key)
        if result:
            return result, "Groq Vision"
    return None, "No vision-capable provider available"

def extract_image_path(text):
    patterns = [
        r'["\']([^"\']+\.(?:jpg|jpeg|png|gif|webp|bmp))["\']',
        r'(\b\w:[\\\/][^\s,]+\.(?:jpg|jpeg|png|gif|webp|bmp))',
        r'((?:~|\.)?[\/\\][^\s,]+\.(?:jpg|jpeg|png|gif|webp|bmp))',
        r'\b([^\s,]+\.(?:jpg|jpeg|png|gif|webp|bmp))\b',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            path = m.group(1).strip()
            path = os.path.expanduser(path)
            return path
    return None


def find_latest_image():
    """Find the most recently modified image on Desktop or Screenshots folder."""
    search_dirs = [
        os.path.join(os.path.expanduser("~"), "Desktop"),
        os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots"),
        os.path.join(os.path.expanduser("~"), "Screenshots"),
        os.path.join(os.path.expanduser("~"), "Pictures"),
        os.path.join(os.path.expanduser("~"), "Downloads"),
    ]
    latest_file = None
    latest_time = 0
    for d in search_dirs:
        if not os.path.exists(d):
            continue
        for f in os.listdir(d):
            ext = os.path.splitext(f)[1].lower()
            if ext in SUPPORTED:
                full = os.path.join(d, f)
                mt   = os.path.getmtime(full)
                if mt > latest_time:
                    latest_time = mt
                    latest_file = full
    return latest_file


def is_image_request(text):
    image_words = [
        "image", "picture", "photo", "pic", "screenshot",
        "look at", "analyze", "analyse", "what is in", "what's in",
        "read this", "describe", "show me", "ocr", "extract text",
        "what does", "can you see", "check this", "look at this",
        ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp",
        "last screenshot", "latest image", "recent photo"
    ]
    tl = text.lower()
    return any(w in tl for w in image_words)


def wants_latest_image(text):
    phrases = [
        "last screenshot", "latest screenshot", "recent screenshot",
        "last image", "latest image", "last photo", "latest photo",
        "last pic", "recent pic", "last picture",
        "analyze image", "analyse image", "look at image",
        "check image", "read image"
    ]
    tl = text.lower()
    return any(p in tl for p in phrases)

