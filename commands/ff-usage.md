---
description: FlowForge spend — account balance plus usage breakdown
argument-hint: [current-month | by-component | by-resource | by-disposition | forecast | insights | agents-efficiency | idle-phones | ledger]
allowed-tools: mcp__flowforge__flowforge_get_balance, mcp__flowforge__flowforge_get_usage
---

Use the **flowforge** skill. Follow the "Check spend" workflow.

Breakdown requested: $ARGUMENTS (default: current-month total)

Steps:
1. `flowforge_get_balance` for prepaid balance and auto-topup state.
2. `flowforge_get_usage` with the requested `breakdown`. With no argument, pull
   `current-month`, `forecast` and `insights`.
3. Summarize current spend, the month-end projection and what's driving it, in
   markdown. Mention `idle-phones` if numbers are costing money without calls
   (releasing one is irreversible — never do it without explicit approval).
