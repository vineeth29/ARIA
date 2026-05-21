import os, json, datetime, re, threading, time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(SCRIPT_DIR, "data")
LOG_FILE   = os.path.join(DATA_DIR, "lifelog.json")
os.makedirs(DATA_DIR, exist_ok=True)

_lock = threading.Lock()

def _load():
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"entries": [], "daily_summaries": {}}

def _save(data):
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)

def _today():
    return datetime.date.today().isoformat()

def log_event(event_type, description, details=None):
    with _lock:
        data = _load()
        entry = {
            "type":        event_type,
            "description": description,
            "details":     details or {},
            "time":        datetime.datetime.now().isoformat(),
            "date":        _today(),
        }
        data["entries"].append(entry)
        data["entries"] = data["entries"][-2000:]
        _save(data)

def log_conversation(user_msg, aria_msg):
    topics = _extract_topics(user_msg + " " + aria_msg)
    if topics:
        log_event("conversation", f"Discussed: {', '.join(topics[:3])}", {"topics": topics})

def log_file_operation(op, path):
    fname = os.path.basename(path)
    log_event("file", f"{op}: {fname}", {"path": path, "op": op})

def log_task_done(task_title):
    log_event("achievement", f"Completed task: {task_title}")

def log_problem_solved(description):
    log_event("achievement", f"Solved: {description}")

def log_learned(topic):
    log_event("learning", f"Learned about: {topic}")

def _extract_topics(text):
    stop = {"i","a","an","the","is","are","was","were","do","did","have","to","of",
            "in","on","at","and","or","but","my","you","it","this","that","what",
            "how","can","will","would","me","for","with","from","about","aria"}
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    return list(dict.fromkeys(w for w in words if w not in stop))[:8]

def get_today_entries():
    data = _load()
    today = _today()
    return [e for e in data["entries"] if e.get("date") == today]

def get_week_entries():
    data = _load()
    week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    return [e for e in data["entries"] if e.get("date", "") >= week_ago]

def generate_daily_summary(date=None):
    if not date:
        date = _today()
    data = _load()
    entries = [e for e in data["entries"] if e.get("date") == date]
    if not entries:
        return f"No activity logged for {date}."
    convos      = [e for e in entries if e["type"] == "conversation"]
    files       = [e for e in entries if e["type"] == "file"]
    achievements= [e for e in entries if e["type"] == "achievement"]
    learnings   = [e for e in entries if e["type"] == "learning"]
    lines = [f"Daily Log — {date}", "─" * 35]
    if achievements:
        lines.append("Accomplished:")
        for e in achievements:
            lines.append(f"  ✅ {e['description']}")
    if learnings:
        lines.append("Learned:")
        for e in learnings:
            lines.append(f"  📚 {e['description']}")
    if convos:
        all_topics = []
        for e in convos:
            all_topics.extend(e.get("details", {}).get("topics", []))
        if all_topics:
            from collections import Counter
            top = [t for t, _ in Counter(all_topics).most_common(5)]
            lines.append(f"Topics discussed: {', '.join(top)}")
    if files:
        lines.append(f"Files worked on: {len(files)}")
    lines.append(f"Total interactions: {len(entries)}")
    summary = "\n".join(lines)
    data["daily_summaries"][date] = summary
    _save(data)
    return summary

def generate_weekly_summary():
    entries = get_week_entries()
    if not entries:
        return "No activity in the past week."
    from collections import Counter
    topics     = []
    achiev     = [e for e in entries if e["type"] == "achievement"]
    learnings  = [e for e in entries if e["type"] == "learning"]
    for e in entries:
        topics.extend(e.get("details", {}).get("topics", []))
    top_topics = [t for t, _ in Counter(topics).most_common(8)]
    active_days = len(set(e.get("date") for e in entries))
    lines = [
        "Weekly Summary",
        "─" * 35,
        f"Active days     : {active_days}/7",
        f"Total events    : {len(entries)}",
        f"Tasks completed : {len(achiev)}",
        f"Things learned  : {len(learnings)}",
    ]
    if top_topics:
        lines.append(f"Main topics     : {', '.join(top_topics[:6])}")
    if achiev:
        lines.append("\nHighlights:")
        for e in achiev[:5]:
            lines.append(f"  ✅ {e['description']}")
    return "\n".join(lines)

def get_stats():
    data  = _load()
    total = len(data["entries"])
    days  = len(set(e.get("date") for e in data["entries"]))
    return f"Life log: {total} events across {days} days"
