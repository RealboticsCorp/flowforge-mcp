---
description: Audit a FlowForge call — transcript, metrics, events, and recording in one view
argument-hint: <call_id | search terms to find the call>
allowed-tools: mcp__flowforge__flowforge_list_calls, mcp__flowforge__flowforge_get_call
---

Use the **flowforge** skill. Follow the "Audit / review a call" workflow.

Target: $ARGUMENTS

Steps:
1. If the argument is a call id, use it. Otherwise find the call with
   `flowforge_list_calls` (use `search`, `date_from`/`date_to`, `agent_id`, or
   `campaign_id`); if several match, list them and ask which.
2. `flowforge_get_call` with
   `include=["transcript","metrics","events","recordings"]`.
3. Summarize in markdown: outcome/disposition, duration, cost, latency, key
   transcript moments, notable events, and a link to the recording if present.
   Keep raw JSON out unless asked.
