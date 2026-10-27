import json
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aria
import automation
import voice


def test_voice_sanitize_removes_control_chars():
    text = "hello\n\x00world"
    safe = voice._sanitize_speech_text(text)
    assert "\x00" not in safe
    assert "hello" in safe


def test_destructive_action_requires_confirmation():
    with patch.object(automation, "shutdown_pc", return_value=True) as fake:
        assert automation.execute_action("shutdown", confirm=False) is False
        fake.assert_not_called()

    with patch.object(automation, "shutdown_pc", return_value=True) as fake:
        assert automation.execute_action("shutdown", confirm=True) is True
        fake.assert_called_once()


def test_memory_round_trip_uses_temp_file(monkeypatch):
    temp_dir = os.path.join(os.getcwd(), "tmp_test_memory")
    os.makedirs(temp_dir, exist_ok=True)
    temp_file = os.path.join(temp_dir, "aria_memory.json")
    monkeypatch.setattr(aria, "MEMORY_FILE", temp_file)

    data = {"name": "ARIA", "session": 1}
    aria.save_memory(data)
    loaded = aria.load_memory()
    assert loaded == data

    if os.path.exists(temp_file):
        os.remove(temp_file)
    if os.path.exists(temp_dir):
        os.rmdir(temp_dir)


def test_missing_config_returns_empty_dict(monkeypatch):
    temp_dir = os.path.join(os.getcwd(), "tmp_cfg_test")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, "config.json")
    monkeypatch.setattr("providers.CONFIG_FILE", temp_path)

    import providers
    assert providers.load_config() == {}

    if os.path.exists(temp_dir):
        for name in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, name))
        os.rmdir(temp_dir)


def test_action_parser_asks_for_confirmation(monkeypatch):
    class FakeUI:
        def __init__(self):
            self.prompts = []

        def get_input(self, message):
            self.prompts.append(message)
            return "yes"

        def print_system(self, *args, **kwargs):
            pass

    fake_ui = FakeUI()
    calls = []

    def fake_execute(action_name, **kwargs):
        calls.append((action_name, kwargs))
        return True

    monkeypatch.setattr("automation.execute_action", fake_execute)
    text = '[ACTION: shutdown(delay="0")]'
    result = aria.parse_and_execute_actions(text, fake_ui)
    assert result is True
    assert any(call[0] == "shutdown" for call in calls)
    assert calls[0][1]["confirm"] is True

    del fake_ui


if __name__ == "__main__":
    test_voice_sanitize_removes_control_chars()
    test_destructive_action_requires_confirmation()
    test_memory_round_trip_uses_temp_file({})
    test_missing_config_returns_empty_dict({})
    test_action_parser_asks_for_confirmation({})
    print("ok")
