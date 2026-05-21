import os, json, datetime, random, re

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
COACH_FILE  = os.path.join(SCRIPT_DIR, "data", "exam_coach.json")
os.makedirs(os.path.join(SCRIPT_DIR, "data"), exist_ok=True)

def _load():
    if os.path.exists(COACH_FILE):
        try:
            with open(COACH_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"sessions": [], "topics": {}, "weak_points": [], "syllabus": {}}

def _save(data):
    with open(COACH_FILE, "w") as f:
        json.dump(data, f, indent=2)

def set_syllabus(subject, topics):
    data = _load()
    data["syllabus"][subject] = {
        "topics":  topics,
        "added":   datetime.datetime.now().isoformat(),
        "subject": subject,
    }
    for topic in topics:
        if topic not in data["topics"]:
            data["topics"][topic] = {
                "correct":   0,
                "wrong":     0,
                "last_seen": None,
                "subject":   subject,
            }
    _save(data)
    return f"Syllabus set for {subject}: {len(topics)} topics"

def log_answer(topic, correct):
    data = _load()
    if topic not in data["topics"]:
        data["topics"][topic] = {"correct": 0, "wrong": 0, "last_seen": None, "subject": "unknown"}
    if correct:
        data["topics"][topic]["correct"] += 1
    else:
        data["topics"][topic]["wrong"] += 1
        if topic not in data["weak_points"]:
            data["weak_points"].append(topic)
    data["topics"][topic]["last_seen"] = datetime.datetime.now().isoformat()
    _save(data)

def get_weak_topics(limit=5):
    data  = _load()
    topics = data.get("topics", {})
    scored = []
    for topic, stats in topics.items():
        total = stats["correct"] + stats["wrong"]
        if total == 0:
            continue
        accuracy = stats["correct"] / total
        priority = (1 - accuracy) * total
        scored.append((topic, accuracy, priority))
    scored.sort(key=lambda x: -x[2])
    return [(t, a) for t, a, _ in scored[:limit]]

def get_unseen_topics(subject=None, limit=5):
    data   = _load()
    topics = data.get("topics", {})
    unseen = [(t, d) for t, d in topics.items()
              if d["last_seen"] is None and (not subject or d.get("subject") == subject)]
    return [t for t, _ in unseen[:limit]]

def build_quiz_prompt(subject=None, num_questions=5):
    data  = _load()
    weak  = get_weak_topics(limit=3)
    unseen = get_unseen_topics(subject=subject, limit=3)
    focus_topics = [t for t, _ in weak] + unseen
    if not focus_topics:
        if subject and subject in data.get("syllabus", {}):
            focus_topics = data["syllabus"][subject]["topics"][:5]
        else:
            focus_topics = list(data.get("topics", {}).keys())[:5]
    if not focus_topics:
        return None, "No syllabus set. Tell me your exam topics first."
    topic_str = ", ".join(focus_topics[:5])
    accuracy_note = ""
    if weak:
        weak_str = ", ".join(f"{t} ({a*100:.0f}% accuracy)" for t, a in weak[:3])
        accuracy_note = f"\nFocus EXTRA on these weak areas: {weak_str}"
    prompt = (
        f"[ADAPTIVE EXAM COACH]\n"
        f"Generate {num_questions} exam-style questions on: {topic_str}\n"
        f"{accuracy_note}\n"
        f"Format:\n"
        f"Q1: [question]\n"
        f"A) ... B) ... C) ... D) ...\n"
        f"Answer: [letter]\n"
        f"Explanation: [why, briefly]\n"
        f"Topic: [which topic this tests]\n\n"
        f"Make questions exam-realistic. Mix difficulty."
    )
    return prompt, None

def get_revision_sheet():
    data  = _load()
    weak  = get_weak_topics(limit=10)
    unseen = get_unseen_topics(limit=5)
    lines = ["PERSONALISED REVISION SHEET", "─" * 35, ""]
    if weak:
        lines.append("YOUR WEAK POINTS (focus here first):")
        for topic, accuracy in weak:
            bar = "█" * int((1-accuracy)*10)
            lines.append(f"  ⚠  {topic:<25} {bar} {accuracy*100:.0f}% correct")
        lines.append("")
    if unseen:
        lines.append("NOT STUDIED YET:")
        for topic in unseen:
            lines.append(f"  ❓ {topic}")
        lines.append("")
    topics = data.get("topics", {})
    strong = [(t, d["correct"]/(d["correct"]+d["wrong"]))
              for t, d in topics.items()
              if d["correct"]+d["wrong"] > 0 and d["correct"]/(d["correct"]+d["wrong"]) > 0.8]
    if strong:
        lines.append("STRONG TOPICS (quick review only):")
        for topic, acc in strong[:5]:
            lines.append(f"  ✅ {topic} ({acc*100:.0f}%)")
    return "\n".join(lines)

def is_exam_request(text):
    keywords = ["quiz me", "test me", "exam", "revise", "revision", "study",
                "weak points", "what should i study", "help me study",
                "practice questions", "set syllabus", "my syllabus"]
    return any(k in text.lower() for k in keywords)

def get_stats():
    data   = _load()
    topics = data.get("topics", {})
    total_q = sum(d["correct"]+d["wrong"] for d in topics.values())
    correct = sum(d["correct"] for d in topics.values())
    accuracy = correct/total_q*100 if total_q else 0
    subjects = list(data.get("syllabus", {}).keys())
    return (
        f"Exam coach stats:\n"
        f"  Subjects     : {', '.join(subjects) or 'none set'}\n"
        f"  Topics       : {len(topics)}\n"
        f"  Questions    : {total_q}\n"
        f"  Accuracy     : {accuracy:.0f}%\n"
        f"  Weak topics  : {len(get_weak_topics())}"
    )
