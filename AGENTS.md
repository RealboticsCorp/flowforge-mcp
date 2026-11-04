# flowforge-mcp — agent guide

MCP server (Python, FastMCP, stdio) exposing the Realbotics FlowForge External API
(`https://api.realbotics.ai/api/v1/external`, `X-API-Key`) to Claude Code, Claude
Desktop and Codex. Users of the tools should load the `flowforge` skill
(`skills/flowforge/`, installed to `~/.claude/skills/` and `~/.agents/skills/` by
`install.sh`); this file is for changing the server itself. Installing for a user:
[INSTALL.md](INSTALL.md).

## Layout

- `flowforge_mcp/app.py` — FastMCP instance, base URL, key env var, timeout.
- `flowforge_mcp/client.py` — the only network path: `api_send` (status + body,
  never raises on HTTP errors) and `api_request` (raises `FlowForgeHTTPError`).
  Handles HTTPS-only manual redirects, GET-only retries on 500/502/503, multipart,
  and `format_error` (status hint + API detail + `request_id`).
- `flowforge_mcp/spec.py` + `data/openapi.json` — bundled OpenAPI index used by
  `flowforge_api_reference` and to validate `flowforge_api_request`.
- `flowforge_mcp/tools/` — one module per area. Action-style "manage" tools build
  a `Route` and call `_dispatch.execute`, which applies the confirm gate.
- `scripts/refresh_spec.py` — re-download the spec and print endpoint diffs.

## Rules

- Never retry non-GET requests: the API has no idempotency keys, and a retried
  `POST /calls/start` places a second real call.
- Anything that dials phones, spends money, drops live calls, deletes, or replaces
  org-wide config must be confirm-gated (`gated=True` on the `Route`, or listed in
  `tools/api.py::_GATED_OPERATIONS`). Keep the existing ungated legacy tools
  (`start_call`, `start_batch_calls`, `end_call`, `control_campaign`, `delete_*`)
  ungated so current users' flows don't break; the skill tells agents to confirm.
- Match request bodies and query names to the spec. Check with
  `uv run python -c "from flowforge_mcp import spec; import json; print(json.dumps(spec.describe(spec.match('POST','/tests/x/run'), include_response=False), indent=1))"`.
- Collection endpoints that ignore `limit`/`offset` (assistants, campaigns,
  phone-numbers, tests) are paged client-side with `formatting.local_page`.
- Use the collection trailing slash (`assistants/`) to avoid the 307 hop.
- Never print or commit API keys. Keys live only in client configs
  (`~/.claude.json`, Claude Desktop config, `~/.codex/config.toml`).
- New tool: add it to the right module (or a new module imported in
  `tools/__init__.py`), then update `skills/flowforge/references/tools.md`, re-run
  `./install.sh --update` to copy the skill locally, and bump the version in
  `pyproject.toml` and `flowforge_mcp/__init__.py`.

## Verify

```bash
uv run python -m py_compile flowforge_mcp/*.py flowforge_mcp/tools/*.py
uv run python -c "import asyncio; from flowforge_mcp.server import mcp; print(len(asyncio.run(mcp.list_tools())))"
```

Live checks: read-only GETs and dry runs only (gated actions without `confirm`).
Do not place calls, buy numbers, start campaigns or delete anything to test.
Restart the client session after changes; running sessions keep the old process.
