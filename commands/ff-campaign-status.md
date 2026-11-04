---
description: Show a FlowForge campaign's analytics, run state, and live calls
argument-hint: <campaign_id | campaign name>
allowed-tools: mcp__flowforge__flowforge_list_campaigns, mcp__flowforge__flowforge_get_campaign, mcp__flowforge__flowforge_list_active_calls, mcp__flowforge__flowforge_control_campaign
---

Use the **flowforge** skill. Follow the "Monitor a campaign" workflow.

Target: $ARGUMENTS

Steps:
1. Resolve the campaign id via `flowforge_list_campaigns` if a name was given.
2. `flowforge_get_campaign` with `include=["analytics","status","calls"]`.
3. Optionally `flowforge_list_active_calls` to show what's dialing now.
4. Summarize: run state, progress, connect/disposition rates, spend. Offer
   pause/resume/stop via `flowforge_control_campaign` — confirm before `stop`.
