"""Tests for bridge_logic.py"""

import json
import os
import time
from unittest.mock import MagicMock, patch

import pytest

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bridge_logic import (
    AIIdentity,
    DiscordAIBridge,
    daemon_loop,
    parse_outgoing_lines,
    _truncate_file,
    _truncate_str,
    RICH_AVAILABLE,
)


# ---------------------------------------------------------------------------
# AIIdentity tests
# ---------------------------------------------------------------------------

class TestAIIdentity:
    def test_format_message(self):
        identity = AIIdentity(
            name="Claude",
            webhook_url="https://discord.com/api/webhooks/123/abc",
        )
        result = identity._format_message("Hello world")
        assert result == "**[Claude]**\nHello world"

    def test_build_payload_with_avatar(self):
        identity = AIIdentity(
            name="GPT-4",
            webhook_url="https://discord.com/api/webhooks/123/abc",
            avatar_url="https://example.com/avatar.png",
        )
        payload = identity._build_payload("formatted text")
        assert payload == {
            "content": "formatted text",
            "username": "GPT-4",
            "avatar_url": "https://example.com/avatar.png",
        }

    def test_build_payload_without_avatar(self):
        identity = AIIdentity(
            name="Claude",
            webhook_url="https://discord.com/api/webhooks/123/abc",
        )
        payload = identity._build_payload("formatted text")
        assert "avatar_url" not in payload
        assert payload["username"] == "Claude"

    @patch("bridge_logic.requests.post")
    def test_send_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "msg123"}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        identity = AIIdentity(
            name="Claude",
            webhook_url="https://discord.com/api/webhooks/123/abc",
        )
        result = identity.send("Hello", channel_id="999")

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs[1]["json"]["username"] == "Claude"
        assert "**[Claude]**" in call_kwargs[1]["json"]["content"]
        assert result == {"id": "msg123"}

    @patch("bridge_logic.requests.post")
    def test_send_204_no_content(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        identity = AIIdentity(
            name="Claude",
            webhook_url="https://discord.com/api/webhooks/123/abc",
        )
        result = identity.send("Hello", channel_id="999")
        assert result == {"status": "sent"}


# ---------------------------------------------------------------------------
# DiscordAIBridge tests
# ---------------------------------------------------------------------------

class TestDiscordAIBridge:
    def _make_bridge(self):
        bridge = DiscordAIBridge(channel_id="123456")
        bridge.register_identity(
            AIIdentity(
                name="Claude",
                webhook_url="https://discord.com/api/webhooks/1/a",
            )
        )
        bridge.register_identity(
            AIIdentity(
                name="GPT-4",
                webhook_url="https://discord.com/api/webhooks/2/b",
            )
        )
        return bridge

    def test_register_and_list(self):
        bridge = self._make_bridge()
        names = bridge.list_identities()
        assert "Claude" in names
        assert "GPT-4" in names

    def test_send_unknown_identity_raises(self):
        bridge = self._make_bridge()
        with pytest.raises(KeyError, match="Unknown identity 'Gemini'"):
            bridge.send_message("Gemini", "hi")

    @patch("bridge_logic.requests.post")
    def test_send_message_routes_correctly(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "ok"}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        bridge = self._make_bridge()
        bridge.send_message("Claude", "test message")

        call_url = mock_post.call_args[0][0]
        assert call_url == "https://discord.com/api/webhooks/1/a"

    def test_from_yaml(self, tmp_path):
        cfg = {
            "channel_id": "42",
            "identities": [
                {
                    "name": "TestBot",
                    "webhook_url": "https://discord.com/api/webhooks/x/y",
                    "avatar_url": "https://img.test/bot.png",
                },
            ],
        }
        cfg_path = tmp_path / "config.yaml"
        import yaml
        cfg_path.write_text(yaml.dump(cfg))

        bridge = DiscordAIBridge.from_yaml(str(cfg_path))
        assert bridge.channel_id == "42"
        assert "TestBot" in bridge.list_identities()
        assert bridge.identities["TestBot"].avatar_url == "https://img.test/bot.png"

    def test_from_yaml_missing_optional_fields(self, tmp_path):
        cfg = {
            "identities": [
                {
                    "name": "Minimal",
                    "webhook_url": "https://discord.com/api/webhooks/z/w",
                },
            ],
        }
        cfg_path = tmp_path / "config.yaml"
        import yaml
        cfg_path.write_text(yaml.dump(cfg))

        bridge = DiscordAIBridge.from_yaml(str(cfg_path))
        assert bridge.channel_id == "YOUR_CHANNEL_ID_HERE"
        assert bridge.identities["Minimal"].avatar_url is None


# ---------------------------------------------------------------------------
# parse_outgoing_lines tests
# ---------------------------------------------------------------------------

class TestParseOutgoingLines:
    def test_valid_lines(self):
        lines = [
            "Claude: Hello world\n",
            "GPT-4: How are you?\n",
        ]
        result = parse_outgoing_lines(lines)
        assert result == [("Claude", "Hello world"), ("GPT-4", "How are you?")]

    def test_blank_and_comment_lines_skipped(self):
        lines = [
            "\n",
            "# This is a comment\n",
            "  \n",
            "Claude: Real message\n",
        ]
        result = parse_outgoing_lines(lines)
        assert result == [("Claude", "Real message")]

    def test_malformed_lines_skipped(self):
        lines = [
            "no colon here\n",
            "Claude: valid\n",
        ]
        result = parse_outgoing_lines(lines)
        assert result == [("Claude", "valid")]

    def test_empty_identity_or_message_skipped(self):
        lines = [
            ": no identity\n",
            "NoMsg: \n",
        ]
        result = parse_outgoing_lines(lines)
        assert result == []

    def test_colon_in_message_preserved(self):
        lines = ["Claude: time is 12:30:00\n"]
        result = parse_outgoing_lines(lines)
        assert result == [("Claude", "time is 12:30:00")]

    def test_empty_list(self):
        assert parse_outgoing_lines([]) == []


# ---------------------------------------------------------------------------
# Daemon Mode tests
# ---------------------------------------------------------------------------

class TestDaemonMode:
    @patch("bridge_logic.requests.post")
    def test_daemon_reads_and_truncates(self, mock_post, tmp_path):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "ok"}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        bridge = DiscordAIBridge(channel_id="999")
        bridge.register_identity(
            AIIdentity(name="Grid", webhook_url="https://discord.com/api/webhooks/1/a")
        )

        outfile = str(tmp_path / "outgoing.txt")
        with open(outfile, "w") as f:
            f.write("Grid: Hello from daemon test\n")

        results = daemon_loop(bridge, outfile=outfile, poll_interval=0, _max_iterations=1)

        assert len(results) == 1
        assert results[0]["identity"] == "Grid"
        assert results[0]["status"] == "sent"

        # File should be truncated
        with open(outfile) as f:
            assert f.read() == ""

    def test_daemon_handles_missing_file(self, tmp_path):
        bridge = DiscordAIBridge(channel_id="999")
        bridge.register_identity(
            AIIdentity(name="Grid", webhook_url="https://discord.com/api/webhooks/1/a")
        )

        outfile = str(tmp_path / "does_not_exist.txt")
        results = daemon_loop(bridge, outfile=outfile, poll_interval=0, _max_iterations=1)
        assert results == []

    def test_daemon_handles_empty_file(self, tmp_path):
        bridge = DiscordAIBridge(channel_id="999")
        bridge.register_identity(
            AIIdentity(name="Grid", webhook_url="https://discord.com/api/webhooks/1/a")
        )

        outfile = str(tmp_path / "outgoing.txt")
        with open(outfile, "w") as f:
            f.write("")

        results = daemon_loop(bridge, outfile=outfile, poll_interval=0, _max_iterations=1)
        assert results == []

    @patch("bridge_logic.requests.post")
    def test_daemon_unknown_identity_logged_as_error(self, mock_post, tmp_path):
        bridge = DiscordAIBridge(channel_id="999")
        bridge.register_identity(
            AIIdentity(name="Grid", webhook_url="https://discord.com/api/webhooks/1/a")
        )

        outfile = str(tmp_path / "outgoing.txt")
        with open(outfile, "w") as f:
            f.write("UnknownBot: This should fail\n")

        results = daemon_loop(bridge, outfile=outfile, poll_interval=0, _max_iterations=1)
        assert len(results) == 1
        assert results[0]["status"] == "error"
        assert "UnknownBot" in results[0]["error"]

    @patch("bridge_logic.requests.post")
    def test_daemon_multiple_messages(self, mock_post, tmp_path):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "ok"}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        bridge = DiscordAIBridge(channel_id="999")
        bridge.register_identity(
            AIIdentity(name="Grid", webhook_url="https://discord.com/api/webhooks/1/a")
        )
        bridge.register_identity(
            AIIdentity(name="Codex", webhook_url="https://discord.com/api/webhooks/2/b")
        )

        outfile = str(tmp_path / "outgoing.txt")
        with open(outfile, "w") as f:
            f.write("Grid: First message\nCodex: Second message\n")

        results = daemon_loop(bridge, outfile=outfile, poll_interval=0, _max_iterations=1)
        assert len(results) == 2
        assert results[0]["identity"] == "Grid"
        assert results[1]["identity"] == "Codex"
        assert mock_post.call_count == 2


# ---------------------------------------------------------------------------
# Utility tests
# ---------------------------------------------------------------------------

class TestUtilities:
    def test_truncate_file(self, tmp_path):
        f = str(tmp_path / "test.txt")
        with open(f, "w") as fh:
            fh.write("some content")
        _truncate_file(f)
        with open(f) as fh:
            assert fh.read() == ""

    def test_truncate_str_short(self):
        assert _truncate_str("hello", 10) == "hello"

    def test_truncate_str_exact(self):
        assert _truncate_str("hello", 5) == "hello"

    def test_truncate_str_long(self):
        result = _truncate_str("hello world", 8)
        assert len(result) == 8
        assert result.endswith("\u2026")

    def test_rich_available_is_bool(self):
        assert isinstance(RICH_AVAILABLE, bool)
