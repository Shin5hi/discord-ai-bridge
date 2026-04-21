"""Tests for bridge_logic.py"""

import json
from unittest.mock import MagicMock, patch

import pytest

import sys
sys.path.insert(0, ".")

from bridge_logic import AIIdentity, DiscordAIBridge


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
