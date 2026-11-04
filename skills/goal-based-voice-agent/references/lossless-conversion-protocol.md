# Lossless Conversion & Iterative Update Protocol

This protocol applies whenever you are NOT building a voice agent from scratch. Use it for:

- **Conversions** — taking an existing prompt (from another agent, a document, a script) and restructuring it into a new agent (e.g., reformatting to SCRIPT, changing product positioning, removing a call phase)
- **Iterative updates** — editing a deployed agent's prompt (adding a new goal, changing a flow, rewriting a section)
- **Cloning with modifications** — starting from a working agent and modifying it for a new use case

The core discipline: **never silently drop functionality.** Every conversion and every update must preserve essential behavior unless the user has explicitly approved its removal. The most common failure mode is rewriting a section so thoroughly that references to critical tools, branches, or phrases get lost in the rewrite.

---

## Why This Matters

Voice agent prompts carry dense, load-bearing details that aren't obvious on first read:

- **Tool references** tell the LLM which tool to call and when. Drop the reference → the agent stops using the tool.
- **Specific branching conditions** determine flow. Drop a condition → prospects fall through the cracks.
- **Named stakeholders, URLs, phone numbers** are business-critical. Drop them → wrong info goes out on real calls.
- **Signature phrases and positioning** are intentional brand choices. Drop them → brand drift.
- **Deployed state** (attached tools, firstMessage, voice, mode) may differ from what the local prompt file says. Ignore this → conflicting config ships to production.

A conversion that looks like a clean rewrite on paper can silently break production. This protocol prevents that.

---

## Step 1: Inventory the Source State

**Before touching the prompt,** build a complete inventory. You need TWO sources of truth:

### 1a. The source prompt itself

Read the full source prompt. Enumerate everything that might be load-bearing:

- **Goals and their order** (Goal 1, 2, 2G, 3, 3A, 3B, 4, 4B, 5...) — the structural skeleton
- **Every tool call** — by name, every place it's referenced, and under what conditions it's called
- **Every branch and edge case** — "if X → do Y", "if empty → fallback to Z"
- **Every variable reference** — `{{first_name}}`, `{{company_name}}`, `{{email}}`, etc. and how each is used (confirm vs. ask vs. reference)
- **Every named stakeholder / URL / phone number / email / product name** — hard facts
- **Every "redline" and "always/never" rule** — explicit prohibitions
- **Every signature phrase** — intentional brand moments (openers, closers, reveals, taglines)
- **Speech patterns and behavioral rules** — filler words, backchanneling, interruption handling
- **Objection handlers** — by name, with their approach

### 1b. The deployed state (if the agent is already live)

**Critical — and easy to miss:** the local prompt file is NOT the source of truth for a deployed agent. The live agent may have:

- Different `toolIds` attached than the prompt's T — TOOLS section references
- A different `firstMessage` or `firstMessageMode` than expected
- A different voice, LLM, transcriber than the local config
- Custom settings (backchanneling, silence timeouts, background sound) configured in the dashboard

Always fetch the live agent state before making changes. The diff between the local prompt's claimed tools and the deployed agent's actual `toolIds` is a common source of bugs.

```bash
# Fetch current live state
curl -s "https://api.vapi.ai/assistant/$ASSISTANT_ID" -H "Authorization: Bearer $VAPI_KEY"
```

Inspect each attached tool:

```bash
curl -s "https://api.vapi.ai/tool/$TOOL_ID" -H "Authorization: Bearer $VAPI_KEY"
```

---

## Step 2: Categorize Essential Functionality

Classify every item from your inventory into one of four buckets. This lets you reason about what to preserve vs. what to change.

| Category | Examples | Preservation rule |
|----------|----------|-------------------|
| **Structural** | Goals, flow order, entry detection, handoff logic | Preserve unless explicitly changing structure. If restructuring, map old goals → new goals. |
| **Operational** | Tool calls, variable usage, capture logic, branching | Preserve every tool reference unless the tool is being intentionally removed. Every attached tool on the deployed agent MUST be referenced in the new prompt OR cleaned up from `toolIds`. |
| **Behavioral** | Speech texture, rapport cues, objection handling, interruption rules | Preserve verbatim unless intentionally changing personality. |
| **Informational** | Named stakeholders, product names, URLs, phone numbers, specific phrases | Preserve verbatim. Only change if the user explicitly says "change X to Y." |

---

## Step 3: Declare the Change Scope

Before editing, write down (to yourself, or in a short summary to the user):

1. **What is intentionally changing?** — "Removing the on-call demo path," "Renaming Northwind → Contoso AI," "Adding a self-reveal moment," etc.
2. **What is incidentally touched but must remain functionally equivalent?** — E.g., "Goal 2 is being rewritten with new beats, but the branching logic (demo / meeting / send info / callback / wrong person) must survive."
3. **What should NOT change?** — E.g., "Character speech patterns, objection handling, tool calls for Calendly, Priya handoff mention."

If the user asked for a specific change and you notice adjacent functionality that might be affected, **flag it and ask before removing**.

---

## Step 4: Preserve via Verbatim Clone or Semantic Equivalence

For every item in Step 1 that's NOT in the "intentionally changing" bucket:

**Verbatim clone** — copy the original text word-for-word into the new prompt. Use this for:
- Named stakeholders and product positioning
- Specific phone numbers, URLs, email addresses
- Redlines and compliance rules
- Signature phrases (opener greetings, closers, taglines)
- Speech texture and interruption rules

**Semantic equivalence** — preserve the functional behavior with restructured wording. Use this when the old text no longer fits the new structure (e.g., you're breaking one goal into three), but the behavior must be identical. Rule: the agent's observable behavior on an identical call should be indistinguishable before and after.

- Old: "If they ask for the demo, call `transfer_to_demo`." → New (in a no-demo version): remove entirely. But if it's still demo-capable, new wording like "If they agree to see it in action, hand off via `demo_handoff`" preserves the behavior.
- Old: "Capture their email with `store_variable`." → New: if `store_variable` is replaced by `book_calendly_appointment`, the new wording must still instruct the agent to capture + act on the email.

---

## Step 5: Diff-Check Before Deploy

After rewriting, run a checklist against your Step 1 inventory. For every item:

- [ ] Is it still in the new prompt?
- [ ] If not, is its removal intentional (in Step 3's "intentionally changing" list)?
- [ ] Does its new form preserve the original behavior (verbatim or semantic equivalence)?

**Tool-specific checks (HIGH PRIORITY):**

- [ ] For every tool in the deployed agent's `toolIds`, is there at least one explicit instruction in the new prompt for when to call it?
- [ ] For every tool call referenced in the new prompt, is the corresponding tool actually attached to the agent's `toolIds`?
- [ ] Are there any "orphan" tool instructions (references in the prompt to tools that aren't attached)?
- [ ] Are there any "orphan" attached tools (tools in `toolIds` with no instruction on when to call them)?

**Variable checks:**

- [ ] Every `{{variable}}` used in the old prompt still resolves in the new prompt (either kept, renamed intentionally, or explicitly removed)
- [ ] Confirm-don't-ask patterns preserved where variables are populated at call time

**Flow checks:**

- [ ] Every branch / edge case / fallback from the source is either preserved or intentionally removed
- [ ] Entry detection (for multi-entry agents) is preserved in Goal 1

**Run a grep:**

```bash
# Search the new prompt for any leftover references to removed concepts
grep -E "old_tool_name|old_stakeholder|removed_phrase" new_prompt.md

# Search the new prompt for every tool attached to the deployed agent
for tool in $DEPLOYED_TOOL_NAMES; do
  grep -c "$tool" new_prompt.md && echo "✓ $tool" || echo "✗ MISSING: $tool"
done
```

---

## Step 6: Document Intentional Removals

When you present the updated prompt to the user, explicitly list what was removed and why. Don't bury removals in a large summary — call them out:

```
Intentional removals (per your request):
- Goal 3A (Demo Handoff) — no demo in this version
- Goal 5 (Post-Demo Return) — scheduling happens inline now
- `transfer_to_demo_agent` tool reference — no longer needed
- "Northwind AI Workforce" product name → replaced with "Contoso AI"

Preserved verbatim:
- Beat 1-6 intro structure (updated wording, same logic)
- All 7 objection handlers
- Speech texture and interruption rules
- Priya mention after booking

Semantic equivalents:
- Old "use store_variable to log disposition" → new "note the disposition mentally" (store_variable wasn't a real tool)
- Old "Goal 3B Meeting Path" → new "Goal 3 Book the Meeting" (same behavior, renamed)
```

This gives the user a chance to catch missed removals before they ship.

---

## Common Failure Modes

### ❌ Rewriting Goal X without checking what tools it referenced

You rewrite "Goal 3: Book the Meeting" from scratch to clean it up. The original had instructions to call `book_calendly_appointment`. Your rewrite doesn't mention the tool. The agent stops booking.

**Fix:** Before rewriting any goal, grep the old version for every tool name. Preserve the tool call instructions in the new version (or explicitly mark them for removal in Step 3).

### ❌ Rewriting T — TOOLS section from the prompt template rather than the deployed state

You rewrite the Tools section based on the original skill template. The deployed agent has different tools attached (e.g., `check_calendly_availability`, `book_calendly_appointment`) that the template doesn't include. The new prompt still lists the old tools (`store_variable`, `end_call`) — which may not even exist.

**Fix:** Always rewrite the Tools section against the deployed agent's actual `toolIds`, not against a template.

### ❌ Dropping a branch because it "doesn't fit the new structure"

You restructure Goal 2 into beats. The old version had "if they say 'send me info' → capture email, confirm, soft-ask about follow-up." Your new beat structure doesn't have a place for that branch, so you drop it.

**Fix:** Branches are load-bearing. Preserve them after the main flow (e.g., "After delivering the CTA, LISTEN. What happens next determines your path: ... if they say 'send me info' ...").

### ❌ Forgetting about edge-case content (objection handlers, error handling, redlines)

You focus on the main flow. You forget the Support section at the bottom has 7 objection handlers and an "If asked if you are AI" rule. You rewrite the top of the prompt thoroughly but leave the bottom half untouched — until a user points out that half of it references the old product name or old flow.

**Fix:** The Support / Principles / Tools / User Information sections ALWAYS need a sweep for consistency with top-level changes. Use the "cleanup pass" pattern: after the main edit, sweep the full prompt for any reference to the old state.

### ❌ Changing personality in a conversion when the user only asked for a structural change

You're asked to convert a squad to a single agent. In the rewrite you clean up some wording you don't like — accidentally making the agent more formal / less warm / differently-paced.

**Fix:** Personality (Character section, speech texture, tone) is a separate dimension from structure. Preserve it verbatim unless the user explicitly asks for personality changes.

### ❌ Not fetching live state before editing a deployed agent

You update the local prompt file and push. Turns out the deployed agent had a hardcoded test `firstMessage` ("Hey, John??") that the user set for testing. Your PATCH wipes it because you used the local file as source of truth.

**Fix:** Always fetch live state first. PATCH only what you intend to change. For prompt-only updates, modify only `model.messages[0].content`, preserve everything else in the `model` object.

---

## Example: Correct Application

**Task:** Convert a Northwind squad intro+demo agent into a single Contoso AI agent with no live demo.

### Step 1: Inventory
- Source prompt: 28,654 chars, 6 Goals (1, 2, 2G, 3A, 3B, 4, 5)
- Tools referenced in prompt: `transfer_to_demo_agent`, `store_variable`, `end_call`
- Deployed agent toolIds: `check_calendly_availability`, `book_calendly_appointment`, `cc_handoff_to_demo` ← **different from prompt references, flag this**
- Stakeholders named: "Priya from Northwind" (not in original, added later)
- Branches to preserve: voicemail → hang up, gatekeeper → 2G, demo / meeting / send info / callback / wrong person

### Step 2: Categorize
- Structural: all Goals (1-5, 2G)
- Operational: Calendly tools (deployed but undocumented in source), entry detection, branches
- Behavioral: Avery persona, 6 beats, speech texture, objection handling
- Informational: product name (changing Northwind → Contoso AI), Priya handoff mention

### Step 3: Change scope
- **Intentionally changing:** Remove Goal 3A/5 (demo path), rename product to Contoso AI, add self-reveal in Goal 4, new objection handler for "who are you really?"
- **Incidentally touched, preserve equivalence:** Goal 2 beats (rewritten wording, same branching), Goal 3B renamed to Goal 3 (Book the Meeting)
- **Do NOT change:** Beat 1 identity confirm, 7 objection handlers, speech texture, interruption rules, Gatekeeper Path

### Step 4 & 5: Preserve + Diff-check
- Tool instructions: removed `transfer_to_demo_agent` and `store_variable` references (intentional), added `check_calendly_availability` + `book_calendly_appointment` instructions (matching deployed tools) — **this is the step that was skipped, causing the booking break**
- Verify every attached tool has prompt instructions: `check_calendly_availability` ✓, `book_calendly_appointment` ✓, `end_call` ✓
- Verify every prompt-referenced tool is attached: all three above ✓
- Remove orphan tool `cc_handoff_to_demo` from `toolIds` (leftover from squad clone, no demo path in new version)

### Step 6: Document
Present intentional removals to the user so they can catch misses.

---

## Quick-Reference Checklist

Copy this when doing a conversion or update:

```
□ Step 1a: Read full source prompt. Inventoried goals, tools, branches, stakeholders, variables, signature phrases.
□ Step 1b: Fetched deployed agent state. Listed actual toolIds, firstMessage, firstMessageMode, voice, LLM.
□ Step 1c: Inspected each attached tool's schema.
□ Step 1d: Flagged mismatches between prompt-referenced tools and actually-attached tools.
□ Step 2: Categorized inventory items (structural / operational / behavioral / informational).
□ Step 3: Declared change scope (what changes, what stays, what's incidentally touched).
□ Step 4: Preserved unchanged items verbatim OR with documented semantic equivalence.
□ Step 5: Diff-checked the new prompt:
    □ Every attached tool has prompt instructions (or is being removed from toolIds).
    □ Every prompt-referenced tool is attached (or scheduled to be added).
    □ Every branch / fallback / edge case preserved or intentionally removed.
    □ Every named stakeholder, URL, variable preserved or intentionally changed.
    □ Support / Policies / Tools / User Information sections swept for consistency.
□ Step 6: Documented intentional removals and semantic equivalents when presenting the change.
□ PATCH only what changed. Fetch live state first. Never partial-PATCH nested objects.
```
