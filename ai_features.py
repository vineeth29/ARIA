import os, json, re, datetime, hashlib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(SCRIPT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)


# ── 1. SMART SUMMARISER ─────────────────────────────────────────────────────

def summarise_text(text, style="brief"):
    styles = {
        "brief":    "Summarise in 3-5 bullet points. Be concise.",
        "detailed": "Give a comprehensive summary with key points and details.",
        "eli5":     "Explain this like I'm 5 years old. Simple words, simple ideas.",
        "tldr":     "Give a one-sentence TL;DR.",
        "bullets":  "Extract key facts as short bullet points.",
        "action":   "Extract only action items and next steps.",
    }
    instruction = styles.get(style, styles["brief"])
    return f"[SUMMARISE — {style.upper()}]\n{instruction}\n\nText to summarise:\n{text[:8000]}"


# ── 2. TASK PLANNER ─────────────────────────────────────────────────────────

TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")

def _load_tasks():
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return []

def _save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

def add_task(title, priority="medium", due=None, tags=None):
    tasks = _load_tasks()
    task = {
        "id":       len(tasks) + 1,
        "title":    title.strip(),
        "priority": priority,
        "due":      due,
        "tags":     tags or [],
        "done":     False,
        "created":  datetime.datetime.now().isoformat(),
    }
    tasks.append(task)
    _save_tasks(tasks)
    return task["id"]

def complete_task(task_id):
    tasks = _load_tasks()
    for t in tasks:
        if t["id"] == int(task_id):
            t["done"] = True
            t["completed_at"] = datetime.datetime.now().isoformat()
    _save_tasks(tasks)

def delete_task(task_id):
    tasks = _load_tasks()
    tasks = [t for t in tasks if t["id"] != int(task_id)]
    _save_tasks(tasks)

def list_tasks(show_done=False):
    tasks = _load_tasks()
    if not tasks:
        return "No tasks yet. Add one: add task <title>"
    active = [t for t in tasks if not t["done"]] if not show_done else tasks
    if not active:
        return "All tasks completed!"
    icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
    lines = [f"Tasks ({len(active)} pending):"]
    for t in sorted(active, key=lambda x: {"high":0,"medium":1,"low":2}.get(x["priority"],1)):
        icon = icons.get(t["priority"], "⚪")
        due  = f" (due: {t['due']})" if t.get("due") else ""
        done = "✅ " if t["done"] else ""
        lines.append(f"  {done}{icon} [{t['id']}] {t['title']}{due}")
    return "\n".join(lines)

def parse_task_command(text):
    tl = text.lower().strip()
    if tl.startswith("add task "):
        title = text[9:].strip()
        priority = "high" if any(w in tl for w in ["urgent","asap","important","high"]) else \
                   "low"  if any(w in tl for w in ["low","later","someday"]) else "medium"
        return "add", title, priority
    if tl.startswith("done task ") or tl.startswith("complete task "):
        parts = tl.split()
        return "done", parts[-1], None
    if tl.startswith("delete task ") or tl.startswith("remove task "):
        parts = tl.split()
        return "delete", parts[-1], None
    if tl in ("/tasks", "my tasks", "show tasks", "list tasks"):
        return "list", None, None
    return None, None, None


# ── 3. EXPLAIN ANYTHING ─────────────────────────────────────────────────────

def build_explain_prompt(topic, level="normal"):
    levels = {
        "simple": "Explain this simply, like to a 10-year-old. Use analogies.",
        "normal": "Explain this clearly with examples. Assume basic knowledge.",
        "deep":   "Explain this deeply and technically. Include how it works under the hood.",
        "eli5":   "Explain Like I'm 5. Extremely simple. Use a real-world comparison.",
    }
    return f"[EXPLAIN MODE — {level.upper()}]\n{levels.get(level, levels['normal'])}\n\nTopic: {topic}"


# ── 4. CODE REVIEWER ────────────────────────────────────────────────────────

def build_code_review_prompt(code, language=""):
    lang = f" ({language})" if language else ""
    return (
        f"[CODE REVIEW{lang}]\n"
        f"Review this code. Check for:\n"
        f"- Bugs and logic errors\n"
        f"- Security issues\n"
        f"- Performance problems\n"
        f"- Code style and readability\n"
        f"- Better approaches\n\n"
        f"Give specific line-by-line feedback where relevant.\n\n"
        f"```\n{code[:6000]}\n```"
    )


# ── 5. WRITING ASSISTANT ────────────────────────────────────────────────────

def build_writing_prompt(request, style="professional"):
    styles = {
        "professional": "formal, professional tone",
        "casual":       "friendly, conversational tone",
        "creative":     "creative, engaging, vivid language",
        "academic":     "academic, structured, evidence-based",
        "simple":       "simple, clear, easy to understand",
    }
    tone = styles.get(style, styles["professional"])
    return (
        f"[WRITING ASSISTANT — {style.upper()}]\n"
        f"Write in a {tone}.\n"
        f"Be complete. Do not truncate.\n\n"
        f"Request: {request}"
    )


# ── 6. DEBATE / ARGUE BOTH SIDES ────────────────────────────────────────────

def build_debate_prompt(topic):
    return (
        f"[DEBATE MODE]\n"
        f"For the topic: '{topic}'\n\n"
        f"Present BOTH sides:\n"
        f"FOR: The strongest arguments in favour\n"
        f"AGAINST: The strongest arguments against\n"
        f"VERDICT: A balanced conclusion\n\n"
        f"Be fair, insightful, and back each point with reasoning."
    )


# ── 7. SMART COMPARISON ─────────────────────────────────────────────────────

def build_compare_prompt(a, b, criteria=None):
    crit = criteria or "features, pros, cons, use cases, and which to choose when"
    return (
        f"[COMPARISON]\n"
        f"Compare {a} vs {b}.\n"
        f"Cover: {crit}\n"
        f"End with a clear recommendation based on different use cases."
    )


# ── 8. SENTIMENT & EMOTION ANALYSER ─────────────────────────────────────────

def build_sentiment_prompt(text):
    return (
        f"[SENTIMENT ANALYSIS]\n"
        f"Analyse the tone and emotion in this text:\n\n"
        f"\"{text[:2000]}\"\n\n"
        f"Identify: overall sentiment (positive/negative/neutral/mixed), "
        f"dominant emotions, tone, intensity (1-10), and notable phrases."
    )


# ── 9. TRANSLATE ANYTHING ───────────────────────────────────────────────────

def build_translate_prompt(text, target_lang):
    return (
        f"[TRANSLATE]\n"
        f"Translate the following to {target_lang}.\n"
        f"Keep the tone and meaning intact.\n\n"
        f"Text: {text}"
    )


# ── 10. QUIZ GENERATOR ──────────────────────────────────────────────────────

def build_quiz_prompt(topic_or_content, num=5, difficulty="medium"):
    return (
        f"[QUIZ GENERATOR]\n"
        f"Generate {num} {difficulty}-difficulty quiz questions about:\n{topic_or_content[:3000]}\n\n"
        f"Format each as:\n"
        f"Q1: [question]\n"
        f"A) option  B) option  C) option  D) option\n"
        f"Answer: [letter]\n"
        f"Explanation: [why]\n\n"
        f"Make them genuinely challenging and educational."
    )


# ── 11. IDEA GENERATOR ──────────────────────────────────────────────────────

def build_ideas_prompt(topic, count=10):
    return (
        f"[IDEA GENERATOR]\n"
        f"Generate {count} creative, original, and actionable ideas for:\n{topic}\n\n"
        f"Each idea should be:\n"
        f"- Specific, not vague\n"
        f"- Actually doable\n"
        f"- Briefly explained (1-2 lines)\n"
        f"Think outside the box."
    )


# ── 12. ROAST / COMPLIMENT ──────────────────────────────────────────────────

def build_roast_prompt(subject):
    return (
        f"[ROAST — for fun only]\n"
        f"Give a clever, funny, good-natured roast of: {subject}\n"
        f"Keep it witty and playful, not mean. Followed by a genuine compliment."
    )


# ── INTENT DETECTION ────────────────────────────────────────────────────────

def detect_ai_intent(text):
    tl = text.lower()
    if any(w in tl for w in ["summarise","summarize","tldr","tl;dr","brief","sum up"]):
        style = "eli5" if "simple" in tl or "easy" in tl else \
                "tldr" if "tldr" in tl or "tl;dr" in tl else \
                "detailed" if "detail" in tl else "brief"
        return "summarise", style
    if any(w in tl for w in ["explain","what is","what are","how does","how do","teach me"]):
        level = "eli5"    if "eli5" in tl or "simple" in tl or "easy" in tl else \
                "deep"    if "deep" in tl or "technical" in tl or "advanced" in tl else "normal"
        return "explain", level
    if "review" in tl and ("code" in tl or "script" in tl or "function" in tl):
        return "code_review", None
    if any(w in tl for w in ["write","draft","compose","create a","make a"]) and \
       any(w in tl for w in ["email","essay","letter","post","article","story","poem","report"]):
        style = "casual"  if "casual" in tl or "friendly" in tl else \
                "creative" if "creative" in tl else "professional"
        return "writing", style
    if "debate" in tl or "both sides" in tl or "argue" in tl or "pros and cons" in tl:
        return "debate", None
    if " vs " in tl or " versus " in tl or "compare" in tl or "difference between" in tl:
        return "compare", None
    if "sentiment" in tl or "tone of" in tl or "emotion in" in tl or "how does this sound" in tl:
        return "sentiment", None
    if any(w in tl for w in ["translate","in tamil","in hindi","in french","in spanish","in japanese"]):
        for lang in ["tamil","hindi","french","spanish","japanese","german","arabic","telugu","kannada","malayalam"]:
            if lang in tl:
                return "translate", lang
        return "translate", "english"
    if "quiz" in tl or "test me" in tl or "questions about" in tl:
        return "quiz", None
    if "ideas for" in tl or "brainstorm" in tl or "suggest" in tl:
        return "ideas", None
    if "roast" in tl:
        return "roast", None
    task_action, _, _ = parse_task_command(text)
    if task_action:
        return "task", task_action
    return None, None
