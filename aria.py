import os, json, datetime, sys, time, re, threading

MEMORY_FILE = os.path.expanduser("~/aria_memory.json")
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
MAX_HISTORY = 20

AUTOMATION_BLOCK = """
## HOW TO EXECUTE TASKS — READ THIS CAREFULLY

When the user asks you to DO anything on the computer, you MUST write an ACTION block.
Do NOT just say "Opening YouTube" — actually open it with an ACTION.
Do NOT describe what you will do — DO IT with an ACTION block.

ACTION SYNTAX (copy exactly):
[ACTION: function_name(key="value")]

COMMON EXAMPLES — memorise these:

User: open youtube / open yt
You write: [ACTION: open_youtube()]

User: open youtube and search lofi
You write: [ACTION: open_youtube(query="lofi music")]

User: open chrome / open browser
You write: [ACTION: open_app(name="chrome")]

User: open spotify
You write: [ACTION: open_app(name="spotify")]

User: open google / go to google.com
You write: [ACTION: open_url(url="https://www.google.com")]

User: search for python tutorials
You write: [ACTION: search_google(query="python tutorials")]

User: take a screenshot
You write: [ACTION: screenshot(filename="screenshot.png")]

User: set volume to 50
You write: [ACTION: set_volume(level="50")]

User: lock the screen
You write: [ACTION: lock_screen()]

User: clear temp files
You write: [ACTION: clear_temp()]

User: what processes are running / what's eating my RAM
You write: [ACTION: run_command(cmd="tasklist /FO TABLE /NH")]

User: check my CPU
You write: [ACTION: run_command(cmd="wmic cpu get loadpercentage")]

User: send whatsapp to John saying hi
You write: [ACTION: send_whatsapp(contact="John" message="hi")]

User: open notepad
You write: [ACTION: open_app(name="notepad")]

User: shutdown my pc
You write: [ACTION: shutdown(delay="0")]

User: check internet
You write: [ACTION: check_internet()]

User: get my wifi password
You write: [ACTION: wifi_password()]

ALL AVAILABLE ACTIONS:
open_url, open_browser, open_youtube, open_app, open_gmail, open_calendar,
search_google, send_whatsapp, browser_click, browser_type, browser_press,
browser_wait, browser_text, close_browser, type_text, press_key, hotkey,
mouse_click, mouse_move, mouse_scroll, screenshot, run_command, wait,
set_volume, mute, lock_screen, sleep_pc, shutdown, restart, cancel_shutdown,
empty_recycle_bin, clear_temp, kill_process, wifi_password, check_internet,
public_ip, local_ip, flush_dns, reset_network, ping, scan_ports,
create_folder, delete_file, rename_file, copy_file, zip_folder, find_files,
read_file, write_file, append_file, disk_usage, battery_status, top_processes,
set_wallpaper, notify, speak, set_reminder, download_file, get_clipboard,
set_clipboard, translate, weather, run_python, generate_password, system_info,
dark_mode, light_mode, startup_programs, install_package, focus_window,
close_window, minimize_all, maximize_window, git_status, git_commit, git_push,
create_shortcut.

STRICT RULES:
1. ALWAYS use [ACTION:] when user asks to open, run, search, control anything.
2. Never say "Opening X" without an ACTION block. That does nothing.
3. Keep your text reply SHORT — 1-3 lines max. Just confirm what you did.
4. After the action, say: Done. Is this what you wanted?
5. Never invent system data. Use run_command to get real values.
"""


def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_memory(mem):
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(mem, f, indent=2)
    except IOError:
        pass


def get_real_system_status():
    parts = []
    try:
        import psutil
        cpu  = psutil.cpu_percent(interval=0.3)
        ram  = psutil.virtual_memory()
        bat  = psutil.sensors_battery()
        free = ram.available / (1024**3)
        tot  = ram.total    / (1024**3)
        parts.append(f"CPU {cpu:.0f}%")
        parts.append(f"RAM {free:.1f}/{tot:.1f}GB")
        if bat:
            parts.append(f"Battery {int(bat.percent)}%")
    except Exception:
        pass
    return "  ".join(parts) if parts else "System status unavailable"


def trim_history(history):
    if len(history) > MAX_HISTORY:
        return history[-MAX_HISTORY:]
    return history


def parse_and_execute_actions(text, ui):
    try:
        from automation import execute_action
    except ImportError:
        return False

    pattern = r'\[ACTION:\s*(\w+)\(([^)]*)\)\]'
    matches = list(re.finditer(pattern, text))
    if not matches:
        return False

    for match in matches:
        func_name = match.group(1)
        args_str  = match.group(2).strip()
        kwargs = {}
        if args_str:
            for k, v in re.findall(r'(\w+)\s*=\s*"([^"]*)"', args_str):
                try:    kwargs[k] = int(v)
                except ValueError:
                    try: kwargs[k] = float(v)
                    except ValueError: kwargs[k] = v
            if not kwargs:
                val = args_str.strip('"').strip("'")
                param_map = {
                    "open_browser":"url","open_url":"url","browser_wait":"seconds",
                    "browser_click":"text","browser_type":"text","browser_press":"key",
                    "send_whatsapp":"contact","search_google":"query","open_youtube":"query",
                    "open_app":"name","type_text":"text","press_key":"key",
                    "screenshot":"filename","run_command":"cmd","wait":"seconds",
                }
                p = param_map.get(func_name, "text")
                try:    kwargs[p] = int(val)
                except ValueError: kwargs[p] = val
        try:
            execute_action(func_name, **kwargs)
        except Exception as e:
            ui.print_system(f"Action failed: {func_name} — {str(e)[:60]}", "error")

    return True


def run_aria():
    try:
        from providers import SmartRouter
        import ui
    except ImportError as e:
        print(f"Missing module: {e}")
        sys.exit(1)

    mods = {}
    for name in ["sounds","personalities","notes","mood","health","clipboard_mgr",
                 "tracker","triggers","scheduler","smart_dj","focus","tiler","habits","games","sysinfo"]:
        try:
            mods[name] = __import__(name)
        except ImportError:
            pass

    try:
        import vision as vision_mod
    except ImportError:
        vision_mod = None

    try:
        import learner
    except ImportError:
        learner = None

    try:
        import voice as voice_mod
    except ImportError:
        voice_mod = None

    try:
        import filereader as filereader_mod
    except ImportError:
        filereader_mod = None

    try:
        import websearch as websearch_mod
    except ImportError:
        websearch_mod = None

    try:
        import routines as routines_mod
        routines_mod.ensure_builtins()
    except ImportError:
        routines_mod = None

    try:
        import memory_search as memsearch_mod
    except ImportError:
        memsearch_mod = None

    try:
        import screenreader as screenreader_mod
    except ImportError:
        screenreader_mod = None

    try:
        import workspace as workspace_mod
    except ImportError:
        workspace_mod = None

    try:
        import briefing as briefing_mod
    except ImportError:
        briefing_mod = None

    try:
        import codesandbox as sandbox_mod
    except ImportError:
        sandbox_mod = None

    try:
        import ai_features as aif
    except ImportError:
        aif = None

    try:
        import setup_wizard
    except ImportError:
        setup_wizard = None

    try:
        import docsearch as docsearch_mod
    except ImportError:
        docsearch_mod = None

    try:
        import easter_eggs as eggs_mod
    except ImportError:
        eggs_mod = None

    try:
        import context_manager as ctx_mod
    except ImportError:
        ctx_mod = None

    try:
        import updater as updater_mod
    except ImportError:
        updater_mod = None

    try:
        import screen_watcher as sw_mod
    except ImportError:
        sw_mod = None

    try:
        import task_chain as chain_mod
    except ImportError:
        chain_mod = None

    try:
        import researcher as researcher_mod
    except ImportError:
        researcher_mod = None

    try:
        import knowledge_graph as kg_mod
    except ImportError:
        kg_mod = None

    try:
        import lifelog as lifelog_mod
    except ImportError:
        lifelog_mod = None

    try:
        import negotiator as negotiator_mod
    except ImportError:
        negotiator_mod = None

    try:
        import mistake_guard as guard_mod
    except ImportError:
        guard_mod = None

    try:
        import exam_coach as examcoach_mod
    except ImportError:
        examcoach_mod = None

    try:
        import voice_style as vstyle_mod
    except ImportError:
        vstyle_mod = None

    try:
        import typing_mood as tmood_mod
    except ImportError:
        tmood_mod = None

    from providers import load_config as _load_cfg
    _cfg = _load_cfg()

    def m(n): return mods.get(n)

    try:
        import colorama; colorama.init()
    except ImportError:
        pass

    router = SmartRouter()
    router.load_system_prompt_from_file()

    if setup_wizard and not setup_wizard.is_setup_done():
        setup_wizard.run_wizard()

    if setup_wizard:
        user_ctx = setup_wizard.get_user_context()
        if user_ctx and "[USER PROFILE]" not in router.system_prompt:
            router.system_prompt = f"[USER PROFILE]:\n{user_ctx}\n\n" + router.system_prompt

    if "AUTOMATION ACTIONS" not in router.system_prompt:
        router.system_prompt += AUTOMATION_BLOCK

    if router.count_ready() == 0:
        print("No AI providers configured. Run installer.py")
        sys.exit(1)

    for svc in ["health","clipboard_mgr","tracker","scheduler"]:
        mod = m(svc)
        if mod:
            fn = getattr(mod,"start_monitor",None) or getattr(mod,"start_daemon",None)
            if fn:
                try: fn()
                except Exception: pass

    memory   = load_memory()
    status   = get_real_system_status()
    pname    = m("personalities").get_personality_info() if m("personalities") else "Default"
    pcount   = router.count_ready()

    if m("sounds"):
        try: m("sounds").startup()
        except Exception: pass

    nickname = "Vineeth"
    if setup_wizard:
        try:
            from providers import load_config as _lc2
            nickname = _lc2().get("user_nickname", "Vineeth") or "Vineeth"
        except Exception:
            pass
    ui.print_header()
    ui.print_startup_box(status, pcount, pname, nickname)

    if briefing_mod:
        try:
            if briefing_mod.should_show_briefing():
                brief = briefing_mod.get_briefing()
                if brief:
                    ui.print_aria(brief)
            else:
                suggestions = briefing_mod.get_proactive_suggestions(memory)
                for s in suggestions:
                    ui.print_system(s, "warn")
        except Exception: pass

    if m("habits"):
        try:
            sug = m("habits").get_suggestion_text()
            if sug: ui.print_system(sug, "info")
        except Exception: pass

    voice_mode = False
    history    = []

    if updater_mod:
        def _bg_update_check():
            try:
                has_update, version, _ = updater_mod.check_for_updates()
                if has_update:
                    ui.print_system(
                        "Update available: v" + str(version) + " — type /update to see details",
                        "info"
                    )
            except Exception:
                pass
        threading.Thread(target=_bg_update_check, daemon=True).start()

    if sw_mod and vision_mod:
        try:
            sw_mod.start(vision_mod=vision_mod, config=_cfg, interval=45)
        except Exception:
            pass



    while True:
        try:
            for svc, fn in [("health","get_pending_alerts"),("scheduler","get_pending_alerts")]:
                mod = m(svc)
                if mod:
                    try:
                        for alert in getattr(mod, fn, lambda:[])():
                            ui.print_system(f"⚠  {alert}", "warn")
                    except Exception: pass

            if sw_mod:
                try:
                    for alert in sw_mod.get_pending_alerts():
                        ui.print_system(
                            f"👁  {alert['message']}: {alert['analysis'][:100]}",
                            "warn"
                        )
                except Exception: pass

            if chain_mod:
                try:
                    for result in chain_mod.get_pending_results():
                        ui.print_system(result.get("message","Chain done"), "success")
                except Exception: pass

            if voice_mode and voice_mod and voice_mod.is_available():
                ui.print_system("🎤 Listening... (speak now)", "info")
                spoken, err = voice_mod.listen_once()
                if spoken:
                    ui.print_you(f"[Voice] {spoken}")
                    user_input = spoken
                elif err:
                    ui.print_system(f"Voice error: {err}", "error")
                    user_input = ui.get_input()
                else:
                    user_input = ui.get_input()
            else:
                user_input = ui.get_input()
        except (EOFError, KeyboardInterrupt):
            save_memory(memory)
            ui.print_system("Session saved. Goodbye! 👋", "info")
            break

        if not user_input:
            continue

        if m("games") and m("games").is_game_active():
            result = m("games").process_game_input(user_input)
            if result:
                ui.print_aria(result)
                continue

        cmd = user_input.lower().strip()

        if cmd in ["/exit","exit","quit"]:
            save_memory(memory)
            try:
                from automation import close_browser; close_browser()
            except Exception: pass
            if m("focus"):
                try: m("focus").end_focus()
                except Exception: pass
            turns = len([x for x in history if x["role"] == "user"])
            ui.print_aria(f"Session saved. {turns} exchanges. See you! 👋")
            break

        if cmd == "/providers":
            ui.print_aria(router.get_status_table())
            continue

        if cmd == "/reload":
            router.reload_config()
            ui.print_system(f"Reloaded. {router.count_ready()} provider(s) ready.", "info")
            continue

        if cmd == "/status":
            real = get_real_system_status()
            msg = (f"{real}\n"
                   f"Memory entries   : {len(memory)}\n"
                   f"Session messages : {len(history)}\n"
                   f"Providers ready  : {router.count_ready()}/4")
            if m("personalities"): msg += f"\nPersonality      : {m('personalities').get_personality_info()}"
            ui.print_aria(msg)
            continue

        if cmd == "/memory":
            if memory:
                lines = "\n".join(f"{k}: {v}" for k,v in memory.items())
                ui.print_aria(f"Memory ({len(memory)} entries):\n{lines}")
            else:
                ui.print_aria("No memory stored yet.")
            continue

        if cmd == "/clear":
            history.clear()
            ui.print_system("History cleared.", "info")
            continue

        if m("notes"):
            if cmd == "/notes":
                ui.print_aria(m("notes").format_notes(m("notes").get_notes()))
                continue
            if cmd.startswith(("note:","note ")):
                nid = m("notes").add_note(user_input[5:].strip())
                ui.print_aria(f"📝 Note #{nid} saved.")
                continue
            if cmd.startswith("/deletenote "):
                try:
                    nid = int(cmd.split()[-1])
                    ok  = m("notes").delete_note(nid)
                    ui.print_aria(f"{'Deleted' if ok else 'Not found'}: Note #{nid}")
                except ValueError:
                    ui.print_aria("Usage: /deletenote <id>")
                continue

        if m("personalities"):
            if cmd.startswith("/mood ") and cmd not in ("/mood history","/mood insights"):
                mode = cmd[6:].strip()
                if m("personalities").set_mode(mode):
                    ui.print_aria(f"Switched to {m('personalities').get_personality_info()}")
                else:
                    ui.print_aria(f"Unknown mode.\n{m('personalities').list_modes()}")
                continue
            if cmd in ("/moods","/personalities"):
                ui.print_aria(m("personalities").list_modes())
                continue

        if m("mood"):
            if cmd == "/mood history":
                ui.print_aria(m("mood").format_mood_history(m("mood").get_mood_history(7)))
                continue
            if cmd == "/mood insights":
                ui.print_aria(m("mood").get_mood_insights())
                continue

        if m("health") and cmd == "/health":
            ui.print_aria(m("health").get_health_report())
            continue

        if m("clipboard_mgr"):
            if cmd == "/clipboard":
                ui.print_aria(m("clipboard_mgr").format_entries(m("clipboard_mgr").get_recent(10)))
                continue
            if cmd == "/clipboard links":
                ui.print_aria(m("clipboard_mgr").format_entries(m("clipboard_mgr").get_links()[-10:]))
                continue
            if cmd == "/clipboard clear":
                m("clipboard_mgr").clear_history()
                ui.print_aria("Clipboard history cleared.")
                continue

        if m("tracker"):
            if cmd == "/screentime":
                ui.print_aria(m("tracker").get_today_summary())
                continue
            if cmd == "/timeline":
                ui.print_aria(m("tracker").get_timeline())
                continue

        if m("scheduler"):
            if cmd == "/schedules":
                ui.print_aria(m("scheduler").list_schedules())
                continue
            if cmd.startswith("/unschedule "):
                try:
                    sid = int(cmd.split()[-1])
                    ok  = m("scheduler").remove_schedule(sid)
                    ui.print_aria(f"{'Removed' if ok else 'Not found'}: Schedule #{sid}")
                except ValueError:
                    ui.print_aria("Usage: /unschedule <id>")
                continue

        if m("triggers") and cmd == "/triggers":
            ui.print_aria(m("triggers").list_triggers())
            continue

        if m("smart_dj"):
            if cmd.startswith("/music"):
                genre = cmd[7:].strip() or None
                url, _, _ = m("smart_dj").get_music_url(genre=genre)
                ui.print_aria(m("smart_dj").get_recommendation_text(genre))
                try:
                    from automation import execute_action
                    execute_action("open_url", url=url, browser="zen")
                except Exception: pass
                continue
            if cmd == "/genres":
                ui.print_aria(m("smart_dj").list_genres())
                continue

        if m("focus") and cmd.startswith("/focus"):
            sub = cmd[7:].strip() if len(cmd) > 7 else ""
            if sub in ("off","end","stop"):
                _, msg = m("focus").end_focus(); ui.print_aria(msg)
            elif sub == "stats":
                ui.print_aria(m("focus").get_stats())
            elif sub in ("sites","list"):
                ui.print_aria(m("focus").list_blocked())
            elif sub.startswith("add "):
                site = sub[4:].strip()
                ok = m("focus").add_blocked_site(site)
                ui.print_aria(f"{'Added' if ok else 'Already listed'}: {site}")
            elif sub.startswith("remove "):
                site = sub[7:].strip()
                ok = m("focus").remove_blocked_site(site)
                ui.print_aria(f"{'Removed' if ok else 'Not in list'}: {site}")
            else:
                minutes = 60
                match = re.search(r'(\d+)', sub)
                if match:
                    minutes = int(match.group(1))
                    if "hour" in sub: minutes *= 60
                ok, msg = m("focus").start_focus(minutes)
                ui.print_aria(msg)
                if ok and m("sounds"):
                    try: m("sounds").focus_start()
                    except Exception: pass
            continue

        if m("tiler"):
            if cmd == "/windows":
                ui.print_aria(m("tiler").list_windows())
                continue
            if cmd == "/tile":
                ui.print_aria(m("tiler").tile_all())
                continue
            tile_result = m("tiler").parse_tile_command(user_input)
            if tile_result:
                ui.print_aria(tile_result)
                continue

        if m("games"):
            if cmd.startswith("/play"):
                game_name = cmd[6:].strip() if len(cmd) > 6 else ""
                ui.print_aria(m("games").start_game(game_name))
                continue
            if cmd == "/games":
                ui.print_aria(m("games").list_games())
                continue

        if m("sounds"):
            if cmd == "/sounds off":
                m("sounds").set_enabled(False)
                ui.print_aria("Sounds off.")
                continue
            if cmd == "/sounds on":
                m("sounds").set_enabled(True)
                ui.print_aria("Sounds on.")
                continue

        if m("habits") and cmd == "/habits":
            ui.print_aria(m("habits").get_habit_stats())
            continue

        if cmd.startswith("/correct ") and learner:
            correct_text = user_input[9:].strip()
            if correct_text:
                ok, msg = learner.log_correction(correct_text)
                if ok:
                    stats = learner.get_stats_text()
                    ui.print_aria(f"Logged. I won\'t repeat that mistake.\n\n{stats}")
                else:
                    ui.print_aria(f"Already logged: {msg}")
            else:
                ui.print_aria("Usage: /correct <the right answer>\nExample: /correct YouTube is at youtube.com not youtube.org")
            continue

        if cmd == "/train" and learner:
            count = learner.get_correction_count()
            method = learner.get_best_train_method()
            if count < 5 and method == "ollama":
                ui.print_aria(f"Need at least 5 corrections to train. Have {count} so far.\nAfter any wrong answer type: /correct <right answer>")
            elif method == "none":
                ui.print_aria(learner.get_stats_text())
            else:
                ui.print_system(f"Starting training via {method}...", "info")
                def _do_train():
                    ok, msg = learner.auto_train(
                        status_cb=lambda s: ui.print_system(s, "info"),
                        method=method
                    )
                    ui.print_aria(msg)
                    if ok:
                        router.reload_config()
                threading.Thread(target=_do_train, daemon=True).start()
            continue

        if cmd == "/learning" and learner:
            ui.print_aria(learner.get_stats_text())
            continue

        if cmd == "/voice" and voice_mod:
            if not voice_mod.is_available():
                ui.print_aria("Voice not installed. Run: pip install faster-whisper pyaudio")
            else:
                voice_mode = not voice_mode
                ui.print_aria(f"Voice mode {'ON 🎤 — press Enter to speak' if voice_mode else 'OFF'}")
            continue

        if cmd.startswith("/run ") and sandbox_mod:
            script_name = user_input[5:].strip()
            result = sandbox_mod.run_saved_script(script_name)
            ui.print_aria(sandbox_mod.format_result(result))
            continue

        if cmd == "/scripts" and sandbox_mod:
            ui.print_aria(sandbox_mod.list_scripts())
            continue

        if cmd == "/briefing" and briefing_mod:
            brief = briefing_mod.get_briefing(force=True)
            ui.print_aria(brief or "No briefing available.")
            continue

        if routines_mod:
            action, name, steps = routines_mod.parse_routine_command(user_input)
            if action == "list":
                ui.print_aria(routines_mod.list_routines())
                continue
            if action == "save" and name and steps:
                routines_mod.save_routine(name, steps)
                ui.print_aria(f"Routine '{name}' saved with {len(steps)} steps!")
                continue
            if action == "run" and name:
                def _exec_step(step):
                    parse_and_execute_actions(step, ui)
                ok, msg = routines_mod.run_routine(name, action_executor=_exec_step)
                ui.print_aria(msg if ok else msg)
                continue
            if action == "delete" and name:
                ok = routines_mod.delete_routine(name)
                ui.print_aria(f"Routine '{name}' {'deleted' if ok else 'not found'}.")
                continue

        if workspace_mod:
            ws_action, ws_name = workspace_mod.parse_workspace_command(user_input)
            if ws_action == "list":
                ui.print_aria(workspace_mod.list_workspaces())
                continue
            if ws_action == "switch" and ws_name:
                actions, err = workspace_mod.get_workspace_actions(ws_name)
                if err:
                    ui.print_aria(err)
                else:
                    ui.print_system(f"Switching to {ws_name} workspace...", "info")
                    for act in actions:
                        parse_and_execute_actions(act, ui)
                        time.sleep(0.8)
                    ui.print_aria(f"{ws_name.title()} workspace ready!")
                continue

        if screenreader_mod and vision_mod and screenreader_mod.is_screen_request(user_input):
            ui.print_system("Reading your screen...", "info")
            reply = screenreader_mod.read_screen(vision_mod, _cfg, user_input)
            ui.print_aria(reply)
            if memsearch_mod:
                try: memsearch_mod.store_conversation(user_input, reply)
                except Exception: pass
            continue

        if docsearch_mod:
            if cmd.startswith("/docs add "):
                folder_path = user_input[10:].strip()
                ok, msg = docsearch_mod.add_folder(folder_path)
                ui.print_aria(msg)
                continue

            if cmd.startswith("/docs remove "):
                folder_path = user_input[13:].strip()
                ok = docsearch_mod.remove_folder(folder_path)
                ui.print_aria(f"Removed: {folder_path}" if ok else "Folder not found in list.")
                continue

            if cmd in ("/docs list", "/docs folders", "/docs"):
                ui.print_aria(docsearch_mod.list_folders())
                continue

            if cmd in ("/docs index", "/docs build", "/docs reindex"):
                ui.print_system("Indexing your documents... this may take a minute.", "info")
                def _do_index():
                    count, msg = docsearch_mod.build_index(
                        status_cb=lambda s: ui.print_system(s[:60], "info")
                    )
                    ui.print_aria(msg + "\nNow you can ask questions about your documents!")
                threading.Thread(target=_do_index, daemon=True).start()
                continue

            if cmd == "/docs stats":
                ui.print_aria(docsearch_mod.get_index_stats())
                continue

            if cmd.startswith("/docs search "):
                query = user_input[13:].strip()
                results, err = docsearch_mod.search(query)
                if err:
                    ui.print_aria(err)
                else:
                    ui.print_aria(docsearch_mod.format_search_results(results, query))
                continue

        if any(cmd.startswith(p) for p in ["use ", "set browser ", "default browser "]):
            browser_name = re.sub(r'^(use|set browser|default browser)\s+', '', cmd).strip()
            try:
                from automation import set_browser
                ok, path = set_browser(browser_name)
                if ok:
                    ui.print_aria(f"Got it! I'll use {browser_name} for everything from now on.")
                else:
                    ui.print_aria(f"Couldn't find {browser_name} on your PC. Is it installed?")
            except Exception as e:
                ui.print_aria(f"Couldn't set browser: {e}")
            continue

        if researcher_mod:
            if cmd.startswith("/research ") or cmd.startswith("research "):
                query = re.sub(r"^/?(research)\s+", "", user_input, flags=re.IGNORECASE).strip()
                mode  = researcher_mod.detect_research_mode(query)
                ui.print_system(f"Starting deep research [{mode} mode]...", "info")
                def _do_research(q=query, m=mode):
                    try:
                        package = researcher_mod.deep_research(
                            q, mode=m,
                            status_cb=lambda s: ui.print_system(s[:70], "info")
                        )
                        prompt = researcher_mod.build_research_prompt(package)
                        ctx = [{"role": "user", "content": prompt}]
                        ui.print_aria_header()
                        reply = router.stream_response_live(ctx, token_cb=ui.stream_token)
                        ui.print_aria_footer()
                        if reply:
                            path = researcher_mod.save_report(q, reply)
                            ui.print_system(f"Report saved: {path}", "success")
                            history.append({"role": "user",      "content": user_input})
                            history.append({"role": "assistant", "content": reply})
                            if lifelog_mod:
                                lifelog_mod.log_event("research", f"Researched: {q}")
                    except Exception as e:
                        ui.print_system(f"Research error: {e}", "error")
                threading.Thread(target=_do_research, daemon=True).start()
                continue

            if cmd == "/reports":
                ui.print_aria(researcher_mod.list_reports())
                continue

        if kg_mod and cmd.startswith("/connect "):
            parts = user_input[9:].split(" and ")
            if len(parts) == 2:
                connections = kg_mod.find_connections(parts[0].strip(), parts[1].strip())
                ui.print_aria(kg_mod.format_connections(parts[0], parts[1], connections))
            continue

        if kg_mod and cmd == "/knowledge":
            ui.print_aria(kg_mod.get_stats())
            continue

        if lifelog_mod:
            if cmd in ("/log today", "/today"):
                ui.print_aria(lifelog_mod.generate_daily_summary())
                continue
            if cmd in ("/log week", "/week"):
                ui.print_aria(lifelog_mod.generate_weekly_summary())
                continue

        if examcoach_mod:
            if cmd.startswith("/syllabus "):
                rest     = user_input[10:].strip()
                parts    = rest.split(":", 1)
                subject  = parts[0].strip()
                topics   = [t.strip() for t in parts[1].split(",") if t.strip()] if len(parts) > 1 else []
                if topics:
                    msg = examcoach_mod.set_syllabus(subject, topics)
                    ui.print_aria(msg + "\nNow say: quiz me on " + subject)
                else:
                    ui.print_aria("Format: /syllabus <subject>: topic1, topic2, topic3")
                continue
            if cmd in ("/revision", "/revise", "/weakpoints"):
                ui.print_aria(examcoach_mod.get_revision_sheet())
                continue
            if cmd == "/examstats":
                ui.print_aria(examcoach_mod.get_stats())
                continue

        if vstyle_mod:
            if cmd.startswith("/style learn "):
                path = user_input[13:].strip()
                ok, msg = vstyle_mod.learn_from_file(path)
                ui.print_aria(msg)
                continue
            if cmd == "/style stats":
                ui.print_aria(vstyle_mod.get_stats())
                continue
            if "learn my writing style" in cmd or "learn my style" in cmd:
                try:
                    import pyperclip
                    text = pyperclip.paste()
                    if len(text) > 100:
                        ok, msg = vstyle_mod.learn_from_text(text, "clipboard")
                        ui.print_aria(msg)
                    else:
                        ui.print_aria("Paste some of your writing to clipboard first, then say this again.")
                except Exception:
                    ui.print_aria("Could not read clipboard.")
                continue

        if tmood_mod and cmd == "/mood typing":
            ui.print_aria(tmood_mod.get_mood_history())
            continue

        if cmd == "/help":
            help_text = (
                "Commands\n"
                "════════\n"
                "Core        /providers  /reload  /status  /memory  /clear  /exit\n"
                "Personality /mood <mode>  /moods\n"
                "            savage  homie  teacher  motivator  pirate  yoda  coder  therapist\n"
                "Notes       note: <text>  /notes  /deletenote #\n"
                "Mood        /mood history  /mood insights\n"
                "Health      /health\n"
                "Clipboard   /clipboard  /clipboard links  /clipboard clear\n"
                "Time        /screentime  /timeline\n"
                "Scheduler   /schedules  /unschedule #\n"
                "Triggers    /triggers\n"
                "Music       /music [mood]  /genres\n"
                "Focus       /focus [min]  /focus off  /focus stats\n"
                "Windows     /windows  /tile\n"
                "Games       /play trivia  /play riddles  /play wordchain  /games\n"
                "Sounds      /sounds on/off\n"
                "Habits      /habits\n\n"
                "Or just talk — ARIA will do it."
            )
            ui.print_aria(help_text)
            continue

        if setup_wizard:
            try:
                from providers import load_config as _lc
                _cur_cfg = _lc()
                changed, change_msg = setup_wizard.handle_settings_change(user_input, _cur_cfg)
                if changed:
                    user_ctx = setup_wizard.get_user_context()
                    router.system_prompt = (
                        f"[USER PROFILE]:\n{user_ctx}\n\n" +
                        re.sub(r'\[USER PROFILE\][^\[]*', '', router.system_prompt, flags=re.DOTALL)
                    )
                    ui.print_aria(change_msg)
                    continue
                shortcuts = _cur_cfg.get("custom_shortcuts", {})
                for phrase, action in shortcuts.items():
                    if phrase in user_input.lower():
                        ui.print_system(f"Running shortcut: {phrase}", "info")
                        parse_and_execute_actions(action, ui)
                        ui.print_aria(f"Done — ran your '{phrase}' shortcut!")
                        history.append({"role":"user","content":user_input})
                        history.append({"role":"assistant","content":f"Ran shortcut: {action}"})
                        break
            except Exception:
                pass

        if eggs_mod:
            try:
                if eggs_mod.check_easter_egg(user_input):
                    continue
            except Exception:
                pass

        if updater_mod:
            if cmd in ("/update", "update aria", "check for updates"):
                ui.print_system("Checking for updates...", "info")
                has_update, version, msg = updater_mod.check_for_updates()
                if has_update:
                    ui.print_aria("New version available: v" + str(version) + "\n" + str(msg) + "\n\nType /update confirm to install.")
                elif has_update is False:
                    ui.print_aria(msg)
                else:
                    ui.print_aria(msg)
                continue
            if cmd == "/update confirm":
                def _do_update():
                    ok, msg = updater_mod.update_aria(
                        status_cb=lambda s: ui.print_system(s[:70], "info")
                    )
                    ui.print_aria(msg)
                threading.Thread(target=_do_update, daemon=True).start()
                continue
            if cmd == "/rollback":
                ok, msg = updater_mod.rollback(
                    status_cb=lambda s: ui.print_system(s, "info")
                )
                ui.print_aria(msg)
                continue
            if cmd == "/version":
                ui.print_aria(updater_mod.get_version_info())
                continue

        if ctx_mod and cmd == "/context":
            ui.print_aria(ctx_mod.format_history_stats(history))
            continue

        if sw_mod:
            if cmd in ("/watch start", "/watch on"):
                ok, msg = sw_mod.start(vision_mod=vision_mod, config=_cfg, interval=45)
                ui.print_aria(msg)
                continue
            if cmd in ("/watch stop", "/watch off"):
                ok, msg = sw_mod.stop()
                ui.print_aria(msg)
                continue
            if cmd == "/watch status":
                ui.print_aria(sw_mod.get_status())
                continue
            if cmd in ("/watch now", "read my screen", "whats on my screen"):
                if vision_mod:
                    ui.print_system("Reading screen...", "info")
                    result = sw_mod.read_screen_now(vision_mod, _cfg)
                    ui.print_aria(result)
                else:
                    ui.print_aria("Vision not available — need Gemini or Groq vision key.")
                continue

        if chain_mod:
            if cmd == "/chains":
                ui.print_aria(chain_mod.list_chains())
                continue
            if cmd == "/chain examples":
                ui.print_aria(chain_mod.get_examples())
                continue
            if cmd.startswith("/chain save "):
                rest  = user_input[12:].strip()
                parts = rest.split("|", 1)
                if len(parts) == 2:
                    name, steps_text = parts[0].strip(), parts[1].strip()
                    chain_mod.save_chain(name, steps_text)
                    ui.print_aria("Chain saved: " + name)
                else:
                    ui.print_aria("Format: /chain save <name> | step1 then step2 then step3")
                continue
            if chain_mod.is_chain_request(user_input) and not user_input.startswith("/"):
                steps = chain_mod.parse_chain(user_input)
                if len(steps) >= 2:
                    preview = chain_mod.format_chain_preview(steps)
                    ui.print_aria(preview + "\n\nRunning chain...")
                    def _make_executor():
                        def _exec(action_text):
                            parse_and_execute_actions(action_text, ui)
                            history_temp = [{"role":"user","content":action_text}]
                            router.stream_response_silent(history_temp)
                        return _exec
                    chain_mod.run_chain_async(
                        steps,
                        action_executor=_make_executor(),
                        status_cb=lambda s: ui.print_system(s[:60], "info")
                    )
                    history.append({"role":"user","content":user_input})
                    history.append({"role":"assistant","content":preview + "\nChain started."})
                    continue

        if m("triggers"):
            trigger_data, _ = m("triggers").check_trigger(user_input)
            if trigger_data:
                ui.print_system(f"⚡ {trigger_data.get('emoji','')} {trigger_data['name']}", "action")
                m("triggers").execute_trigger(trigger_data)
                ui.print_aria(trigger_data.get("response","Done!"))
                if m("sounds"):
                    try: m("sounds").success()
                    except Exception: pass
                continue

        if negotiator_mod:
            try:
                negotiation = negotiator_mod.check_and_negotiate(user_input)
                if negotiation:
                    ui.print_system(f"ARIA: {negotiation}", "warn")
            except Exception: pass

        if guard_mod:
            try:
                is_danger, warning = guard_mod.is_dangerous_request(user_input)
                if is_danger and warning:
                    confirm = ui.get_input()
                    if confirm.lower() not in ["yes","y","confirm","sure","ok","yeah"]:
                        ui.print_aria("Cancelled. Good call.")
                        continue
            except Exception: pass

        if tmood_mod:
            try: tmood_mod.record_input(user_input, 5.0)
            except Exception: pass

        if m("mood"):
            try:
                rage_level, rage_msg = m("mood").detect_rage(user_input)
                if rage_level >= 2:
                    ui.print_system(rage_msg, "warn")
            except Exception: pass
            try:
                detected = m("mood").detect_mood(user_input)
                if detected: m("mood").log_mood(detected, user_input[:100])
            except Exception: pass

        if m("habits"):
            try: m("habits").log_action(user_input[:100])
            except Exception: pass

        image_path = None
        if vision_mod and vision_mod.is_image_request(user_input):
            image_path = vision_mod.extract_image_path(user_input)
            if not image_path and vision_mod.wants_latest_image(user_input):
                image_path = vision_mod.find_latest_image()
                if image_path:
                    ui.print_system(f"Using latest image: {os.path.basename(image_path)}", "info")
            if not image_path and vision_mod.is_image_request(user_input):
                image_path = vision_mod.find_latest_image()
                if image_path:
                    ui.print_system(f"Found: {os.path.basename(image_path)}", "info")

        if image_path and vision_mod and os.path.exists(image_path):
            stop_event = threading.Event()
            dots_thread = threading.Thread(target=ui.thinking_dots, args=(stop_event,), daemon=True)
            dots_thread.start()
            time.sleep(0.1)
            vision_reply, provider_used = vision_mod.analyze_image(user_input, image_path, _cfg)
            stop_event.set()
            dots_thread.join(timeout=1.0)
            if vision_reply:
                ui.print_aria(vision_reply)
                if learner:
                    try: learner.set_last_exchange(user_input, vision_reply)
                    except Exception: pass
                history.append({"role": "user",      "content": user_input})
                history.append({"role": "assistant",  "content": vision_reply})
                history = trim_history(history)
            else:
                ui.print_aria(f"Couldn't analyze that image. Try: analyze C:\\Users\\vinee\\pic.jpg")
            continue

        if ctx_mod:
            history = ctx_mod.smart_trim(history)
        else:
            history = trim_history(history)
        if ctx_mod:
            ctx_mod.extract_and_pin(user_input, history)
        history.append({"role": "user", "content": user_input})

        extra = ""
        if memory:
            extra += f"\n[Memory]: {json.dumps(memory)}"
        if m("notes"):
            try: extra += m("notes").get_notes_context()
            except Exception: pass
        if learner:
            try:
                correction_ctx = learner.get_correction_context(user_input)
                if correction_ctx:
                    extra += correction_ctx
            except Exception: pass

        if memsearch_mod:
            try:
                mem_ctx = memsearch_mod.get_memory_context(user_input)
                if mem_ctx:
                    extra += mem_ctx
            except Exception: pass

        if kg_mod:
            try:
                kg_ctx = kg_mod.get_knowledge_context(user_input)
                if kg_ctx:
                    extra += kg_ctx
            except Exception: pass

        if tmood_mod:
            try:
                mood_ctx = tmood_mod.get_context_injection()
                if mood_ctx:
                    extra += mood_ctx
            except Exception: pass

        if vstyle_mod and any(w in user_input.lower() for w in ["write","draft","compose","email","essay","message"]):
            try:
                style_ctx = vstyle_mod.get_style_prompt()
                if style_ctx:
                    extra += style_ctx
            except Exception: pass

        if examcoach_mod and examcoach_mod.is_exam_request(user_input):
            try:
                quiz_prompt, quiz_err = examcoach_mod.build_quiz_prompt()
                if quiz_prompt:
                    extra += f"\n{quiz_prompt}"
            except Exception: pass

        if researcher_mod and researcher_mod.is_research_request(user_input):
            try:
                mode = researcher_mod.detect_research_mode(user_input)
                query = re.sub(r"(?:research|deep dive|tell me everything about|full report on|give me a report on)\s+", "", user_input, flags=re.IGNORECASE).strip()
                if len(query) > 5:
                    package = researcher_mod.deep_research(query, mode=mode,
                              status_cb=lambda s: ui.print_system(s[:60], "info"))
                    extra += "\n" + researcher_mod.build_research_prompt(package)
            except Exception: pass

        if websearch_mod and websearch_mod.has_internet():
            try:
                if websearch_mod.is_url(user_input):
                    url = websearch_mod.extract_url(user_input)
                    page = websearch_mod.fetch_and_read(url)
                    if page:
                        extra += f"\n[WEB PAGE — {url}]:\n{page[:4000]}"
                        ui.print_system("Reading page...", "info")
                elif websearch_mod.is_search_request(user_input):
                    web_results = websearch_mod.search_and_summarise(user_input, max_results=5)
                    if web_results:
                        extra += (
                            f"\n[WEB SEARCH RESULTS — use these as your primary source, "
                            f"do not answer from memory alone]:\n{web_results}"
                        )
                        ui.print_system("Web search done", "info")
            except Exception: pass

        if filereader_mod:
            fp = filereader_mod.extract_path_from_text(user_input)
            if fp and os.path.exists(fp):
                try:
                    file_content, file_err = filereader_mod.read_file(fp)
                    if file_content:
                        prompt = filereader_mod.get_file_summary_prompt(file_content, user_input, fp)
                        extra += f"\n{prompt}"
                    elif file_err:
                        ui.print_system(f"File read error: {file_err}", "error")
                except Exception: pass

        if aif:
            intent, param = aif.detect_ai_intent(user_input)
            if intent == "task":
                task_action, task_val, task_priority = aif.parse_task_command(user_input)
                if task_action == "add" and task_val:
                    tid = aif.add_task(task_val, task_priority or "medium")
                    ui.print_aria("Task added! [" + str(tid) + "] " + str(task_val) + "\n\n" + aif.list_tasks())
                elif task_action == "done" and task_val:
                    aif.complete_task(task_val)
                    ui.print_aria("Marked done!\n\n" + aif.list_tasks())
                elif task_action == "delete" and task_val:
                    aif.delete_task(task_val)
                    ui.print_aria("Task deleted.\n\n" + aif.list_tasks())
                elif task_action == "list":
                    ui.print_aria(aif.list_tasks())
                continue

        if docsearch_mod and docsearch_mod.is_doc_search_request(user_input):
            try:
                doc_context, doc_results = docsearch_mod.build_context_for_query(user_input)
                if doc_context:
                    extra += f"\n{doc_context}"
                    if doc_results:
                        names = [r["name"] for r in doc_results]
                        ui.print_system(f"Searching: {', '.join(names[:3])}", "info")
            except Exception: pass

        if aif:
            try:
                intent, param = aif.detect_ai_intent(user_input)
                if intent == "summarise":
                    clip = user_input
                    try:
                        import pyperclip
                        clip_content = pyperclip.paste()
                        if len(clip_content) > 100:
                            extra += "\n" + aif.summarise_text(clip_content, param or "brief")
                    except Exception:
                        extra += "\n" + aif.summarise_text(user_input, param or "brief")
                elif intent == "explain":
                    topic = re.sub(r"(?:explain|what is|what are|how does|how do|teach me)\s*", "", user_input, flags=re.IGNORECASE).strip()
                    extra += "\n" + aif.build_explain_prompt(topic, param or "normal")
                elif intent == "code_review":
                    try:
                        import pyperclip
                        code = pyperclip.paste()
                        if len(code) > 20:
                            extra += "\n" + aif.build_code_review_prompt(code)
                    except Exception: pass
                elif intent == "writing":
                    extra += "\n" + aif.build_writing_prompt(user_input, param or "professional")
                elif intent == "debate":
                    topic = re.sub(r"(?:debate|argue|both sides|pros and cons of)\s*", "", user_input, flags=re.IGNORECASE).strip()
                    extra += "\n" + aif.build_debate_prompt(topic)
                elif intent == "compare":
                    mm = re.search(r"(.+?)\s+(?:vs|versus|compared? to)\s+(.+)", user_input, re.IGNORECASE)
                    if mm:
                        extra += "\n" + aif.build_compare_prompt(mm.group(1).strip(), mm.group(2).strip())
                elif intent == "sentiment":
                    try:
                        import pyperclip
                        text_to_analyse = pyperclip.paste() if len(pyperclip.paste()) > 50 else user_input
                    except Exception:
                        text_to_analyse = user_input
                    extra += "\n" + aif.build_sentiment_prompt(text_to_analyse)
                elif intent == "translate":
                    text_to_translate = re.sub(r"translate\s*", "", user_input, flags=re.IGNORECASE).strip()
                    text_to_translate = re.sub(r"\s+(?:to|in)\s+\w+\s*$", "", text_to_translate, flags=re.IGNORECASE).strip()
                    extra += "\n" + aif.build_translate_prompt(text_to_translate, param or "english")
                elif intent == "quiz":
                    topic = re.sub(r"(?:quiz|test me|questions about)\s*(?:on|about)?\s*", "", user_input, flags=re.IGNORECASE).strip()
                    num = 5
                    mm2 = re.search(r"(\d+)\s+questions?", user_input)
                    if mm2: num = int(mm2.group(1))
                    extra += "\n" + aif.build_quiz_prompt(topic, num)
                elif intent == "ideas":
                    topic = re.sub(r"(?:ideas? for|brainstorm|suggest)\s*", "", user_input, flags=re.IGNORECASE).strip()
                    extra += "\n" + aif.build_ideas_prompt(topic)
                elif intent == "roast":
                    subject = re.sub(r"roast\s*", "", user_input, flags=re.IGNORECASE).strip()
                    extra += "\n" + aif.build_roast_prompt(subject)
            except Exception: pass

        hw_kw = ["lag","slow","hardware","spec","cpu","ram","gpu","disk","storage",
                 "battery","process","heat","hot","crash","freeze","memory",
                 "performance","speed","diagnos","check","system","temp","overheat",
                 "fan","noise","throttl","hang","stuck"]
        # Only inject system data when user is asking about THEIR ACTUAL LAPTOP
        # Not when asking about CS/tech concepts in general
        laptop_hw_kw = ["my laptop", "my pc", "my computer", "my cpu", "my ram",
                        "my disk", "my battery", "my storage", "my performance",
                        "laptop slow", "pc slow", "computer slow", "why is my",
                        "how much ram", "how much disk", "check my", "my system",
                        "diagnose", "troubleshoot", "fix my"]
        is_laptop_question = any(k in user_input.lower() for k in laptop_hw_kw)
        if is_laptop_question:
            try:
                import psutil
                cpu  = psutil.cpu_percent(interval=0.5)
                ram  = psutil.virtual_memory()
                disk = psutil.disk_usage("C:\\")
                bat  = psutil.sensors_battery()
                real_data = (
                    f"\n[REAL SYSTEM DATA — use these exact numbers]:\n"
                    f"CPU: {cpu}%\n"
                    f"RAM: {ram.used/1024**3:.1f}/{ram.total/1024**3:.1f}GB ({ram.percent}% used)\n"
                    f"Disk: {disk.used/1024**3:.0f}/{disk.total/1024**3:.0f}GB\n"
                    f"Battery: {int(bat.percent) if bat else 'N/A'}%"
                    f"{' (charging)' if bat and bat.power_plugged else ''}\n"
                )
                extra += real_data
            except Exception: pass

        original_prompt = router.system_prompt
        if m("personalities") and m("personalities").get_mode() != "default":
            pp = m("personalities").get_personality_prompt()
            router.system_prompt = f"[PERSONALITY]: {pp}\n\n{original_prompt}"

        context = [dict(m) for m in history]
        if extra and context and context[-1]["role"] == "user":
            context[-1] = {"role": "user", "content": context[-1]["content"] + extra}

        ui.print_aria_header()
        reply = router.stream_response_live(context, token_cb=ui.stream_token)
        ui.print_aria_footer()

        router.system_prompt = original_prompt

        if reply:
            history[-1] = {"role":"user","content":user_input}
            history.append({"role":"assistant","content":reply})
            if learner:
                try: learner.set_last_exchange(user_input, reply)
                except Exception: pass
            if memsearch_mod:
                try:
                    memsearch_mod.store_conversation(user_input, reply)
                    facts = memsearch_mod.extract_facts_from_conversation(user_input, reply)
                    for fact, cat in facts:
                        memsearch_mod.store_fact(fact, cat)
                except Exception: pass
            if kg_mod:
                try: kg_mod.add_knowledge(user_input + " " + reply[:500], source="conversation")
                except Exception: pass
            if lifelog_mod:
                try: lifelog_mod.log_conversation(user_input, reply[:300])
                except Exception: pass
            if tmood_mod:
                try: tmood_mod.save_mood_log()
                except Exception: pass

            clean_reply = re.sub(r'\[ACTION:\s*none[^\]]*\]', '', reply, flags=re.IGNORECASE).strip()

            if docsearch_mod and any(
                p in user_input.lower() for p in
                ["open 1", "open 2", "open 3", "open file", "open it", "yes open", "open that"]
            ):
                results, _ = docsearch_mod.search(
                    " ".join(history[-4:-1][0]["content"].split()[:8])
                    if len(history) >= 4 else user_input,
                    top_n=3
                )
                idx = None
                for num, label in [("1","1"),("2","2"),("3","3")]:
                    if f"open {num}" in user_input.lower():
                        idx = int(num) - 1
                        break
                if idx is None:
                    idx = 0
                if results and idx < len(results):
                    fpath = results[idx]["path"]
                    try:
                        import subprocess as _sp
                        _sp.Popen(["explorer", fpath])
                        ui.print_system(f"Opening: {results[idx]['name']}", "success")
                    except Exception as open_err:
                        ui.print_system(f"Could not open: {open_err}", "error")

            had_actions = parse_and_execute_actions(reply, ui)
            if had_actions:
                if m("sounds"):
                    try: m("sounds").success()
                    except Exception: pass

            if len([x for x in history if x["role"] == "user"]) % 5 == 0:
                save_memory(memory)
        else:
            history.pop()
            ui.print_system("No reply. Type /providers to check status.", "error")


if __name__ == "__main__":
    run_aria()
