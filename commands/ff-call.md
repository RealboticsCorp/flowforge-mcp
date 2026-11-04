---
description: Place a single FlowForge outbound call (resolves assistant name, confirms, dials)
argument-hint: <phone E.164> with <assistant name> [from <caller number>] [vars: k=v,...]
allowed-tools: mcp__flowforge__flowforge_list_assistants, mcp__flowforge__flowforge_list_phone_numbers, mcp__flowforge__flowforge_start_call, mcp__flowforge__flowforge_get_call
---

Use the **flowforge** skill. Follow the "Place a single call" workflow.

Request: $ARGUMENTS

Steps:
1. Parse the destination number, the assistant (name or id), an optional caller
   number, and any `template_variables`.
2. Resolve the assistant name → id with `flowforge_list_assistants`. If a caller
   number was named, resolve it with `flowforge_list_phone_numbers`.
3. Validate the destination is E.164 (`+...`); if not, stop and ask.
4. **Confirm before dialing**: show destination, assistant, caller id, and any
   variables, and wait for an explicit go-ahead. This places a real, billable
   call.
5. On confirmation, call `flowforge_start_call`. Report the `call_id` and offer
   `/ff-call-review <call_id>`.
