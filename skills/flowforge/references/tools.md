# FlowForge MCP tool reference (v0.2.0, 48 tools)

Bare names; prefix per client (`mcp__flowforge__…` in Claude Code). Every tool
accepts `response_format` (`json` default | `markdown`) unless noted. `*` =
required. Gated actions return `{"dry_run": true, "would_send": …}` until called
again with `confirm=true`.

For any body not spelled out here: `flowforge_api_reference method=<M> path=<P>`.

## Full-API access

| Tool | Key params | Notes |
| --- | --- | --- |
| `flowforge_api_reference` | `query`, `group`, `method`+`path`, `include_response_schema`, `limit` | Offline, bundled OpenAPI. No args = group index. `method`+`path` = full params + resolved body schema. |
| `flowforge_api_request` | `method`*, `path`*, `query`, `body`, `confirm`, `allow_undocumented`, `max_chars` | Any documented endpoint. Returns `{status, request_id, endpoint, body}`; non-2xx come back as data with an `error` summary. Gated: every DELETE, `/calls/start`, `/calls/batch`, `/calls/end-all`, campaign `start`/`resume`, `/phone-numbers/purchase`, org MCP-server replace, custom MCP tool call, character/role instant tests. Unknown paths are refused with `did_you_mean`. |
| `flowforge_health` | — | Unauthenticated host check + base URL + bundled spec version. |

## Assistants

| Tool | Key params | Notes |
| --- | --- | --- |
| `flowforge_list_assistants` | `limit` (50), `offset` | API returns all; paged client-side. |
| `flowforge_get_assistant` | `assistant_id`*, `detailed`, `include[]` | `include`: `prompt-variables`, `flow`, `knowledge-base`, `stats`, `export`. Result keyed `assistant` + one key per include. |
| `flowforge_create_assistant` | `name`*, `system_prompt`, `first_message`, `agent_speak_first`, `model`, `temperature`, `tts_settings`, `stt_settings`, `mcp_servers`, `extra_config` | `extra_config` merges any other create field (e.g. `flow_data`, `webhook_tools`). RAG flags are PATCH-only. |
| `flowforge_update_assistant` | `assistant_id`*, `fields`* | PATCH; arrays replace wholesale. Common: `system_prompt`, `knowledge_base_id`, `enable_rag_tool`, `enable_search_tool`, `webhook_tools`, `mcp_servers`, `end_of_call_report_config`, `structured_data_config`, `success_evaluation_config`, `system_tools_config`, `template_variables`. |
| `flowforge_delete_assistant` | `assistant_id`* | Permanent, ungated — confirm with the user first. |
| `flowforge_assistant_lifecycle` | `assistant_id`*, `action`* (`clone`/`publish`) | |
| `flowforge_import_assistant` | `data`*, `name_override`, `slug_override`, `import_character`/`role`/`flow` | `data` = the `export` include. Cross-org copy: export on one server, import on another. |
| `flowforge_manage_branches` | `assistant_id`*, `action`* (`list`/`get`/`create`/`update`), `branch_id`, `version`, `fields` | create `fields`: `{name*, description, source_branch_id, source_version}`. update `fields`: any assistant config field (new version on that branch). |
| `flowforge_manage_pronunciations` | `assistant_id`*, `action`* (`list`/`create`/`update`/`delete`), `pronunciation_id`, `fields`, `confirm` | `fields`: `{written*, spoken*, ipa, case_sensitive, match_whole_word, priority, enabled}`. Duplicate word → 409. delete gated. |

## Voice

| Tool | Key params | Notes |
| --- | --- | --- |
| `flowforge_voice_catalog` | `catalog` (`summary`/`tts`/`stt`/`presets`/`agent-presets`/`cloned`), `provider` | Pick valid `tts_settings`/`stt_settings`. Preview audio: `api_request POST /voice/preview {text*, provider*, voice, model}`. |
| `flowforge_clone_voice` | `action`* (`create`/`delete`), `file_path`, `name`, `provider` (`chatterbox`), `voice_id`, `confirm` | Uploads a local audio file (≤50 MB). delete gated. Only with rights to the voice. |

## Calls

| Tool | Key params | Notes |
| --- | --- | --- |
| `flowforge_start_call` | `phone_number`*, `assistant_id`*, `caller_phone_number`, `template_variables` | Dials a real phone. Not gated — confirm first. 402 = balance empty. |
| `flowforge_start_batch_calls` | `assistant_id`*, `calls`* (≤100: `{phone_number*, template_variables, reference_id}`), `caller_phone_number`, `delay_between_calls_ms` (500) | `reference_id` is echoed per result, not stored. |
| `flowforge_list_calls` | `limit`, `offset`, `status_filter`, `direction_filter`, `agent_id`, `campaign_id`, `date_from`, `date_to`, `search`, `disposition_name`, `sort_by`, `sort_order` | Server-side paging. |
| `flowforge_get_call` | `call_id`*, `include[]` (`transcript`, `metrics`, `events`, `recordings`) | Recording URLs expire (1 h default). |
| `flowforge_list_active_calls` | — | |
| `flowforge_end_call` | `call_id` or `all_calls=true` | Drops live calls. Confirm first. |

## Campaigns

| Tool | Key params | Notes |
| --- | --- | --- |
| `flowforge_list_campaigns` | `status`, `direction`, `agent_id`, `limit`, `offset` | Server filters; paged client-side. |
| `flowforge_create_campaign` | `name`*, `agent_id`, `campaign_type`, `direction`, `phone_number_id`/`phone_pool_id`, `parallel_lines`, `total_dial_attempts`, `recipients`, `extra_config` | |
| `flowforge_get_campaign` | `campaign_id`*, `include[]` (`analytics`, `status`, `leads`, `calls`) | |
| `flowforge_control_campaign` | `campaign_id`*, `action`* (`start`/`stop`/`pause`/`resume`/`clone`) | Not gated. Start prerequisites in SKILL.md gotchas. |
| `flowforge_update_campaign_settings` | `campaign_id`*, `settings`* | PATCH `/settings`: agent, number/pool, schedule, dialer, compliance, voicemail drop, webhook, pacing, branch. |
| `flowforge_add_campaign_leads` | `campaign_id`*, `leads`* (≤1000: `{phone_number*, first_name, last_name, email, custom_fields}`), `allow_duplicates`, `allow_self_dial` | Response: added/skipped/duplicates_skipped/errors. |
| `flowforge_remove_campaign_leads` | `campaign_id`*, `status_filter[]`, `confirm` | Omit filter = ALL leads. 400 while running/scheduled. Gated. |
| `flowforge_manage_dispositions` | `action`* (`list`/`create`/`update`/`outcomes_decision`/`keep_platform_defaults`/`org_list`), `campaign_id`, `disposition_id`, `fields` | create `fields`: `{name*, label*, category*, is_terminal, criteria, retry_strategy, actions, routing_rules, compliance_action}`. |
| `flowforge_list_campaign_calls` | `campaign_id`*, `status`, `disposition_id`, `date_from`, `date_to`, `search`, `limit`, `offset` | Falls back to `/calls/?campaign_id=` when the campaign endpoint 500s (`source` says so). |
| `flowforge_delete_campaign` | `campaign_id`* | Permanent, ungated — confirm first. |

## Phone numbers & pools

| Tool | Key params | Notes |
| --- | --- | --- |
| `flowforge_list_phone_numbers` | `limit`, `offset` | Paged client-side (200+ numbers). |
| `flowforge_search_phone_numbers` | `country_code` (US), `area_code`, `contains`, `limit` (10) | Purchasable inventory. Server 500s as of 2026-11-03. |
| `flowforge_assign_phone_number` | `phone_number_id`*, `agent_id` or `unassign=true` | Inbound routing. |
| `flowforge_manage_phone_number` | `action`* (`get`/`rename`/`purchase`/`release`/`countries`/`area_codes`), `phone_number_id`, `phone_number`, `capabilities` (`["voice"]`), `friendly_name`, `country_code`, `confirm` | purchase + release gated. |
| `flowforge_manage_phone_pools` | `action`* (`list`/`get`/`create`/`update`/`delete`/`add_member`/`remove_member`/`next_phone`/`statistics`), `pool_id`, `phone_number_id`, `weight`, `priority`, `fields`, `confirm` | create `fields`: `{name*, description, distribution_strategy (round_robin|weighted|least_used|random|local_presence), phone_number_ids}`. delete + remove_member gated. |

## Knowledge

| Tool | Key params | Notes |
| --- | --- | --- |
| `flowforge_search_knowledge` | `query`*, `full_text`, `agent_id`, `document_ids`, `limit` (8), `context_lines`, `case_sensitive` | `full_text=true` greps (`query` is the pattern). |
| `flowforge_list_documents` | `knowledge_base_id`, `limit`, `offset` | API pages by page number; offset rounds to a page. |
| `flowforge_manage_documents` | `action`* (`get`/`content`/`upload`/`import_url`/`delete`/`list_for_agent`/`link_to_agent`/`reindex`), `document_id`, `document_ids`, `agent_id`, `file_path`, `url`, `knowledge_base_id`, `title`, `source_url`, `confirm` | upload takes a local path. delete gated. |
| `flowforge_manage_knowledge_bases` | `action`* (`list`/`get`/`create`/`update`/`delete`), `kb_id`, `name`, `description`, `confirm` | delete gated. |

## Tests

| Tool | Key params | Notes |
| --- | --- | --- |
| `flowforge_list_tests` | `assistant_id`, `folder_id`, `test_type`, `limit`, `offset` | Paged client-side. |
| `flowforge_run_test` | `test_id`*, `assistant_id`*, `branch_id`, `n_iterations`, `draft` | Async: returns a queued run. |
| `flowforge_get_test_run` | `run_id`*, `include_results` (true), `retry`, `retry_iterations` | Poll until terminal. |
| `flowforge_manage_tests` | `action`* (`get`/`create`/`update`/`delete`/`attach`/`detach`/`list_runs`/`run_all`/`list_folders`/`create_folder`), `test_id`, `assistant_id`, `branch_id`, `n_iterations`, `folder_name`, `fields`, `limit`, `confirm` | create `fields`: `{name*, test_type* (scenario|tool_call|simulation|span_replay), config*, folder_id, attach_to_assistant_id}` — copy `config` from an existing test (`get`). delete gated. |

## Org, MCP servers, spend

| Tool | Key params | Notes |
| --- | --- | --- |
| `flowforge_get_organization` | `include_concurrency` | |
| `flowforge_update_organization` | `action`* (`update`/`update_concurrency`/`get_test_phone_number`/`set_test_phone_number`), `fields`, `test_phone_number_id` | |
| `flowforge_manage_mcp_servers` | `action`* (`catalog`/`server_tools`/`org_list`/`org_set`/`org_remove`/`custom_list`/`custom_add`/`custom_test`/`custom_call`/`custom_delete`), `server_id`, `server_ids`, `url`, `name`, `prefix`, `description`, `tool_name`, `arguments`, `confirm` | org_set REPLACES the list (`[]` disables all). Gated: org_set, org_remove, custom_call, custom_delete. Attach to an agent via its `mcp_servers`. |
| `flowforge_get_usage` | `breakdown` (`current-month`/`by-component`/`by-resource`/`by-disposition`/`forecast`/`insights`/`agents-efficiency`/`idle-phones`/`ledger`), `date_from`, `date_to`, `period_days`, `threshold_days`, `limit` | `ledger` falls back to ledger.csv rows when the JSON ledger 500s. |
| `flowforge_get_balance` | — | |

## Only via `flowforge_api_request`

Characters (`/characters/…`, incl. `from-template`, `instant-test`), roles
(`/roles/…`), Vapi import (`/vapi-import/fetch-assistant|fetch-assistants|preview|import`),
voice preview, call events filtered by `event_type`, recordings with custom
`expires_in`, campaign analytics `time_range`/`period`/`tz`, campaign leads paging
(`/campaigns/{id}/leads/?limit&offset`).
