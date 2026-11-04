---
description: FlowForge operational health — org concurrency caps and live calls
argument-hint: (no arguments)
allowed-tools: mcp__flowforge__flowforge_get_organization, mcp__flowforge__flowforge_list_active_calls
---

Use the **flowforge** skill. Follow the "Check operational health" workflow.

Steps:
1. `flowforge_get_organization` with `include_concurrency=true` — outbound /
   inbound / web concurrency caps.
2. `flowforge_list_active_calls` — what's live right now.
3. Report headroom (active vs. cap per direction) and flag if near the limit.
