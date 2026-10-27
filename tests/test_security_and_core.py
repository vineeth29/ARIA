# ARIA — AI Desktop Assistant

ARIA is a Windows-first Python desktop assistant that combines an LLM-backed chat loop with local desktop automation, voice, image analysis, memory, and scheduling. The project is built as a personal productivity and automation tool rather than a web service, and it is intended to run on a local Windows machine with provider keys configured for Groq, Gemini, Cerebras, or Ollama.

## What is implemented

- Chat interface with provider abstraction
- Multiple LLM backends: Groq, Gemini, Cerebras, Ollama
- Local memory and context persistence
- Voice capture/transcription support
- Vision/image analysis support for screenshots and images
- Browser and app launching actions via automation helpers
- Scheduling and reminder features
- Screen-watching workflow for monitoring UI changes and alerting on patterns
- Local search and knowledge-memory features

## Architecture

```mermaid
flowchart TD
    User --> UI[ui.py]
    UI --> ARIA[aria.py]
    ARIA --> Router[providers.py SmartRouter]
    Router --> Groq[Groq API]
    Router --> Gemini[Gemini API]
    Router --> Cerebras[Cerebras API]
    Router --> Ollama[Ollama local server]

    ARIA --> Voice[voice.py]
    ARIA --> Vision[vision.py]
    ARIA --> Actions[automation.py]
    ARIA --> Memory[JSON/SQLite-style local memory]
    ARIA --> Watch[screen_watcher.py]
    ARIA --> Scheduler[scheduler.py]
    Actions --> OS[Windows apps, browser, files, shell]
```

## Prerequisites

This project is primarily designed for Windows.

- Python 3.10+
- Windows 10 or 11
- Internet access for provider calls or local Ollama for offline use
- A configured API key for the chosen provider

## Setup

1. Clone the repository:

```bash
git clone https://github.com/vineeth29/ARIA.git
cd ARIA
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Copy the template config and fill in local values:

```bash
copy config.template.json config.json
```

Then update `config.json` with your keys and settings:

```json
{
  "groq_api_key": "",
  "cerebras_api_key": "",
  "gemini_api_key": "",
  "ollama_model": "llama3.1",
  "ollama_url": "http://localhost:11434",
  "preferred_provider": "auto",
  "personality_mode": "default",
  "allow_screen_watcher": false
}
```

Important:
- Use placeholder values only in documentation and examples.
- Do not commit real secrets.
- `allow_screen_watcher` defaults to `false` for privacy safety.

## Launch

```bash
python aria.py
```

## Example workflow

```text
User: Open Google and search for Python tutorials.
ARIA: [ACTION: open_url(url="https://www.google.com")]
ARIA: [ACTION: search_google(query="Python tutorials")]
```

```text
User: Summarize the current screen.
ARIA: [ACTION: read my screen]
```

## Security and privacy notes

- Screen capturing and monitoring are disabled by default and must be explicitly enabled.
- Local memory and recorded outputs are stored on disk; avoid storing sensitive content in the app data directory.
- Shell execution and destructive actions require explicit confirmation before execution.
- PowerShell calls and app-launch commands are intentionally restricted to explicit user intent and validated input.

## Known limitations

- The project is Windows-oriented and not a general cross-platform app.
- Some automation features depend on local OS state, installed apps, and browser availability.
- Screen monitoring and speech features require the relevant local dependencies and may behave differently across machines.
- Provider reliability and rate-limit handling are basic and should be improved for production reliability.
- The project is a solid personal engineering prototype, not a hardened enterprise automation platform.

## Planned improvements

- Stronger retry and fallback logic for provider failures
- Broader test coverage with mocked provider responses
- Safer command execution and explicit approval flow for system actions
- Cleaner packaging and module boundaries
- Better deployment and onboarding documentation

## Repository status

This project is a working prototype that demonstrates practical AI integration, local automation, and a usable assistant loop. It is suitable for a technical portfolio submission after safety and documentation updates, but it should not be presented as a production-ready business automation system.
