---
description: Create and launch a FlowForge outbound campaign, optionally seeding leads
argument-hint: <campaign name> with <assistant> [from <number/pool>] [leads: ... | csv: <path>]
allowed-tools: mcp__flowforge__flowforge_list_assistants, mcp__flowforge__flowforge_list_phone_numbers, mcp__flowforge__flowforge_create_campaign, mcp__flowforge__flowforge_add_campaign_leads, mcp__flowforge__flowforge_control_campaign, mcp__flowforge__flowforge_get_campaign, mcp__flowforge__flowforge_update_campaign_settings, mcp__flowforge__flowforge_manage_dispositions, mcp__flowforge__flowforge_manage_phone_pools, Read
---

Use the **flowforge** skill. Follow the "Launch an outbound campaign" workflow.

Request: $ARGUMENTS

Steps:
1. Resolve the assistant (`flowforge_list_assistants`) and the dialing source
   (`flowforge_list_phone_numbers` → `phone_number_id`, or a `phone_pool_id`).
2. `flowforge_create_campaign` with `name`, `agent_id`, the dialing source, and
   any dialing settings (`parallel_lines`, `total_dial_attempts`, or
   `extra_config` like `send_rate_per_hour`).
3. Set the schedule/rules with `flowforge_update_campaign_settings` (outbound
   needs start date, times, days, timezone).
4. Outcomes: `flowforge_manage_dispositions action=outcomes_decision`; if not
   decided, `action=keep_platform_defaults` (or create dispositions with criteria).
5. Add leads (`flowforge_add_campaign_leads`, ≤1000 per call) from inline list or
   CSV (Read it); validate E.164.
6. **Confirm**, then `flowforge_control_campaign` with `action="start"` — this
   begins real outbound dialing.
   A 400 names the missing prerequisite — fix it and retry.
7. Report the campaign id and suggest `/ff-campaign-status <id>` to monitor.
