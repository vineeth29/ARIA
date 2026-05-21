import json, os, time, datetime, subprocess, threading, hashlib, shutil, sys

SCRIPT_DIR       = os.path.dirname(os.path.abspath(__file__))
DATA_DIR         = os.path.join(SCRIPT_DIR, "data")
CONVERSATIONS_FILE = os.path.join(DATA_DIR, "conversations.jsonl")
CORRECTIONS_FILE   = os.path.join(DATA_DIR, "corrections.jsonl")
DATASET_FILE       = os.path.join(DATA_DIR, "finetune_dataset.jsonl")
STATS_FILE         = os.path.join(DATA_DIR, "learner_stats.json")
LORA_DIR           = os.path.join(SCRIPT_DIR, "lora_output")
TRAIN_DIR          = os.path.join(SCRIPT_DIR, "training")

os.makedirs(DATA_DIR,   exist_ok=True)
os.makedirs(LORA_DIR,   exist_ok=True)
os.makedirs(TRAIN_DIR,  exist_ok=True)

_last_user_msg  = None
_last_aria_msg  = None
_lock = threading.Lock()


def set_last_exchange(user_msg, aria_reply):
    global _last_user_msg, _last_aria_msg
    with _lock:
        _last_user_msg = user_msg
        _last_aria_msg = aria_reply
    _auto_log_conversation(user_msg, aria_reply)


def _auto_log_conversation(user_msg, aria_reply):
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "user": user_msg,
        "aria": aria_reply,
        "hash": hashlib.md5((user_msg + aria_reply).encode()).hexdigest()
    }
    with open(CONVERSATIONS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def log_correction(correct_answer):
    with _lock:
        if not _last_user_msg:
            return False, "No previous message to correct."
        h = hashlib.md5((_last_user_msg + correct_answer).encode()).hexdigest()
        existing = _load_hashes(CORRECTIONS_FILE)
        if h in existing:
            return False, "Already have this correction."
        entry = {
            "timestamp":      datetime.datetime.now().isoformat(),
            "user_message":   _last_user_msg,
            "wrong_answer":   _last_aria_msg or "",
            "correct_answer": correct_answer.strip(),
            "hash":           h
        }
        with open(CORRECTIONS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        _update_stats("corrections")
        return True, "Logged."


def _load_hashes(filepath):
    hashes = set()
    if not os.path.exists(filepath):
        return hashes
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            try:
                hashes.add(json.loads(line.strip()).get("hash", ""))
            except Exception:
                continue
    return hashes


def load_corrections():
    if not os.path.exists(CORRECTIONS_FILE):
        return []
    out = []
    with open(CORRECTIONS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    continue
    return out


def load_conversations():
    if not os.path.exists(CONVERSATIONS_FILE):
        return []
    out = []
    with open(CONVERSATIONS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    continue
    return out


def get_correction_count():
    return len(load_corrections())


def get_conversation_count():
    return len(load_conversations())


def build_finetune_dataset():
    corrections   = load_corrections()
    conversations = load_conversations()
    entries = []
    system = "You are ARIA, a personal offline AI assistant. You execute tasks, answer accurately, and keep replies short and direct."

    for c in corrections:
        entries.append({
            "messages": [
                {"role": "system",    "content": system},
                {"role": "user",      "content": c["user_message"]},
                {"role": "assistant", "content": c["correct_answer"]}
            ]
        })

    for c in conversations[-200:]:
        if len(c.get("aria", "")) > 10 and len(c.get("user", "")) > 3:
            entries.append({
                "messages": [
                    {"role": "system",    "content": system},
                    {"role": "user",      "content": c["user"]},
                    {"role": "assistant", "content": c["aria"]}
                ]
            })

    with open(DATASET_FILE, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")

    return len(entries)


def _is_ollama_running():
    try:
        import requests
        return requests.get("http://localhost:11434/", timeout=2).status_code == 200
    except Exception:
        return False


def _get_config():
    try:
        with open(os.path.join(SCRIPT_DIR, "config.json")) as f:
            return json.load(f)
    except Exception:
        return {}


def _update_config(key, value):
    path = os.path.join(SCRIPT_DIR, "config.json")
    try:
        with open(path) as f:
            c = json.load(f)
        c[key] = value
        with open(path, "w") as f:
            json.dump(c, f, indent=2)
    except Exception:
        pass


def _get_system_prompt():
    path = os.path.join(SCRIPT_DIR, "aria_prompt.txt")
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()[:3000]
    except Exception:
        return "You are ARIA, a personal offline AI assistant."


def build_ollama_modelfile(base_model):
    corrections = load_corrections()
    system = _get_system_prompt()

    examples_block = ""
    for c in corrections[-30:]:
        u = c["user_message"].replace('"', "'")
        a = c["correct_answer"].replace('"', "'")
        examples_block += f'\nMESSAGE user {u}\nMESSAGE assistant {a}'

    modelfile = f'FROM {base_model}\n\nSYSTEM """{system}"""\n\nPARAMETER temperature 0.4\nPARAMETER num_ctx 8192\nPARAMETER top_p 0.9\nPARAMETER repeat_penalty 1.1\n{examples_block}\n'

    path = os.path.join(SCRIPT_DIR, "Modelfile")
    with open(path, "w", encoding="utf-8") as f:
        f.write(modelfile)
    return path


def train_with_ollama(status_cb=None):
    if not _is_ollama_running():
        return False, "Ollama is not running. Open a terminal and run: ollama serve"

    config     = _get_config()
    base_model = config.get("ollama_model", "llama3.1")

    count = build_finetune_dataset()
    corrections = load_corrections()
    if not corrections:
        return False, "No corrections yet. After any wrong answer, type:\n/correct <the right answer>"

    if status_cb:
        status_cb(f"Building model from {len(corrections)} corrections + {count - len(corrections)} conversations...")

    modelfile_path = build_ollama_modelfile(base_model)

    if status_cb:
        status_cb(f"Running ollama create aria (base: {base_model})...")

    try:
        proc = subprocess.Popen(
            ["ollama", "create", "aria", "-f", modelfile_path],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="ignore"
        )
        output_lines = []
        for line in proc.stdout:
            line = line.strip()
            if line:
                output_lines.append(line)
                if status_cb:
                    status_cb(line)
        proc.wait(timeout=300)
        if proc.returncode != 0:
            return False, f"ollama create failed:\n" + "\n".join(output_lines[-5:])
    except subprocess.TimeoutExpired:
        return False, "Timed out after 5 minutes."
    except FileNotFoundError:
        return False, "Ollama not found. Install from https://ollama.com then run: ollama pull llama3.1"

    _update_config("ollama_model", "aria")
    _update_stats("trainings")

    return True, f"Done! Local model 'aria' rebuilt with {len(corrections)} corrections baked in.\nOllama model updated to: aria\nNext time you run ARIA offline it uses this model."


def _check_llamacpp():
    return shutil.which("llama-finetune") or shutil.which("llama-cli")


def _check_unsloth():
    try:
        import importlib
        return importlib.util.find_spec("unsloth") is not None
    except Exception:
        return False


def train_with_llamacpp(base_model_path, status_cb=None):
    binary = shutil.which("llama-finetune")
    if not binary:
        return False, ("llama-finetune not found.\n"
                       "Install llama.cpp: https://github.com/ggerganov/llama.cpp\n"
                       "Then run: cmake -B build && cmake --build build --config Release")

    count = build_finetune_dataset()
    if count == 0:
        return False, "No training data yet. Use /correct first."

    if status_cb:
        status_cb(f"Fine-tuning with llama.cpp on {count} examples...")

    cmd = [
        binary,
        "--model-base", base_model_path,
        "--train-data", DATASET_FILE,
        "--lora-out",   os.path.join(LORA_DIR, "aria-lora.bin"),
        "--ctx",        "2048",
        "--epochs",     "3",
        "--batch",      "4",
        "--lr",         "1e-4",
        "--save-every", "100",
    ]

    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="ignore"
        )
        for line in proc.stdout:
            line = line.strip()
            if line and status_cb:
                status_cb(line)
        proc.wait(timeout=3600)
        if proc.returncode != 0:
            return False, "llama-finetune failed. Check output above."
    except subprocess.TimeoutExpired:
        return False, "Training timed out (>1 hour)."

    _update_stats("trainings")
    return True, (f"LoRA fine-tune complete!\n"
                  f"LoRA weights saved to: {LORA_DIR}/aria-lora.bin\n"
                  f"Trained on: {count} examples\n"
                  f"To use: load your base model + this LoRA in llama.cpp")


def train_with_unsloth(status_cb=None):
    if not _check_unsloth():
        return False, ("unsloth not installed.\n"
                       "Install: pip install unsloth\n"
                       "Requires NVIDIA GPU with CUDA.")

    count = build_finetune_dataset()
    if count == 0:
        return False, "No training data yet. Use /correct first."

    script = os.path.join(TRAIN_DIR, "train_unsloth.py")
    _write_unsloth_script(script, count)

    if status_cb:
        status_cb(f"Starting unsloth fine-tune on {count} examples...")
        status_cb("This will take 10-30 minutes depending on GPU...")

    try:
        proc = subprocess.Popen(
            [sys.executable, script],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="ignore"
        )
        for line in proc.stdout:
            line = line.strip()
            if line and status_cb:
                status_cb(line)
        proc.wait(timeout=7200)
        if proc.returncode != 0:
            return False, "Unsloth training failed. Check GPU and CUDA setup."
    except subprocess.TimeoutExpired:
        return False, "Training timed out (>2 hours)."

    _update_stats("trainings")
    return True, (f"Fine-tune complete!\n"
                  f"Model saved to: {LORA_DIR}/aria-finetuned\n"
                  f"Convert to GGUF and use with Ollama:\n"
                  f"  python convert_hf_to_gguf.py {LORA_DIR}/aria-finetuned --outfile aria-finetuned.gguf\n"
                  f"  ollama create aria-finetuned -f Modelfile")


def _write_unsloth_script(script_path, count):
    config = _get_config()
    base   = config.get("ollama_model", "llama3.1").replace(":", "-")
    model_map = {
        "llama3.1": "unsloth/Meta-Llama-3.1-8B-Instruct",
        "llama3":   "unsloth/Meta-Llama-3-8B-Instruct",
        "mistral":  "unsloth/mistral-7b-instruct-v0.3",
        "qwen2.5":  "unsloth/Qwen2.5-7B-Instruct",
        "phi3":     "unsloth/Phi-3-mini-4k-instruct",
    }
    hf_model = model_map.get(base.split("-")[0], "unsloth/Meta-Llama-3.1-8B-Instruct")

    script = f'''
import json
from datasets import Dataset
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="{hf_model}",
    max_seq_length=2048,
    load_in_4bit=True,
)

model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing=True,
)

data = []
with open("{DATASET_FILE}", "r") as f:
    for line in f:
        line = line.strip()
        if line:
            data.append(json.loads(line))

def format_chat(example):
    msgs = example.get("messages", [])
    text = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)
    return {{"text": text}}

dataset = Dataset.from_list(data).map(format_chat)

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=2048,
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        num_train_epochs=3,
        learning_rate=2e-4,
        fp16=True,
        logging_steps=10,
        output_dir="{LORA_DIR}",
        save_strategy="epoch",
    ),
)

trainer.train()
model.save_pretrained("{LORA_DIR}/aria-finetuned")
tokenizer.save_pretrained("{LORA_DIR}/aria-finetuned")
print("Training complete. Model saved.")
'''
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)


def get_best_train_method():
    if _check_unsloth():
        return "unsloth"
    if _check_llamacpp():
        return "llamacpp"
    if _is_ollama_running():
        return "ollama"
    return "none"


def auto_train(status_cb=None, method=None):
    if method is None:
        method = get_best_train_method()

    if method == "unsloth":
        return train_with_unsloth(status_cb)
    elif method == "llamacpp":
        config = _get_config()
        model_path = config.get("base_model_path", "")
        if not model_path:
            return False, ("llama.cpp found but no base model path set.\n"
                           "Add to config.json: \"base_model_path\": \"C:\\path\\to\\model.gguf\"")
        return train_with_llamacpp(model_path, status_cb)
    elif method == "ollama":
        return train_with_ollama(status_cb)
    else:
        return False, ("No training method available.\n\n"
                       "Options (pick one):\n"
                       "  1. Install Ollama (easiest): https://ollama.com\n"
                       "     Then: ollama pull llama3.1\n\n"
                       "  2. Install unsloth (best, needs NVIDIA GPU):\n"
                       "     pip install unsloth\n\n"
                       "  3. Build llama.cpp (works on CPU):\n"
                       "     https://github.com/ggerganov/llama.cpp")


def get_correction_context(user_message):
    corrections = load_corrections()
    if not corrections:
        return ""
    user_words = set(user_message.lower().split())
    best_score = 0
    best = None
    for c in corrections:
        q_words = set(c["user_message"].lower().split())
        overlap = len(user_words & q_words)
        total   = len(user_words | q_words)
        score   = overlap / max(total, 1)
        if score > best_score and score > 0.45:
            best_score = score
            best = c
    if not best:
        return ""
    return (
        f"\n[PAST CORRECTION — use this]: "
        f"When asked '{best['user_message']}' the correct answer is: "
        f"'{best['correct_answer']}'. Do not repeat the previous wrong answer."
    )


def _load_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"corrections": 0, "trainings": 0, "last_trained": None}


def _update_stats(key):
    stats = _load_stats()
    stats[key] = stats.get(key, 0) + 1
    if key == "trainings":
        stats["last_trained"] = datetime.datetime.now().isoformat()
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)


def get_stats_text():
    stats  = _load_stats()
    count  = get_correction_count()
    convos = get_conversation_count()
    method = get_best_train_method()
    trained = stats.get("last_trained")
    trained_str = trained[:10] if trained else "never"

    method_label = {
        "unsloth":  "unsloth (real GPU fine-tune)",
        "llamacpp": "llama.cpp (CPU LoRA fine-tune)",
        "ollama":   "ollama create (system prompt + examples)",
        "none":     "none available — install Ollama or unsloth"
    }.get(method, method)

    lines = [
        f"Conversations logged : {convos}",
        f"Corrections logged   : {count}",
        f"Training runs        : {stats.get('trainings', 0)}",
        f"Last trained         : {trained_str}",
        f"Train method         : {method_label}",
    ]
    if count == 0:
        lines.append("Next step: after any wrong answer type /correct <right answer>")
    elif count < 5:
        lines.append(f"Need {5 - count} more corrections before /train")
    else:
        lines.append("Ready to train — type /train")

    return "\n".join(lines)
