import json, os, time
from abc import ABC, abstractmethod

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
    except IOError as e:
        print(f"  [WARNING] Could not save config: {e}")


class Provider(ABC):
    def __init__(self, name, model, api_key=None):
        self.name = name
        self.model = model
        self.api_key = api_key
        self.is_available = False
        self.last_error = None
        self.last_used = 0
        self.rate_limited_until = 0
        self.fail_count = 0

    @abstractmethod
    def stream_silent(self, messages, system_prompt=""):
        pass

    def is_ready(self):
        if not self.api_key and self.name != "Ollama":
            return False
        if time.time() < self.rate_limited_until:
            return False
        return True

    def mark_rate_limited(self, seconds=60):
        self.rate_limited_until = time.time() + seconds
        self.last_error = f"Rate limited ({seconds}s)"
        self.fail_count += 1

    def mark_failed(self, error):
        self.last_error = str(error)[:100]
        self.fail_count += 1
        wait = min(30 * self.fail_count, 300)
        self.rate_limited_until = time.time() + wait

    def mark_success(self):
        self.is_available = True
        self.last_used = time.time()
        self.fail_count = 0

    def rate_limit_remaining(self):
        return max(0, int(self.rate_limited_until - time.time()))

    def status_emoji(self):
        if not self.api_key and self.name != "Ollama":
            return "⚪"
        if time.time() < self.rate_limited_until:
            return "🟡"
        if self.is_available:
            return "🟢"
        return "🔴"


class GroqProvider(Provider):
    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, api_key=None):
        super().__init__("Groq", "llama-3.3-70b-versatile", api_key)

    def stream_silent(self, messages, system_prompt=""):
        import requests
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = []
        if system_prompt:
            payload.append({"role": "system", "content": system_prompt})
        payload.extend(messages)
        r = requests.post(
            self.BASE_URL, headers=headers, stream=True, timeout=30,
            json={"model": self.model, "messages": payload,
                  "stream": True, "temperature": 0.4, "max_tokens": 1024}
        )
        if r.status_code == 429:
            self.mark_rate_limited(60)
            raise Exception("Rate limited")
        if r.status_code != 200:
            raise Exception(f"HTTP {r.status_code}: {r.text[:80]}")
        full = ""
        for line in r.iter_lines():
            if line:
                s = line.decode("utf-8", errors="ignore")
                if s.startswith("data: "):
                    d = s[6:]
                    if d.strip() == "[DONE]":
                        break
                    try:
                        tok = json.loads(d).get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if tok:
                            full += tok
                    except Exception:
                        continue
        self.mark_success()
        return full


    def stream_live(self, messages, system_prompt="", token_cb=None):
        import requests
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = []
        if system_prompt:
            payload.append({"role": "system", "content": system_prompt})
        payload.extend(messages)
        r = requests.post(self.BASE_URL, headers=headers, stream=True, timeout=60,
                          json={"model": self.model, "messages": payload,
                                "stream": True, "temperature": 0.7, "max_tokens": 4096})
        if r.status_code == 429:
            self.mark_rate_limited(60); raise Exception("Rate limited")
        if r.status_code != 200:
            raise Exception(f"HTTP {r.status_code}: {r.text[:80]}")
        full = ""
        for line in r.iter_lines():
            if line:
                s = line.decode("utf-8", errors="ignore")
                if s.startswith("data: "):
                    d = s[6:]
                    if d.strip() == "[DONE]": break
                    try:
                        tok = json.loads(d).get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if tok:
                            if token_cb: token_cb(tok)
                            full += tok
                    except Exception: continue
        self.mark_success()
        return full

    def stream_live(self, messages, system_prompt="", token_cb=None):
        import requests
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = []
        if system_prompt:
            payload.append({"role": "system", "content": system_prompt})
        payload.extend(messages)
        r = requests.post(self.BASE_URL, headers=headers, stream=True, timeout=60,
                          json={"model": self.model, "messages": payload,
                                "stream": True, "temperature": 0.7, "max_tokens": 4096})
        if r.status_code == 429:
            self.mark_rate_limited(60); raise Exception("Rate limited")
        if r.status_code != 200:
            raise Exception(f"HTTP {r.status_code}: {r.text[:80]}")
        full = ""
        for line in r.iter_lines():
            if line:
                s = line.decode("utf-8", errors="ignore")
                if s.startswith("data: "):
                    d = s[6:]
                    if d.strip() == "[DONE]": break
                    try:
                        tok = json.loads(d).get("choices",[{}])[0].get("delta",{}).get("content","")
                        if tok:
                            if token_cb: token_cb(tok)
                            full += tok
                    except Exception: continue
        self.mark_success()
        return full

class CerebrasProvider(Provider):
    BASE_URL = "https://api.cerebras.ai/v1/chat/completions"

    def __init__(self, api_key=None):
        super().__init__("Cerebras", "llama3.1-8b", api_key)

    def stream_silent(self, messages, system_prompt=""):
        import requests
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = []
        if system_prompt:
            payload.append({"role": "system", "content": system_prompt})
        payload.extend(messages)
        r = requests.post(
            self.BASE_URL, headers=headers, stream=True, timeout=30,
            json={"model": self.model, "messages": payload,
                  "stream": True, "temperature": 0.4, "max_tokens": 1024}
        )
        if r.status_code == 429:
            self.mark_rate_limited(60)
            raise Exception("Rate limited")
        if r.status_code != 200:
            raise Exception(f"HTTP {r.status_code}: {r.text[:80]}")
        full = ""
        for line in r.iter_lines():
            if line:
                s = line.decode("utf-8", errors="ignore")
                if s.startswith("data: "):
                    d = s[6:]
                    if d.strip() == "[DONE]":
                        break
                    try:
                        tok = json.loads(d).get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if tok:
                            full += tok
                    except Exception:
                        continue
        self.mark_success()
        return full


    def stream_live(self, messages, system_prompt="", token_cb=None):
        import requests
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = []
        if system_prompt:
            payload.append({"role": "system", "content": system_prompt})
        payload.extend(messages)
        r = requests.post(self.BASE_URL, headers=headers, stream=True, timeout=60,
                          json={"model": self.model, "messages": payload,
                                "stream": True, "temperature": 0.7, "max_tokens": 4096})
        if r.status_code == 429:
            self.mark_rate_limited(60); raise Exception("Rate limited")
        if r.status_code != 200:
            raise Exception(f"HTTP {r.status_code}: {r.text[:80]}")
        full = ""
        for line in r.iter_lines():
            if line:
                s = line.decode("utf-8", errors="ignore")
                if s.startswith("data: "):
                    d = s[6:]
                    if d.strip() == "[DONE]": break
                    try:
                        tok = json.loads(d).get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if tok:
                            if token_cb: token_cb(tok)
                            full += tok
                    except Exception: continue
        self.mark_success()
        return full

    def stream_live(self, messages, system_prompt="", token_cb=None):
        import requests
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = []
        if system_prompt:
            payload.append({"role": "system", "content": system_prompt})
        payload.extend(messages)
        r = requests.post(self.BASE_URL, headers=headers, stream=True, timeout=60,
                          json={"model": self.model, "messages": payload,
                                "stream": True, "temperature": 0.7, "max_tokens": 4096})
        if r.status_code == 429:
            self.mark_rate_limited(60); raise Exception("Rate limited")
        if r.status_code != 200:
            raise Exception(f"HTTP {r.status_code}: {r.text[:80]}")
        full = ""
        for line in r.iter_lines():
            if line:
                s = line.decode("utf-8", errors="ignore")
                if s.startswith("data: "):
                    d = s[6:]
                    if d.strip() == "[DONE]": break
                    try:
                        tok = json.loads(d).get("choices",[{}])[0].get("delta",{}).get("content","")
                        if tok:
                            if token_cb: token_cb(tok)
                            full += tok
                    except Exception: continue
        self.mark_success()
        return full

class GeminiProvider(Provider):
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, api_key=None):
        super().__init__("Gemini", "gemini-2.0-flash", api_key)

    def stream_silent(self, messages, system_prompt=""):
        import requests
        url = f"{self.BASE_URL}/{self.model}:streamGenerateContent?alt=sse&key={self.api_key}"
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        if not contents or contents[-1]["role"] != "user":
            raise Exception("Gemini: last message must be user")
        payload = {
            "contents": contents,
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 1024}
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        r = requests.post(
            url, json=payload, stream=True, timeout=30,
            headers={"Content-Type": "application/json"}
        )
        if r.status_code == 429:
            self.mark_rate_limited(60)
            raise Exception("Rate limited")
        if r.status_code != 200:
            raise Exception(f"HTTP {r.status_code}: {r.text[:80]}")
        full = ""
        for line in r.iter_lines():
            if line:
                s = line.decode("utf-8", errors="ignore")
                if s.startswith("data: "):
                    try:
                        cands = json.loads(s[6:]).get("candidates", [])
                        if cands:
                            for part in cands[0].get("content", {}).get("parts", []):
                                tok = part.get("text", "")
                                if tok:
                                    full += tok
                    except Exception:
                        continue
        self.mark_success()
        return full


    def stream_live(self, messages, system_prompt="", token_cb=None):
        import requests
        url = f"{self.BASE_URL}/{self.model}:streamGenerateContent?alt=sse&key={self.api_key}"
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        if not contents or contents[-1]["role"] != "user":
            raise Exception("Gemini: last message must be user")
        payload = {"contents": contents,
                   "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4096}}
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        r = requests.post(url, json=payload, stream=True, timeout=60,
                          headers={"Content-Type": "application/json"})
        if r.status_code == 429:
            self.mark_rate_limited(60); raise Exception("Rate limited")
        if r.status_code != 200:
            raise Exception(f"HTTP {r.status_code}: {r.text[:80]}")
        full = ""
        for line in r.iter_lines():
            if line:
                s = line.decode("utf-8", errors="ignore")
                if s.startswith("data: "):
                    try:
                        cands = json.loads(s[6:]).get("candidates", [])
                        if cands:
                            for part in cands[0].get("content", {}).get("parts", []):
                                tok = part.get("text", "")
                                if tok:
                                    if token_cb: token_cb(tok)
                                    full += tok
                    except Exception: continue
        self.mark_success()
        return full

    def stream_live(self, messages, system_prompt="", token_cb=None):
        import requests
        url = f"{self.BASE_URL}/{self.model}:streamGenerateContent?alt=sse&key={self.api_key}"
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        if not contents or contents[-1]["role"] != "user":
            raise Exception("Gemini: last message must be user")
        payload = {"contents": contents,
                   "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4096}}
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        r = requests.post(url, json=payload, stream=True, timeout=60,
                          headers={"Content-Type": "application/json"})
        if r.status_code == 429:
            self.mark_rate_limited(60); raise Exception("Rate limited")
        if r.status_code != 200:
            raise Exception(f"HTTP {r.status_code}: {r.text[:80]}")
        full = ""
        for line in r.iter_lines():
            if line:
                s = line.decode("utf-8", errors="ignore")
                if s.startswith("data: "):
                    try:
                        cands = json.loads(s[6:]).get("candidates", [])
                        if cands:
                            for part in cands[0].get("content",{}).get("parts",[]):
                                tok = part.get("text","")
                                if tok:
                                    if token_cb: token_cb(tok)
                                    full += tok
                    except Exception: continue
        self.mark_success()
        return full

class OllamaProvider(Provider):
    def __init__(self, model="llama3.1", ollama_url="http://localhost:11434"):
        super().__init__("Ollama", model)
        self.ollama_url = ollama_url
        self.api_key = "local"

    def is_ready(self):
        try:
            import requests
            return requests.get(f"{self.ollama_url}/", timeout=2).status_code == 200
        except Exception:
            return False

    def _start_server(self):
        import subprocess, requests
        try:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )
            for _ in range(10):
                time.sleep(1)
                try:
                    if requests.get(f"{self.ollama_url}/", timeout=2).status_code == 200:
                        return True
                except Exception:
                    pass
        except FileNotFoundError:
            pass
        return False

    def stream_silent(self, messages, system_prompt=""):
        import requests
        if not self.is_ready():
            if not self._start_server():
                raise Exception("Ollama not running")
        trimmed = system_prompt[:1500] if system_prompt else ""
        payload = []
        if trimmed:
            payload.append({"role": "system", "content": trimmed})
        payload.extend(messages)
        r = requests.post(
            f"{self.ollama_url}/api/chat",
            json={"model": self.model, "messages": payload, "stream": True},
            stream=True, timeout=120
        )
        if r.status_code != 200:
            raise Exception(f"Ollama HTTP {r.status_code}")
        full = ""
        for line in r.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    tok = chunk.get("message", {}).get("content", "")
                    if tok:
                        full += tok
                    if chunk.get("done"):
                        break
                except Exception:
                    continue
        self.mark_success()
        return full


    def stream_live(self, messages, system_prompt="", token_cb=None):
        import requests
        if not self.is_ready():
            if not self._start_server():
                raise Exception("Ollama not running")
        trimmed = system_prompt[:2000] if system_prompt else ""
        payload = []
        if trimmed:
            payload.append({"role": "system", "content": trimmed})
        payload.extend(messages)
        r = requests.post(f"{self.ollama_url}/api/chat",
                          json={"model": self.model, "messages": payload, "stream": True},
                          stream=True, timeout=300)
        if r.status_code != 200:
            raise Exception(f"Ollama HTTP {r.status_code}")
        full = ""
        for line in r.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    tok = chunk.get("message", {}).get("content", "")
                    if tok:
                        if token_cb: token_cb(tok)
                        full += tok
                    if chunk.get("done"): break
                except Exception: continue
        self.mark_success()
        return full

    def stream_live(self, messages, system_prompt="", token_cb=None):
        import requests
        if not self.is_ready():
            if not self._start_server():
                raise Exception("Ollama not running")
        trimmed = system_prompt[:2000] if system_prompt else ""
        payload = []
        if trimmed:
            payload.append({"role": "system", "content": trimmed})
        payload.extend(messages)
        r = requests.post(f"{self.ollama_url}/api/chat",
                          json={"model": self.model, "messages": payload, "stream": True},
                          stream=True, timeout=300)
        if r.status_code != 200:
            raise Exception(f"Ollama HTTP {r.status_code}")
        full = ""
        for line in r.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    tok = chunk.get("message",{}).get("content","")
                    if tok:
                        if token_cb: token_cb(tok)
                        full += tok
                    if chunk.get("done"): break
                except Exception: continue
        self.mark_success()
        return full

class SmartRouter:
    def __init__(self):
        config = load_config()
        self.providers = [
            GroqProvider(api_key=config.get("groq_api_key")),
            CerebrasProvider(api_key=config.get("cerebras_api_key")),
            GeminiProvider(api_key=config.get("gemini_api_key")),
            OllamaProvider(
                model=config.get("ollama_model", "llama3.1"),
                ollama_url=config.get("ollama_url", "http://localhost:11434")
            ),
        ]
        self.sticky_provider = None
        self.last_provider = None
        self.system_prompt = ""
        self._prompt_loaded = False

    def set_system_prompt(self, prompt):
        self.system_prompt = prompt

    def load_system_prompt_from_file(self):
        if self._prompt_loaded:
            return True
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aria_prompt.txt")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.system_prompt = f.read()
                self._prompt_loaded = True
                return True
            except IOError:
                pass
        return False

    def get_ready_providers(self):
        return [p for p in self.providers if p.is_ready()]

    def _pick_order(self):
        if self.sticky_provider and self.sticky_provider.is_ready():
            return [self.sticky_provider] + [
                p for p in self.providers
                if p.is_ready() and p is not self.sticky_provider
            ]
        return self.get_ready_providers()


    def stream_response_live(self, messages, token_cb=None, retries=2):
        for attempt in range(retries + 1):
            order = self._pick_order()
            if not order:
                if attempt < retries:
                    import time; time.sleep(2)
                    continue
                return None
            errors = []
            for provider in order:
                try:
                    reply = provider.stream_live(
                        messages, self.system_prompt, token_cb=token_cb
                    )
                    if not reply or len(reply.strip()) < 2:
                        raise Exception("Empty response")
                    if self.sticky_provider is not provider:
                        self.sticky_provider = provider
                    self.last_provider = provider
                    return reply
                except KeyboardInterrupt:
                    return None
                except Exception as e:
                    msg = str(e)
                    errors.append(f"{provider.name}: {msg[:60]}")
                    if "rate limit" in msg.lower() or "429" in msg:
                        provider.mark_rate_limited(60)
                    elif "timeout" in msg.lower():
                        provider.mark_rate_limited(15)
                    else:
                        provider.mark_failed(msg)
                    if provider is self.sticky_provider:
                        self.sticky_provider = None
                    continue
            if attempt < retries:
                import time
                wait = 3 * (attempt + 1)
                print(f"  [All providers failed, retrying in {wait}s...]")
                time.sleep(wait)
        return None

    def stream_response_silent(self, messages):
        order = self._pick_order()
        if not order:
            return None
        errors = []
        for provider in order:
            try:
                reply = provider.stream_silent(messages, self.system_prompt)
                if self.sticky_provider is not provider:
                    self.sticky_provider = provider
                self.last_provider = provider
                return reply
            except KeyboardInterrupt:
                return None
            except Exception as e:
                msg = str(e)
                errors.append(f"{provider.name}: {msg[:60]}")
                if "rate limit" in msg.lower() or "429" in msg:
                    provider.mark_rate_limited(60)
                else:
                    provider.mark_failed(msg)
                if provider is self.sticky_provider:
                    self.sticky_provider = None
        return None

    def count_ready(self):
        return len(self.get_ready_providers())

    def reload_config(self):
        config = load_config()
        for p in self.providers:
            if isinstance(p, GroqProvider):
                p.api_key = config.get("groq_api_key")
            elif isinstance(p, CerebrasProvider):
                p.api_key = config.get("cerebras_api_key")
            elif isinstance(p, GeminiProvider):
                p.api_key = config.get("gemini_api_key")
        self.sticky_provider = None

    def get_status_table(self):
        lines = [
            "  ┌──────────┬─────────────┬──────────────────────────────────┐",
            "  │ Status   │ Provider    │ Model                            │",
            "  ├──────────┼─────────────┼──────────────────────────────────┤",
        ]
        for p in self.providers:
            star = "★ " if p is self.sticky_provider else "  "
            if not p.api_key and p.name != "Ollama":
                st, info = "No Key", "run installer.py"
            elif time.time() < p.rate_limited_until:
                st, info = "Cooling", f"ready in {p.rate_limit_remaining()}s"
            elif p.is_available:
                st, info = "Ready", p.model[:32]
            else:
                st, info = "Standby", p.model[:32]
            lines.append(
                f"  │ {p.status_emoji()}{star}{st:<5} │ {p.name:<11} │ {info:<32} │"
            )
        lines.append("  └──────────┴─────────────┴──────────────────────────────────┘")
        if self.sticky_provider:
            lines.append(f"  ★ Active: {self.sticky_provider.name} ({self.sticky_provider.model})")
        return "\n".join(lines)
