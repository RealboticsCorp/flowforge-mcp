# FlowForge Workflows

Step-by-step recipes. Each maps to a `/ff-*` slash command where one exists but can
be followed directly. Tool names omit the client prefix and the `flowforge_` stem
(`list_assistants` = `flowforge_list_assistants`).

Throughout: resolve names → UUIDs with list tools first; confirm every real-world
side effect (calls, purchases, deletes, campaign start/stop) before acting; read
`api_reference` for any body you are unsure of.

---

## Place a single call  (`/ff-call`)

1. Resolve the assistant: `list_assistants` → id by name/slug.
2. Optional caller ID: `list_phone_numbers` (the number must be active in this org,
   else 400).
3. Check the prompt's variables: `get_assistant include=["prompt-variables"]`; gather
   values for each.
4. Validate the destination is E.164.
5. **Confirm**: "Call `<dest>` with `<assistant>` from `<caller id|default>`,
   variables `<…>`?"
6. `start_call`. Record the `call_id`. On timeout/5xx do NOT resend — search
   `list_calls search=<dest> date_from=<now-2m>` first.
7. Offer a review (below) once it ends.

## Place a batch of calls  (`/ff-batch`)

1. Resolve the assistant.
2. Build `calls`: `{phone_number, template_variables?, reference_id?}`; reject
   non-E.164 numbers.
3. **State the count and confirm.** Split >100 into multiple batches.
4. `start_batch_calls`; summarize successes/failures by `reference_id`.
5. For recurring or large lists, prefer a campaign (retries, pacing, schedule).

## Audit / review a call  (`/ff-call-review`)

1. Find it: `list_calls` (`search`, `date_from/to`, `agent_id`, `campaign_id`,
   `disposition_name`) or `list_campaign_calls`.
2. `get_call include=["transcript","metrics","events","recordings"]`.
3. Summarize: outcome/disposition, ended reason, duration, cost, latency, key
   transcript moments, tool calls and their responses (events), recording link
   (expires in ~1 h).
4. Note: structured-data / success-evaluation results are only in the end-of-call
   webhook payload, not the API.

## Launch an outbound campaign  (`/ff-campaign`)

1. Resolve the assistant and dialing source (`list_phone_numbers` or
   `manage_phone_pools action=list`).
2. `create_campaign` with `name`, `agent_id`, `direction="outbound"`,
   `phone_number_id` or `phone_pool_id`, `parallel_lines`, `total_dial_attempts`.
3. Schedule and rules: `update_campaign_settings` with `schedule` (start date,
   times, days, timezone), `dialer_settings`, `compliance`,
   `enforce_local_calling_hours`, voicemail drop, `webhook_url`. Read the exact
   shape with `api_reference method=PATCH path=/campaigns/x/settings`.
4. Outcomes: `manage_dispositions action=outcomes_decision`. If `decided=false`,
   either `keep_platform_defaults` or create dispositions with `criteria`.
5. Leads: `add_campaign_leads` (≤1000 per call; `custom_fields` feed template
   variables). Report added/skipped/errors.
6. **Confirm**, then `control_campaign action=start`. A 400 names the missing
   prerequisite — fix and retry.
7. Report the campaign id and how to monitor it.

## Monitor a campaign  (`/ff-campaign-status`)

1. Resolve the campaign (`list_campaigns status=running`).
2. `get_campaign include=["analytics","status"]`; calls via `list_campaign_calls`.
3. `list_active_calls` for what is dialing now; `get_organization
   include_concurrency=true` if leads look stuck in `queued` (concurrency saturated).
4. Summarize state, progress, connect/disposition rates, spend. Offer
   pause/resume/stop (confirm stop). To retry only failures: pause →
   `remove_campaign_leads status_filter=["failed","no_answer","busy"]` (confirmed)
   → re-add those numbers → resume.

## Inspect / create / update an assistant  (`/ff-assistant`)

- **Inspect:** `get_assistant detailed=true include=["prompt-variables","knowledge-base","stats"]`.
- **Create:** `voice_catalog` (summary → tts) to choose valid voice settings, then
  `create_assistant` (`name`, `system_prompt`, `first_message`, `model`,
  `tts_settings`, `stt_settings`; flow agents: `extra_config={"flow_data": …}`).
  Then PATCH RAG flags / webhooks / end-of-call report with `update_assistant`.
- **Update a live agent safely:** use the branch workflow below rather than
  editing Main directly.
- **Pronunciations:** `manage_pronunciations create fields={"written": "SQL", "spoken": "sequel"}`.

## Change an agent safely: branch → test → promote

1. `manage_branches action=create fields={"name": "prompt-v5"}` (forks Main).
2. `manage_branches action=update branch_id=… fields={"system_prompt": …}`.
3. Tests: `list_tests assistant_id=…` (attached tests), then
   `manage_tests action=run_all assistant_id=… branch_id=…` or
   `run_test test_id=… assistant_id=… branch_id=… n_iterations=3`.
4. Poll `get_test_run run_id=…` until terminal; compare with the Main baseline
   (`manage_tests action=list_runs`).
5. Report pass/fail with failure reasons. Promotion / traffic split is done in the
   builder (or `update_campaign_settings branch_id=…` to pin a campaign to a
   branch); `assistant_lifecycle publish` deploys Main.

## Run an agent test  (`/ff-test`)

1. `list_tests` (filter `assistant_id`, `test_type`, `folder_id`) → `test_id`.
2. `run_test test_id assistant_id` (both required) → queued run id.
3. Poll `get_test_run` until completed/failed; summarize scores and reasons.
4. New test: `manage_tests action=get` on a similar test, copy its `config`, then
   `action=create` with `attach_to_assistant_id`.

## Give an agent a knowledge base

1. `manage_knowledge_bases action=create name=…` (or reuse one from `list`).
2. Add docs: `manage_documents action=upload file_path=… knowledge_base_id=…` or
   `action=import_url url=…`.
3. `update_assistant fields={"knowledge_base_id": "<kb>", "enable_rag_tool": true}`.
4. Add a prompt line telling the agent when to use `retrieve_knowledge`.
5. Verify retrieval: `search_knowledge query=<typical caller question> agent_id=<id>`.

## Build a webhook tool for an assistant  (`/ff-tool`)

1. Gather: tool `name`, when to call it (description), method + public HTTPS URL,
   the parameters the agent fills, auth secret.
2. Read current tools: `get_assistant detailed=true` → `webhook_tools`.
3. Build the entry (shape in
   [coding-against-api.md](coding-against-api.md#webhooks-you-receive)):
   `bodyParams: [{name, type, description, required}]`,
   `headers: [{name, value}]`, `preToolSpeech`, `responseTimeout`, `responseFields`.
4. `update_assistant fields={"webhook_tools": [<existing…>, <new>]}` — the array
   is replaced wholesale.
5. Endpoint must be idempotent (tool calls retry up to 3×) and return a clear JSON
   error body. Validate with a `tool_call` test or one confirmed `start_call`.

## Attach an MCP server to an assistant  (`/ff-tool`)

1. Registry servers: `manage_mcp_servers action=catalog` → `server_tools` to inspect.
   Custom servers: `action=custom_add url=… prefix=…`, then `custom_test`, then a
   confirmed `custom_call` to exercise one tool.
2. Read the assistant's current `mcp_servers`; write the merged list via
   `update_assistant fields={"mcp_servers": [...]}`.
3. Validate with a test or a confirmed call.

## Copy an assistant (same org or across orgs)

1. Source server: `get_assistant assistant_id=… include=["export"]` → `export`.
2. Target server (e.g. `flowforge-acme`): `import_assistant data=<export>
   name_override=…`. Knowledge-base docs, phone numbers and MCP-server IDs are
   org-specific — re-link them on the target.
3. Same org, quick copy: `assistant_lifecycle action=clone`.

## Check spend  (`/ff-usage`)

1. `get_balance`.
2. `get_usage breakdown=current-month`, then `forecast` (month-end projection),
   `insights` (anomalies), `agents-efficiency` (cost per agent), `idle-phones`
   (numbers costing money without calls), `by-disposition`.
3. Line items: `breakdown=ledger date_from=… limit=200`.
4. Summarize spend drivers and concrete savings (e.g. release idle numbers — confirm
   each; release is irreversible).

## Check operational health  (`/ff-status`)

1. `health` (host up, base URL, spec version).
2. `get_organization include_concurrency=true` — outbound/inbound/web caps.
3. `list_active_calls` — live now. Report headroom vs caps.
