import json, os, re, datetime, sqlite3, hashlib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE    = os.path.join(SCRIPT_DIR, "data", "memory.db")
os.makedirs(os.path.join(SCRIPT_DIR, "data"), exist_ok=True)

def _db():
    con = sqlite3.connect(DB_FILE)
    con.row_factory = sqlite3.Row
    con.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_msg  TEXT,
            aria_msg  TEXT,
            keywords  TEXT,
            hash      TEXT UNIQUE
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS facts (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            fact      TEXT,
            category  TEXT,
            hash      TEXT UNIQUE
        )
    """)
    con.commit()
    return con

def _keywords(text):
    stop = {"i","a","an","the","is","are","was","were","be","been","being",
            "have","has","had","do","does","did","will","would","could","should",
            "may","might","can","to","of","in","on","at","by","for","with",
            "about","into","through","and","or","but","if","then","my","your",
            "it","this","that","what","how","when","where","who","why","me","you"}
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    return " ".join(w for w in words if w not in stop)

def store_conversation(user_msg, aria_msg):
    h = hashlib.md5((user_msg + aria_msg).encode()).hexdigest()
    kw = _keywords(user_msg + " " + aria_msg)
    try:
        con = _db()
        con.execute(
            "INSERT OR IGNORE INTO conversations (timestamp,user_msg,aria_msg,keywords,hash) VALUES (?,?,?,?,?)",
            (datetime.datetime.now().isoformat(), user_msg, aria_msg, kw, h)
        )
        con.commit()
        con.close()
    except Exception:
        pass

def store_fact(fact, category="general"):
    h = hashlib.md5(fact.encode()).hexdigest()
    try:
        con = _db()
        con.execute(
            "INSERT OR IGNORE INTO facts (timestamp,fact,category,hash) VALUES (?,?,?,?)",
            (datetime.datetime.now().isoformat(), fact, category, h)
        )
        con.commit()
        con.close()
    except Exception:
        pass

def search_memory(query, limit=5):
    kw = _keywords(query)
    words = kw.split()
    if not words:
        return []
    try:
        con = _db()
        results = []
        for word in words[:5]:
            rows = con.execute(
                "SELECT user_msg, aria_msg, timestamp FROM conversations "
                "WHERE keywords LIKE ? ORDER BY timestamp DESC LIMIT ?",
                (f"%{word}%", limit)
            ).fetchall()
            for r in rows:
                entry = {"user": r["user_msg"], "aria": r["aria_msg"], "time": r["timestamp"][:10]}
                if entry not in results:
                    results.append(entry)
        con.close()
        return results[:limit]
    except Exception:
        return []

def search_facts(query, limit=5):
    kw = _keywords(query)
    words = kw.split()
    if not words:
        return []
    try:
        con = _db()
        results = []
        for word in words[:3]:
            rows = con.execute(
                "SELECT fact, category, timestamp FROM facts "
                "WHERE fact LIKE ? ORDER BY timestamp DESC LIMIT ?",
                (f"%{word}%", limit)
            ).fetchall()
            for r in rows:
                entry = {"fact": r["fact"], "category": r["category"]}
                if entry not in results:
                    results.append(entry)
        con.close()
        return results[:limit]
    except Exception:
        return []

def get_memory_context(query):
    convos = search_memory(query, limit=3)
    facts  = search_facts(query, limit=3)
    if not convos and not facts:
        return ""
    parts = ["\n[RELEVANT PAST CONTEXT]:"]
    for f in facts:
        parts.append(f"  Fact: {f['fact']}")
    for c in convos:
        parts.append(f"  Past [{c['time']}]: You asked '{c['user'][:80]}' — ARIA said '{c['aria'][:100]}'")
    return "\n".join(parts)

def extract_facts_from_conversation(user_msg, aria_msg):
    facts = []
    patterns = [
        (r"my name is ([A-Z][a-z]+(?: [A-Z][a-z]+)*)", "name"),
        (r"i (?:am|'m) (\d+) years old",                "age"),
        (r"i (?:work|study) (?:at|in) ([^.!?]+)",       "work/study"),
        (r"i (?:live|stay) (?:in|at) ([^.!?]+)",        "location"),
        (r"my (?:laptop|pc|computer) is ([^.!?]+)",      "device"),
        (r"i (?:like|love|prefer|use) ([^.!?]{5,40})",  "preference"),
    ]
    for pattern, category in patterns:
        m = re.search(pattern, user_msg, re.IGNORECASE)
        if m:
            facts.append((m.group(0).strip(), category))
    return facts

def get_stats():
    try:
        con = _db()
        n_convos = con.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
        n_facts  = con.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
        con.close()
        return f"Memory: {n_convos} conversations, {n_facts} facts stored"
    except Exception:
        return "Memory: unavailable"
