# FlowForge for coding agents

Give Claude Code, Codex or Claude Desktop full control of the
[Realbotics FlowForge](https://flowforge.docs.buildwithfern.com) voice-agent
platform: build and test AI phone agents, place calls, run campaigns, manage
numbers and knowledge bases, and read usage, from a chat with your agent.

## Install

Paste this into your coding agent:

> Install https://github.com/RealboticsCorp/flowforge-mcp

The agent follows [INSTALL.md](INSTALL.md). (**Coding agents:** read and follow
[INSTALL.md](INSTALL.md) step by step.) It will ask for your FlowForge API key
(dashboard → **Settings → API Keys**). Prefer to do it yourself:

```bash
git clone https://github.com/RealboticsCorp/flowforge-mcp.git ~/.flowforge-mcp/src
~/.flowforge-mcp/src/install.sh
```

Needs macOS or Linux with [uv](https://docs.astral.sh/uv/) or Python 3.10+.
Restart your agent afterwards.

## What you get

- **MCP server** (`flowforge-mcp`, 48 tools). Curated tools cover daily work, and
  `flowforge_api_reference` + `flowforge_api_request` reach all 160 External API
  endpoints using the API spec bundled with the server.
- **`flowforge` skill** teaches the agent the platform's rules and traps: which
  actions ring real phones or spend money, branch-then-test before publishing,
  campaign start requirements, knowledge-base flags, webhook-tool shapes, and how
  to write code against the REST API.
- **`goal-based-voice-agent` skill** designs a voice agent from an idea, call
  script or SOP using the SCRIPT framework, then deploys it to FlowForge (or
  VAPI): prompt, tools, voice and test plan.
- **Slash commands** for Claude Code: `/ff-call`, `/ff-batch`, `/ff-call-review`,
  `/ff-campaign`, `/ff-campaign-status`, `/ff-assistant`, `/ff-test`, `/ff-tool`,
  `/ff-usage`, `/ff-status`.

### Tool areas

- **Assistants:** list, get (prompt variables, flow, knowledge base, stats,
  export), create, update, delete, clone/publish, import, branches,
  pronunciations.
- **Voice:** TTS/STT catalog, presets, voice cloning.
- **Calls:** start, batch (≤100), list, get (transcript, metrics, events,
  recordings), active calls, end.
- **Campaigns:** create, control, settings, leads, dispositions and outcomes,
  campaign calls.
- **Phone numbers:** list, search, assign, purchase/release, pools.
- **Knowledge:** semantic and full-text search, document upload/URL import,
  knowledge bases.
- **Tests:** run, manage, read results.
- **Org and spend:** organization settings, MCP servers attached to agents, usage
  reports, balance.

## Safety

- Deletes and actions that dial, spend money or replace org-wide config return a
  `dry_run` preview until the agent repeats the call with `confirm=true`. The
  skill tells the agent to show you the preview and wait for your go-ahead.
- Requests other than GET are never retried automatically: FlowForge has no
  idempotency keys, so a retried call request would dial the person twice.
- Path IDs are validated, the API key never follows a redirect to another host,
  and file uploads refuse hidden paths such as `~/.ssh` or `.env`.
- Your key is stored only in each client's own MCP config.

## Several organizations

Each API key belongs to one organization. Install the first key as `flowforge`
and add more with:

```bash
FLOWFORGE_API_KEY=ff_live_… ~/.flowforge-mcp/src/install.sh --name flowforge-acme --server-only
```

The installer records which server belongs to which organization in
`~/.config/flowforge/servers.md`, and the skill reads that file.

## Configuration

| Variable | Required | Default |
| --- | --- | --- |
| `FLOWFORGE_API_KEY` | yes | — |
| `FLOWFORGE_BASE_URL` | no | `https://api.realbotics.ai/api/v1/external` |

## Development

```bash
uv run python -c "import asyncio; from flowforge_mcp.server import mcp; print(len(asyncio.run(mcp.list_tools())))"
FLOWFORGE_API_KEY=… uv run flowforge-mcp --check
uv run --with httpx python scripts/refresh_spec.py   # pull the latest API spec
```

```
flowforge_mcp/
  app.py          # FastMCP instance + constants
  client.py       # authenticated async HTTP client + error translation
  formatting.py   # JSON/Markdown rendering, truncation, pagination
  models.py       # shared Pydantic input mixins
  server.py       # entry point (--check verifies the install)
  spec.py         # index over data/openapi.json (bundled API spec)
  tools/          # one module per resource group; _dispatch.py = confirm gate
skills/          # agent skills: flowforge/, goal-based-voice-agent/
commands/         # Claude Code /ff-* slash commands
install.sh        # installer (see INSTALL.md)
```

Contributor rules: [AGENTS.md](AGENTS.md).

## License

MIT, see [LICENSE](LICENSE).
