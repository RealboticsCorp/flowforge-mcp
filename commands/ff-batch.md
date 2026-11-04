---
description: Place a batch of FlowForge outbound calls (up to 100) from a list or CSV
argument-hint: with <assistant name> [numbers: +1...,+1... | csv: <path>]
allowed-tools: mcp__flowforge__flowforge_list_assistants, mcp__flowforge__flowforge_list_phone_numbers, mcp__flowforge__flowforge_start_batch_calls, Read
---

Use the **flowforge** skill. Follow the "Place a batch of calls" workflow.

Request: $ARGUMENTS

Steps:
1. Resolve the assistant name → id with `flowforge_list_assistants`.
2. Build the recipient list from the inline numbers or the referenced CSV (Read
   it). Each item: `{phone_number, template_variables?, reference_id?}`. Validate
   every number is E.164 and flag any that aren't.
3. **State the total count and confirm before sending** — these are real,
   billable calls. If more than 100, split into multiple batches and say so.
4. On confirmation, call `flowforge_start_batch_calls`.
5. Summarize `successful` / `failed`; list each failure with its `error` and
   `reference_id`/`phone_number`.
