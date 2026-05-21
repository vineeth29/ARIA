import json, re, os, datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(SCRIPT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

MAX_TOKENS_ESTIMATE = 6000
ALWAYS_KEEP_FIRST   = 2
ALWAYS_KEEP_LAST    = 8

IMPORTANT_MARKERS = [
    r"remember\s+(?:this|that)",
    r"important[:\s]",
    r"don't forget",
    r"note[:\s]",
    r"my name is",
    r"i am\s+\w+",
    r"i work\s+",
    r"i study\s+",
    r"my project",
    r"always\s+",
    r"never\s+",
    r"i prefer",
    r"i like\s+",
    r"i hate\s+",
    r"deadline",
    r"exam\s+(?:on|tomorrow|today)",
    r"syllabus",
    r"pin this",
    r"keep this",
]

def _estimate_tokens(text):
    return len(text) // 4

def _is_important(message):
    content = message.get("content", "").lower()
    return any(re.search(p, content) for p in IMPORTANT_MARKERS)

def _message_tokens(message):
    return _estimate_tokens(message.get("content", ""))

def smart_trim(history, max_tokens=MAX_TOKENS_ESTIMATE):
    if not history:
        return []

    total = sum(_message_tokens(m) for m in history)
    if total <= max_tokens:
        return history

    # Separate pinned (important) messages from regular
    pinned  = []
    regular = []
    for i, msg in enumerate(history):
        if i < ALWAYS_KEEP_FIRST * 2:
            pinned.append((i, msg))
        elif _is_important(msg):
            pinned.append((i, msg))
        else:
            regular.append((i, msg))

    # Always keep last N messages
    keep_last  = history[-ALWAYS_KEEP_LAST:]
    keep_last_indices = set(range(len(history) - ALWAYS_KEEP_LAST, len(history)))

    # Build result: pinned + keep_last (deduplicated, order preserved)
    seen    = set()
    result  = []
    indices = set(i for i, _ in pinned) | keep_last_indices

    for i, msg in enumerate(history):
        if i in indices and i not in seen:
            result.append(msg)
            seen.add(i)

    # Check if still too long — if so, drop middle pinned
    total = sum(_message_tokens(m) for m in result)
    if total > max_tokens:
        result = history[-ALWAYS_KEEP_LAST:]

    return result

def build_context_summary(history):
    if len(history) < 20:
        return ""
    topics  = []
    facts   = []
    actions = []
    for msg in history[:-10]:
        content = msg.get("content", "")
        if msg["role"] == "user":
            words = [w for w in content.lower().split() if len(w) > 4]
            topics.extend(words[:3])
            if _is_important(msg):
                facts.append(content[:100])
        elif msg["role"] == "assistant":
            if "[ACTION:" in content:
                act = re.search(r'\[ACTION:\s*(\w+)', content)
                if act:
                    actions.append(act.group(1))
    summary_parts = []
    if facts:
        summary_parts.append(f"Important things user mentioned: {' | '.join(facts[:3])}")
    if actions:
        from collections import Counter
        top = [a for a, _ in Counter(actions).most_common(3)]
        summary_parts.append(f"Recent actions taken: {', '.join(top)}")
    if not summary_parts:
        return ""
    return "\n[EARLIER CONVERSATION SUMMARY]: " + " | ".join(summary_parts)

def inject_summary_if_needed(history, system_prompt):
    if len(history) > 20:
        summary = build_context_summary(history)
        if summary and summary not in system_prompt:
            return system_prompt + summary
    return system_prompt

def extract_and_pin(user_input, history):
    tl = user_input.lower()
    if any(p in tl for p in ["remember this", "pin this", "keep this", "don't forget", "important:"]):
        for msg in history[-2:]:
            if msg.get("role") == "user":
                msg["_pinned"] = True
        return True
    return False

def get_pinned_messages(history):
    return [m for m in history if m.get("_pinned")]

def format_history_stats(history):
    total   = len(history)
    tokens  = sum(_message_tokens(m) for m in history)
    pinned  = len(get_pinned_messages(history))
    user_msgs = len([m for m in history if m["role"] == "user"])
    return (
        f"Conversation: {user_msgs} exchanges | "
        f"~{tokens} tokens | "
        f"{pinned} pinned messages"
    )
