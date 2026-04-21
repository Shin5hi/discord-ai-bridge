# Discord AI Bridge 🤖🌉

**Route messages from multiple AI identities into a single Discord channel — each with its own name and avatar.**

The Discord AI Bridge lets you funnel output from different AI models (Claude, GPT-4, Gemini, or any custom persona) into one Discord channel via webhooks. Every message is clearly labelled so readers always know *which AI is speaking*.

---

## Features

- **Multi-identity support** — register as many AI personas as you like.
- **Webhook-based** — no bot token required; uses standard Discord Webhooks.
- **Custom avatars** — each identity can have its own profile picture.
- **YAML config** — one file to manage channel IDs, webhook URLs, and API keys.
- **Interactive CLI** — type messages in your terminal and see them appear in Discord.

---

## Requirements

| Package    | Version | Purpose                        |
|------------|---------|--------------------------------|
| Python     | ≥ 3.10  | Runtime                        |
| `requests` | ≥ 2.28  | HTTP calls to Discord Webhooks |
| `PyYAML`   | ≥ 6.0   | YAML config parsing            |

> **Note:** `discord.py` is *not* required for the webhook-only bridge. Add it to your project if you later want full bot functionality.

### Install dependencies

```bash
pip install requests pyyaml
```

---

## Quick Start

### 1. Create a Discord Webhook

1. Open your Discord server → **Server Settings → Integrations → Webhooks**.
2. Click **New Webhook**, pick a channel, and copy the **Webhook URL**.
3. Repeat for each AI identity (or reuse one webhook — the bridge overrides the display name per message).

### 2. Configure

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` and fill in your real webhook URLs and channel ID.

### 3. Run

```bash
python bridge_logic.py --config config.yaml
```

You'll see an interactive prompt:

```
Loaded 3 identities from config.yaml
Identities: ['Claude', 'GPT-4', 'Gemini']
Channel ID: 123456789012345678

Type messages as  <identity>: <message>   (Ctrl-C to quit)
> Claude: Hello from the bridge!
  ✓ Sent (...)
```

### 4. Programmatic usage

```python
from bridge_logic import DiscordAIBridge, AIIdentity

bridge = DiscordAIBridge(channel_id="123456789012345678")

bridge.register_identity(AIIdentity(
    name="Claude",
    webhook_url="https://discord.com/api/webhooks/ID/TOKEN",
    avatar_url="https://example.com/claude.png",
))

bridge.send_message("Claude", "Thinking out loud…")
```

---

## Project Structure

```
discord-ai-bridge/
├── bridge_logic.py        # Core bridge logic & CLI
├── config.example.yaml    # Configuration template
├── README.md              # You are here
└── tests/
    └── test_bridge.py     # Unit tests
```

---

## Project Mission

> **Make AI collaboration visible.**
>
> As AI agents become teammates rather than tools, teams need a shared space
> where every AI’s contribution is transparent and attributable. The Discord
> AI Bridge turns a standard Discord channel into that shared workspace —
> giving each AI a distinct voice so humans (and other AIs) can follow the
> conversation naturally.

---

## License

MIT — use it however you like.
