---
name: flowforge
description: Operate and build on the Realbotics FlowForge voice-agent platform through its MCP tools (flowforge_*) and External REST API. Use for any request mentioning FlowForge, voice agents/assistants, outbound or inbound calls, call transcripts/recordings, dialing campaigns, leads, dispositions, phone numbers or pools, knowledge bases, agent tests, branches, pronunciations, voice cloning, webhook or MCP tools for agents, usage/billing — and when writing code that calls api.realbotics.ai. Works in Claude Code and Codex. Pairs with the /ff-* slash commands.
---

# FlowForge (Realbotics) — voice agents via MCP + REST

## Overview

FlowForge runs AI voice agents ("assistants") that place and answer phone calls,
run campaigns, and ground answers in knowledge bases. Two ways in:

1. **MCP tools** `flowforge_*` (48 tools) — curated tools for common work, plus
   `flowforge_api_reference` and `flowforge_api_request`, which together reach
   **every one of the 160 External API endpoints**.
2. **REST** `https://api.realbotics.ai/api/v1/external`, header `X-API-Key: ff_live_…`
   — for code you write. Read [references/coding-against-api.md](references/coding-against-api.md)
   before writing integration code.

Tool-name prefix depends on the client: Claude Code `mcp__flowforge__flowforge_list_assistants`,
Codex `flowforge.flowforge_list_assistants` (or the `flowforge` server's tool list).
This skill uses the bare tool names.

## Which server = which org

Each FlowForge API key belongs to one organization, so each org gets its own MCP
server entry running the same code: `flowforge` (the default) plus optional
`flowforge-<org>` entries. If `~/.config/flowforge/servers.md` exists, read it: the
installer records there which server name maps to which org. Otherwise confirm with
`flowforge_get_organization` before doing anything that matters.

IDs are org-scoped: an ID from one server 404s on another. To copy an agent across
orgs: `flowforge_get_assistant include=["export"]` on the source server, then
`flowforge_import_assistant` on the target.

## Core rules

1. **Resolve IDs, never guess.** Tools take UUIDs. Use the matching list tool first.
2. **Real-world side effects need the user's go-ahead.** Calls ring real phones and
   cost money; buying numbers costs money; deletes are permanent. Gated tools return a
   `dry_run` preview until `confirm=true` — show the preview, get approval, then
   re-call. Ungated but still real: `flowforge_start_call`, `flowforge_start_batch_calls`,
   `flowforge_end_call`, `flowforge_control_campaign` (start/stop), `flowforge_delete_*`.
3. **Never blindly retry a call-starting write.** There are no idempotency keys; a
   retried `/calls/start` places a second call. On timeout or 5xx, look first:
   `flowforge_list_calls search=<number> date_from=<send time>`.
4. **Check the contract before writing.** Before a non-trivial create/update or any
   `flowforge_api_request`, run `flowforge_api_reference method=… path=…` for the exact
   body (trailing `*` = required). For webhook-tool and flow shapes, copy from an
   existing assistant (`flowforge_get_assistant detailed=true`).
5. **Arrays are replaced wholesale.** `webhook_tools`, `mcp_servers`,
   `knowledge_base_documents` on PATCH overwrite the whole list: read current, merge,
   write the merged list.
6. **Spend context carefully.** Use small `limit`s; follow `next_offset`. The org has
   100k+ calls, 200+ numbers, 150+ tests. `response_format="markdown"` for summaries.
7. **E.164 phone numbers** (`+14155551234`) everywhere.
8. **Errors are instructions.** They read `Error: HTTP <code>. <cause/next step>.
   Details: … request_id: …`. Fix 400/422 inputs; don't retry 401/402/403/404; quote
   the `request_id` when reporting a 500 to Realbotics.
9. **Change agents safely.** Branch (`flowforge_manage_branches create`) → edit the
   branch → run tests on it (`flowforge_run_test branch_id=…` / `flowforge_manage_tests
   run_all`) → poll `flowforge_get_test_run` → then publish/promote.

## Tool map

Full parameters: [references/tools.md](references/tools.md).

- **Full API access:** `api_reference` (search/describe any endpoint, offline),
  `api_request` (call any documented endpoint; confirm-gated), `health`
- **Assistants:** `list_assistants`, `get_assistant` (`detailed`, `include`:
  prompt-variables/flow/knowledge-base/stats/export), `create_assistant`,
  `update_assistant`, `delete_assistant`, `assistant_lifecycle` (clone/publish),
  `import_assistant`, `manage_branches`, `manage_pronunciations`
- **Voice:** `voice_catalog` (summary/tts/stt/presets/agent-presets/cloned), `clone_voice`
- **Calls:** `start_call`, `start_batch_calls` (≤100), `list_calls`, `get_call`
  (`include` transcript/metrics/events/recordings), `list_active_calls`, `end_call`
- **Campaigns:** `list_campaigns`, `create_campaign`, `get_campaign` (`include`
  analytics/status/leads/calls), `control_campaign`, `update_campaign_settings`,
  `add_campaign_leads` (≤1000/request), `remove_campaign_leads`,
  `manage_dispositions`, `list_campaign_calls`, `delete_campaign`
- **Numbers:** `list_phone_numbers`, `search_phone_numbers`, `assign_phone_number`,
  `manage_phone_number` (get/rename/purchase/release/countries/area_codes),
  `manage_phone_pools`
- **Knowledge:** `search_knowledge` (semantic or full-text), `list_documents`,
  `manage_documents` (upload file / import URL / link / reindex / delete),
  `manage_knowledge_bases`
- **Tests:** `list_tests`, `run_test`, `manage_tests`, `get_test_run`
- **Org & spend:** `get_organization`, `update_organization`, `manage_mcp_servers`,
  `get_usage` (current-month, by-*, forecast, insights, agents-efficiency,
  idle-phones, ledger), `get_balance`

Reach for `api_request` for: characters, roles, vapi-import, voice preview,
`/calls/{id}/events?event_type=`, campaign analytics with time ranges, and anything
newer than the bundled spec.

## Platform gotchas (bite every time)

- **Campaign won't start** until it has an agent, a phone number or pool, a schedule
  (outbound), and — if it has never run — an outcomes decision:
  `manage_dispositions action=keep_platform_defaults` or dispositions with `criteria`.
  Check with `action=outcomes_decision`.
- **Knowledge base attached but unused:** set `enable_rag_tool=true` (PATCH only;
  create ignores it) and tell the agent in its prompt when to search.
- **Post-call analysis** (`structuredData`, `successEvaluation`, captured variables)
  is delivered only by the end-of-call webhook — no endpoint returns it later.
- **Webhook tools** retry up to 3× on 5xx/timeouts → make write endpoints idempotent.
  Neither webhooks nor webhook tools are signed; authenticate with a header secret.
- **Test runs are async:** `run_test` returns `queued`; poll `get_test_run`.
- **Known server 500s (2026-11-03):** phone-number search/countries/area-codes,
  JSON ledger, campaign-scoped call list. The MCP falls back automatically for the
  last two (ledger.csv; `/calls/?campaign_id=`). Number search has no fallback —
  buy in the dashboard or retry later.

## Workflows & slash commands

Step-by-step recipes: [references/workflows.md](references/workflows.md). Slash
commands (Claude Code: `~/.claude/commands/ff-*.md`) are thin entry points:
`/ff-call`, `/ff-batch`, `/ff-call-review`, `/ff-campaign`, `/ff-campaign-status`,
`/ff-assistant`, `/ff-test`, `/ff-tool`, `/ff-usage`, `/ff-status`.

## Setup & troubleshooting

Server source, config locations for Claude Code and Codex, keys, host history and the
spec-refresh procedure: [references/api.md](references/api.md). If `flowforge_*`
tools are missing, the server is not running — start there. `flowforge_health`
confirms the host and bundled spec version.
