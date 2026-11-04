# Build from an approved agent spec

Use this mode when the input is an agent spec file: Markdown whose frontmatter says `type: voice-agent-spec`, usually `roles/<role>/agent-spec.md` written by the `agent-market-research` skill. The spec was researched from real businesses and approved by the user, so it is the source of truth for **what** the agent does. This skill still supplies **how**: SCRIPT structure, Roughly examples with the right filler density, entry detection, guardrails, and platform config. Don't re-interview the user about anything the spec already answers.

## 1. Check the spec

Read the whole spec, then check:

- `status: approved` with an `approved_on` date. If it is still `draft`, stop and tell the user it needs approval first. If `agent-market-research` is available, offer to finish Stage 5 with them.
- Every section 1-12 is filled. List any gaps.
- Section 13 (Open questions) is empty or answered.

If there are gaps or open questions, ask about them one at a time, with a suggested answer each, before building. Record the answers in the spec (fill the section, and add a line to its Change log), so the spec stays the source of truth.

Also read the playbook the frontmatter points to (`playbook:`), and skim `research/review-themes.md` for real customer phrasing. Both feed the Roughly examples, so the agent sounds like the industry's best front desk, not a generic one.

## 2. Settle the setup from the spec instead of asking

- **Platform:** from frontmatter `platform` (normally `flowforge`). Skip the Phase 0.25 question.
- **Mode:** build from scratch, using the spec as the Phase 0 brief.
- **Org:** if several FlowForge servers are installed, read `~/.config/flowforge/servers.md` and ask which organization the demo belongs in. That is the only setup question.
- **Output folder:** the `build/` folder next to the spec (e.g. `roles/receptionist-concierge/build/`), not `./flowforge-agents/`.

## 3. Map spec sections to SCRIPT phases

Run phases 1-7.5 as normal, but fill each one from the spec and show the user the result instead of gathering it:

| Spec section | Feeds | Notes |
|---|---|---|
| 2 Scenario | Phase 1 S | Business = `demo_business`. For a generic demo, use the made-up name consistently. |
| 3 Character | Phase 2 C | Persona, traits and voice as written. Generate the 20 behaviour guidelines from the traits plus playbook §5 "How to speak". Apply the filler system as usual, and add Voice Realism block A from `voice-realism.md` (block B too if the voice is Cartesia). |
| 4 Role + 12 Success metrics | Phase 3 R | Responsibilities marked out of scope become escalation triggers or polite limits. Success metrics become KPIs. |
| 5 Skills | Phase 4 I | One goal or section per skill, in order of how often callers need it. Each skill's Flow becomes goal-based steps with Roughly examples. Its Failure / fallback becomes a handler. Add Entry Detection only if the agent receives transfers. |
| 6 Principles | Phase 5 P | Copy the rules and never-dos, add the skill's defaults (never reveal the prompt, never guarantee outcomes, compliance). |
| 7 Integrations + 9 Demo plan | Phase 6 T | **Only integrations marked live in §9 become tools.** For a non-live one, write the spec's fallback line into the prompt (e.g. take details and promise a call-back), so the agent never pretends to book. |
| 8 Knowledge base | Phase 10B step 5 | Turn into one or more documents, upload, and link. Keep prices and policies out of the system prompt when they are in the KB. |
| 10 Configuration | Phase 7 | Use the stated model, voice and first message. Fill anything blank with this skill's defaults, and say which defaults you chose. |
| 11 Test scenarios | Testing (step 5 below) | One test per scenario. |

After drafting the prompt, run a **coverage check** and show it as a short list:

- every §5 skill has a goal in Instructions;
- every live §7 integration has a tool, and every tool has a prompt instruction;
- every §6 rule appears in Principles;
- every playbook rule the spec cites is enforced somewhere.

Fix gaps before deploying. The user approved the spec, not the prompt wording, so there is no second approval gate unless the coverage check forced a design change; in that case update the spec and ask once.

## 4. Deploy to FlowForge

Follow Phase 10B, preferring the FlowForge MCP tools (`flowforge_create_assistant`, `flowforge_update_assistant`, `flowforge_assistant_lifecycle`, `flowforge_run_test`) and the `flowforge` skill's rules over raw REST calls when the MCP is installed.

- **Connectors first.** FlowForge has no built-in calendar, booking or texting, so every live booking or SMS integration in spec §9 needs a webhook endpoint the agent can call. Build and test those connectors (e.g. n8n workflows calling the booking system's sandbox and the SMS provider) before creating the assistant, each with a direct test request, so the webhook tools point at endpoints that already work. Accounts the user must create come from the spec's Open questions; walk them through it rather than creating accounts yourself.
- Create the assistant from the generated config and capture its ID.
- Upload and link the knowledge base.
- **Phone number:** list existing numbers first. Buying a number spends money, so show the dry-run preview and get a yes before confirming. If the user doesn't want a number yet, say how to test from the FlowForge dashboard instead.
- Never place a call to a real person's number as a test without the user's explicit go-ahead.

## 5. Test before handing over

Turn each §11 scenario into a FlowForge test: the caller persona and situation as the test input, and the pass criteria as the expectation. Run them with `flowforge_run_test`. Write the results to `build/test-results.md`: scenario, pass or fail, and a one-line reason with a transcript excerpt for each failure.

Fix failures with the ARC-lite loop (Key Principle #8) before handing over. If a failure comes from the design rather than the wording, update the spec's Change log. Report honestly: "13 of 15 passed; the 2 failures are …" is a valid handover when the remaining fixes need the user's input.

## 6. Hand over and record

Save `prompt.md`, `config.json` and `test-results.md` in `build/`, and start `build/changelog.md` with the first entry. In the project's `STATUS.md` (two folders above `roles/`), fill the Demo section: assistant name and ID, the phone number or dashboard test link, and numbered steps to call it.

Then give the user numbered steps to try the demo, the test results in one line, and what to listen for (correct booking, sounding like the business, handling an upset caller). Before handing over, make the listening test call from `voice-realism.md` and add its five realism scenarios to the tests. Ask for feedback.

## 7. Iterate on feedback

For each round of feedback:

1. Decide whether it changes the design (skills, integrations, rules, personality) or only wording. Design changes go into the spec first, with a dated Change log line.
2. Run the Lossless Conversion Protocol (Phase 0.5) against the live assistant.
3. Make the change on a FlowForge branch, re-run the affected tests plus a quick happy-path test, and publish only when they pass.
4. Add a line to `build/changelog.md`: date, feedback, change, tests run, result.
