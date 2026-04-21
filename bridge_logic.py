"""
Discord AI Bridge — bridge_logic.py

Routes messages from multiple AI identities to a single Discord channel
via webhooks. Each AI identity has its own display name and avatar,
making it easy to tell who (or what) is speaking.

Usage:
    python bridge_logic.py                        # interactive demo
    python bridge_logic.py --config cfg.yaml      # load from a YAML config
    python bridge_logic.py --daemon               # daemon mode (watches outgoing.txt)
    python bridge_logic.py --daemon --outfile out  # custom outgoing file path
"""

import argparse
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

import requests
import yaml

# ---------------------------------------------------------------------------
# Rich console — graceful fallback if not installed
# ---------------------------------------------------------------------------

try:
    from rich.console import Console
    from rich.logging import RichHandler
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

if RICH_AVAILABLE:
    console = Console()
else:
    class _FallbackConsole:
        """Minimal shim so the rest of the code can call console.print()."""
        def print(self, *args, **kwargs):
            style = kwargs.pop("style", None)
            parts = []
            for a in args:
                parts.append(str(a))
            print(" ".join(parts))

        def rule(self, title="", **kwargs):
            print(f"--- {title} ---")

        def log(self, *args, **kwargs):
            self.print(*args, **kwargs)

    console = _FallbackConsole()


def _setup_logging(verbose: bool = False) -> logging.Logger:
    level = logging.DEBUG if verbose else logging.INFO
    if RICH_AVAILABLE:
        handler = RichHandler(
            console=console,
            rich_tracebacks=True,
            show_path=False,
        )
    else:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger = logging.getLogger("bridge")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger


log = _setup_logging()


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class AIIdentity:
    """Represents a single AI persona that can post to Discord."""

    name: str
    webhook_url: str
    avatar_url: Optional[str] = None

    def send(self, content: str, channel_id: str) -> dict:
        """Send a formatted message to Discord via the identity's webhook.

        Args:
            content:    The raw text the AI wants to say.
            channel_id: The target Discord channel ID (used for logging /
                        routing; the webhook itself is already bound to a
                        channel).

        Returns:
            The JSON response from the Discord API.

        Raises:
            requests.HTTPError: If Discord returns a non-2xx status.
        """
        formatted = self._format_message(content)
        payload = self._build_payload(formatted)
        return self._post(payload)

    # -- private helpers ----------------------------------------------------

    def _format_message(self, content: str) -> str:
        return f"**[{self.name}]**\n{content}"

    def _build_payload(self, formatted_content: str) -> dict:
        payload: dict = {
            "content": formatted_content,
            "username": self.name,
        }
        if self.avatar_url:
            payload["avatar_url"] = self.avatar_url
        return payload

    def _post(self, payload: dict) -> dict:
        resp = requests.post(
            self.webhook_url,
            json=payload,
            params={"wait": "true"},
            timeout=15,
        )
        resp.raise_for_status()
        if resp.status_code == 204:
            return {"status": "sent"}
        return resp.json()


@dataclass
class DiscordAIBridge:
    """Central hub that manages AI identities and dispatches messages."""

    channel_id: str = "YOUR_CHANNEL_ID_HERE"
    identities: dict[str, AIIdentity] = field(default_factory=dict)

    # -- public API ---------------------------------------------------------

    def register_identity(self, identity: AIIdentity) -> None:
        self.identities[identity.name] = identity

    def send_message(self, identity_name: str, content: str) -> dict:
        if identity_name not in self.identities:
            raise KeyError(
                f"Unknown identity '{identity_name}'. "
                f"Registered: {list(self.identities.keys())}"
            )
        identity = self.identities[identity_name]
        return identity.send(content, self.channel_id)

    def list_identities(self) -> list[str]:
        return list(self.identities.keys())

    # -- config helpers -----------------------------------------------------

    @classmethod
    def from_yaml(cls, path: str) -> "DiscordAIBridge":
        with open(path, "r") as fh:
            cfg = yaml.safe_load(fh)

        bridge = cls(channel_id=cfg.get("channel_id", "YOUR_CHANNEL_ID_HERE"))

        for entry in cfg.get("identities", []):
            identity = AIIdentity(
                name=entry["name"],
                webhook_url=entry["webhook_url"],
                avatar_url=entry.get("avatar_url"),
            )
            bridge.register_identity(identity)

        return bridge


# ---------------------------------------------------------------------------
# Daemon Mode — file-watcher for outgoing messages
# ---------------------------------------------------------------------------

DEFAULT_OUTFILE = "outgoing.txt"
DAEMON_POLL_INTERVAL = 2.0  # seconds


def parse_outgoing_lines(lines: list[str]) -> list[tuple[str, str]]:
    """Parse lines from the outgoing file.

    Expected format per line:
        <identity>: <message>

    Blank lines and lines starting with '#' are skipped.

    Returns:
        List of (identity_name, message) tuples.
    """
    parsed: list[tuple[str, str]] = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            log.warning("Skipping malformed line (no colon): %s", line)
            continue
        name, message = line.split(":", 1)
        name = name.strip()
        message = message.strip()
        if name and message:
            parsed.append((name, message))
        else:
            log.warning("Skipping incomplete line: %s", line)
    return parsed


def daemon_loop(
    bridge: DiscordAIBridge,
    outfile: str = DEFAULT_OUTFILE,
    poll_interval: float = DAEMON_POLL_INTERVAL,
    *,
    _max_iterations: Optional[int] = None,
) -> list[dict]:
    """Watch *outfile* for new messages and send them via the bridge.

    The daemon reads the file, processes all lines, then **truncates** it so
    lines are not sent twice.  It then sleeps for *poll_interval* seconds and
    checks again.

    Args:
        bridge:          Configured DiscordAIBridge instance.
        outfile:         Path to the outgoing message file.
        poll_interval:   Seconds between polls.
        _max_iterations: (testing only) stop after N cycles; ``None`` = forever.

    Returns:
        List of send results (only meaningful when _max_iterations is set).
    """
    results: list[dict] = []
    iterations = 0

    log.info("Daemon started — watching '%s' every %.1fs", outfile, poll_interval)
    if RICH_AVAILABLE:
        console.print(
            Panel(
                f"[bold green]Daemon Mode[/bold green]\n"
                f"Watching: [cyan]{outfile}[/cyan]\n"
                f"Poll interval: [yellow]{poll_interval}s[/yellow]\n"
                f"Identities: {', '.join(bridge.list_identities())}",
                title="\U0001f916 Discord AI Bridge — Daemon",
                border_style="green",
            )
        )

    while True:
        if _max_iterations is not None and iterations >= _max_iterations:
            break
        iterations += 1

        if not os.path.exists(outfile):
            log.debug("Outfile '%s' does not exist yet — waiting…", outfile)
            time.sleep(poll_interval)
            continue

        try:
            with open(outfile, "r") as fh:
                lines = fh.readlines()
        except OSError as exc:
            log.error("Failed to read '%s': %s", outfile, exc)
            time.sleep(poll_interval)
            continue

        if not lines or all(l.strip() == "" for l in lines):
            log.debug("No new messages in '%s'", outfile)
            time.sleep(poll_interval)
            continue

        messages = parse_outgoing_lines(lines)
        if not messages:
            _truncate_file(outfile)
            time.sleep(poll_interval)
            continue

        log.info("Found %d message(s) to send", len(messages))

        for identity_name, content in messages:
            try:
                result = bridge.send_message(identity_name, content)
                results.append({"identity": identity_name, "status": "sent", "result": result})
                log.info("\u2713 [%s] %s", identity_name, _truncate_str(content, 60))
            except KeyError as exc:
                results.append({"identity": identity_name, "status": "error", "error": str(exc)})
                log.error("\u2717 %s", exc)
            except requests.HTTPError as exc:
                results.append({"identity": identity_name, "status": "error", "error": str(exc)})
                log.error("\u2717 Discord error for [%s]: %s", identity_name, exc)

        _truncate_file(outfile)
        time.sleep(poll_interval)

    return results


def _truncate_file(path: str) -> None:
    """Clear the contents of a file."""
    try:
        with open(path, "w") as fh:
            fh.truncate(0)
        log.debug("Truncated '%s'", path)
    except OSError as exc:
        log.error("Failed to truncate '%s': %s", path, exc)


def _truncate_str(s: str, maxlen: int) -> str:
    return s if len(s) <= maxlen else s[: maxlen - 1] + "\u2026"


# ---------------------------------------------------------------------------
# CLI helpers (rich-enhanced)
# ---------------------------------------------------------------------------

def _print_banner(bridge: DiscordAIBridge, config_source: str) -> None:
    """Print a pretty startup banner."""
    if RICH_AVAILABLE:
        table = Table(title="Registered Identities", show_header=True, header_style="bold cyan")
        table.add_column("Name", style="bold")
        table.add_column("Webhook URL", style="dim")
        table.add_column("Avatar", style="dim")
        for name, ident in bridge.identities.items():
            webhook_display = ident.webhook_url[:45] + "\u2026" if len(ident.webhook_url) > 45 else ident.webhook_url
            table.add_row(name, webhook_display, ident.avatar_url or "\u2014")

        console.print(
            Panel(
                f"[bold green]Discord AI Bridge[/bold green]\n"
                f"Config: [cyan]{config_source}[/cyan] \u2022 "
                f"Channel: [yellow]{bridge.channel_id}[/yellow]",
                title="\U0001f916\U0001f309",
                border_style="blue",
            )
        )
        console.print(table)
    else:
        print(f"Loaded from {config_source}")
        print(f"Identities: {bridge.list_identities()}")
        print(f"Channel ID: {bridge.channel_id}")


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Discord AI Bridge — route AI messages to Discord",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to a YAML config file (see config.example.yaml).",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run in daemon mode: watch an outgoing file for new messages.",
    )
    parser.add_argument(
        "--outfile",
        type=str,
        default=DEFAULT_OUTFILE,
        help=f"Path to the outgoing message file (default: {DEFAULT_OUTFILE}).",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=DAEMON_POLL_INTERVAL,
        help=f"Seconds between file polls in daemon mode (default: {DAEMON_POLL_INTERVAL}).",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug-level logging.",
    )
    args = parser.parse_args()

    global log
    log = _setup_logging(verbose=args.verbose)

    if args.config:
        bridge = DiscordAIBridge.from_yaml(args.config)
        _print_banner(bridge, args.config)
    else:
        bridge = DiscordAIBridge(channel_id="000000000000000000")
        bridge.register_identity(
            AIIdentity(
                name="Claude",
                webhook_url="https://discord.com/api/webhooks/PLACEHOLDER/TOKEN",
                avatar_url="https://example.com/claude-avatar.png",
            )
        )
        bridge.register_identity(
            AIIdentity(
                name="GPT-4",
                webhook_url="https://discord.com/api/webhooks/PLACEHOLDER/TOKEN",
                avatar_url="https://example.com/gpt4-avatar.png",
            )
        )
        _print_banner(bridge, "demo placeholders")

    # --- Daemon mode -------------------------------------------------------
    if args.daemon:
        try:
            daemon_loop(bridge, outfile=args.outfile, poll_interval=args.poll_interval)
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Daemon stopped.[/bold yellow]" if RICH_AVAILABLE else "\nDaemon stopped.")
        return

    # --- Interactive mode --------------------------------------------------
    console.rule("Interactive Mode") if RICH_AVAILABLE else print("\n--- Interactive Mode ---")
    console.print(
        "[dim]Type messages as[/dim]  [bold]<identity>: <message>[/bold]   [dim](Ctrl-C to quit)[/dim]"
    ) if RICH_AVAILABLE else print("Type messages as  <identity>: <message>   (Ctrl-C to quit)")

    try:
        while True:
            raw = input("> ").strip()
            if not raw:
                continue
            if ":" not in raw:
                log.warning("Format: <identity>: <message>")
                continue
            name, message = raw.split(":", 1)
            name = name.strip()
            message = message.strip()
            try:
                result = bridge.send_message(name, message)
                log.info("\u2713 Sent as [%s]: %s", name, _truncate_str(message, 50))
            except KeyError as exc:
                log.error("\u2717 %s", exc)
            except requests.HTTPError as exc:
                log.error("\u2717 Discord error: %s", exc)
    except (KeyboardInterrupt, EOFError):
        console.print("\n[bold yellow]Bye![/bold yellow]" if RICH_AVAILABLE else "\nBye!")


if __name__ == "__main__":
    main()
