---
description: Run a FlowForge agent test (or list available tests)
argument-hint: [test name/id — omit to list tests]
allowed-tools: mcp__flowforge__flowforge_list_tests, mcp__flowforge__flowforge_run_test, mcp__flowforge__flowforge_get_test_run, mcp__flowforge__flowforge_list_assistants, mcp__flowforge__flowforge_manage_tests
---

Use the **flowforge** skill. Follow the "Run an agent test" workflow.

Target: $ARGUMENTS

Steps:
1. If no argument, `flowforge_list_tests` and present the tests for the user to
   pick.
2. Otherwise resolve the `test_id` (via `flowforge_list_tests` if a name was
   given) and the assistant to test against (`assistant_id` is required; use the
   test's attached assistant or ask). Optional `branch_id` to test a branch.
3. `flowforge_run_test` returns a queued run. Poll `flowforge_get_test_run` with
   its run id until the status is terminal.
4. Report pass/fail, scores and failure reasons. To run every attached test:
   `flowforge_manage_tests action=run_all assistant_id=…`.
