"""
ARIA Mini Games
=================
Text-based games: Trivia, 20 Questions, Word Chain, Riddles, Story Builder.
"""

import random

# ════════════════════════════════════════════════════════════════
# TRIVIA
# ════════════════════════════════════════════════════════════════

TRIVIA_QUESTIONS = [
    {"q": "What planet is known as the Red Planet?", "a": "mars", "options": ["Venus", "Mars", "Jupiter", "Saturn"]},
    {"q": "What is the largest ocean on Earth?", "a": "pacific", "options": ["Atlantic", "Indian", "Pacific", "Arctic"]},
    {"q": "Who painted the Mona Lisa?", "a": "leonardo da vinci", "options": ["Picasso", "Van Gogh", "Leonardo da Vinci", "Michelangelo"]},
    {"q": "What is the chemical symbol for gold?", "a": "au", "options": ["Ag", "Au", "Fe", "Cu"]},
    {"q": "How many bones are in the adult human body?", "a": "206", "options": ["196", "206", "216", "256"]},
    {"q": "What is the smallest country in the world?", "a": "vatican city", "options": ["Monaco", "Vatican City", "San Marino", "Liechtenstein"]},
    {"q": "What year did the Titanic sink?", "a": "1912", "options": ["1905", "1912", "1918", "1920"]},
    {"q": "What is the speed of light in km/s (approximately)?", "a": "300000", "options": ["150,000", "300,000", "500,000", "1,000,000"]},
    {"q": "Which element has the atomic number 1?", "a": "hydrogen", "options": ["Helium", "Hydrogen", "Oxygen", "Carbon"]},
    {"q": "What is the largest mammal?", "a": "blue whale", "options": ["Elephant", "Blue Whale", "Giraffe", "Hippo"]},
    {"q": "Who developed the theory of relativity?", "a": "einstein", "options": ["Newton", "Einstein", "Hawking", "Tesla"]},
    {"q": "What is the capital of Japan?", "a": "tokyo", "options": ["Osaka", "Tokyo", "Kyoto", "Seoul"]},
    {"q": "How many hearts does an octopus have?", "a": "3", "options": ["1", "2", "3", "4"]},
    {"q": "What programming language was created by Guido van Rossum?", "a": "python", "options": ["Java", "Python", "Ruby", "C++"]},
    {"q": "What is the hardest natural substance on Earth?", "a": "diamond", "options": ["Gold", "Iron", "Diamond", "Titanium"]},
]

RIDDLES = [
    {"q": "I have cities, but no houses. Forests, but no trees. Water, but no fish. What am I?", "a": "a map"},
    {"q": "The more you take, the more you leave behind. What am I?", "a": "footsteps"},
    {"q": "I speak without a mouth and hear without ears. I have no body, but I come alive with wind. What am I?", "a": "an echo"},
    {"q": "What has keys but no locks?", "a": "a keyboard"},
    {"q": "I have hands, but can't clap. What am I?", "a": "a clock"},
    {"q": "What gets wetter the more it dries?", "a": "a towel"},
    {"q": "What can you break without touching it?", "a": "a promise"},
    {"q": "What has a head and a tail but no body?", "a": "a coin"},
    {"q": "What runs but never walks?", "a": "water"},
    {"q": "I'm tall when I'm young and short when I'm old. What am I?", "a": "a candle"},
]

# ════════════════════════════════════════════════════════════════
# GAME STATE
# ════════════════════════════════════════════════════════════════

_active_game = None
_game_state = {}

def is_game_active():
    return _active_game is not None

def get_active_game():
    return _active_game

def end_game():
    global _active_game, _game_state
    _active_game = None
    _game_state = {}
    return "  Game ended! 🎮"

# ════════════════════════════════════════════════════════════════
# TRIVIA GAME
# ════════════════════════════════════════════════════════════════

def start_trivia():
    global _active_game, _game_state
    questions = random.sample(TRIVIA_QUESTIONS, min(5, len(TRIVIA_QUESTIONS)))
    _active_game = "trivia"
    _game_state = {"questions": questions, "current": 0, "score": 0, "total": len(questions)}
    return _ask_trivia_question()

def _ask_trivia_question():
    s = _game_state
    if s["current"] >= s["total"]:
        result = f"\n  🏆 Trivia Over! Score: {s['score']}/{s['total']}"
        end_game()
        return result
    q = s["questions"][s["current"]]
    lines = [f"\n  📝 Question {s['current']+1}/{s['total']}:"]
    lines.append(f"  {q['q']}")
    for i, opt in enumerate(q["options"], 1):
        lines.append(f"    {i}. {opt}")
    lines.append("  Type your answer (or /quit to stop):")
    return "\n".join(lines)

def answer_trivia(answer):
    s = _game_state
    q = s["questions"][s["current"]]
    correct = q["a"]
    answer_lower = answer.lower().strip()
    # Check by option number or text
    is_correct = False
    try:
        idx = int(answer_lower) - 1
        if 0 <= idx < len(q["options"]) and q["options"][idx].lower() == correct.lower():
            is_correct = True
        elif correct.lower() in q["options"][idx].lower():
            is_correct = True
    except ValueError:
        if correct in answer_lower or answer_lower in correct:
            is_correct = True
    if is_correct:
        s["score"] += 1
        result = "  ✅ Correct! 🎉"
    else:
        result = f"  ❌ Wrong! Answer: {correct}"
    s["current"] += 1
    return result + "\n" + _ask_trivia_question()

# ════════════════════════════════════════════════════════════════
# RIDDLES GAME
# ════════════════════════════════════════════════════════════════

def start_riddles():
    global _active_game, _game_state
    riddles = random.sample(RIDDLES, min(5, len(RIDDLES)))
    _active_game = "riddles"
    _game_state = {"riddles": riddles, "current": 0, "score": 0, "total": len(riddles)}
    return _ask_riddle()

def _ask_riddle():
    s = _game_state
    if s["current"] >= s["total"]:
        result = f"\n  🏆 Riddles Over! Score: {s['score']}/{s['total']}"
        end_game()
        return result
    r = s["riddles"][s["current"]]
    return f"\n  🧩 Riddle {s['current']+1}/{s['total']}:\n  {r['q']}\n  (Type your answer or /hint or /skip):"

def answer_riddle(answer):
    s = _game_state
    r = s["riddles"][s["current"]]
    if answer.lower().strip() == "/hint":
        a = r["a"]
        hint = a[:len(a)//2] + "..." 
        return f"  💡 Hint: starts with \"{hint}\""
    if answer.lower().strip() == "/skip":
        s["current"] += 1
        return f"  ⏭ Answer was: {r['a']}\n" + _ask_riddle()
    if r["a"].lower() in answer.lower() or answer.lower() in r["a"].lower():
        s["score"] += 1
        s["current"] += 1
        return "  ✅ Correct! 🧠\n" + _ask_riddle()
    s["current"] += 1
    return f"  ❌ Not quite! Answer: {r['a']}\n" + _ask_riddle()

# ════════════════════════════════════════════════════════════════
# WORD CHAIN
# ════════════════════════════════════════════════════════════════

def start_wordchain():
    global _active_game, _game_state
    _active_game = "wordchain"
    words = ["apple", "elephant", "tiger", "rocket", "mountain"]
    start_word = random.choice(words)
    _game_state = {"last_word": start_word, "used": {start_word}, "score": 0}
    return f"\n  🔗 Word Chain!\n  Rules: Each word must start with the last letter of the previous word.\n  No repeating words. Type /quit to stop.\n\n  I start: {start_word}\n  Your turn (word starting with '{start_word[-1]}'):"

def play_wordchain(word):
    s = _game_state
    word = word.lower().strip()
    if len(word) < 2:
        return "  Word too short. Try again:"
    if word in s["used"]:
        return f"  ❌ '{word}' was already used! Try again:"
    if word[0] != s["last_word"][-1]:
        return f"  ❌ Must start with '{s['last_word'][-1]}'. Try again:"
    s["used"].add(word)
    s["score"] += 1
    s["last_word"] = word
    # AI picks next word
    target = word[-1]
    ai_words = ["nature","echo","orange","emerald","dolphin","night","tornado",
                 "arrow","wave","energy","yellow","window","water","rain","nail",
                 "lion","nest","tree","earth","heaven","noble","eagle","elephant"]
    candidates = [w for w in ai_words if w.startswith(target) and w not in s["used"]]
    if not candidates:
        return f"  ✅ I can't think of a word starting with '{target}'! You win! 🏆 Score: {s['score']}\n" + end_game()
    ai_word = random.choice(candidates)
    s["used"].add(ai_word)
    s["last_word"] = ai_word
    return f"  ✅ Good! My turn: {ai_word}\n  Your turn (starts with '{ai_word[-1]}'):"

# ════════════════════════════════════════════════════════════════
# GAME ROUTER
# ════════════════════════════════════════════════════════════════

def process_game_input(text):
    """Process input when a game is active."""
    if text.lower().strip() in ["/quit", "/endgame", "/stop"]:
        return end_game()
    if _active_game == "trivia":
        return answer_trivia(text)
    elif _active_game == "riddles":
        return answer_riddle(text)
    elif _active_game == "wordchain":
        return play_wordchain(text)
    return None

def start_game(game_name):
    """Start a game by name."""
    game_name = game_name.lower().strip()
    if game_name in ("trivia", "quiz"):
        return start_trivia()
    elif game_name in ("riddles", "riddle"):
        return start_riddles()
    elif game_name in ("wordchain", "word chain", "chain"):
        return start_wordchain()
    else:
        return "  Available games:\n    🧠 /play trivia\n    🧩 /play riddles\n    🔗 /play wordchain"

def list_games():
    return "  🎮 Available Games:\n    🧠 /play trivia — Knowledge quiz\n    🧩 /play riddles — Brain teasers\n    🔗 /play wordchain — Word chain game"
