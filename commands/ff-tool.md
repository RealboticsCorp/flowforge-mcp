---
description: Build and attach a webhook or MCP tool to a FlowForge assistant
argument-hint: <assistant name> [webhook|mcp] [tool details...]
allowed-tools: mcp__flowforge__flowforge_list_assistants, mcp__flowforge__flowforge_get_assistant, mcp__flowforge__flowforge_manage_mcp_servers, mcp__flowforge__flowforge_update_assistant, mcp__flowforge__flowforge_assistant_lifecycle, mcp__flowforge__flowforge_run_test, mcp__flowforge__flowforge_get_test_run
---

Use the **flowforge** skill. Follow the "Build a webhook or MCP tool for an
assistant" workflow.

Request: $ARGUMENTS

Steps:
1. Resolve the assistant id (`flowforge_list_assistants`).
2. **Read current state first:** `flowforge_get_assistant` with `detailed=true`
   and note the existing `webhook_tools` and `mcp_servers` arrays — they are
   replaced wholesale, so never overwrite them with a single entry.
3. **Webhook tool:** gather name, description (when to call), method + public
   HTTPS URL, parameters, auth secret. Build the entry with `bodyParams:
   [{name, type, description, required}]`, `headers: [{name, value}]`,
   `preToolSpeech`, `responseTimeout`, `responseFields` (see the skill's
   coding-against-api.md; mirror an existing tool's shape if present). Attach via
   `flowforge_update_assistant` `fields={"webhook_tools": [ ...existing, <new> ]}`.
   Remind the user the endpoint must be idempotent (FlowForge retries 5xx up to 3×).
4. **MCP tool server:** `flowforge_manage_mcp_servers action=catalog` (registry) or
   `custom_list` / `custom_add` + `custom_test` (own server), then
   `flowforge_update_assistant` `fields={"mcp_servers": [ ...existing, <id> ]}`.
5. Publish if needed (`flowforge_assistant_lifecycle` `publish`) and validate via
   `flowforge_run_test` or a single confirmed test call.
