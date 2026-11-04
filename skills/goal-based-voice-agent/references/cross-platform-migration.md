# Cross-Platform Migration & Mirror Sync (VAPI ⇄ FlowForge)

Two-way migration of voice agents between **VAPI** and **FlowForge**, plus parallel-update sync to keep a 1:1 mirror of a single agent on both platforms.

Use this protocol when the user asks to:
- Move an existing agent from one platform to the other ("migrate Riley from VAPI to FlowForge").
- Set up a mirror so an agent runs on both platforms simultaneously ("clone Casey onto FlowForge and keep them in sync").
- Apply a single change (prompt edit, tool addition, voice swap) to both halves of an existing mirror in one operation.

This protocol always runs **on top of** the [Lossless Conversion Protocol](lossless-conversion-protocol.md) — you must inventory the source state, categorize functionality, and diff-check before any cross-platform operation. Cross-platform adds a second concern: **mapping fidelity** between two structurally different config shapes.

---

## When to mirror vs migrate vs stay single-platform

Three operating modes — pick one explicitly with the user before doing any work.

**Migrate (one-time)** — move an agent from one platform to the other and decommission the source.
- Use when: the source platform no longer fits the use case, costs are prohibitive, or the user is consolidating onto a single vendor.
- Source agent gets archived (not deleted) until the destination is verified in production.

**Mirror (ongoing 1:1 sync)** — run the same agent on both platforms in parallel, keeping them functionally equivalent.
- Use when: failover/redundancy is required, the user is A/B testing platforms, or different phone numbers route to different platforms but should behave identically.
- Updates are applied to **both** agents in a single operation (see "Parallel Update" below).
- Drift between mirrors is treated as a defect — diff-check on every change.

**Single-platform** — stay on one platform.
- Default. Don't recommend mirroring or migrating unless the user has an explicit reason. Mirroring doubles the surface area of every change.

---

## Feature Parity Matrix

Before migrating or mirroring, map every functional element of the source to the destination. Anything in the "no equivalent" column means a **structural blocker** the user must resolve before the operation can proceed.

### Identity & Persona
- **Agent name** — both platforms support; copy verbatim. VAPI: `name` (≤40 char). FlowForge: `name`.
- **Description** — VAPI: not a first-class field (lives in metadata). FlowForge: `description`.
- **System prompt / SCRIPT** — VAPI: `model.messages[0].content`. FlowForge: `system_prompt`. Direct copy.
- **First message** — VAPI: `firstMessage`. FlowForge: `first_message`. Direct copy.
- **Speaks-first behavior** — VAPI: `firstMessageMode` (enum: `assistant-speaks-first`, `assistant-waits-for-user`, `assistant-speaks-first-with-model-generated-message`). FlowForge: `agent_speak_first` (boolean) + `first_message`. Mapping: `assistant-speaks-first` → `agent_speak_first: true`; `assistant-waits-for-user` → `agent_speak_first: false`. **Blocker:** `assistant-speaks-first-with-model-generated-message` has no FlowForge equivalent — convert to `agent_speak_first: true` with a `first_message` template using `{{variables}}`, and document the loss to the user.

### LLM
- **Provider + model** — VAPI: `model.provider` + `model.model` (nested). FlowForge: `model` (flat string identifier). Mapping: `openai/gpt-4.1` → `"gpt-4.1"`, `anthropic/claude-sonnet-4.6` → `"claude-sonnet-4.6"`, etc. Confirm the destination platform supports the exact model id; substitute the closest equivalent if not (and document).
- **Temperature** — VAPI: `model.temperature`. FlowForge: `temperature`. Direct copy.

### Voice (TTS)
- **Provider + voice ID** — VAPI: `voice.provider` + `voice.voiceId` (+ optional `voice.model`). FlowForge: `tts_settings.provider` + `tts_settings.voice` (+ optional `tts_settings.model`). Mapping is direct for ElevenLabs, OpenAI, Cartesia, Deepgram, PlayHT. **Blocker:** if the source uses a provider only one platform supports (e.g. VAPI's `vapi`-native voices, Hume EVI2, Inworld, WellSaid, Rime, Azure on VAPI side), the destination has no equivalent — pick the closest provider/voice and document the swap.
- **Voice clones** — Custom voice IDs are tied to the provider's account, not the platform. If the same provider key is connected to both platforms, the same clone ID works in both. Otherwise the clone needs to be uploaded to the destination provider account first.

### Transcription (STT)
- **Provider + model + languages** — VAPI: `transcriber.provider` + `transcriber.model`. FlowForge: `stt_settings.provider` + `stt_settings.model` + `stt_settings.languages`. Mapping is direct for Deepgram (Nova-3, Flux), Cartesia (Ink-Whisper). FlowForge requires `languages` array — default to `["en"]` if VAPI source did not specify.

### Tools
This is where the highest fidelity loss happens. Map every source tool to the destination shape:
- **VAPI `endCall`** → **FlowForge `system_tools_config.end_conversation: true`**.
- **VAPI `transferCall`** → **FlowForge `system_tools_config.transfer_call: true`** + destination configured at the phone-number routing or flow layer (FlowForge does not store destination numbers per-tool the way VAPI does — this is a structural move).
- **VAPI `sms`** (Twilio `from` number) → **FlowForge `webhook_tools[]` entry calling Twilio's API directly**. FlowForge has no first-class SMS tool; you build a webhook tool with the Twilio endpoint, headers (basic auth or API key), and a JSON schema for `to`/`body`. Document the auth credential needed.
- **VAPI `function`** (server URL + JSON schema) → **FlowForge `webhook_tools[]` entry** with same `url`, `method`, `headers`, and `parameters` JSON schema. Direct shape conversion.
- **VAPI `apiRequest`** → **FlowForge `webhook_tools[]` entry**. Same as function tool.
- **VAPI `mcp`** → **FlowForge `mcp_servers[]`** (server ID from org allow-list). Confirm the destination FlowForge org has the MCP server allow-listed; if not, add via `PUT /mcp-tools/orgs/mcp-servers` first.
- **VAPI `dtmf`** → **No FlowForge equivalent as a tool**. Move to a `flow_data` node or a webhook that triggers Twilio `<Play>`. **Blocker** for prompt-based FlowForge agents.
- **VAPI `voicemail`** → handled at call-start level on FlowForge (`POST /calls/start` payload), not as an assistant tool. Migrate by setting voicemail-detection options on outbound calls instead.
- **VAPI `google.calendar` / `google.sheets` / `slack`** → **FlowForge `webhook_tools[]` entries** wrapping the respective service APIs (or `mcp_servers[]` if a Google/Slack MCP server is allow-listed in the FlowForge org). FlowForge does not ship first-class OAuth integrations for these.
- **VAPI `handoff`** (silent multi-agent handoff with `contextEngineeringPlan` + `variableExtractionPlan`) → **No 1:1 FlowForge equivalent**. Migrate by either: (a) collapsing the squad into a single FlowForge `flow_data` graph with branch nodes; (b) keeping the multi-agent split but using telephony-layer warm transfer (breaks the silent UX); or (c) keeping that specific agent on VAPI and only migrating the rest. **This is the most common migration blocker** — flag to the user immediately.

### Knowledge Bases
- VAPI: KBs attached via `model.knowledgeBaseId` or query tools. FlowForge: documents uploaded → KB created → linked via the assistant KB endpoint. Migration requires re-uploading documents to the destination platform; KB IDs do not transfer.

### Voicemail / Inbound Behavior
- VAPI: `firstMessageMode: assistant-waits-for-user` for inbound. FlowForge: `agent_speak_first: false`. Direct map.

### Compliance / Observability
- VAPI: `compliancePlan.hipaaEnabled`, `compliancePlan.pciEnabled`, scorecards via `artifactPlan.scorecardIds`, monitors via the monitors API. FlowForge: HIPAA/PCI configured at the org level (not per-assistant); structured outputs / scorecards via `structured_data_config` + `success_evaluation_config`; monitoring via the calls/events endpoints. **Migration requires reconfiguring observability from scratch on the destination** — the IDs and shapes do not transfer.

### Phone Numbers
- Phone numbers belong to the platform that owns the Twilio (or other carrier) integration. **Numbers do not transfer** between platforms. Migration requires either:
  - **Number porting** through Twilio (slow, days-to-weeks) if the user wants the same DID on the destination platform; OR
  - **Acquiring a new number** on the destination platform and updating any external systems (CRM, marketing, signage) that reference the old number.
  - For mirrors: each platform owns its own DID. Calls route to whichever DID the caller dialed.

---

## Phase M0: Pre-Migration Inventory (REQUIRED)

Before touching the destination platform, build a complete inventory of the source agent. Reuse the [Lossless Conversion Protocol](lossless-conversion-protocol.md) Step 1 ("Inventory the source state") and extend it with cross-platform mapping notes.

1. **Fetch the deployed source state.**
   - VAPI: `GET /assistant/{id}` → capture full assistant JSON, plus `GET /tool/{id}` for every tool in `model.toolIds`.
   - FlowForge: `GET /assistants/{assistant_id}/detailed` → returns full assistant + flow + KB attachments + tool config in one call.
2. **Run through the Feature Parity Matrix above** — for each section, write down the source value and the destination mapping. Flag every "no equivalent" or "structural blocker" item.
3. **Save the inventory** to the project as `./voice-agents/{agent-name}/migration-inventory.md`. This becomes the audit trail.
4. **Surface blockers to the user before continuing.** Do not silently drop functionality. Common blockers:
   - VAPI silent handoffs (squad → FlowForge) with no `flow_data` plan.
   - VAPI `dtmf` tool (no FlowForge prompt-based equivalent).
   - Provider-specific voice or transcriber not supported on the destination.
   - OAuth-based integrations (Google Calendar/Sheets, Slack) that need re-auth on the destination.
   - Phone number portability decisions.

If the user accepts the blockers (with explicit acknowledgment of each), proceed. Otherwise stop and resolve.

---

## Phase M1: Migration (One-Way: VAPI → FlowForge)

After inventory.

1. **Generate the FlowForge config** from the inventory using `assets/flowforge-agent-config-template.json`. Field-for-field translation per the Feature Parity Matrix.
2. **Pre-deploy the destination support resources:**
   - Add any required MCP servers to the FlowForge org allow-list (`PUT /mcp-tools/orgs/mcp-servers`).
   - Upload any KB documents and create the KB.
   - Acquire a destination phone number (if not porting): `POST /phone-numbers/purchase` or pick from `GET /phone-numbers/`.
3. **Create the FlowForge assistant:** `POST /assistants/` with the full body. Capture the returned `assistant_id`.
4. **Link the KB** (if applicable) to the new assistant.
5. **Assign the phone number:** `POST /phone-numbers/{id}/assign-agent` with the new assistant ID.
6. **Test the destination:** `POST /calls/start` with a test customer number. Inspect transcript, recording, metrics, and events. Walk through every branch and tool call from the source agent.
7. **Run the diff-check:** open the source VAPI agent and the new FlowForge agent side by side. For every section of the Feature Parity Matrix, confirm the destination behaves equivalently. Document any deviations.
8. **Cutover:** update any external systems (CRM webhooks, marketing materials, signage) to point at the new FlowForge phone number. If porting, schedule the port and cut over when the port completes.
9. **Decommission the source:** do **not** delete. Either disable inbound on the source phone number, or unassign the source agent from its number. Keep the agent record for at least 30 days as a rollback target.
10. **Document removals:** anything intentionally dropped (silent handoffs collapsed into a flow, dtmf removed, etc.) goes into a `migration-deviations.md` next to the inventory.

## Phase M1: Migration (One-Way: FlowForge → VAPI)

Same shape as VAPI → FlowForge, with the field mappings inverted:

1. **Generate the VAPI config** from the inventory using `assets/agent-config-template.json`. The `system_prompt` becomes `model.messages[0].content`. `tts_settings` / `stt_settings` become nested `voice` / `transcriber` objects. `webhook_tools[]` entries become VAPI `function` tools that must be **created first via the tool registry** (`mcp__vapi-mcp__create_tool` or REST), capturing returned IDs to put in `model.toolIds`. `system_tools_config.end_conversation` becomes a separate `endCall` tool entry. `system_tools_config.transfer_call` becomes a `transferCall` tool with the destination number(s) confirmed with the user.
2. **Pre-deploy:** create every tool first, capture IDs.
3. **Create the VAPI assistant:** `mcp__vapi-mcp__create_assistant` with the nested model object including `toolIds`. Capture the assistant ID.
4. **Acquire / assign a VAPI phone number.**
5. **Test the destination, run the diff-check, cutover, decommission, document removals** — same as the VAPI → FlowForge direction.

**Migration-direction-specific notes:**
- FlowForge → VAPI **gains** silent multi-agent handoff capability. If the source was a `flow_data` graph, you can choose to either (a) keep it as a single VAPI assistant with branch-style instructions, or (b) split it into a VAPI squad with `handoff` tools. Recommend (b) when the flow has 3+ distinct phases with different objectives.
- VAPI → FlowForge **loses** silent multi-agent handoff. If the source is a squad, the user must choose `flow_data` modeling, telephony-layer transfer (warm), or keeping the squad on VAPI.

---

## Phase M2: Mirror Setup (Both Platforms in Parallel)

A mirror runs the same agent on both platforms simultaneously. Setup:

1. **Run M0 (inventory) on whichever platform has the source.** If neither does (a brand-new agent), build the SCRIPT prompt first via the standard skill phases 0-7, then mirror to both platforms in parallel.
2. **Generate both configs from the same inventory.** Both must derive from a single source-of-truth artifact set:
   ```
   ./voice-agents/{agent-name}/
   ├── prompt.md                  # Single source of truth — the SCRIPT prompt
   ├── inventory.md               # Feature Parity Matrix mapping (source state)
   ├── vapi/
   │   └── config.json            # VAPI-shape config derived from prompt.md + inventory.md
   ├── flowforge/
   │   └── config.json            # FlowForge-shape config derived from prompt.md + inventory.md
   └── deviations.md              # Any intentional drift between the two (should be near-empty for a true mirror)
   ```
3. **Deploy both:**
   - VAPI: tools first, then assistant, then phone-number assignment (Phase 10A).
   - FlowForge: assistant first (tools inline), then phone-number assignment (Phase 10B).
4. **Capture both assistant IDs and both phone numbers** in `inventory.md` under a "Live Deployment" section.
5. **Test both** with the same test-call script. The behavior should be observationally identical from the caller's perspective.
6. **Document any unavoidable deviations** in `deviations.md`. Common unavoidable items:
   - Voice provider/voice ID differences (when one provider isn't supported on one platform).
   - Compliance flag locations (per-assistant on VAPI, org-level on FlowForge).
   - Squad vs flow-based execution if the agent has multi-stage logic.
7. **Set up monitoring on both platforms** so drift in production behavior (e.g. one platform's call success rate diverging from the other) shows up in dashboards.

**Routing patterns for mirrors:**
- **A/B test:** different phone numbers route to each platform; compare KPIs.
- **Failover:** primary number on one platform, secondary on the other; failover triggered manually or via Twilio routing if the primary platform errors.
- **Geographic split:** different regional numbers route to different platforms (e.g. US numbers on FlowForge, EU on VAPI).

---

## Phase M3: Parallel Update (Sync Edits Across the Mirror)

When the user requests a change ("update Sarah's pitch beat", "add a new webhook tool for CRM lookup"), apply it to **both** mirrors in a single operation. Drift is the enemy.

### Update sequence

1. **Restate the change** to the user and confirm scope: "Updating both the VAPI and FlowForge mirrors of {agent-name}. Change: {summary}." Get explicit confirmation before touching either platform.
2. **Run the [Lossless Conversion Protocol](lossless-conversion-protocol.md)** — this is mandatory for any mirror update beyond a single wording tweak. Inventory both deployed states. Categorize what's changing. Declare scope.
3. **Edit the source-of-truth artifact first.** If the change is prompt-related, edit `prompt.md`. If it's a tool addition, decide which artifact owns the tool definition and edit there.
4. **Translate the change into both config shapes.** Update `vapi/config.json` and `flowforge/config.json` in the same commit. Diff them against the previous version locally before deploying.
5. **Deploy to both platforms in parallel:**
   - VAPI: fetch current assistant, replace the changed model fields, PATCH with **complete model object** (never partial PATCH on `model`). For tool additions: create the new VAPI tool first, capture ID, then PATCH `model.toolIds`.
   - FlowForge: PATCH `/assistants/{assistant_id}` with **only the changed fields** (FlowForge accepts partial PATCH). For webhook tool additions: include the updated `webhook_tools[]` array.
   - Run both PATCH calls in parallel, not sequentially. If one fails and the other succeeds, you have drift.
6. **Verify both deployments:** re-fetch each assistant and confirm the change landed. For mirror integrity, also re-run the Feature Parity Matrix diff — the same source value should now appear in both.
7. **Test both with a real call.** Same test scenario on both platforms. If behavior diverges beyond documented deviations, that's a bug — investigate before declaring the update complete.
8. **Update `deviations.md`** if the change introduced any new unavoidable platform-specific behavior.

### Failure handling

If a parallel update fails on one platform:
- **Do not** roll back the successful platform unless the user explicitly approves. The successful side is now ahead; the failed side is the problem to fix.
- Diagnose the failure, fix it, re-deploy to the failed platform.
- Re-run the verification step to confirm the mirror is in sync.
- If the failure is unrecoverable on one platform (e.g. the destination doesn't support a feature the change requires), surface that to the user immediately — they need to decide whether to revert the successful side, accept the deviation, or split the mirror.

### Drift detection

Periodically (and definitely before any further updates) run a drift check:
1. Fetch full state from both platforms.
2. Run through the Feature Parity Matrix.
3. Anything that should match but doesn't, and isn't in `deviations.md`, is drift. Resolve before applying new updates.

A practical drift-check is to grep both deployed system prompts for the same canonical phrase (a stakeholder name, a redline, a signature greeting). If the phrase exists on one and not the other, you have drift.

---

## Quick Reference: Field-Level Mapping

When in a hurry, this table is the cheat sheet. Full caveats are in the Feature Parity Matrix above.

| Concern | VAPI | FlowForge |
|---------|------|-----------|
| Agent name | `name` | `name` |
| System prompt | `model.messages[0].content` | `system_prompt` |
| LLM | `model.provider` + `model.model` | `model` (flat string) |
| Temperature | `model.temperature` | `temperature` |
| First message text | `firstMessage` | `first_message` |
| Speaks-first | `firstMessageMode` (enum) | `agent_speak_first` (bool) |
| Voice provider | `voice.provider` | `tts_settings.provider` |
| Voice ID | `voice.voiceId` | `tts_settings.voice` |
| STT provider | `transcriber.provider` | `stt_settings.provider` |
| STT model | `transcriber.model` | `stt_settings.model` |
| End-call action | `endCall` tool in `model.toolIds` | `system_tools_config.end_conversation: true` |
| Transfer-call action | `transferCall` tool with destinations | `system_tools_config.transfer_call: true` (destination at routing layer) |
| SMS action | `sms` tool with Twilio `from` | `webhook_tools[]` calling Twilio directly |
| Custom function | `function` tool in registry | `webhook_tools[]` entry |
| MCP server | `mcp` tool | `mcp_servers[]` (org allow-list) |
| Silent handoff | `handoff` tool | `flow_data` graph (no 1:1) |
| Knowledge base | `model.knowledgeBaseId` | KB resource linked via assistant endpoint |
| HIPAA | `compliancePlan.hipaaEnabled` | Org-level config |
| Auth header | `Authorization: Bearer <key>` | `x-api-key: <key>` |
| Base URL | `https://api.vapi.ai` | `https://api.realbotics.ai/api/v1/external` |
| Iteration PATCH | Full `model` object required | Partial PATCH supported |
| Tool creation order | Tools first, then assistant references by ID | Tools inline on assistant |

---

## Anti-Patterns to Avoid

1. **Mirror without a source-of-truth artifact.** Editing `vapi/config.json` and `flowforge/config.json` directly without a shared `prompt.md` guarantees drift within weeks.
2. **Sequential parallel updates.** PATCH one platform, then "I'll do the other in a minute" — if the second update gets dropped, the mirror is silently broken. Run them together.
3. **Migrating without inventorying tools.** The most common migration regression is a tool that worked on the source but isn't wired up on the destination because nobody noticed it in `model.toolIds` or `webhook_tools[]`.
4. **Assuming voice ID portability across providers.** A custom ElevenLabs clone ID only works if both platforms talk to the same ElevenLabs account. Confirm before assuming.
5. **Deleting the source agent before the destination has run a week of real traffic.** Rollback is much cheaper if the source is just disabled, not gone.
6. **Mirroring an agent that doesn't need to be mirrored.** Single-platform is the default. Mirroring is overhead — it's only worth it for explicit failover, A/B, or geo-routing requirements.
7. **Letting `deviations.md` grow.** Every entry in `deviations.md` is technical debt against the mirror. If it grows past ~3-4 items, the agents have functionally diverged and should be split into two separate single-platform agents.

---

## Reference Files

- [`lossless-conversion-protocol.md`](lossless-conversion-protocol.md) — mandatory inventory + diff-check protocol that this migration/sync protocol extends.
- [`vapi-config-reference.md`](vapi-config-reference.md) — VAPI config shape, tool schemas, deployment.
- [`flowforge-config-reference.md`](flowforge-config-reference.md) — FlowForge config shape, endpoint inventory, deployment.
- [`../assets/agent-config-template.json`](../assets/agent-config-template.json) — VAPI single-agent config template.
- [`../assets/flowforge-agent-config-template.json`](../assets/flowforge-agent-config-template.json) — FlowForge single-agent config template.
