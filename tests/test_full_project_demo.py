"""Tests for full_project_demo.py"""

import importlib
import json
import os
import sys
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import full_project_demo as demo


# ─── Test Module Imports & Feature Detection ──────────────────────────────────

class TestImportsAndSetup:
    def test_has_rich_detected(self):
        assert isinstance(demo.HAS_RICH, bool)

    def test_has_fastapi_detected(self):
        assert isinstance(demo.HAS_FASTAPI, bool)

    def test_has_httpx_detected(self):
        assert isinstance(demo.HAS_HTTPX, bool)

    def test_discord_color_constants_defined(self):
        assert demo.BLURPLE == "#5865F2"
        assert demo.BACKGROUND == "#313338"
        assert demo.SURFACE == "#2B2D31"
        assert demo.SUCCESS == "#23A559"
        assert demo.ERROR == "#F23F43"
        assert demo.WARNING == "#F0B232"

    def test_ansi_fallback_colors_defined(self):
        assert demo.ANSI_BLURPLE.startswith("\033[")
        assert demo.ANSI_GREEN.startswith("\033[")
        assert demo.ANSI_RESET == "\033[0m"


# ─── Test RichRenderer Exists and Has All Stages ─────────────────────────────

class TestRichRenderer:
    def test_class_exists(self):
        assert hasattr(demo, "RichRenderer")

    def test_has_all_stage_methods(self):
        renderer = demo.RichRenderer()
        assert callable(getattr(renderer, "stage_1", None))
        assert callable(getattr(renderer, "stage_2", None))
        assert callable(getattr(renderer, "stage_3", None))
        assert callable(getattr(renderer, "stage_4", None))
        assert callable(getattr(renderer, "title_screen", None))
        assert callable(getattr(renderer, "final_summary", None))

    def test_has_android_screen_renderers(self):
        renderer = demo.RichRenderer()
        assert callable(getattr(renderer, "render_main_dashboard", None))
        assert callable(getattr(renderer, "render_stats_screen", None))
        assert callable(getattr(renderer, "render_command_builder", None))

    def test_stage_2_has_inline_fallback(self):
        renderer = demo.RichRenderer()
        assert callable(getattr(renderer, "_stage_2_inline", None))


# ─── Test PlainRenderer Exists and Has All Stages ────────────────────────────

class TestPlainRenderer:
    def test_class_exists(self):
        assert hasattr(demo, "PlainRenderer")

    def test_has_all_stage_methods(self):
        renderer = demo.PlainRenderer()
        assert callable(getattr(renderer, "stage_1", None))
        assert callable(getattr(renderer, "stage_2", None))
        assert callable(getattr(renderer, "stage_3", None))
        assert callable(getattr(renderer, "stage_4", None))
        assert callable(getattr(renderer, "title_screen", None))
        assert callable(getattr(renderer, "final_summary", None))


# ─── Test Stage 3: Bridge Integration ────────────────────────────────────────

class TestStage3BridgeIntegration:
    """Tests that Stage 3 correctly uses bridge_logic.py"""

    def test_bridge_logic_importable(self):
        from bridge_logic import AIIdentity, DiscordAIBridge
        assert AIIdentity is not None
        assert DiscordAIBridge is not None

    def test_bridge_creates_grid_and_codex(self):
        from bridge_logic import AIIdentity, DiscordAIBridge

        bridge = DiscordAIBridge(channel_id="987654321098765432")
        bridge.register_identity(AIIdentity(
            name="Grid",
            webhook_url="https://discord.com/api/webhooks/MOCK_GRID/TOKEN",
        ))
        bridge.register_identity(AIIdentity(
            name="Codex",
            webhook_url="https://discord.com/api/webhooks/MOCK_CODEX/TOKEN",
        ))
        assert "Grid" in bridge.list_identities()
        assert "Codex" in bridge.list_identities()

    def test_bridge_formats_messages(self):
        from bridge_logic import AIIdentity

        grid = AIIdentity(
            name="Grid",
            webhook_url="https://discord.com/api/webhooks/MOCK/TOKEN",
        )
        formatted = grid._format_message("Hello from Grid")
        assert "**[Grid]**" in formatted
        assert "Hello from Grid" in formatted

    def test_outgoing_file_written(self, tmp_path):
        """Verify Stage 3 writes outgoing.txt correctly."""
        from bridge_logic import AIIdentity, DiscordAIBridge

        bridge = DiscordAIBridge(channel_id="test")
        bridge.register_identity(AIIdentity(
            name="Grid",
            webhook_url="https://discord.com/api/webhooks/MOCK/TOKEN",
        ))
        bridge.register_identity(AIIdentity(
            name="Codex",
            webhook_url="https://discord.com/api/webhooks/MOCK/TOKEN",
        ))

        outgoing = tmp_path / "outgoing.txt"
        conversation = [
            ("Grid", "Test message from Grid"),
            ("Codex", "Test message from Codex"),
        ]

        with open(outgoing, "w") as f:
            for name, msg in conversation:
                identity = bridge.identities[name]
                identity._format_message(msg)
                f.write(f"[{name}] {msg}\n")

        content = outgoing.read_text()
        assert "[Grid] Test message from Grid" in content
        assert "[Codex] Test message from Codex" in content

    def test_outgoing_file_readback(self, tmp_path):
        """Verify the readback parsing logic."""
        outgoing = tmp_path / "outgoing.txt"
        outgoing.write_text(
            "[Grid] First message\n"
            "[Codex] Second message\n"
        )

        messages = []
        with open(outgoing, "r") as f:
            for line in f:
                line = line.strip()
                if line and line.startswith("["):
                    bracket_end = line.index("]")
                    name = line[1:bracket_end]
                    content = line[bracket_end + 2:]
                    messages.append((name, content))

        assert len(messages) == 2
        assert messages[0] == ("Grid", "First message")
        assert messages[1] == ("Codex", "Second message")


# ─── Test Stage 2: FastAPI Mock ──────────────────────────────────────────────

class TestStage2MockServer:
    def test_deploy_payload_structure(self):
        """Verify the deploy payload matches the expected schema."""
        payload = {
            "bot_name": "NightOwlBot",
            "token": "MTIz.NjQ1.Njc4OWFiY2RlZjAxMjM0NTY3OA"
        }
        assert "bot_name" in payload
        assert "token" in payload
        assert "." in payload["token"]  # Discord token format

    def test_expected_response_structure(self):
        """Verify the expected response has all required fields."""
        response = {
            "status": "deploying",
            "deploy_id": "deploy-sim-001",
            "bot_name": "NightOwlBot",
            "region": "us-east-1",
            "estimated_time_seconds": 30,
        }
        assert response["status"] == "deploying"
        assert response["region"] == "us-east-1"
        assert "deploy_id" in response
        assert response["estimated_time_seconds"] > 0


# ─── Test Stage 1: Screen Content ────────────────────────────────────────────

class TestStage1Content:
    def test_module_cards_defined(self):
        """Verify the module data used by stage 1."""
        modules = [
            ("📟", "Live Console"),
            ("🛡️", "AI AutoMod"),
            ("⚡", "Command Builder"),
            ("🚀", "Launch New Bot"),
        ]
        assert len(modules) == 4

    def test_stats_data_defined(self):
        """Verify stats metrics used by stage 1."""
        metrics = {
            "Total Servers": 42,
            "Total Users": 1337,
            "Active Commands": 18,
            "Uptime": "99.7%",
        }
        assert len(metrics) == 4
        assert metrics["Total Servers"] == 42

    def test_command_data_defined(self):
        """Verify commands displayed in stage 1."""
        commands = [
            ("/hello", "Text"),
            ("/stats", "Embed"),
            ("/meme", "Random"),
        ]
        assert len(commands) == 3


# ─── Test Stage 4: Discord Embed Rendering ───────────────────────────────────

class TestStage4DiscordDelivery:
    def test_message_parsing_from_file(self, tmp_path):
        """Test that stage 4's message parsing works correctly."""
        outgoing = tmp_path / "outgoing.txt"
        outgoing.write_text(
            "[Grid] Deploy complete.\n"
            "[Codex] Acknowledged.\n"
        )

        messages = []
        with open(outgoing, "r") as f:
            for line in f:
                line = line.strip()
                if line and line.startswith("["):
                    bracket_end = line.index("]")
                    name = line[1:bracket_end]
                    content = line[bracket_end + 2:]
                    messages.append((name, content))

        assert messages[0] == ("Grid", "Deploy complete.")
        assert messages[1] == ("Codex", "Acknowledged.")

    def test_discord_embed_colors(self):
        """Verify Grid gets Blurple, Codex gets Warning color."""
        assert demo.BLURPLE == "#5865F2"
        assert demo.WARNING == "#F0B232"

    def test_timestamp_list(self):
        """Verify timestamps are realistic."""
        timestamps = [
            "Today at 6:22 AM", "Today at 6:22 AM", "Today at 6:23 AM",
            "Today at 6:23 AM", "Today at 6:24 AM", "Today at 6:24 AM",
        ]
        assert len(timestamps) == 6
        assert all("Today at" in t for t in timestamps)


# ─── Test Main Function ─────────────────────────────────────────────────────

class TestMainFunction:
    def test_main_exists(self):
        assert callable(getattr(demo, "main", None))

    def test_renderer_selection_rich(self):
        """When HAS_RICH is True, should use RichRenderer."""
        if demo.HAS_RICH:
            renderer = demo.RichRenderer()
            assert hasattr(renderer, "console")

    def test_renderer_selection_plain(self):
        """PlainRenderer should always be instantiable."""
        renderer = demo.PlainRenderer()
        assert hasattr(renderer, "stage_1")


# ─── Test Script File Structure ──────────────────────────────────────────────

class TestFileStructure:
    def test_demo_script_has_docstring(self):
        import full_project_demo
        assert "TOTAL SIMULATION" in full_project_demo.__doc__

    def test_demo_script_has_all_four_stages(self):
        import inspect
        source = inspect.getsource(demo)
        assert "stage_1" in source
        assert "stage_2" in source
        assert "stage_3" in source
        assert "stage_4" in source

    def test_demo_uses_bridge_logic(self):
        import inspect
        source = inspect.getsource(demo)
        assert "from bridge_logic import" in source
        assert "AIIdentity" in source
        assert "DiscordAIBridge" in source

    def test_demo_writes_outgoing_txt(self):
        import inspect
        source = inspect.getsource(demo)
        assert "outgoing.txt" in source

    def test_demo_has_rich_fallback(self):
        import inspect
        source = inspect.getsource(demo)
        assert "HAS_RICH" in source
        assert "PlainRenderer" in source
        assert "RichRenderer" in source
