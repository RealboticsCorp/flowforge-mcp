# FlowForge Configuration Reference

Reference for voice, LLM, transcriber, tool, and deployment configuration when deploying agents to **FlowForge**.

Use this when the user selected **FlowForge** as the deployment platform in Phase 0.25. For VAPI, see `vapi-config-reference.md`.

**Last verified against the live API: 2026-09-04**, by deploying a production agent end to end and diffing every field against `GET /assistants/{id}/detailed`.

> **Ground truth is the live API, not this file.** FlowForge's public docs lag the deployed API, and this reference has been wrong before. Before building any config, run
> `GET /assistants/{id}/detailed` on an existing agent in the target org and derive the shape from what comes back. Treat everything below as a starting point that still needs confirming.

---

## API Structure

FlowForge uses a **flat assistant config** — the system prompt lives directly on the assistant (`system_prompt`), and tools are configured via separate fields (`webhook_tools`, `system_tools_config`, `mcp_servers`). Structurally different from VAPI's nested `model.messages` + `model.toolIds`.

**Key differences vs VAPI:**
- `system_prompt` is a flat string, not nested in `model.messages[0].content`
- `model` is a flat, **provider-prefixed** string (see below)
- Tools are inline on the assistant — no separate "create tool then attach by ID" step
- snake_case (FlowForge) vs camelCase (VAPI)
- `agent_speak_first` (boolean) replaces VAPI's `firstMessageMode` enum

---

## Base URL

```
https://api.realbotics.ai/api/v1/external
```

Older docs and configs list other, retired hosts. Those return `404 {"status":"error","code":404,"message":"Application not found"}` for **every** request, even with a valid key. The failure looks like an auth or provisioning problem and is not; it is the wrong host.

The FlowForge MCP server in this repo uses this value by default (`flowforge_mcp/app.py`), overridable with the `FLOWFORGE_BASE_URL` env var. If calls start 404-ing again, re-read that constant before debugging anything else.

---

## Authentication

`x-api-key` header on every request.

```
x-api-key: <FLOWFORGE_API_KEY_<ORG>>
```

Keep keys in an untracked `.env`, namespaced per org (`FLOWFORGE_API_KEY_ACME`, `FLOWFORGE_API_KEY_GLOBEX`), or use the FlowForge MCP server, which holds one key per server entry. Keys are `ff_liv...`, 51 chars. Never hardcode, never echo a value into terminal output.

Keys are org-scoped — the wrong key silently operates on the wrong workspace. Confirm the org before writing anything.

---

## Endpoint Inventory

### Assistants
- `POST /assistants/` — create
- `GET /assistants/` — list
- `GET /assistants/{id}` — detail
- `GET /assistants/{id}/detailed` — **full agent + flow. This is your ground truth.**
- `PATCH /assistants/{id}` — partial update
- `DELETE /assistants/{id}` — delete
- `POST /assistants/{id}/clone` / `publish` / `export`, `POST /assistants/import`
- `GET /assistants/{id}/flow`, `/prompt-variables`, `/stats`
- `GET /assistants/{id}/knowledge-base` — **GET ONLY** (see Knowledge Bases)
- `GET|POST|PATCH|DELETE /assistants/{id}/pronunciations[...]`

### Calls
- `POST /calls/start`, `POST /calls/batch` (up to 100)
- `GET /calls/`, `/{id}`, `/{id}/transcript`, `/{id}/recordings`, `/{id}/metrics`, `/{id}/events`
- `GET /calls/dispositions`, `GET /calls/live/active`
- `DELETE /calls/{id}/end`, `POST /calls/end-all`

### Phone Numbers
- `GET /phone-numbers/search`, `/countries`, `/area-codes/{cc}`
- `POST /phone-numbers/purchase`
- `GET /phone-numbers/`, `/{id}`; `PATCH /{id}`; `DELETE /{id}`
- `POST /phone-numbers/{id}/assign-agent` / `unassign-agent`

### Knowledge
- `GET /knowledge/documents` — list (paginated: `documents`, `total`, `page`, `page_size`, `total_pages`)
- `POST /knowledge/documents/upload` — multipart `file=@path;type=<mime>`. Accepts **PDF, TXT, MD** only.
- `DELETE /knowledge/documents/{id}` — returns 204
- `GET /knowledge/knowledge-bases` — org KBs. A "Default" KB exists per org and uploads land in it automatically.
- `POST /knowledge/search` — body `{query, assistant_id, limit}`

### MCP / Custom Tools
- `GET /mcp-tools/servers`, `/servers/{id}/tools`, `/orgs/mcp-servers`
- `PUT|DELETE /mcp-tools/orgs/mcp-servers[...]`
- `GET|POST /mcp-tools/custom`, `POST /mcp-tools/custom/{id}/test|call`, `DELETE /mcp-tools/custom/{id}`

### Endpoints that do NOT exist on the external API
`/voices`, `/tts/voices`, `/models`, `/organizations/voices`, `/organizations/me`, `/documents/`, `/knowledge-bases/` — all 404. **There is no way to enumerate available voices or models through this API.** Discover both by reading an existing assistant in the org, or from the FlowForge UI.

---

## `model` — provider-prefixed string

**CORRECTION:** this file previously showed bare identifiers like `"gpt-4o-mini"`. The live API uses a `provider:model` form.

Verified working: `openai:gpt-4.1`, `openai:gpt-4.1-mini`, `groq:qwen/qwen3-32b` (the default on a freshly provisioned assistant).

House precedent: `openai:gpt-4.1-mini` at `temperature: 0.4` for a straightforward agent; `openai:gpt-4.1` when branching is heavy or the domain vocabulary is dense. `temperature` is `null` on a new assistant — set it explicitly.

There is no models endpoint. To confirm a model string is accepted, PATCH it and re-fetch — a rejected value will not persist.

---

## `system_tools_config` — objects, not booleans

**CORRECTION:** this file previously documented `{"end_conversation": true, "transfer_call": false}`. Both the shape and the key names were wrong. Every value is an **object with an `enabled` flag**, and there is no `transfer_call` key.

Live shape from a freshly provisioned assistant:

```jsonc
{
  "send_sms":            { "enabled": false },
  "send_dtmf":           { "enabled": false },
  "skip_turn":           { "enabled": false },
  "knowledge_base":      { "enable_read_tool": true },        // NOTE: not "enabled"
  "end_conversation":    { "enabled": false, "cancels_speech": true },
  "variable_capture":    { "mode": "free", "enabled": false, "variables": [] },
  "transfer_to_agent":   { "enabled": false, "destinations": [] },
  "transfer_to_number":  { "enabled": false, "destinations": [], "allow_any_number": false },
  "voicemail_detection": { "enabled": false }
}
```

Notes that matter:

- **SMS is first-class.** `send_sms` is a built-in system tool. This file previously claimed FlowForge had no SMS tool and that you must build a Twilio webhook. That was wrong.
- **`transfer_to_number` is the warm-transfer mechanism**, carrying its own `destinations[]` and an `allow_any_number` guard. `transfer_to_agent` is agent-to-agent, with `destinations[]` entries shaped `{agent_id, agent_name, context_mode, transfer_mode, handoff_message, variables_to_capture, ai_routing_description}`.
- **`knowledge_base.enable_read_tool` uses a different key name** than every other entry. It is how the agent is allowed to read the KB at all — preserve it when patching.
- `end_conversation.cancels_speech` and `variable_capture.mode`/`variables` are easy to clobber. **Always start from the live object and mutate it**, never rebuild this field from scratch.

---

## `webhook_tools[]` — `bodyParams`, not JSON Schema

**CORRECTION:** this file previously showed a JSON-Schema `parameters` object. The live API uses a flat `bodyParams` array.

```jsonc
{
  "id": "webhook_111e9bb5ee5e",            // arbitrary but must be unique
  "name": "check_availability",
  "url": "https://n8n.example.com/webhook/<uuid>",
  "method": "POST",
  "headers": [],
  "description": "Told to the LLM: what it does, when to call it, and what to do when it fails.",
  "bodyParams": [
    { "name": "action",     "type": "string", "required": false, "description": "...", "defaultValue": "get_availability" },
    { "name": "start_time", "type": "string", "required": true,  "description": "ISO 8601 ..." }
  ],
  "executionMode": "await",
  "preToolSpeech": "auto",                 // "auto" | "none"
  "responseTimeout": 20,
  "disableInterruptions": true
}
```

**Proven pattern:** point several tools at **one** webhook URL and discriminate with an `action` param carrying a `defaultValue`. One n8n workflow with a Switch node then serves the whole agent. Used in production by several FlowForge orgs.

Put failure guidance in `description` — the LLM reads it. "If this returns zero results, do not retry more than twice; fall back to taking a message" belongs there, not only in the prompt.

---

## `tts_settings` — org-scoped voice catalogue

```jsonc
{
  "provider": "elevenlabs",
  "model": "eleven_turbo_v2_5",
  "voice": "<voice-id>",
  "voices": [ { "id": "elevenlabs-<voice-id>", "name": "...", "provider": "elevenlabs",
                "model": "eleven_turbo_v2_5", "voice": "<voice-id>",
                "settings": { "style": 0, "stability": 0.5, "similarity_boost": 0.75,
                              "use_speaker_boost": true, "enable_ssml_parsing": false },
                "isPrimary": true } ],
  "settings": { /* same object as the primary voice's settings */ }
}
```

**Voice IDs are org-scoped.** A voice registered in one org is not available in another — a new org needs its own. On a freshly provisioned assistant `settings` is `{}`; fill it explicitly. Raise `stability` (0.6-0.7) for a composed register, keep `style: 0` unless you want expressiveness.

There is no voice catalogue endpoint and no way to read a voice's gender or characteristics through the API. **You cannot verify a voice by ID — you have to listen to it.** Flag this for a human ear check rather than assuming.

---

## `stt_settings`

```jsonc
{
  "provider": "deepgram",
  "model": "flux-general-en",
  "language": "en",
  "languages": [ { "code": "en", "name": "English", "model": "flux-general-en",
                   "provider": "deepgram", "isDefault": true } ],
  "turn_detection": "stt"
}
```

`languages[]` holds **objects**, not ISO strings. `turn_detection` is undocumented but present — preserve it. House configs also carry `settings: { eager_eot_threshold: 0.7, stop_speaking_num_words: 4 }`.

`flux-general-en` is the house default for latency. Consider `nova-3` for calls dense in alphanumerics (site codes, units, bandwidth figures) — accuracy there is worth the latency.

---

## Fields present in the live API but absent from the docs

All of these are real and settable. Ignoring them leaves aggressive or wrong defaults in place.

**Backchannels** — `backchannels_enabled`, `backchannel_listening_enabled`, `backchannel_thinking_mode` (`"melody"` and `"side_track"` both observed), `backchannel_phrases[]`, `thinking_filler_phrases[]`, `backchannel_tuning` (`{listening: {phrases:[{text,weight}], selection:"weighted", max_per_turn}, thinking_melody: {pace_ms, phrases:[...]}}`).

These are the native complement to the prompt-level filler system in `filler-disfluency-patterns.md`. Enable `backchannel_listening_enabled` for inbound agents who listen to long explanations; it suits a listener role better than an outbound pitcher.

**Inactivity** — `inactivity_check_interval_seconds`, `inactivity_initial_grace_seconds`, `inactivity_prompts[]`, `inactivity_ends_call`. A new assistant defaults to a **5-second** check interval, which interrupts any caller who pauses to think. House value is 30 with a 3-second grace.

**Reporting and evaluation** — these are FlowForge's answer to VAPI scorecards and the main reason to bother with a structured brief:
- `end_of_call_report_config`: `{enabled, server_url, headers, include_items:{metrics, recording, transcript, structured_data, captured_variables, success_evaluation}, timeout_seconds, auth_credential_id}`
- `structured_data_config`: `{enabled, prompt, timeout_seconds, schema_fields:[{name, type, is_enum, required, description, enum_values}]}`
- `success_evaluation_config`: `{enabled, prompt, gating_mode, rubric_type:"checklist", checklist_items:[{criterion, weight, required, gating_role}]}`

Map `structured_data_config.schema_fields` to the capture sheet and `success_evaluation_config.checklist_items` to the R-section KPIs. Give redline compliance the highest weight and `gating_role: "required"`.

Also live: `character_id`, `role_id`, `default_personality`, `slug`, `run_count`, `organization_id`.

---

## Knowledge Bases

Uploads land in the org's **Default** knowledge base automatically. There is no need to create one.

1. `POST /knowledge/documents/upload`, multipart, one file per call. PDF, TXT, MD only.
2. Link to the assistant. **`/assistants/{id}/knowledge-base` is GET-only** — `PATCH`, `POST`, and `PUT` all return 405, and the route's `Allow` header confirms `GET`. Link through the assistant instead:

```
PATCH /assistants/{id}   {"knowledge_base_documents": ["<doc-id>", ...], "enable_rag_tool": true}
```

3. Verify with `GET /assistants/{id}/knowledge-base` — expect `enable_rag_tool: true` and a populated `knowledge_base_documents`.
4. Note `enable_rag_tool` (assistant-level, gates retrieval) is a **different flag** from `system_tools_config.knowledge_base.enable_read_tool`. Set both.

### KNOWN BREAKAGE — uploads do not embed (as of 2026-09-04)

Documents uploaded through the API reach `status: "ready"` but stay at `chunk_count: 0` and `has_embeddings: false`, and `POST /knowledge/search` returns zero results for them.

Verified across both a brand-new org and an established one, and across MD, TXT, and PDF. PDFs briefly enter `status: "processing"` before landing at `ready` with no chunks; MD and TXT skip `processing` entirely. Pre-existing documents in an older org do have embeddings (263 chunks), so the pipeline worked at some point — this is a regression in the ingestion path, not org provisioning and not a file-type restriction.

**Consequences for the build:**
- Do not architect an agent that depends on KB retrieval for anything load-bearing until this is fixed. Verify with `POST /knowledge/search` before trusting it.
- Keep every redline, refusal rule, and high-frequency fact **in the system prompt**, where retrieval cannot fail. Use the KB only for depth the agent can afford to lose.
- After uploading, always check `chunk_count > 0` and `has_embeddings: true`. `status: "ready"` alone means nothing.

---

## First Message Behavior

- `agent_speak_first: true` + `first_message: "..."` → outbound, or an inbound agent that greets on pickup
- `agent_speak_first: false` → wait for the caller to speak first
- `first_message_interruptible: true` and `allow_interruptions: true` → natural barge-in, recommended

No `model-generated` mode. For a dynamic greeting, use `{{variables}}` in `first_message`.

---

## Pronunciations

Per-assistant overrides at `/assistants/{id}/pronunciations`. Use for brand names, technical terms, and names the TTS mangles, instead of forcing spelling hacks into the prompt. Note the prompt should still spell out acronyms the agent must say as letters.

---

## Deployment Sequence

1. Confirm `FLOWFORGE_API_KEY_<ORG>` is in `.env` and matches the intended org.
2. **Read an existing assistant** in that org via `GET /assistants/{id}/detailed` and derive your config shape from it.
3. `POST /assistants/` with the full body, or `PATCH` an already-provisioned skeleton.
4. Upload KB documents, link via assistant PATCH, then **verify chunks and embeddings actually exist**.
5. `GET /phone-numbers/` or search + purchase.
6. `POST /phone-numbers/{id}/assign-agent`.
7. `POST /assistants/{id}/publish` (optional).
8. `POST /calls/start`, then read `/transcript`, `/recordings`, `/metrics`, `/events`.

Injecting a long prompt without pasting it through the shell:

```bash
jq --rawfile p prompt.md '.system_prompt = $p' config.json > /tmp/payload.json
curl -s -X POST "$BASE/assistants/" -H "x-api-key: $KEY" \
     -H 'content-type: application/json' -d @/tmp/payload.json
```

---

## Iteration Pattern (PATCH Safety)

`PATCH /assistants/{id}` takes a partial body. Easier than VAPI's full-model replacement, but it makes silent drift easy.

1. `GET /assistants/{id}/detailed` first — capture full current state.
2. Diff intended changes against it.
3. For nested objects (`system_tools_config`, `tts_settings`, `stt_settings`), **mutate the live object rather than rebuilding it**, or you will drop fields like `cancels_speech`, `turn_detection`, and `knowledge_base.enable_read_tool`.
4. PATCH only what should change.
5. **Re-fetch and assert.** A `200` is not confirmation. Verify the prompt landed byte-exact (sha256 against your local file), the model string persisted, tool counts match, and the locked decisions still hold.

For anything beyond a wording tweak, run the **Lossless Conversion Protocol** (`references/lossless-conversion-protocol.md`).

---

## Pre-Deployment Checklist

- [ ] Base URL is `api.realbotics.ai`, not an older, retired host
- [ ] `FLOWFORGE_API_KEY_<ORG>` matches the intended org, and is not committed
- [ ] `system_prompt` is the full SCRIPT prompt, no decorative emojis (Key Principle #10)
- [ ] `model` is provider-prefixed and confirmed to persist after a re-fetch
- [ ] `temperature` set explicitly (defaults to `null`)
- [ ] `tts_settings.settings` populated (defaults to `{}`), voice confirmed **by listening**
- [ ] `stt_settings` keeps `turn_detection` and the `languages[]` object shape
- [ ] `system_tools_config` derived from live state; `end_conversation.enabled` true; `knowledge_base.enable_read_tool` preserved
- [ ] Transfer tools deliberately set, not left at whatever the skeleton had
- [ ] `inactivity_check_interval_seconds` raised from the 5-second default
- [ ] Every prompt-referenced tool exists in `webhook_tools[]`, and every entry has a prompt instruction
- [ ] `structured_data_config` and `success_evaluation_config` populated, or consciously skipped
- [ ] KB documents show `chunk_count > 0` and `has_embeddings: true`, and `POST /knowledge/search` returns hits
- [ ] `agent_speak_first` matches inbound vs outbound intent
- [ ] Phone number assigned via `assign-agent`

---

## Multi-Agent / Squad Equivalence

No 1:1 equivalent of VAPI's silent `handoff` with `contextEngineeringPlan` and `variableExtractionPlan`. Two paths:

1. **Flow-based agent (`flow_data`)** — a ReactFlow graph with branches, conditionals, and tool nodes. FlowForge's first-class multi-stage pattern.
2. **`system_tools_config.transfer_to_agent`** — agent-to-agent transfer with `context_mode` (e.g. `full_history`), `transfer_mode` (e.g. `in_session`), `handoff_message`, `variables_to_capture`, and `ai_routing_description` telling the LLM when to route. Closer to VAPI's handoff than this file previously suggested, though without structured variable extraction.

If silent handoff with structured extraction is a hard requirement, deploy that agent on **VAPI**.

---

## When to Choose FlowForge vs VAPI

**FlowForge** when: the user prefers a flatter API; the agent is one prompt plus a few webhook tools; flow-based authoring fits; a FlowForge org and key already exist.

**VAPI** when: silent multi-agent handoffs with structured variable extraction are needed; first-class scorecards and monitoring matter; the broadest provider matrix is needed; **or the agent depends on knowledge-base retrieval** while the ingestion regression above is unresolved.

Default to whatever the workspace already uses — check `.env` for `FLOWFORGE_API_KEY_<ORG>` vs VAPI credentials.
