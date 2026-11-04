# FlowForge MCP setup, connectivity & maintenance

Read when `flowforge_*` tools are missing, auth/connection errors appear, or the
API docs changed.

## The MCP server

- Source: <https://github.com/RealboticsCorp/flowforge-mcp> (Python, FastMCP,
  stdio). `install.sh` installs it as the `flowforge-mcp` command with
  `uv tool install` (or into `~/.flowforge-mcp/venv` when uv is missing).
- Layout: `client.py` (auth, HTTPS-safe redirects, GET retries, error
  translation), `spec.py` + `data/openapi.json` (bundled spec index),
  `tools/*.py` (one module per area; `_dispatch.py` = shared action routing and
  confirm gate).
- Where clients keep the server entry (one entry per org key):
  - Claude Code: `~/.claude.json` → `mcpServers` (`claude mcp list`)
  - Claude Desktop: `~/Library/Application Support/Claude/claude_desktop_config.json`
    (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows)
  - Codex: `~/.codex/config.toml` → `[mcp_servers.<name>]` (`codex mcp list`)
- `~/.config/flowforge/servers.md` lists which server name maps to which org
  (written by `install.sh`).
- After updating, restart the client session (or reconnect the MCP server) —
  running sessions keep the old process.

## Install, update, add an org

From a clone of the repo:

```bash
FLOWFORGE_API_KEY=ff_live_… ./install.sh                          # first install, server "flowforge"
FLOWFORGE_API_KEY=ff_live_… ./install.sh --name flowforge-acme --server-only   # another org
git pull && ./install.sh --update                                 # update code + skill + commands
```

## Auth & host

- Header `X-API-Key: ff_live_…` from the `FLOWFORGE_API_KEY` env var in each
  server's config entry. Keys come from the FlowForge dashboard (Settings → API
  Keys) and are shown once.
- Host: `https://api.realbotics.ai/api/v1/external` (code default in `app.py`).
  Override with `FLOWFORGE_BASE_URL` only when Realbotics tells you to.
- Health: `flowforge_health`, or unauthenticated
  `GET https://api.realbotics.ai/api/v1/external/health` →
  `{"status":"ok","api":"external","auth":"api_key"}`.

## Errors

Tool errors read `Error: HTTP <code>. <cause + next step>. Details: <API detail>
request_id: <id>`. `flowforge_api_request` returns non-2xx as data
(`status`, `error`, `body`). Status meanings and retry rules:
[coding-against-api.md](coding-against-api.md#errors).

## Known server-side issues (observed 2026-11-03, report with request_ids)

| Endpoint | Symptom | MCP behaviour |
| --- | --- | --- |
| `GET /phone-numbers/search`, `/countries`, `/area-codes/{cc}` | 500 "Failed to …" even with no params | error surfaced; no fallback |
| `GET /billing/ledger` | 500 | falls back to `/billing/ledger.csv` rows |
| `GET /campaigns/{id}/calls` | 500 | falls back to `/calls/?campaign_id=` |
| `GET /assistants/`, `/campaigns/`, `/phone-numbers/`, `/tests/` | ignore `limit`/`offset` | paged client-side |
| collection routes without trailing slash | 307 with `http://` Location | redirects followed manually over HTTPS |

## Refreshing the API spec

The curated tools are hand-written; `flowforge_api_reference` /
`flowforge_api_request` read the bundled spec. When the docs change, in a clone:

```bash
uv run --with httpx python scripts/refresh_spec.py
```

It prints added/removed endpoints. New endpoints are reachable via
`flowforge_api_request` after reinstalling (`./install.sh --update`) and
restarting; add a curated tool only for ones agents use often.
