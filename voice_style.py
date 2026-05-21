import os, json, re, datetime, collections

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(SCRIPT_DIR, "data")
STYLE_FILE = os.path.join(DATA_DIR, "writing_style.json")
os.makedirs(DATA_DIR, exist_ok=True)

def _load():
    if os.path.exists(STYLE_FILE):
        try:
            with open(STYLE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"samples": [], "profile": {}, "trained": False}

def _save(data):
    with open(STYLE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def analyse_text(text):
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    words = re.findall(r'\b\w+\b', text.lower())
    word_freq = collections.Counter(words)
    avg_sentence_len = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
    avg_word_len = sum(len(w) for w in words) / max(len(words), 1)
    filler_words = [w for w in ["basically", "literally", "actually", "honestly", "like", "so", "just", "really", "very", "quite"] if word_freq[w] > 0]
    starters = [s.split()[0].lower() for s in sentences if s.split()]
    common_starters = [w for w, c in collections.Counter(starters).most_common(5)]
    contractions = len(re.findall(r"\b\w+n't\b|\b\w+'ll\b|\b\w+'ve\b|\bi'm\b|\bwe're\b", text.lower()))
    return {
        "avg_sentence_len":  round(avg_sentence_len, 1),
        "avg_word_len":      round(avg_word_len, 1),
        "filler_words":      filler_words[:5],
        "common_starters":   common_starters,
        "contraction_rate":  round(contractions / max(len(sentences), 1), 2),
        "vocabulary_size":   len(set(words)),
        "top_words":         [w for w, _ in word_freq.most_common(20) if len(w) > 3],
    }

def learn_from_file(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        if len(text) < 100:
            return False, "File too short"
        profile = analyse_text(text)
        data = _load()
        data["samples"].append({"path": path, "chars": len(text), "date": datetime.datetime.now().isoformat()})
        existing = data.get("profile", {})
        for key in ["avg_sentence_len", "avg_word_len", "contraction_rate"]:
            if key in existing:
                existing[key] = round((existing[key] + profile[key]) / 2, 2)
            else:
                existing[key] = profile[key]
        for key in ["filler_words", "common_starters", "top_words"]:
            old = set(existing.get(key, []))
            new = set(profile.get(key, []))
            existing[key] = list(old | new)[:20]
        data["profile"] = existing
        data["trained"] = True
        _save(data)
        return True, f"Learned from {os.path.basename(path)} — {len(text)} chars"
    except Exception as e:
        return False, str(e)

def learn_from_text(text, label="manual"):
    if len(text) < 50:
        return False, "Too short"
    profile = analyse_text(text)
    data = _load()
    data["samples"].append({"label": label, "chars": len(text), "date": datetime.datetime.now().isoformat()})
    existing = data.get("profile", {})
    for key in ["avg_sentence_len", "avg_word_len", "contraction_rate"]:
        if key in existing:
            existing[key] = round((existing[key] + profile[key]) / 2, 2)
        else:
            existing[key] = profile[key]
    for key in ["filler_words", "common_starters", "top_words"]:
        old = set(existing.get(key, []))
        new_vals = set(profile.get(key, []))
        existing[key] = list(old | new_vals)[:20]
    data["profile"] = existing
    data["trained"] = True
    _save(data)
    return True, "Writing style updated"

def get_style_prompt():
    data = _load()
    if not data.get("trained") or not data.get("profile"):
        return ""
    p = data["profile"]
    parts = ["\n[WRITING STYLE — write exactly like this]:"]
    if p.get("avg_sentence_len"):
        tone = "short punchy sentences" if p["avg_sentence_len"] < 12 else "longer detailed sentences" if p["avg_sentence_len"] > 20 else "medium-length sentences"
        parts.append(f"Sentence style: {tone} (avg {p['avg_sentence_len']} words)")
    if p.get("contraction_rate", 0) > 0.3:
        parts.append("Use contractions freely (I'm, don't, won't, it's)")
    if p.get("filler_words"):
        parts.append(f"Naturally use these words: {', '.join(p['filler_words'][:4])}")
    if p.get("common_starters"):
        parts.append(f"Often start sentences with: {', '.join(p['common_starters'][:3])}")
    if p.get("avg_word_len", 5) < 4.5:
        parts.append("Use simple everyday words, avoid complex vocabulary")
    elif p.get("avg_word_len", 5) > 5.5:
        parts.append("Use varied sophisticated vocabulary")
    parts.append("Match this person's exact voice — make it sound like THEY wrote it.")
    return "\n".join(parts)

def get_stats():
    data = _load()
    samples = data.get("samples", [])
    profile = data.get("profile", {})
    if not samples:
        return "No writing samples learned yet.\nUse: /style learn <file_path>\nOr paste text and say: learn my writing style"
    lines = [f"Writing style profile ({len(samples)} samples learned):"]
    if profile.get("avg_sentence_len"):
        lines.append(f"  Sentence length  : {profile['avg_sentence_len']} words avg")
    if profile.get("avg_word_len"):
        lines.append(f"  Word complexity  : {profile['avg_word_len']} chars avg")
    if profile.get("contraction_rate"):
        lines.append(f"  Contraction rate : {profile['contraction_rate']}")
    if profile.get("filler_words"):
        lines.append(f"  Your words       : {', '.join(profile['filler_words'][:5])}")
    return "\n".join(lines)
