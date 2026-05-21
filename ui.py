import os, sys, textwrap, shutil, datetime, threading, time

try:
    import colorama
    colorama.init()
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False

RESET  = "\033[0m"      if HAS_COLOR else ""
BOLD   = "\033[1m"      if HAS_COLOR else ""
DIM    = "\033[2m"      if HAS_COLOR else ""

C_YOU       = "\033[38;5;117m"   if HAS_COLOR else ""   # soft blue  — your messages
C_YOU_BG    = "\033[48;5;24m"    if HAS_COLOR else ""   # blue bg bubble
C_ARIA      = "\033[38;5;120m"   if HAS_COLOR else ""   # soft green — ARIA messages
C_ARIA_BG   = "\033[48;5;22m"    if HAS_COLOR else ""   # green bg bubble
C_TIME      = "\033[38;5;240m"   if HAS_COLOR else ""   # dark grey timestamp
C_BORDER    = "\033[38;5;236m"   if HAS_COLOR else ""   # very dark border
C_HEADER    = "\033[38;5;39m"    if HAS_COLOR else ""   # bright blue header
C_WARN      = "\033[38;5;214m"   if HAS_COLOR else ""   # orange warning
C_ERR       = "\033[38;5;196m"   if HAS_COLOR else ""   # red error
C_CMD       = "\033[38;5;183m"   if HAS_COLOR else ""   # purple commands
C_ACTION    = "\033[38;5;228m"   if HAS_COLOR else ""   # yellow actions
C_STATUS    = "\033[38;5;245m"   if HAS_COLOR else ""   # mid grey status


def term_width():
    return max(shutil.get_terminal_size((100, 24)).columns, 60)


def now_str():
    return datetime.datetime.now().strftime("%H:%M")


def wrap_text(text, width):
    lines = []
    for paragraph in text.split("\n"):
        if paragraph.strip() == "":
            lines.append("")
            continue
        wrapped = textwrap.wrap(paragraph, width=width)
        lines.extend(wrapped if wrapped else [""])
    return lines


def print_you(text):
    """Print user bubble — right aligned, blue."""
    w = term_width()
    bubble_max = min(55, w - 10)
    lines = wrap_text(text.strip(), bubble_max)
    ts = now_str()

    print()
    for i, line in enumerate(lines):
        pad = w - len(line) - 6
        if i == 0:
            print(f"{C_YOU_BG}{BOLD} {line} {RESET}{C_TIME} {ts}{RESET}")
        else:
            print(f"{' ' * max(0, pad)}{C_YOU} {line} {RESET}")
    print()


def _aria_line(line, ts_shown, ts, first_line):
    prefix = f"{C_ARIA_BG}{BOLD}ARIA{RESET} " if first_line else "     "
    time_part = f" {C_TIME}{ts}{RESET}" if first_line and not ts_shown else ""
    print(f"{prefix}{C_ARIA}{line}{RESET}{time_part}")


def print_aria(text):
    """Print ARIA bubble — left side, green."""
    w = term_width()
    bubble_max = min(70, w - 10)
    text = text.strip()
    lines = wrap_text(text, bubble_max)
    ts = now_str()

    print()
    for i, line in enumerate(lines):
        if i == 0:
            print(f"{C_ARIA_BG}{BOLD} ARIA {RESET} {C_TIME}{ts}{RESET}")
        if line.startswith("[ACTION:") or line.startswith("[RUNNING]") or line.startswith("[FIXED]"):
            print(f"     {C_ACTION}{line}{RESET}")
        elif line.startswith("[ERROR]") or line.startswith("  Error"):
            print(f"     {C_ERR}{line}{RESET}")
        elif line.startswith("[WARNING]") or line.startswith("  Warning"):
            print(f"     {C_WARN}{line}{RESET}")
        elif line.startswith("/") or line.strip().startswith("/"):
            print(f"     {C_CMD}{line}{RESET}")
        else:
            print(f"     {C_ARIA}{line}{RESET}")
    print()


def print_aria_stream_start():
    """Print the ARIA header before streaming starts."""
    ts = now_str()
    print()
    print(f"{C_ARIA_BG}{BOLD} ARIA {RESET} {C_TIME}{ts}{RESET}")
    print(f"     ", end="", flush=True)


def print_aria_stream_token(token):
    """Print a single streaming token with color."""
    sys.stdout.write(f"{C_ARIA}{token}{RESET}")
    sys.stdout.flush()


def print_aria_stream_end():
    """End the streaming output cleanly."""
    print(f"\n{RESET}")


def print_system(text, kind="info"):
    """Print a system/status line — not a chat bubble."""
    w = term_width()
    color = {
        "info":    C_STATUS,
        "warn":    C_WARN,
        "error":   C_ERR,
        "action":  C_ACTION,
        "success": C_ARIA,
    }.get(kind, C_STATUS)
    print(f"  {color}{text}{RESET}")


def print_divider():
    w = term_width()
    print(f"{C_BORDER}{'─' * w}{RESET}")


def print_header(provider_name=""):
    w = term_width()
    os.system("cls" if os.name == "nt" else "clear")
    now = datetime.datetime.now().strftime("%d %b %Y  %H:%M")
    title = "  ARIA  —  Offline AI Agent"
    right = f"{now}  {provider_name}"
    gap = w - len(title) - len(right) - 2
    print(f"\n{C_HEADER}{BOLD}{title}{RESET}{' ' * max(0, gap)}{C_TIME}{right}{RESET}")
    print(f"{C_BORDER}{'═' * w}{RESET}\n")


def print_startup_box(status_line, provider_count, personality, nickname=""):
    w = term_width()
    inner = w - 4
    greeting = f"Hey {nickname}!" if nickname else "Ready!"
    lines = [
        f"ARIA v10.0  —  Personal AI Agent",
        f"",
        f"{greeting}",
        f"",
        f"Providers ready  : {provider_count}/4",
        f"Personality      : {personality}",
        f"",
        status_line,
        f"",
        f"Type naturally or /help for commands",
    ]
    print(f"  {C_BORDER}╔{'═' * inner}╗{RESET}")
    for line in lines:
        pad = inner - len(line) - 2
        print(f"  {C_BORDER}║{RESET} {C_HEADER}{line}{RESET}{' ' * max(0, pad)} {C_BORDER}║{RESET}")
    print(f"  {C_BORDER}╚{'═' * inner}╝{RESET}\n")


def get_input(prompt_extra=""):
    """Get user input with a styled prompt."""
    ts = now_str()
    prompt = f"{C_YOU_BG}{BOLD} You {RESET} {C_TIME}{ts}{RESET} {C_YOU}› {RESET}"
    try:
        raw = input(prompt)
        return raw
    except (EOFError, KeyboardInterrupt):
        return "/exit"


def thinking_dots(stop_event):
    """Show animated thinking dots while ARIA is processing."""
    frames = ["   ⠋", "   ⠙", "   ⠹", "   ⠸", "   ⠼", "   ⠴", "   ⠦", "   ⠧", "   ⠇", "   ⠏"]
    i = 0
    print(f"  {C_STATUS}ARIA is thinking{RESET}", end="", flush=True)
    while not stop_event.is_set():
        sys.stdout.write(f"\r  {C_STATUS}ARIA is thinking {frames[i % len(frames)]}{RESET}")
        sys.stdout.flush()
        time.sleep(0.08)
        i += 1
    sys.stdout.write(f"\r{' ' * 40}\r")
    sys.stdout.flush()


def print_action_result(action_name, success=True):
    icon = "✅" if success else "❌"
    print_system(f"{icon} {action_name}", "success" if success else "error")


def print_provider_switch(name, model):
    print_system(f"↪ Switched to {name} ({model})", "info")


def format_table(headers, rows):
    """Format a simple table for terminal output."""
    cols = len(headers)
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    sep = "  ┼".join("─" * (w + 2) for w in widths)
    header_row = "  │".join(f" {h:<{widths[i]}} " for i, h in enumerate(headers))
    lines = [
        f"  ┌{'┬'.join('─'*(w+2) for w in widths)}┐",
        f"  │{header_row}│",
        f"  ├{'┼'.join('─'*(w+2) for w in widths)}┤",
    ]
    for row in rows:
        r = "  │".join(f" {str(row[i]):<{widths[i]}} " for i in range(cols))
        lines.append(f"  │{r}│")
    lines.append(f"  └{'┴'.join('─'*(w+2) for w in widths)}┘")
    return "\n".join(lines)


_streaming_active = False
_stream_line_len  = 0

def print_aria_header():
    """Print ARIA bubble header, then wait for streaming tokens."""
    global _streaming_active, _stream_line_len
    ts = now_str()
    print()
    print(f"{C_ARIA_BG}{BOLD} ARIA {RESET} {C_TIME}{ts}{RESET}")
    sys.stdout.write(f"     {C_ARIA}")
    sys.stdout.flush()
    _streaming_active = True
    _stream_line_len  = 0


def stream_token(token):
    """Write a single token live to the terminal — word-wrap aware."""
    global _stream_line_len
    w = term_width() - 6
    for char in token:
        if char == "\n":
            sys.stdout.write(f"{RESET}\n     {C_ARIA}")
            _stream_line_len = 0
        else:
            sys.stdout.write(char)
            _stream_line_len += 1
            if _stream_line_len >= w and char == " ":
                sys.stdout.write(f"{RESET}\n     {C_ARIA}")
                _stream_line_len = 0
    sys.stdout.flush()


def print_aria_footer():
    """Close the streaming bubble cleanly."""
    global _streaming_active
    sys.stdout.write(f"{RESET}\n\n")
    sys.stdout.flush()
    _streaming_active = False
