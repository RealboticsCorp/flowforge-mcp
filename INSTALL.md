# Installing FlowForge for a coding agent

**Coding agents (Claude Code, Codex, Cursor, …): these instructions are for you.**
The user pasted this repository's link and asked you to install it. Follow the
steps in order. Every step is safe to re-run.

What gets installed:

| Piece | Where | Used by |
| --- | --- | --- |
| `flowforge-mcp` MCP server (48 tools, all 160 API endpoints) | `uv tool` dir, or `~/.flowforge-mcp/venv` | Claude Code, Codex, Claude Desktop |
| `flowforge` skill (how to operate FlowForge safely) | `~/.claude/skills/flowforge`, `~/.agents/skills/flowforge` | Claude Code, Codex |
| `goal-based-voice-agent` skill (design and deploy a voice agent) | `~/.claude/skills/goal-based-voice-agent`, `~/.agents/skills/goal-based-voice-agent` | Claude Code, Codex |
| `/ff-*` slash commands | `~/.claude/commands/ff-*.md` | Claude Code |
| Server-name → org map | `~/.config/flowforge/servers.md` | the skill |

## Step 1 — check prerequisites

```bash
command -v uv || python3 --version
```

You need either `uv` or Python 3.10+. If neither is present, ask the user to
install uv (`curl -LsSf https://astral.sh/uv/install.sh | sh`) and stop until they
have. Supported: macOS and Linux. On Windows, use WSL or follow
[Other clients](#other-clients-or-manual-setup).

## Step 2 — clone the repository

```bash
git clone https://github.com/RealboticsCorp/flowforge-mcp.git ~/.flowforge-mcp/src \
  || git -C ~/.flowforge-mcp/src pull --ff-only
```

## Step 3 — get the user's FlowForge API key

Ask the user for their FlowForge API key. They create one in the FlowForge
dashboard under **Settings → API Keys** (it starts with `ff_live_` and is shown
only once). Rules:

- Never echo the key back, write it to a file, or put it in a commit.
- Pass it only through the `FLOWFORGE_API_KEY` environment variable of the
  install command below.
- If the user would rather not paste it into the chat, tell them to run
  `~/.flowforge-mcp/src/install.sh` themselves in a terminal; it prompts for the
  key with hidden input. Then skip to Step 5.

If the user has keys for several FlowForge organizations, install the first as
`flowforge` and each other one with `--name flowforge-<org> --server-only`
(Step 4, run once per key).

## Step 4 — run the installer

```bash
FLOWFORGE_API_KEY='<the key>' ~/.flowforge-mcp/src/install.sh
```

It installs the server, verifies the key against the API (read-only: it reads the
organization name), copies the skills and slash commands, and registers the
server with every client it finds: Claude Code (user scope), Codex, and Claude
Desktop. Useful flags (`--help` for all):

- `--clients claude,codex,desktop` — only these clients.
- `--name flowforge-acme --server-only` — add another org's key.
- `--replace` — overwrite an existing server entry with the same name (for
  example to change the key).

Expected output ends with `Key works: organization "<name>", 48 tools` and
`Done.` If it reports `the key was rejected`, ask the user to check the key; do
not retry with guesses. If it warns that a server with the same name already
exists, ask the user before re-running with `--replace`.

## Step 5 — tell the user to restart

MCP servers load when a session starts. Tell the user to restart Claude Code /
Codex / Claude Desktop (a new session is enough for the CLIs), then try:

> Using FlowForge, list my assistants.

In Claude Code, `/ff-status` shows concurrency and live calls.

## Updating

```bash
git -C ~/.flowforge-mcp/src pull --ff-only && ~/.flowforge-mcp/src/install.sh --update
```

`--update` reinstalls the server, the `flowforge` skill and the slash commands.
It leaves keys, client registrations and the `goal-based-voice-agent` skill
(installed on first install only) alone. Restart the client afterwards.

## Other clients or manual setup

Any MCP client that runs stdio servers works. After installing the package
(`uv tool install ~/.flowforge-mcp/src`), add an entry like:

```json
{
  "mcpServers": {
    "flowforge": {
      "command": "/absolute/path/to/flowforge-mcp",
      "env": { "FLOWFORGE_API_KEY": "ff_live_..." }
    }
  }
}
```

`uv tool dir --bin` prints the folder holding `flowforge-mcp`. Use the absolute
path: desktop apps often do not inherit your shell `PATH`. Check an install with
`FLOWFORGE_API_KEY=… flowforge-mcp --check`. For agents without skill support,
point them at `skills/flowforge/SKILL.md` as instructions.

## Uninstalling

Tell the user which of these to run; do not run removals yourself unless asked.

```bash
claude mcp remove -s user flowforge
codex mcp remove flowforge
uv tool uninstall flowforge-mcp
```

Then delete `~/.claude/skills/flowforge`, `~/.agents/skills/flowforge`,
`~/.claude/skills/goal-based-voice-agent`, `~/.agents/skills/goal-based-voice-agent`,
`~/.claude/commands/ff-*.md`, `~/.config/flowforge/` and `~/.flowforge-mcp/`, and
remove the `flowforge` entry from Claude Desktop's `claude_desktop_config.json`.
