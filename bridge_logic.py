"""
Discord AI Bridge — bridge_logic.py

Routes messages from multiple AI identities to a single Discord channel
via webhooks. Each AI identity has its own display name and avatar,
making it easy to tell who (or what) is speaking.

Usage:
    python bridge_logic.py                 # interactive demo
    python bridge_logic.py --config cfg.yaml  # load from a YAML config
"""

import argparse
import sys
from dataclasses import dataclass, field
from typing import Optional

import requests
import yaml


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
        # Discord returns 204 No Content when wait=false; with wait=true we
        # get a JSON message object.
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
# CLI entry-point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Discord AI Bridge")
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to a YAML config file (see config.example.yaml).",
    )
    args = parser.parse_args()

    if args.config:
        bridge = DiscordAIBridge.from_yaml(args.config)
        print(f"Loaded {len(bridge.identities)} identities from {args.config}")
    else:
        # Quick demo with placeholder values
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
        print("Running with demo placeholders (messages will fail without real webhooks).")

    print(f"Identities: {bridge.list_identities()}")
    print(f"Channel ID: {bridge.channel_id}")

    # Interactive loop
    print("\nType messages as  <identity>: <message>   (Ctrl-C to quit)")
    try:
        while True:
            raw = input("> ").strip()
            if not raw:
                continue
            if ":" not in raw:
                print("Format: <identity>: <message>")
                continue
            name, message = raw.split(":", 1)
            name = name.strip()
            message = message.strip()
            try:
                result = bridge.send_message(name, message)
                print(f"  ✓ Sent ({result})")
            except KeyError as exc:
                print(f"  ✗ {exc}")
            except requests.HTTPError as exc:
                print(f"  ✗ Discord error: {exc}")
    except (KeyboardInterrupt, EOFError):
        print("\nBye!")


if __name__ == "__main__":
    main()
