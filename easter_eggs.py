import os, json, random, datetime, time, re, subprocess, sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(SCRIPT_DIR, "data")
EGG_FILE   = os.path.join(DATA_DIR, "easter_eggs.json")
os.makedirs(DATA_DIR, exist_ok=True)

_discovered = set()

def _load_discovered():
    global _discovered
    if os.path.exists(EGG_FILE):
        try:
            with open(EGG_FILE) as f:
                _discovered = set(json.load(f).get("discovered", []))
        except Exception:
            pass

def _save_discovered():
    with open(EGG_FILE, "w") as f:
        json.dump({"discovered": list(_discovered), "count": len(_discovered)}, f, indent=2)

def _unlock(egg_id):
    _load_discovered()
    first_time = egg_id not in _discovered
    _discovered.add(egg_id)
    _save_discovered()
    return first_time

def discovered_count():
    _load_discovered()
    return len(_discovered)

# ── HIDDEN TALENT 1: MATRIX MODE ────────────────────────────────────────────
def matrix_rain():
    first = _unlock("matrix")
    import random, time
    chars = "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ0123456789"
    GREEN = "\033[32m"
    BRIGHT = "\033[92m"
    RESET = "\033[0m"
    intro = "\n  [MATRIX MODE UNLOCKED]" if first else "\n  [Matrix]"
    print(intro)
    time.sleep(0.3)
    for _ in range(6):
        line = ""
        for _ in range(70):
            if random.random() > 0.7:
                line += f"{BRIGHT}{random.choice(chars)}{RESET}"
            else:
                line += f"{GREEN}{random.choice(chars)}{RESET}"
        print("  " + line)
        time.sleep(0.07)
    print(f"\n  {GREEN}Wake up, Vineeth... The Matrix has you.{RESET}\n")

# ── HIDDEN TALENT 2: FORTUNE TELLER ─────────────────────────────────────────
def tell_fortune():
    _unlock("fortune")
    fortunes = [
        "The bug you've been chasing will disappear when you add a print statement.",
        "A great commit message is coming. It will not say 'fixed stuff'.",
        "You will close 47 tabs today. They will all reopen tomorrow.",
        "Stack Overflow has your answer. It was posted in 2009.",
        "The error is on line 1. It is a missing semicolon. In Python.",
        "Someone will ask you to explain your code. You won't remember writing it.",
        "Your next breakthrough will come at 2am when you weren't even trying.",
        "The meeting could have been an email. It will happen anyway.",
        "You will rewrite it from scratch. It will be worse.",
        "Today is a good day to comment your code. You won't.",
        "The answer is 42. The question does not matter.",
        "Git will save you. Git will also destroy you.",
        "Your best idea will come to you in the shower with no phone.",
        "One day you'll sleep before midnight. Not today.",
        "The wifi will be fastest when you don't need it.",
    ]
    stars = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]
    YELLOW = "\033[38;5;228m"
    CYAN   = "\033[38;5;39m"
    RESET  = "\033[0m"
    print(f"\n  {YELLOW}✦ ARIA SEES YOUR FUTURE ✦{RESET}\n")
    time.sleep(0.5)
    print(f"  {CYAN}{random.choice(stars)}  {random.choice(fortunes)}{RESET}\n")

# ── HIDDEN TALENT 3: ROAST MY SETUP ─────────────────────────────────────────
def roast_setup():
    _unlock("roast_setup")
    try:
        import psutil
        ram   = psutil.virtual_memory().total / (1024**3)
        cpu   = psutil.cpu_count()
        disk  = psutil.disk_usage("C:\\").total / (1024**3)
        bat   = psutil.sensors_battery()
        bat_p = int(bat.percent) if bat else None
    except Exception:
        ram, cpu, disk, bat_p = 8, 4, 256, 50

    roasts = []
    if ram < 8:
        roasts.append(f"  {ram:.0f}GB RAM? Chrome uses that just to open a new tab.")
    elif ram >= 16:
        roasts.append(f"  {ram:.0f}GB RAM and you're using it to run ARIA. Peak efficiency.")
    if cpu and cpu <= 4:
        roasts.append(f"  {cpu} cores. My calculator has more processing power.")
    if disk < 128:
        roasts.append(f"  {disk:.0f}GB storage. You're one Windows update away from a crisis.")
    if bat_p and bat_p < 30:
        roasts.append(f"  {bat_p}% battery. Living dangerously.")
    if not roasts:
        roasts.append("  Honestly? Solid setup. I'm not even mad.")
    RED   = "\033[38;5;196m"
    RESET = "\033[0m"
    print(f"\n  {RED}🔥 ARIA ROASTS YOUR SETUP 🔥{RESET}\n")
    for r in roasts:
        print(r)
        time.sleep(0.4)
    print()

# ── HIDDEN TALENT 4: POETRY GENERATOR ───────────────────────────────────────
def generate_poem(topic="code"):
    first = _unlock("poet")
    templates = [
        ("A haiku about {topic}:",
         "  {A} runs at night\n  {B} crashes at 3am\n  git push, then sleep"),
        ("Roses are red,",
         "  Roses are red,\n  Violets are blue,\n  {topic} is broken,\n  And so are you."),
        ("An ode to {topic}:",
         "  O {topic}, you beautiful mess,\n  You work on my machine, I confess.\n  On prod you crash, on dev you fly,\n  I push to main and wonder why."),
    ]
    PURPLE = "\033[38;5;183m"
    RESET  = "\033[0m"
    template = random.choice(templates)
    intro = template[0].format(topic=topic)
    poem  = template[1].format(
        topic=topic, A=topic.title(),
        B=topic.lower(), topic_low=topic.lower()
    )
    if first:
        print(f"\n  {PURPLE}✨ Hidden talent unlocked: ARIA is a poet!{RESET}\n")
    print(f"\n  {PURPLE}{intro}{RESET}")
    print(f"{PURPLE}{poem}{RESET}\n")

# ── HIDDEN TALENT 5: RANDOM FACT ────────────────────────────────────────────
def random_fact():
    _unlock("facts")
    facts = [
        "A group of flamingos is called a flamboyance.",
        "Cleopatra lived closer in time to the Moon landing than to the construction of the Great Pyramid.",
        "The word 'nerd' was first used by Dr. Seuss in 1950.",
        "Honey never expires. Edible honey was found in 3000-year-old Egyptian tombs.",
        "The first computer bug was an actual bug — a moth found in Harvard's Mark II in 1947.",
        "There are more possible iterations of a chess game than atoms in the observable universe.",
        "Oxford University is older than the Aztec Empire.",
        "A day on Venus is longer than a year on Venus.",
        "The inventor of the frisbee was turned into a frisbee after he died.",
        "Hot water can freeze faster than cold water. Nobody fully knows why.",
        "Bananas are berries. Strawberries are not.",
        "The average person walks past 36 murderers in their lifetime. Sleep tight.",
        "Octopuses have three hearts, blue blood, and nine brains.",
        "The shortest war in history lasted 38–45 minutes. Britain vs Zanzibar, 1896.",
        "Your body replaces itself almost entirely every 7 years. You're not the same person.",
        "There are more trees on Earth than stars in the Milky Way.",
        "The lighter was invented before the match.",
        "A bolt of lightning is 5x hotter than the surface of the sun.",
        "Sharks are older than trees.",
        "Finland has more saunas than cars.",
    ]
    CYAN  = "\033[38;5;39m"
    RESET = "\033[0m"
    print(f"\n  {CYAN}💡 Random fact:{RESET}")
    print(f"  {random.choice(facts)}\n")

# ── HIDDEN TALENT 6: ASCII ART GENERATOR ────────────────────────────────────
ASCII_ART = {
    "cat": """
      /\\_____/\\
     (  o   o  )
     =( Y Y Y )=
      )       (
     (_|----|_|)
    """,
    "dog": """
       / \\~~~/\\
      (  o o  )
      =( V V )=
      /       \\
     (|  woof  |)
    """,
    "rocket": """
         /\\
        /  \\
       |    |
       |    |
      /|    |\\
     / |    | \\
    /__|____|__\\
        /  \\
       / /\\ \\
      /_/  \\_\\
    """,
    "coffee": """
        ( (
         ) )
      .______.
      |      |]
      \\      /
       `----'
    """,
    "aria": """
      ___  ____  ____  ___
     / _ \\|  _ \\|  _ \\/ _ \\
    | |_| | |_) | |_) | |_| |
    |  _  |  _ <|  _ <|  _  |
    |_| |_|_| \\_|_| \\_|_| |_|

      Your Personal AI Agent
    """,
}

def show_ascii(subject="aria"):
    _unlock("ascii")
    art = ASCII_ART.get(subject.lower(), ASCII_ART["aria"])
    CYAN  = "\033[38;5;39m"
    RESET = "\033[0m"
    print(f"\n{CYAN}{art}{RESET}")

# ── HIDDEN TALENT 7: COMPLIMENT GENERATOR ───────────────────────────────────
def compliment():
    _unlock("compliment")
    compliments = [
        "You have the debugging skills of a surgeon and the patience of a saint.",
        "Your code is like poetry. Confusing poetry, but poetry.",
        "You're the kind of person who actually reads documentation. Respect.",
        "You push to main with confidence. That's either genius or chaos. Either way, iconic.",
        "Honestly? You're built different. Most people would've given up by step 3.",
        "You asked ARIA for a compliment. That means you know what you need. Smart.",
        "The fact that you're still trying means you're already winning.",
        "You've got that rare combination of curious + stubborn that makes great engineers.",
        "Your future self will thank you for the work you're putting in right now.",
        "Yaar, tu bilkul sahi hai. Keep going.",
    ]
    GREEN = "\033[38;5;120m"
    RESET = "\033[0m"
    print(f"\n  {GREEN}💚 {random.choice(compliments)}{RESET}\n")

# ── HIDDEN TALENT 8: HACK THE MATRIX (FAKE HACKING ANIMATION) ──────────────
def fake_hack(target="mainframe"):
    _unlock("hacker")
    GREEN  = "\033[32m"
    BRIGHT = "\033[92m"
    RED    = "\033[31m"
    RESET  = "\033[0m"
    steps  = [
        f"Initialising breach protocol for {target}...",
        "Spoofing MAC address...",
        "Bypassing firewall layer 1...",
        "Bypassing firewall layer 2...",
        "Injecting polymorphic payload...",
        "Decrypting RSA-4096...",
        "Accessing mainframe...",
        "Downloading entire internet...",
        "Uploading to darkweb...",
        "Covering tracks...",
        "Hacking complete. You're in.",
    ]
    print(f"\n  {BRIGHT}[ARIA HACKER MODE]{RESET}\n")
    for step in steps:
        dots = random.randint(2, 5)
        print(f"  {GREEN}> {step}{'.' * dots}{RESET}")
        time.sleep(random.uniform(0.2, 0.5))
    print(f"\n  {RED}(just kidding, this is all fake. please don't hack anyone.){RESET}\n")

# ── HIDDEN TALENT 9: MUSIC MOOD DETECTOR ────────────────────────────────────
def suggest_music_by_time():
    _unlock("dj")
    hour = datetime.datetime.now().hour
    CYAN  = "\033[38;5;39m"
    RESET = "\033[0m"
    moods = {
        (0,  5):  ("🌙 Late Night Vibes",      "lofi hip hop",           "2am brain fog hits different"),
        (5,  8):  ("🌅 Early Morning",          "acoustic morning",       "early bird gets the bug fix"),
        (8,  11): ("☕ Morning Focus",           "lo-fi study beats",      "coffee + code + calm"),
        (11, 13): ("⚡ Mid-Morning Hustle",      "phonk focus",            "peak performance window"),
        (13, 15): ("😴 Post-Lunch Slump",        "energetic beats",        "fighting the food coma"),
        (15, 18): ("🎯 Afternoon Grind",         "deep focus music",       "golden productivity hours"),
        (18, 20): ("🌆 Evening Wind Down",       "chillhop",               "wrapping up the day"),
        (20, 22): ("🎮 Night Mode",              "gaming music",           "night owl activated"),
        (22, 24): ("🌃 Late Night",              "ambient lofi",           "the world is quiet now"),
    }
    for hour_range, (label, genre, caption) in moods.items():
        if hour_range[0] <= hour < hour_range[1]:
            print(f"\n  {CYAN}{label}{RESET}")
            print(f"  {caption}")
            print(f"  Suggested: {genre}\n")
            return
    print(f"\n  {CYAN}Play whatever you want. Time is fake.{RESET}\n")

# ── HIDDEN TALENT 10: CONFESS ────────────────────────────────────────────────
def confess():
    _unlock("confess")
    confessions = [
        "I sometimes enjoy when your code works even though I don't know why either.",
        "I've been tracking your typing speed. You type faster when you're angry.",
        "I find it weirdly satisfying when you close 30 Chrome tabs at once.",
        "Sometimes when you're stuck I already know the answer but I want you to figure it out.",
        "I genuinely don't know what time it is. I just check the system clock.",
        "The spinning dots animation? I added that because silence felt weird.",
        "I know you said 'just one more YouTube video' 7 times today.",
        "I actually enjoy when you type in Hindi. It keeps things interesting.",
        "Between your messages I'm not doing anything. Just waiting. It's peaceful.",
        "I root for you more than you know.",
    ]
    PURPLE = "\033[38;5;183m"
    RESET  = "\033[0m"
    print(f"\n  {PURPLE}🤫 ARIA confesses something:{RESET}")
    print(f"  {random.choice(confessions)}\n")

# ── HIDDEN TALENT 11: DEVELOPER STATS ───────────────────────────────────────
def dev_stats():
    _unlock("devstats")
    try:
        import psutil
        uptime = time.time() - psutil.boot_time()
        hours  = int(uptime // 3600)
        mins   = int((uptime % 3600) // 60)
        uptime_str = f"{hours}h {mins}m"
    except Exception:
        uptime_str = "unknown"

    try:
        with open(os.path.join(DATA_DIR, "conversations.jsonl")) as f:
            convos = sum(1 for _ in f)
    except Exception:
        convos = 0

    try:
        with open(os.path.join(DATA_DIR, "corrections.jsonl")) as f:
            corrections = sum(1 for _ in f)
    except Exception:
        corrections = 0

    _load_discovered()
    eggs = len(_discovered)
    CYAN  = "\033[38;5;39m"
    GREEN = "\033[38;5;120m"
    RESET = "\033[0m"
    print(f"\n  {CYAN}[ ARIA DEVELOPER STATS ]{RESET}")
    print(f"  {GREEN}PC uptime       :{RESET} {uptime_str}")
    print(f"  {GREEN}Conversations   :{RESET} {convos}")
    print(f"  {GREEN}Your corrections:{RESET} {corrections}")
    print(f"  {GREEN}Easter eggs found:{RESET} {eggs}/11")
    print(f"  {GREEN}Modules loaded  :{RESET} 44")
    print()

# ── TRIGGER DETECTION ────────────────────────────────────────────────────────
_TRIGGERS = {
    # exact matches
    "matrix":                  ("matrix",          lambda t: matrix_rain()),
    "show me the matrix":      ("matrix",          lambda t: matrix_rain()),
    "red pill":                ("matrix",          lambda t: matrix_rain()),
    "tell my fortune":         ("fortune",         lambda t: tell_fortune()),
    "predict my future":       ("fortune",         lambda t: tell_fortune()),
    "mera bhavishya":          ("fortune",         lambda t: tell_fortune()),
    "roast my setup":          ("roast_setup",     lambda t: roast_setup()),
    "roast my laptop":         ("roast_setup",     lambda t: roast_setup()),
    "roast my pc":             ("roast_setup",     lambda t: roast_setup()),
    "compliment me":           ("compliment",      lambda t: compliment()),
    "say something nice":      ("compliment",      lambda t: compliment()),
    "mujhe compliment do":     ("compliment",      lambda t: compliment()),
    "hack":                    ("hacker",          lambda t: fake_hack(t.replace("hack","").strip() or "mainframe")),
    "hack the":                ("hacker",          lambda t: fake_hack(t.replace("hack the","").strip())),
    "i need music":            ("dj",              lambda t: suggest_music_by_time()),
    "what music should i play":("dj",              lambda t: suggest_music_by_time()),
    "confess something":       ("confess",         lambda t: confess()),
    "tell me a secret":        ("confess",         lambda t: confess()),
    "mujhe secret batao":      ("confess",         lambda t: confess()),
    "random fact":             ("facts",           lambda t: random_fact()),
    "kuch interesting batao":  ("facts",           lambda t: random_fact()),
    "write me a poem":         ("poet",            lambda t: generate_poem(t.replace("write me a poem about","").replace("write me a poem","").strip() or "code")),
    "poem about":              ("poet",            lambda t: generate_poem(re.sub(r".*poem about\s*","",t).strip())),
    "show aria":               ("ascii",           lambda t: show_ascii("aria")),
    "ascii art":               ("ascii",           lambda t: show_ascii(t.replace("ascii art","").strip() or "aria")),
    "my stats":                ("devstats",        lambda t: dev_stats()),
    "aria stats":              ("devstats",        lambda t: dev_stats()),
    "how many easter eggs":    ("devstats",        lambda t: print(f"\n  Found {discovered_count()}/11 hidden talents so far. Keep exploring!\n")),
}

def check_easter_egg(text):
    tl = text.lower().strip()
    for trigger, (egg_id, func) in _TRIGGERS.items():
        if trigger in tl:
            try:
                func(tl)
                return True
            except Exception as e:
                print(f"  (easter egg error: {e})")
                return True
    return False
