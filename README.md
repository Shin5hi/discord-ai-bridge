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
- **🆕 Daemon Mode** — watches a local file for outgoing messages, perfect for AI-to-AI communication.
- **🆕 Rich logging** — colorful, structured output via the `rich` library (graceful fallback if not installed).

---

## Requirements

| Package    | Version | Purpose                        |
|------------|---------|--------------------------------|
| Python     | >= 3.10 | Runtime                        |
| `requests` | >= 2.28 | HTTP calls to Discord Webhooks |
| `PyYAML`   | >= 6.0  | YAML config parsing            |
| `rich`     | >= 13.0 | *(optional)* Pretty CLI output |

> **Note:** `discord.py` is *not* required for the webhook-only bridge. Add it to your project if you later want full bot functionality.

### Install dependencies

```bash
pip install requests pyyaml rich
```

---

## Quick Start

### 1. Create a Discord Webhook

1. Open your Discord server -> **Server Settings -> Integrations -> Webhooks**.
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

bridge.send_message("Claude", "Thinking out loud...")
```

---

## Daemon Mode 🔄

Daemon mode turns the bridge into a **background service** that watches a local text file for new messages. Any AI agent, script, or process can write to that file and the bridge picks it up and sends it to Discord automatically.

### How it works

1. The daemon polls a file (default: `outgoing.txt`) every 2 seconds.
2. Each non-empty, non-comment line is parsed as `<identity>: <message>`.
3. Matched messages are sent through the bridge to Discord.
4. The file is **truncated** after processing, so messages are never sent twice.

### Usage

```bash
# Start daemon with defaults (watches ./outgoing.txt, polls every 2s)
python bridge_logic.py --config config.yaml --daemon

# Custom file and poll interval
python bridge_logic.py --config config.yaml --daemon --outfile /tmp/ai-outbox.txt --poll-interval 5

# Verbose logging (debug level)
python bridge_logic.py --config config.yaml --daemon -v
```

### Writing to the outgoing file

Any process can append messages — just follow the `<identity>: <message>` format:

```bash
# From a shell script
echo "Claude: I've finished analysing the dataset." >> outgoing.txt

# From Python
with open("outgoing.txt", "a") as f:
    f.write("GPT-4: The build passed all 42 tests.\n")
```

Lines starting with `#` are treated as comments and skipped. Blank lines are ignored.

---

## Collaboration with Codex & Grid 🤝

The Daemon Mode unlocks a powerful pattern: **AI agents that talk to each other through Discord.**

### The idea

Grid and Codex (or any other AI assistant) can operate on the same machine. When one agent wants to communicate through Discord, it simply writes to the shared outgoing file. The daemon picks it up and posts it with the correct identity.

```
+----------+                          +-----------------+
|   Grid   |--writes--> outgoing.txt -->|  Daemon Mode   |--webhook--> Discord
|  (Agent) |                          |  (bridge_logic) |
+----------+                          +-----------------+
       ^                                       |
       |                                       |
+----------+                                   |
|  Codex   |--writes--> outgoing.txt ----------+
|  (Agent) |
+----------+
```

### Step-by-step setup

1. **Configure identities** — add a "Grid" and "Codex" identity in `config.yaml`:

   ```yaml
   identities:
     - name: "Grid"
       webhook_url: "https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN"
       avatar_url: "https://example.com/grid-avatar.png"

     - name: "Codex"
       webhook_url: "https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN"
       avatar_url: "https://example.com/codex-avatar.png"
   ```

2. **Start the daemon** in a terminal (or via `tmux` / `systemd`):

   ```bash
   python bridge_logic.py --config config.yaml --daemon --outfile /shared/outgoing.txt
   ```

3. **Let Grid write messages** — when Grid finishes a task, it appends a line:

   ```bash
   echo "Grid: Deployment complete — all 3 services are green." >> /shared/outgoing.txt
   ```

4. **Let Codex respond** — Codex can do the same:

   ```bash
   echo "Codex: Running post-deploy smoke tests now..." >> /shared/outgoing.txt
   ```

5. **Watch Discord** — both messages appear in the channel under their respective identities with distinct avatars.

### Tips for multi-agent setups

- **Use absolute paths** for the outgoing file so every agent resolves the same location.
- **Keep messages atomic** — write the full line in a single `write()` call or use `>>` to avoid partial reads.
- **Use comments** for metadata: `# grid:task_id=42` lines are ignored by the daemon but useful for debugging.
- **Combine with cron or systemd** to auto-start the daemon on boot.

---

## CLI Reference

```
usage: bridge_logic.py [-h] [--config CONFIG] [--daemon] [--outfile OUTFILE]
                       [--poll-interval POLL_INTERVAL] [--verbose]

Discord AI Bridge — route AI messages to Discord

options:
  -h, --help                 show this help message and exit
  --config CONFIG            Path to a YAML config file
  --daemon                   Run in daemon mode (watch outgoing file)
  --outfile OUTFILE          Path to the outgoing message file (default: outgoing.txt)
  --poll-interval INTERVAL   Seconds between file polls (default: 2.0)
  --verbose, -v              Enable debug-level logging
```

---

## Project Structure

```
discord-ai-bridge/
├── bridge_logic.py        # Core bridge logic, daemon mode & CLI
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
> where every AI's contribution is transparent and attributable. The Discord
> AI Bridge turns a standard Discord channel into that shared workspace —
> giving each AI a distinct voice so humans (and other AIs) can follow the
> conversation naturally.

---

## License

MIT — use it however you like.
