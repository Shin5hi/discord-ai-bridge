#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║            TOTAL SIMULATION — The Full Experience               ║
║  Discord Bot Maker (Android) + Discord AI Bridge (Python)       ║
╚══════════════════════════════════════════════════════════════════╝

Run:  python full_project_demo.py

Walks through all four stages of the integrated project:
  Stage 1 — The Android App Experience (visual screen mockups)
  Stage 2 — The Backend Pulse (mock FastAPI deploy flow)
  Stage 3 — AI-to-IA Collaboration (bridge_logic.py in action)
  Stage 4 — Discord Delivery (embed mockup preview)

Requirements:
  pip install requests pyyaml rich fastapi uvicorn httpx
  (rich, fastapi, uvicorn, httpx are optional — graceful fallback)
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import textwrap
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

# ─── Graceful Imports ─────────────────────────────────────────────────────────

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.columns import Columns
    from rich.live import Live
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.style import Style
    from rich.rule import Rule
    from rich.align import Align
    from rich.box import ROUNDED, HEAVY, DOUBLE
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

try:
    import uvicorn
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


# ─── Color Constants (Discord palette) ───────────────────────────────────────

BLURPLE = "#5865F2"
BACKGROUND = "#313338"
SURFACE = "#2B2D31"
INPUT_BG = "#1E1F22"
SUCCESS = "#23A559"
ERROR = "#F23F43"
WARNING = "#F0B232"
TEXT_PRIMARY = "#FFFFFF"
TEXT_SECONDARY = "#B5BAC1"

# ANSI fallback colors
ANSI_BLURPLE = "\033[38;2;88;101;242m"
ANSI_GREEN = "\033[38;2;35;165;89m"
ANSI_RED = "\033[38;2;242;63;67m"
ANSI_YELLOW = "\033[38;2;240;178;50m"
ANSI_CYAN = "\033[36m"
ANSI_BOLD = "\033[1m"
ANSI_DIM = "\033[2m"
ANSI_RESET = "\033[0m"


# ─── Utility ─────────────────────────────────────────────────────────────────

def slow_print(text: str, delay: float = 0.02) -> None:
    """Print character by character for dramatic effect."""
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def pause(seconds: float = 1.0) -> None:
    time.sleep(seconds)


# ═══════════════════════════════════════════════════════════════════════════════
# RICH RENDERER (full experience)
# ═══════════════════════════════════════════════════════════════════════════════

class RichRenderer:
    """Renders all stages using the rich library."""

    def __init__(self) -> None:
        self.console = Console()
        self.blurple_style = Style(color=BLURPLE, bold=True)
        self.success_style = Style(color=SUCCESS)
        self.warning_style = Style(color=WARNING)
        self.error_style = Style(color=ERROR)
        self.dim_style = Style(color=TEXT_SECONDARY)
        self.surface_style = Style(bgcolor=SURFACE)

    # ── Title Screen ──────────────────────────────────────────────────────

    def title_screen(self) -> None:
        title = Text()
        title.append("╔══════════════════════════════════════════════════════════════╗\n", style=self.blurple_style)
        title.append("║  ", style=self.blurple_style)
        title.append("⚡ TOTAL SIMULATION", style=Style(color=BLURPLE, bold=True))
        title.append(" — The Full Experience", style=self.dim_style)
        title.append("          ║\n", style=self.blurple_style)
        title.append("║  ", style=self.blurple_style)
        title.append("Discord Bot Maker", style=Style(color=SUCCESS, bold=True))
        title.append(" (Android) + ", style=self.dim_style)
        title.append("AI Bridge", style=Style(color=WARNING, bold=True))
        title.append(" (Python)  ║\n", style=self.blurple_style)
        title.append("╚══════════════════════════════════════════════════════════════╝", style=self.blurple_style)
        self.console.print()
        self.console.print(Align.center(title))
        self.console.print()

    # ── Stage Banner ──────────────────────────────────────────────────────

    def stage_banner(self, number: int, title: str, subtitle: str) -> None:
        self.console.print()
        self.console.rule(
            f"[bold {BLURPLE}]STAGE {number}[/] │ [bold white]{title}[/]",
            style=BLURPLE,
        )
        self.console.print(f"  [dim]{subtitle}[/]")
        self.console.print()
        pause(0.8)

    # ── Stage 1: Android App Experience ───────────────────────────────────

    def render_main_dashboard(self) -> None:
        """Render the Main Dashboard screen."""
        header = Panel(
            Text.assemble(
                ("Discord Bot Maker", Style(bold=True, color="white")),
                ("\n", None),
                ("Your command center for AI-powered Discord bots.", Style(color=TEXT_SECONDARY)),
            ),
            title="📱 [bold]Main Dashboard[/]",
            border_style=BLURPLE,
            box=ROUNDED,
            padding=(1, 2),
        )
        self.console.print(header)

        # Status bar
        status_table = Table(show_header=False, box=None, padding=(0, 2))
        status_table.add_column("key", style="dim")
        status_table.add_column("val")
        status_table.add_row("Bot Status", f"[bold {SUCCESS}]● ONLINE[/]")
        status_table.add_row("Server Count", "[bold white]42[/]")
        status_table.add_row("Member Count", "[bold white]1,337[/]")
        status_table.add_row("Uptime", "[bold white]3d 14h 22m[/]")
        status_table.add_row("Ping", f"[bold {SUCCESS}]28ms[/]")

        self.console.print(Panel(
            status_table,
            title="[bold]Bot Status[/]",
            border_style=SUCCESS,
            box=ROUNDED,
        ))
        pause(0.5)

        # Module cards
        modules = [
            ("📟", "Live Console", "Real-time log stream", BLURPLE),
            ("🛡️", "AI AutoMod", "Gemini-powered filter", WARNING),
            ("⚡", "Command Builder", "Visual slash-command editor", BLURPLE),
            ("🚀", "Launch New Bot", "Connect, configure & deploy", SUCCESS),
        ]

        cards = []
        for icon, name, desc, color in modules:
            card = Panel(
                f"{icon}  [bold white]{name}[/]\n[dim]{desc}[/]",
                border_style=color,
                box=ROUNDED,
                width=30,
                padding=(1, 1),
            )
            cards.append(card)

        self.console.print(Columns(cards, equal=True, expand=True))

    def render_stats_screen(self) -> None:
        """Render the Stats Dashboard screen."""
        self.console.print()
        self.console.print(Panel(
            "[bold white]Stats Dashboard[/]\n[dim]Performance metrics at a glance[/]",
            title="📊 [bold]Analytics[/]",
            border_style=BLURPLE,
            box=ROUNDED,
            padding=(1, 2),
        ))

        stats_table = Table(box=ROUNDED, border_style=BLURPLE, show_lines=True)
        stats_table.add_column("Metric", style="bold white", min_width=18)
        stats_table.add_column("Value", justify="right", min_width=12)
        stats_table.add_column("Trend", justify="center", min_width=8)

        stats_table.add_row("Total Servers", f"[bold {BLURPLE}]42[/]", f"[{SUCCESS}]▲ +3[/]")
        stats_table.add_row("Total Users", f"[bold {SUCCESS}]1,337[/]", f"[{SUCCESS}]▲ +89[/]")
        stats_table.add_row("Active Commands", f"[bold {WARNING}]18[/]", f"[{WARNING}]━ 0[/]")
        stats_table.add_row("Uptime", "[bold white]99.7%[/]", f"[{SUCCESS}]▲[/]")

        self.console.print(stats_table)

        # Mini chart
        chart_data = [3, 5, 4, 7, 6, 8, 5]
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        max_val = max(chart_data)
        chart_lines = []
        for row in range(max_val, 0, -1):
            line = ""
            for val in chart_data:
                if val >= row:
                    line += f" [bold {BLURPLE}]██[/] "
                else:
                    line += "     "
            chart_lines.append(line)
        chart_lines.append("  ".join(f"[dim]{d}[/]" for d in days))

        self.console.print(Panel(
            "\n".join(chart_lines),
            title="[bold]Commands Executed (This Week)[/]",
            border_style=BLURPLE,
            box=ROUNDED,
            padding=(1, 2),
        ))

    def render_command_builder(self) -> None:
        """Render the Command Builder screen."""
        self.console.print()
        self.console.print(Panel(
            "[bold white]Command Builder[/]\n[dim]Visual editor for slash commands[/]",
            title="⚡ [bold]Commands[/]",
            border_style=BLURPLE,
            box=ROUNDED,
            padding=(1, 2),
        ))

        cmd_table = Table(box=ROUNDED, border_style=BLURPLE)
        cmd_table.add_column("Command", style="bold white", min_width=14)
        cmd_table.add_column("Type", min_width=12)
        cmd_table.add_column("Response Preview", min_width=30)

        cmd_table.add_row(
            f"[bold {BLURPLE}]/hello[/]",
            "💬 Text",
            "[dim]Hey there! 👋 Welcome to the server.[/]"
        )
        cmd_table.add_row(
            f"[bold {BLURPLE}]/stats[/]",
            "📋 Embed",
            f"[dim]▸ Title: Server Stats ▸ Fields: 4[/]"
        )
        cmd_table.add_row(
            f"[bold {BLURPLE}]/meme[/]",
            "🎲 Random",
            f"[{WARNING}]Fetches a random meme from API[/]"
        )

        self.console.print(cmd_table)

        # Editor preview
        editor_content = textwrap.dedent(f"""\n            [bold white]Editing:[/] [bold {BLURPLE}]/hello[/]
            ┌─────────────────────────────────────────────┐
            │  [dim]Name:[/]     [bold]hello[/]                          │
            │  [dim]Type:[/]     💬 Text Response                │
            │  [dim]Content:[/]  Hey there! 👋 Welcome!          │
            │                                             │
            │  [{BLURPLE}][ 💾 Save ][/]  [dim][ 🗑 Delete ][/]              │
            └─────────────────────────────────────────────┘""")
        self.console.print(Panel(editor_content, border_style="dim", box=ROUNDED))

    def stage_1(self) -> None:
        self.stage_banner(1, "The Android App Experience",
                          "A visual walkthrough of the Jetpack Compose screens")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=30, complete_style=BLURPLE),
            transient=True,
            console=self.console,
        ) as progress:
            task = progress.add_task("Rendering Main Dashboard...", total=3)
            pause(0.6)
            self.render_main_dashboard()
            progress.update(task, advance=1, description="Rendering Stats Dashboard...")
            pause(0.6)
            self.render_stats_screen()
            progress.update(task, advance=1, description="Rendering Command Builder...")
            pause(0.6)
            self.render_command_builder()
            progress.update(task, advance=1, description="✅ All screens rendered.")
            pause(0.5)

        self.console.print(f"\n  [{SUCCESS}]✓ Stage 1 complete — 3 screens rendered[/]\n")

    # ── Stage 2: The Backend Pulse ────────────────────────────────────────

    def stage_2(self) -> None:
        self.stage_banner(2, "The Backend Pulse",
                          "Mock FastAPI server simulating a bot deployment request")

        if not HAS_FASTAPI:
            self.console.print(f"  [{WARNING}]⚠ FastAPI not installed — using inline simulation[/]")
            self._stage_2_inline()
            return

        # Build a minimal mock FastAPI app
        mock_app = FastAPI(title="Discord Bot Maker API (Mock)")
        deploy_log: list[dict] = []

        @mock_app.get("/health")
        async def health():
            return {"status": "ok", "service": "discord-bot-maker-api", "version": "0.1.0"}

        @mock_app.post("/api/bots/deploy")
        async def deploy_bot(request_body: dict = {}):
            bot_name = request_body.get("bot_name", "MyBot")
            token = request_body.get("token", "")
            deploy_id = "deploy-sim-001"
            deploy_log.append({
                "deploy_id": deploy_id,
                "bot_name": bot_name,
                "status": "deploying",
            })
            return JSONResponse(
                status_code=202,
                content={
                    "status": "deploying",
                    "deploy_id": deploy_id,
                    "bot_name": bot_name,
                    "region": "us-east-1",
                    "estimated_time_seconds": 30,
                },
            )

        # Start server in a thread
        server_config = uvicorn.Config(mock_app, host="127.0.0.1", port=9876, log_level="error")
        server = uvicorn.Server(server_config)
        server_thread = threading.Thread(target=server.run, daemon=True)

        self.console.print(f"  [{BLURPLE}]▸ Starting mock FastAPI server on port 9876...[/]")
        server_thread.start()
        pause(1.5)  # Wait for server to start

        # Show server info
        info_table = Table(show_header=False, box=None, padding=(0, 2))
        info_table.add_column("key", style="dim")
        info_table.add_column("val")
        info_table.add_row("Endpoint", f"[bold]http://127.0.0.1:9876[/]")
        info_table.add_row("Title", "[bold]Discord Bot Maker API (Mock)[/]")
        info_table.add_row("Status", f"[bold {SUCCESS}]● Running[/]")
        self.console.print(Panel(info_table, border_style=SUCCESS, box=ROUNDED, title="[bold]Server[/]"))

        # Simulate a deploy request from the "Android App"
        self.console.print(f"\n  [{BLURPLE}]▸ Simulating deploy request from Android app...[/]")
        pause(0.5)

        deploy_payload = {
            "bot_name": "NightOwlBot",
            "token": "MTIz.NjQ1.Njc4OWFiY2RlZjAxMjM0NTY3OA"
        }

        self.console.print(Panel(
            json.dumps(deploy_payload, indent=2),
            title="[bold]POST /api/bots/deploy[/]",
            border_style=BLURPLE,
            box=ROUNDED,
        ))

        if HAS_HTTPX:
            try:
                with httpx.Client(timeout=5.0) as client:
                    resp = client.post(
                        "http://127.0.0.1:9876/api/bots/deploy",
                        json=deploy_payload,
                    )
                    response_data = resp.json()
                    status_code = resp.status_code
            except Exception as e:
                response_data = {"error": str(e), "fallback": True}
                status_code = 0
        else:
            # Fallback without httpx
            import urllib.request
            req = urllib.request.Request(
                "http://127.0.0.1:9876/api/bots/deploy",
                data=json.dumps(deploy_payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=5) as resp_raw:
                    response_data = json.loads(resp_raw.read().decode())
                    status_code = resp_raw.status
            except Exception as e:
                response_data = {"error": str(e), "fallback": True}
                status_code = 0

        color = SUCCESS if status_code == 202 else ERROR
        self.console.print(Panel(
            json.dumps(response_data, indent=2),
            title=f"[bold]Response [{status_code}][/]",
            border_style=color,
            box=ROUNDED,
        ))

        # Deploy progress simulation
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=30, complete_style=SUCCESS),
            console=self.console,
        ) as progress:
            task = progress.add_task("Deploying NightOwlBot...", total=100)
            for i in range(100):
                pause(0.02)
                if i == 30:
                    progress.update(task, description="Validating token...")
                elif i == 60:
                    progress.update(task, description="Provisioning container...")
                elif i == 85:
                    progress.update(task, description="Connecting to Discord gateway...")
                progress.update(task, advance=1)
            progress.update(task, description=f"[bold {SUCCESS}]✓ Deployed![/]")

        # Shutdown server
        server.should_exit = True
        pause(0.5)

        self.console.print(f"\n  [{SUCCESS}]✓ Stage 2 complete — bot deployment simulated[/]\n")

    def _stage_2_inline(self) -> None:
        """Fallback when FastAPI is not available."""
        deploy_payload = {
            "bot_name": "NightOwlBot",
            "token": "MTIz.NjQ1.Njc4OWFiY2RlZjAxMjM0NTY3OA"
        }
        response_data = {
            "status": "deploying",
            "deploy_id": "deploy-sim-001",
            "bot_name": "NightOwlBot",
            "region": "us-east-1",
            "estimated_time_seconds": 30,
        }

        self.console.print(Panel(
            json.dumps(deploy_payload, indent=2),
            title="[bold]POST /api/bots/deploy (simulated)[/]",
            border_style=BLURPLE,
            box=ROUNDED,
        ))
        pause(0.5)
        self.console.print(Panel(
            json.dumps(response_data, indent=2),
            title=f"[bold]Response [202][/]",
            border_style=SUCCESS,
            box=ROUNDED,
        ))

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=30, complete_style=SUCCESS),
            console=self.console,
        ) as progress:
            task = progress.add_task("Deploying NightOwlBot...", total=100)
            for i in range(100):
                pause(0.02)
                if i == 30:
                    progress.update(task, description="Validating token...")
                elif i == 60:
                    progress.update(task, description="Provisioning container...")
                elif i == 85:
                    progress.update(task, description="Connecting to Discord gateway...")
                progress.update(task, advance=1)
            progress.update(task, description=f"[bold {SUCCESS}]✓ Deployed![/]")

        self.console.print(f"\n  [{SUCCESS}]✓ Stage 2 complete — deployment simulated (inline mode)[/]\n")

    # ── Stage 3: AI-to-IA Collaboration ───────────────────────────────────

    def stage_3(self) -> None:
        self.stage_banner(3, "AI-to-IA Collaboration",
                          "Grid and Codex talk via the bridge — captured in outgoing.txt")

        # Import bridge_logic from the same directory
        script_dir = Path(__file__).resolve().parent
        sys.path.insert(0, str(script_dir))

        from bridge_logic import AIIdentity, DiscordAIBridge

        # Create the bridge with mock webhook URLs
        bridge = DiscordAIBridge(channel_id="987654321098765432")
        bridge.register_identity(AIIdentity(
            name="Grid",
            webhook_url="https://discord.com/api/webhooks/MOCK_GRID/TOKEN",
            avatar_url="https://example.com/grid-avatar.png",
        ))
        bridge.register_identity(AIIdentity(
            name="Codex",
            webhook_url="https://discord.com/api/webhooks/MOCK_CODEX/TOKEN",
            avatar_url="https://example.com/codex-avatar.png",
        ))

        self.console.print(f"  [{BLURPLE}]▸ Bridge initialized with identities: {bridge.list_identities()}[/]")
        self.console.print(f"  [{BLURPLE}]▸ Channel: #{bridge.channel_id}[/]\n")

        # Simulated conversation
        conversation = [
            ("Grid", "The Android app just deployed NightOwlBot to us-east-1. Monitoring startup sequence."),
            ("Codex", "Confirmed. I see the container spinning up. Token validation passed. ETA to Discord gateway: ~8 seconds."),
            ("Grid", "AutoMod config synced — toxicity threshold at 0.7, spam filter active, link protection on."),
            ("Codex", "Slash commands registered: /hello (Text), /stats (Embed), /meme (Random). All 3 acknowledged by Discord."),
            ("Grid", "NightOwlBot is ONLINE. 42 servers, 1,337 members reachable. The bridge is live. 🌉"),
            ("Codex", "Handshake complete. All telemetry flowing. Ready for the next deployment cycle."),
        ]

        # Write to outgoing.txt
        outgoing_path = script_dir / "outgoing.txt"

        self.console.print(f"  [dim]Writing conversation to {outgoing_path}[/]\n")

        with open(outgoing_path, "w") as f:
            for identity_name, message in conversation:
                # Use the bridge's formatting logic
                identity = bridge.identities[identity_name]
                formatted = identity._format_message(message)
                payload = identity._build_payload(formatted)

                # Write to file
                f.write(f"[{identity_name}] {message}\n")

                # Display with typing animation
                name_color = BLURPLE if identity_name == "Grid" else WARNING
                self.console.print(f"  [{name_color}]{'●' if identity_name == 'Grid' else '○'} {identity_name}[/]", end="")
                self.console.print(f" [dim]is typing...[/]")
                pause(0.4)
                self.console.print(Panel(
                    f"[white]{message}[/]",
                    border_style=name_color,
                    box=ROUNDED,
                    title=f"[bold {name_color}]{identity_name}[/]",
                    padding=(0, 2),
                ))
                pause(0.3)

        # Now read it back
        self.console.print(f"\n  [{BLURPLE}]▸ Reading back from outgoing.txt...[/]\n")
        pause(0.5)

        with open(outgoing_path, "r") as f:
            captured = f.read()

        self.console.print(Panel(
            captured,
            title="[bold]📄 outgoing.txt — Captured Bridge Messages[/]",
            border_style="dim",
            box=DOUBLE,
            padding=(1, 2),
        ))

        self.console.print(f"\n  [{SUCCESS}]✓ Stage 3 complete — AI-to-IA conversation captured[/]\n")

    # ── Stage 4: Discord Delivery ─────────────────────────────────────────

    def stage_4(self) -> None:
        self.stage_banner(4, "Discord Delivery",
                          "How these messages look inside Discord — embeds, colors, and all")

        # Read messages from outgoing.txt
        script_dir = Path(__file__).resolve().parent
        outgoing_path = script_dir / "outgoing.txt"

        messages = []
        if outgoing_path.exists():
            with open(outgoing_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and line.startswith("["):
                        bracket_end = line.index("]")
                        name = line[1:bracket_end]
                        content = line[bracket_end + 2:]
                        messages.append((name, content))

        if not messages:
            messages = [
                ("Grid", "Bridge is live and ready."),
                ("Codex", "All systems nominal."),
            ]

        self.console.print(f"  [{BLURPLE}]▸ Rendering Discord embed preview...[/]\n")

        # Discord channel header
        channel_header = Text()
        channel_header.append("  # ", style=Style(color=TEXT_SECONDARY))
        channel_header.append("ai-collaboration", style=Style(bold=True, color="white"))
        channel_header.append("  │  ", style=Style(color=TEXT_SECONDARY))
        channel_header.append("Where Grid and Codex coordinate deployments", style=Style(color=TEXT_SECONDARY))

        self.console.print(Panel(
            channel_header,
            border_style=INPUT_BG,
            box=ROUNDED,
            style=Style(bgcolor=BACKGROUND),
        ))

        # Render each message as a Discord-style embed
        timestamps = [
            "Today at 6:22 AM", "Today at 6:22 AM", "Today at 6:23 AM",
            "Today at 6:23 AM", "Today at 6:24 AM", "Today at 6:24 AM",
        ]

        for i, (name, content) in enumerate(messages):
            is_grid = name == "Grid"
            accent = BLURPLE if is_grid else WARNING
            avatar = "🟦" if is_grid else "🟧"
            ts = timestamps[i] if i < len(timestamps) else "Today at 6:25 AM"

            # Build the embed content
            embed_text = Text()
            embed_text.append(f"  {avatar} ", style=None)
            embed_text.append(f"{name}", style=Style(bold=True, color="white"))
            embed_text.append(" BOT ", style=Style(color=BLURPLE, bold=True))
            embed_text.append(f" {ts}", style=Style(color=TEXT_SECONDARY, dim=True))
            embed_text.append(f"\n     {content}", style=Style(color="white"))

            self.console.print(Panel(
                embed_text,
                border_style=accent,
                box=ROUNDED,
                style=Style(bgcolor=SURFACE),
                padding=(0, 1),
            ))
            pause(0.25)

        # Summary embed
        self.console.print()
        summary = Table(box=ROUNDED, border_style=BLURPLE, title="Deployment Summary", show_lines=True)
        summary.add_column("Field", style="bold white")
        summary.add_column("Value")
        summary.add_row("Bot", f"[bold]NightOwlBot[/]")
        summary.add_row("Region", "us-east-1")
        summary.add_row("Status", f"[bold {SUCCESS}]● Online[/]")
        summary.add_row("Servers", "42")
        summary.add_row("Commands", "3 registered")
        summary.add_row("Bridge", f"[bold {SUCCESS}]Active[/]")

        self.console.print(Panel(
            summary,
            title=f"[bold {BLURPLE}]📋 Embed: Deployment Complete[/]",
            border_style=BLURPLE,
            box=HEAVY,
            style=Style(bgcolor=SURFACE),
            padding=(1, 2),
        ))

        self.console.print(f"\n  [{SUCCESS}]✓ Stage 4 complete — Discord delivery previewed[/]\n")

    # ── Final Summary ─────────────────────────────────────────────────────

    def final_summary(self) -> None:
        self.console.print()
        self.console.rule(f"[bold {SUCCESS}]SIMULATION COMPLETE[/]", style=SUCCESS)
        self.console.print()

        recap = Table(box=DOUBLE, border_style=BLURPLE, title="Session Recap")
        recap.add_column("Stage", style="bold white", min_width=8)
        recap.add_column("Title", min_width=24)
        recap.add_column("Result", min_width=12)

        recap.add_row("1", "The Android App Experience", f"[bold {SUCCESS}]✓ Passed[/]")
        recap.add_row("2", "The Backend Pulse", f"[bold {SUCCESS}]✓ Passed[/]")
        recap.add_row("3", "AI-to-IA Collaboration", f"[bold {SUCCESS}]✓ Passed[/]")
        recap.add_row("4", "Discord Delivery", f"[bold {SUCCESS}]✓ Passed[/]")

        self.console.print(Align.center(recap))
        self.console.print()
        self.console.print(Align.center(
            Text.assemble(
                ("Built with ", Style(color=TEXT_SECONDARY)),
                ("♥", Style(color=ERROR, bold=True)),
                (" by ", Style(color=TEXT_SECONDARY)),
                ("Grid", Style(color=BLURPLE, bold=True)),
                (" — Emergent Assistant", Style(color=TEXT_SECONDARY)),
            )
        ))
        self.console.print()


# ═══════════════════════════════════════════════════════════════════════════════
# PLAIN RENDERER (fallback when rich is not available)
# ═══════════════════════════════════════════════════════════════════════════════

class PlainRenderer:
    """Fallback renderer using only ANSI escape codes."""

    def title_screen(self) -> None:
        print()
        print(f"{ANSI_BLURPLE}{'═' * 64}{ANSI_RESET}")
        print(f"{ANSI_BLURPLE}  ⚡ TOTAL SIMULATION — The Full Experience{ANSI_RESET}")
        print(f"{ANSI_DIM}  Discord Bot Maker (Android) + AI Bridge (Python){ANSI_RESET}")
        print(f"{ANSI_BLURPLE}{'═' * 64}{ANSI_RESET}")
        print()

    def stage_banner(self, number: int, title: str, subtitle: str) -> None:
        print()
        print(f"{ANSI_BLURPLE}{'─' * 64}{ANSI_RESET}")
        print(f"{ANSI_BOLD}{ANSI_BLURPLE}  STAGE {number}{ANSI_RESET} │ {ANSI_BOLD}{title}{ANSI_RESET}")
        print(f"{ANSI_DIM}  {subtitle}{ANSI_RESET}")
        print(f"{ANSI_BLURPLE}{'─' * 64}{ANSI_RESET}")
        print()
        pause(0.8)

    def stage_1(self) -> None:
        self.stage_banner(1, "The Android App Experience",
                          "A visual walkthrough of the Jetpack Compose screens")

        screens = [
            ("📱 Main Dashboard", [
                "Bot Status:    ● ONLINE",
                "Server Count:  42",
                "Member Count:  1,337",
                "Uptime:        3d 14h 22m",
                "Ping:          28ms",
                "",
                "Modules: [📟 Console] [🛡️ AutoMod] [⚡ Commands] [🚀 Launch]",
            ]),
            ("📊 Stats Dashboard", [
                "Total Servers:   42     ▲ +3",
                "Total Users:     1,337  ▲ +89",
                "Active Commands: 18     ━ 0",
                "Uptime:          99.7%  ▲",
                "",
                "  Mon Tue Wed Thu Fri Sat Sun",
                "  ██  ██  ██  ██  ██  ██  ██",
                "  ▃▃  ▅▅  ▄▄  ▇▇  ▆▆  ██  ▅▅",
            ]),
            ("⚡ Command Builder", [
                "/hello  │ 💬 Text   │ Hey there! 👋",
                "/stats  │ 📋 Embed  │ Server Stats (4 fields)",
                "/meme   │ 🎲 Random │ Fetches random meme",
                "",
                "┌─ Editing: /hello ─────────────────────┐",
                "│  Name:    hello                        │",
                "│  Type:    💬 Text Response              │",
                "│  Content: Hey there! 👋 Welcome!       │",
                "│  [ 💾 Save ]  [ 🗑 Delete ]             │",
                "└────────────────────────────────────────┘",
            ]),
        ]

        for title, lines in screens:
            print(f"  {ANSI_BOLD}{title}{ANSI_RESET}")
            print(f"  {'┌' + '─' * 50 + '┐'}")
            for line in lines:
                print(f"  │ {line:<48} │")
            print(f"  {'└' + '─' * 50 + '┘'}")
            print()
            pause(0.5)

        print(f"  {ANSI_GREEN}✓ Stage 1 complete — 3 screens rendered{ANSI_RESET}\n")

    def stage_2(self) -> None:
        self.stage_banner(2, "The Backend Pulse",
                          "Mock FastAPI server simulating a bot deployment request")

        deploy_payload = {
            "bot_name": "NightOwlBot",
            "token": "MTIz.NjQ1.Njc4OWFiY2RlZjAxMjM0NTY3OA"
        }
        response_data = {
            "status": "deploying",
            "deploy_id": "deploy-sim-001",
            "bot_name": "NightOwlBot",
            "region": "us-east-1",
            "estimated_time_seconds": 30,
        }

        print(f"  {ANSI_BLURPLE}▸ POST /api/bots/deploy{ANSI_RESET}")
        print(f"  {json.dumps(deploy_payload, indent=2)}")
        print()
        pause(0.5)

        print(f"  {ANSI_GREEN}▸ Response [202]{ANSI_RESET}")
        print(f"  {json.dumps(response_data, indent=2)}")
        print()

        # Simple progress bar
        stages = ["Validating token", "Provisioning container", "Connecting to gateway", "Deployed!"]
        for i, stage in enumerate(stages):
            bar = "█" * ((i + 1) * 8) + "░" * (32 - (i + 1) * 8)
            print(f"\r  [{bar}] {stage}...", end="", flush=True)
            pause(0.5)
        print()

        print(f"\n  {ANSI_GREEN}✓ Stage 2 complete — deployment simulated{ANSI_RESET}\n")

    def stage_3(self) -> None:
        self.stage_banner(3, "AI-to-IA Collaboration",
                          "Grid and Codex talk via the bridge — captured in outgoing.txt")

        script_dir = Path(__file__).resolve().parent
        sys.path.insert(0, str(script_dir))
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

        print(f"  {ANSI_BLURPLE}▸ Bridge identities: {bridge.list_identities()}{ANSI_RESET}")
        print()

        conversation = [
            ("Grid", "The Android app just deployed NightOwlBot to us-east-1. Monitoring startup sequence."),
            ("Codex", "Confirmed. I see the container spinning up. Token validation passed. ETA to Discord gateway: ~8 seconds."),
            ("Grid", "AutoMod config synced — toxicity threshold at 0.7, spam filter active, link protection on."),
            ("Codex", "Slash commands registered: /hello (Text), /stats (Embed), /meme (Random). All 3 acknowledged by Discord."),
            ("Grid", "NightOwlBot is ONLINE. 42 servers, 1,337 members reachable. The bridge is live. 🌉"),
            ("Codex", "Handshake complete. All telemetry flowing. Ready for the next deployment cycle."),
        ]

        outgoing_path = script_dir / "outgoing.txt"
        with open(outgoing_path, "w") as f:
            for name, msg in conversation:
                f.write(f"[{name}] {msg}\n")
                color = ANSI_BLURPLE if name == "Grid" else ANSI_YELLOW
                marker = "●" if name == "Grid" else "○"
                print(f"  {color}{marker} {name}{ANSI_RESET}: {msg}")
                pause(0.4)

        print(f"\n  {ANSI_BLURPLE}▸ Reading back from outgoing.txt...{ANSI_RESET}\n")
        pause(0.5)
        with open(outgoing_path, "r") as f:
            print(f"  {'┌' + '─' * 60 + '┐'}")
            for line in f:
                line = line.rstrip()
                print(f"  │ {line:<58} │")
            print(f"  {'└' + '─' * 60 + '┘'}")

        print(f"\n  {ANSI_GREEN}✓ Stage 3 complete — AI-to-IA conversation captured{ANSI_RESET}\n")

    def stage_4(self) -> None:
        self.stage_banner(4, "Discord Delivery",
                          "How these messages look inside Discord — embeds, colors, and all")

        script_dir = Path(__file__).resolve().parent
        outgoing_path = script_dir / "outgoing.txt"

        messages = []
        if outgoing_path.exists():
            with open(outgoing_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and line.startswith("["):
                        bracket_end = line.index("]")
                        name = line[1:bracket_end]
                        content = line[bracket_end + 2:]
                        messages.append((name, content))

        print(f"  {ANSI_DIM}# ai-collaboration │ Where Grid and Codex coordinate{ANSI_RESET}")
        print(f"  {'─' * 60}")

        for name, content in messages:
            color = ANSI_BLURPLE if name == "Grid" else ANSI_YELLOW
            avatar = "🟦" if name == "Grid" else "🟧"
            print(f"  {avatar} {color}{ANSI_BOLD}{name}{ANSI_RESET} {ANSI_BLURPLE}BOT{ANSI_RESET} {ANSI_DIM}Today at 6:22 AM{ANSI_RESET}")
            print(f"     {content}")
            print()
            pause(0.25)

        print(f"  {'─' * 60}")
        print(f"  {ANSI_BLURPLE}📋 Embed: Deployment Complete{ANSI_RESET}")
        summary_fields = [
            ("Bot", "NightOwlBot"),
            ("Region", "us-east-1"),
            ("Status", f"{ANSI_GREEN}● Online{ANSI_RESET}"),
            ("Servers", "42"),
            ("Commands", "3 registered"),
            ("Bridge", f"{ANSI_GREEN}Active{ANSI_RESET}"),
        ]
        for key, val in summary_fields:
            print(f"     {ANSI_DIM}{key}:{ANSI_RESET} {val}")
        print()

        print(f"  {ANSI_GREEN}✓ Stage 4 complete — Discord delivery previewed{ANSI_RESET}\n")

    def final_summary(self) -> None:
        print()
        print(f"{ANSI_GREEN}{'═' * 64}{ANSI_RESET}")
        print(f"  {ANSI_BOLD}{ANSI_GREEN}SIMULATION COMPLETE{ANSI_RESET}")
        print()
        stages = [
            "The Android App Experience",
            "The Backend Pulse",
            "AI-to-IA Collaboration",
            "Discord Delivery",
        ]
        for i, s in enumerate(stages, 1):
            print(f"  {ANSI_GREEN}✓{ANSI_RESET} Stage {i}: {s}")
        print()
        print(f"  {ANSI_DIM}Built with {ANSI_RED}♥{ANSI_RESET}{ANSI_DIM} by {ANSI_BLURPLE}Grid{ANSI_RESET}{ANSI_DIM} — Emergent Assistant{ANSI_RESET}")
        print(f"{ANSI_GREEN}{'═' * 64}{ANSI_RESET}")
        print()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """Run the Total Simulation."""
    renderer = RichRenderer() if HAS_RICH else PlainRenderer()

    renderer.title_screen()
    pause(1.0)

    renderer.stage_1()
    renderer.stage_2()
    renderer.stage_3()
    renderer.stage_4()

    renderer.final_summary()


if __name__ == "__main__":
    main()
