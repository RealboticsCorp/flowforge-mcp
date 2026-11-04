---
description: Inspect, create, or update a FlowForge assistant (voice agent)
argument-hint: <inspect|create|update> <name> [details...]
allowed-tools: mcp__flowforge__flowforge_list_assistants, mcp__flowforge__flowforge_get_assistant, mcp__flowforge__flowforge_create_assistant, mcp__flowforge__flowforge_update_assistant, mcp__flowforge__flowforge_assistant_lifecycle, mcp__flowforge__flowforge_manage_branches, mcp__flowforge__flowforge_voice_catalog, mcp__flowforge__flowforge_manage_pronunciations
---

Use the **flowforge** skill. Follow the "Inspect / create / update an assistant"
workflow.

Request: $ARGUMENTS

Steps:
1. Determine intent (inspect / create / update) from the request.
2. **Inspect:** `flowforge_list_assistants` to resolve the name, then
   `flowforge_get_assistant` with `detailed=true` and
   `include=["prompt-variables","knowledge-base","stats"]`; summarize the config.
3. **Create:** `flowforge_create_assistant` (`name` required; gather
   `system_prompt`, `model`, `temperature`, `tts_settings`, `stt_settings`, or
   `extra_config.flow_data` for a flow agent). Offer to publish via
   `flowforge_assistant_lifecycle` `action="publish"`.
4. **Update:** resolve the id, then `flowforge_update_assistant` with only the
   changed `fields`. For risky changes to a live agent, prefer a branch
   (`flowforge_manage_branches` create → update → run tests on it) over editing
   Main. Use `flowforge_voice_catalog` to pick valid voice settings.
5. Confirm before publishing an agent so it answers live calls.
