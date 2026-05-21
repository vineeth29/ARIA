import os, json, time, threading, datetime, re, queue

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
CHAINS_FILE = os.path.join(SCRIPT_DIR, "data", "task_chains.json")
os.makedirs(os.path.join(SCRIPT_DIR, "data"), exist_ok=True)

_pending_queue = queue.Queue()
_running_chains = {}
_lock = threading.Lock()

def _load():
    if os.path.exists(CHAINS_FILE):
        try:
            with open(CHAINS_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"chains": [], "history": []}

def _save(data):
    with open(CHAINS_FILE, "w") as f:
        json.dump(data, f, indent=2)

class ChainStep:
    def __init__(self, raw):
        self.raw        = raw.strip()
        self.delay      = 0
        self.condition  = None
        self.action     = raw.strip()
        self._parse()

    def _parse(self):
        delay_m = re.search(r"wait\s+(\d+)\s*(min|minute|second|sec|hour|hr)?", self.raw, re.IGNORECASE)
        if delay_m:
            num  = int(delay_m.group(1))
            unit = (delay_m.group(2) or "sec").lower()
            if "min" in unit:
                self.delay = num * 60
            elif "hour" in unit or "hr" in unit:
                self.delay = num * 3600
            else:
                self.delay = num
            self.action = re.sub(r"wait\s+\d+\s*(?:min|minute|second|sec|hour|hr)?", "", self.raw, flags=re.IGNORECASE).strip()
            return
        if_m = re.search(r"if\s+(.+?)\s+then\s+(.+)", self.raw, re.IGNORECASE)
        if if_m:
            self.condition = if_m.group(1).strip()
            self.action    = if_m.group(2).strip()

    def __repr__(self):
        parts = []
        if self.delay:
            parts.append(f"wait {self.delay}s")
        if self.condition:
            parts.append(f"if {self.condition}")
        parts.append(self.action)
        return " → ".join(parts)

def parse_chain(text):
    separators = [r"\s+then\s+", r",\s*then\s+", r";\s*", r"\band\s+then\s+", r"\bafter\s+that\s+"]
    parts = [text]
    for sep in separators:
        new_parts = []
        for part in parts:
            splits = re.split(sep, part, flags=re.IGNORECASE)
            new_parts.extend(s.strip() for s in splits if s.strip())
        parts = new_parts
    return [ChainStep(p) for p in parts if len(p) > 2]

def is_chain_request(text):
    indicators = [
        r"\bthen\b", r"\bafter that\b", r"\bafterwards\b",
        r"\bwait \d+", r"\bin \d+ (min|sec|hour)", r"\bfollowed by\b",
        r"\bthen open\b", r"\bthen send\b", r"\bthen play\b",
        r"\bthen check\b", r"\bthen remind\b", r"\bthen close\b",
    ]
    tl = text.lower()
    return sum(1 for p in indicators if re.search(p, tl)) >= 1

def execute_chain(steps, action_executor, status_cb=None, chain_id=None):
    results = []
    for i, step in enumerate(steps, 1):
        if status_cb:
            status_cb(f"Step {i}/{len(steps)}: {step.action[:50]}")
        if step.delay > 0:
            if status_cb:
                status_cb(f"Waiting {step.delay}s...")
            time.sleep(step.delay)
        if step.condition:
            cond_lower = step.condition.lower()
            passed     = True
            if "battery" in cond_lower:
                try:
                    import psutil
                    bat    = psutil.sensors_battery()
                    level  = int(bat.percent) if bat else 100
                    needed = int(re.search(r"\d+", step.condition).group())
                    passed = level < needed
                except Exception:
                    passed = True
            if "internet" in cond_lower:
                try:
                    import socket
                    socket.create_connection(("8.8.8.8", 53), timeout=3)
                    passed = True
                except Exception:
                    passed = "no" not in cond_lower
            if not passed:
                if status_cb:
                    status_cb(f"Condition not met: {step.condition} — skipping")
                results.append({"step": i, "action": step.action, "skipped": True})
                continue
        try:
            result = action_executor(step.action)
            results.append({"step": i, "action": step.action, "done": True})
        except Exception as e:
            results.append({"step": i, "action": step.action, "error": str(e)})
        time.sleep(0.5)
    if chain_id:
        with _lock:
            _running_chains.pop(chain_id, None)
    return results

def run_chain_async(steps, action_executor, status_cb=None):
    chain_id = datetime.datetime.now().strftime("%H%M%S")
    def _run():
        results = execute_chain(steps, action_executor, status_cb, chain_id)
        done    = sum(1 for r in results if r.get("done"))
        skipped = sum(1 for r in results if r.get("skipped"))
        errors  = sum(1 for r in results if r.get("error"))
        msg = f"Chain done: {done} steps completed"
        if skipped: msg += f", {skipped} skipped"
        if errors:  msg += f", {errors} errors"
        _pending_queue.put({"type": "chain_done", "message": msg})
    with _lock:
        _running_chains[chain_id] = {"steps": len(steps), "started": datetime.datetime.now().isoformat()}
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return chain_id

def get_pending_results():
    results = []
    while not _pending_queue.empty():
        try:
            results.append(_pending_queue.get_nowait())
        except queue.Empty:
            break
    return results

def save_chain(name, steps_text):
    data = _load()
    data["chains"].append({
        "name":    name,
        "steps":   steps_text,
        "created": datetime.datetime.now().isoformat(),
    })
    _save(data)

def get_saved_chains():
    return _load().get("chains", [])

def list_chains():
    chains = get_saved_chains()
    if not chains:
        return "No saved chains. Create one with: /chain save <name> | step1 then step2"
    lines = ["Saved chains:"]
    for c in chains:
        lines.append(f"  {c['name']} — {c['steps'][:60]}")
    return "\n".join(lines)

def format_chain_preview(steps):
    lines = ["Chain preview:"]
    for i, step in enumerate(steps, 1):
        delay_str = f" [wait {step.delay}s]" if step.delay else ""
        cond_str  = f" [if {step.condition}]" if step.condition else ""
        lines.append(f"  {i}.{delay_str}{cond_str} {step.action}")
    return "\n".join(lines)

EXAMPLE_CHAINS = [
    "open spotify then wait 3 seconds then set volume to 60",
    "take a screenshot then open gmail",
    "clear temp files then check disk space then notify Done cleaning",
    "set reminder in 25 minutes for break time then set volume to 40 then open youtube",
    "check internet then if battery below 30 then set reminder in 5 minutes to plug in charger",
]

def get_examples():
    lines = ["Example chains (just type these naturally):"]
    for ex in EXAMPLE_CHAINS:
        lines.append(f"  • {ex}")
    return "\n".join(lines)
