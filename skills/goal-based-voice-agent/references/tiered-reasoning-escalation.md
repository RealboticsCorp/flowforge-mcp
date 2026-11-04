# Tiered Reasoning Escalation Pattern

A two-agent squad architecture that uses GPT-4.1 Mini as the front-line agent and silently escalates to GPT-5.4 Mini only when the conversation requires reasoning capability that 4.1 Mini can't handle reliably. The caller never knows the handoff happened. Same voice, same persona, same conversational flow — just a smarter brain when the moment demands it.

This is fundamentally an **economic optimization pattern.** The vast majority of voice agent calls don't need reasoning capability — they're voicemails, immediate hang-ups, or amicable callers who just say yes. Running a $0.75/$4.50 reasoning model on those calls burns margin. But for the small percentage of calls that need genuine objection handling, complex qualification, or emotional nuance, $0.40/$1.60 isn't enough — you lose conversions you could have won.

This pattern lets you have both: 4.1 Mini economics on the easy 80%, 5.4 Mini reasoning quality on the hard 20%.

---

## Table of Contents

1. When to Use This Pattern
2. Architecture Overview
3. Handoff Trigger Logic
4. Build Sequence (Six Phases)
5. The Mirror Prompt Pattern
6. Voice and Persona Consistency Requirements
7. Handoff Tool Configuration
8. Cost Modeling and Volume Math
9. Common Failure Modes & Fixes
10. Reference Doc Cross-Map
11. FlowForge Migration Notes (Future)

---

## 1. When to Use This Pattern

This pattern is justified when **all four** of these are true:

- **High call volume** — at least hundreds of calls per day, ideally thousands. The economic case depends on the easy-call cost savings being meaningful at scale.
- **Variable call complexity** — the call distribution has a long tail. Most calls are short (voicemail, hang-up, easy yes), but some require persistent objection handling, complex qualification, or emotional nuance.
- **Lead value justifies reasoning quality on hard calls** — if a converted lead is worth $50+, the 5.4 Mini cost on the small percentage of escalated calls pays for itself many times over in conversion lift.
- **Single LLM choice is unsatisfying either way** — pure 4.1 Mini loses conversions on the hard calls, pure 5.4 Mini wastes money on the easy ones.

**Don't use this pattern when:**
- All calls are roughly equally simple (just use 4.1 Mini)
- All calls are roughly equally complex (just use 5.4 Mini)
- Lead values are too low to justify the engineering complexity
- Call volume is small enough that 5.4 Mini for every call is affordable

**Concrete fits:**
- High-volume legal intake — most callers are voicemails or quick disqualifications, but qualified leads with objections are worth $200–500+ each
- Outbound SDR campaigns — most prospects don't pick up or hang up immediately, but the ones who engage need real reasoning
- Accounting-firm inbound — most callers want to be transferred quickly, but tax-question deep-dives need 5.4 reasoning
- FormFast checkout pilot — most users complete or abandon quickly, but hesitant users with complex questions are the high-value escalation case

---

## 2. Architecture Overview

```
Squad: [Agent Name] System

┌─────────────────────────────────────────────────────────┐
│  Agent A: Front-Line (GPT-4.1 Mini)                     │
│  - Handles greeting, qualification, easy paths          │
│  - Same voice, persona, name as Agent B                 │
│  - Owns the call from connect to (usually) end          │
│  - Has a handoff_to_reasoning tool                      │
│  - Triggers handoff on specific behavioral patterns     │
└─────────────────────────────────────────────────────────┘
                         │
                         │ Silent handoff (handoff tool)
                         │ - contextEngineeringPlan: userAndAssistantMessages
                         │ - variableExtractionPlan: passes call state
                         │ - No "transferring you" announcement
                         ▼
┌─────────────────────────────────────────────────────────┐
│  Agent B: Reasoning (GPT-5.4 Mini)                      │
│  - Same voice, persona, name as Agent A                 │
│  - Same SCRIPT structure, optimized for reasoning model │
│  - reasoning_effort: low, verbosity: low                │
│  - Inherits full conversation history via handoff       │
│  - Finishes the call (no handoff back to A)             │
└─────────────────────────────────────────────────────────┘
```

**Key architectural rules:**

1. **Same voice, same persona, same name.** The Character (C) section is identical between both agents. Persona description, speech patterns, filler words, name — everything that affects the caller's perception of who they're talking to is identical. The voice provider, voice ID, and voice model in the VAPI config must match exactly.

2. **Same SCRIPT structure, different prompt style.** Both agents share the same Scenario, Character, Role, and Tools sections. The Instructions and Policies sections differ in *style* — Agent A uses 4.1 Mini's literal-instruction-following pattern (enumerated branches, scripted transitions), while Agent B uses 5.4 Mini's goal-based reasoning pattern (outcome-based goals, principle-based edge cases). Both produce equivalent behavior; the prompts just play to each model's strengths.

3. **One-way escalation only — enforced by omission.** Agent B never hands back to Agent A. The mechanism is structural, not instructional: Agent B does not have the `handoff_to_reasoning` tool in its `model.toolIds`, and Agent B's prompt contains zero references to escalation, tiered systems, front-line agents, or the existence of Agent A. There is no "do not hand back" Policy — that would introduce the concept of handing back into Agent B's context for no benefit. Agents don't attempt behaviors that aren't in their tools and prompts. The cost optimization is on the average call — most never escalate at all.

4. **Handoff is invisible to the caller.** No "let me transfer you," no pause, no voice change. The caller experiences a single continuous conversation. This is why same-voice, same-name, and the silent-handoff tool configuration are non-negotiable.

5. **Agent B inherits full context.** The handoff tool is configured with `contextEngineeringPlan: userAndAssistantMessages` so Agent B sees the entire conversation history. The `variableExtractionPlan` passes structured state (caller name, qualification answers, tools fired, etc.) so Agent B doesn't have to re-collect anything.

---

## 3. Handoff Trigger Logic

The decision of *when* to escalate is the most important design choice in this pattern. Trigger too eagerly and you lose the cost savings. Trigger too late and 4.1 Mini has already lost the call.

The recommended trigger model is **behavioral signals + turn count**, encoded in the handoff tool's `description` field so the LLM evaluates the trigger conditions on every turn.

### Behavioral signals that should trigger escalation

These are call patterns that 4.1 Mini handles poorly and 5.4 Mini handles well:

- **Objection persistence pattern** — the caller has raised the same objection 2+ times despite the agent's HEART framework attempts. This is the most common and highest-value escalation trigger. 4.1 Mini follows the HEART script literally; 5.4 Mini reasons about *why* the objection isn't resolving and adapts.
- **Complex multi-part questions** — caller asks something that combines multiple concerns ("So if I sign this and then change my mind and want a refund but I've already started talking to a lawyer, what happens?"). 4.1 Mini answers part of it and misses the rest; 5.4 Mini reasons through all the conditions.
- **Repeated misunderstandings** — the agent has asked the caller to repeat themselves 2+ times AND the caller is frustrated, OR the agent has misinterpreted intent twice. This signals the caller's communication style requires more nuanced parsing.
- **Emotional escalation beyond standard empathy** — caller is crying, panicking, or expressing acute distress that exceeds the standard sympathy patterns. 4.1 Mini's scripted empathy ("I'm so sorry to hear that") becomes inadequate; 5.4 Mini reads the emotional weight and adapts.
- **Out-of-scope but adjacent requests** — caller is asking about something the agent wasn't designed for but related to the use case ("I have a workers' comp case AND a personal injury case from the same incident, can you help with both?"). 4.1 Mini disqualifies or deflects; 5.4 Mini reasons about whether to handle, escalate to human, or capture for routing.
- **Caller explicitly requests a manager or expert** — even after the agent's first attempt to address their concern. This is a hard signal that 4.1 Mini's response was inadequate.

### Turn-count thresholds

Pure behavioral triggers are subjective and inconsistent. Pair each with a turn-count threshold to make escalation decisions deterministic:

- **2+ failed objection attempts** — the caller has rejected the agent's first HEART pass and the agent is on its second attempt. If the second attempt also doesn't land, escalate before attempting a third.
- **3+ clarification rounds on the same topic** — caller and agent have been circling the same subject for three turns without progress.
- **5+ turns into an off-script branch** — caller has driven the conversation off the happy path for five or more turns and the agent hasn't recovered to the planned flow.
- **Total call length > 8 minutes without reaching the close** — the call is taking longer than the average qualified call but hasn't progressed to the agreement step. This usually means 4.1 Mini is stuck.

### How to encode triggers in the handoff tool description

The handoff tool's `description` field is what the LLM reads to decide whether to call the tool. Be explicit, behavioral, and pair conditions with turn counts:

```
Use this tool to silently transfer the call to your supervisor 
when you encounter situations that require deeper reasoning 
than you can provide. Do NOT announce the transfer — just call 
the tool and the supervisor will continue the conversation 
seamlessly with the same voice and persona.

Trigger conditions (call the tool when ANY of these are true):

1. The caller has raised the same objection 2 or more times 
   and your HEART framework attempts have not resolved it.

2. The caller has asked a multi-part question or a question 
   that requires reasoning about multiple conditions, 
   exceptions, or hypotheticals.

3. The caller is showing signs of acute emotional distress 
   that go beyond what standard empathy phrases can address.

4. The caller has explicitly asked to speak with a manager, 
   expert, or someone more senior — even after you've 
   addressed their initial concern.

5. The caller is asking about something adjacent to your 
   scope but that requires judgment about whether and how 
   to help (e.g., overlapping case types, edge-case 
   eligibility questions).

6. You have been on the same topic for 3+ turns without 
   progress, OR the call has exceeded 8 minutes without 
   reaching the close.

DO NOT trigger this tool for:
- Simple disqualifications (handle directly)
- Voicemail or hang-up scenarios (these never reach trigger 
  conditions)
- Standard objections that resolve on the first HEART attempt
- Callers who are amicable and ready to book — handle these 
  yourself, this is what you're optimized for
```

The LLM will read this description on every turn and decide whether to call the tool. Because 4.1 Mini follows instructions literally, this enumerated list works well. The turn-count conditions ("2 or more times," "3+ turns," "8 minutes") give 4.1 Mini concrete numerical thresholds it can pattern-match against the conversation state.

---

## 4. Build Sequence (Six Phases)

This pattern requires building two coordinated agents. The build order matters — you must build Agent A first, validate it independently, then derive Agent B from it, then bind them as a squad.

### Phase 1: Build Agent A (4.1 Mini front-line) using the standard wizard

Run the standard goal-based-voice-agent wizard from Phase 0 through Phase 9 with these specific choices:

- **Phase 0.25 — Platform Selection:** VAPI
- **Phase 7 — LLM:** GPT-4.1 Mini. Load `references/gpt-4.1-mini-voice-guide.md` and apply its enumeration-heavy patterns to Instructions and Policies.
- **Phase 7.5 — Architecture Assessment:** Single agent (you'll convert to a squad later — don't pre-architect for handoff yet).

The output of this phase is a complete, deployable single-agent config for Agent A. Do not add the handoff tool yet — that comes in Phase 4 of this build sequence.

**Why build A first:** You need a fully-formed, tested 4.1 Mini agent before you can derive the 5.4 Mini mirror. Building both in parallel leads to drift and mismatched behavior. Build A, validate A, then mirror.

### Phase 2: Validate Agent A standalone

Deploy Agent A and run the VAPI Simulations suite per `references/vapi-simulations.md`. This phase is non-negotiable — Agent A is the foundation, and any defect in A will propagate to B.

Build the simulation suite with two scenario tiers:

- **Tier 1 — Easy paths:** voicemail detection, hang-up handling, amicable yes from a qualified caller, simple disqualification. These should pass on Agent A alone with high confidence.
- **Tier 2 — Hard paths:** persistent objections, complex multi-part questions, emotional callers, out-of-scope requests. These will likely fail on Agent A alone — that's expected and is part of how you validate the trigger conditions in Phase 4.

Do not proceed to Phase 3 until Tier 1 scenarios pass at >90% on Agent A. If Tier 1 is failing, fix Agent A first — escalation to B can't compensate for a broken front-line.

### Phase 3: Mirror-convert Agent A to Agent B (5.4 Mini)

Use the conversion guide and the 5.4 Mini guide together:

1. Load `references/conversion-guide.md` for the goal-based methodology
2. Load `references/gpt-5.4-mini-voice-guide.md` for the 5.4-specific patterns
3. Run the **Lossless Conversion Protocol** (`references/lossless-conversion-protocol.md`) to ensure no functionality is silently dropped during the conversion

The conversion is a 4.1 Mini → 5.4 Mini migration following the 9-step checklist in the 5.4 guide Section 7:

1. Switch the model to gpt-5.4-mini, leave the prompt unchanged at first
2. Set `reasoning_effort: low` and `verbosity: low`
3. Convert Instructions from enumerated branches to outcome-based goals
4. Collapse behavioral rules into the Character description
5. Replace scripted edge cases with principles
6. Convert scripted objection responses to substance-only
7. Cut Policies by ~50% (remove rules now implicit in the reasoning model)
8. Run evals to compare against the 4.1 baseline

**Critical preservation requirements:**

- **Same Character section, verbatim.** Persona, voice, speech patterns, filler word examples, interruption handling — all of this stays identical. Voice consistency requires Character consistency.
- **Same Tools section, minus the handoff tool.** Both agents have the same tool inventory (CRM lookup, transfer, send_agreement, etc.). The only difference is Agent B does NOT have the `handoff_to_reasoning` tool — it's the reasoning agent, it doesn't escalate further.
- **Same Scenario section.** Both agents are operating in the same business context with the same value proposition.
- **Same Role/Objectives.** Both agents have the same KPIs and accountability metrics. The whole point is they're functionally interchangeable from the caller's perspective.

**Critical omission requirements (don't introduce concepts that aren't relevant):**

- **No mention of Agent A, the front-line, the tier system, or escalation in Agent B's prompt.** From Agent B's perspective, it's just an agent handling calls. The only place tier-related concepts appear in Agent B is the `escalation_reason` / `open_objection` variables in the inherited context that the Opening Context section reads — and that section uses the information to inform Agent B's approach without narrating it to the caller.
- **No "do not hand back" or "do not escalate further" rules in Agent B's Policies.** Agent B doesn't have a handoff tool. It has no instruction telling it that handing off is even a possibility. Adding a negative rule introduces the concept of handing off into Agent B's context window for no benefit — pink-elephant priming. Omission is the enforcement mechanism, not negative instruction.
- **No "you are the reasoning agent" framing.** Don't tell Agent B that it's the smart one, the supervisor, the reasoning tier, or anything that implies it sits above another agent. It's just "the agent." The whole tier system is invisible to Agent B itself.

The Instructions and Policies sections are where the divergence happens — same destination, different driving style.

### Phase 4: Add the handoff tool to Agent A

Now add the `handoff_to_reasoning` tool to Agent A's tool set. This is a VAPI `handoff` type tool (not `transferCall` — that's for external phone numbers).

**Tool configuration:**

```json
{
  "type": "handoff",
  "function": {
    "name": "handoff_to_reasoning",
    "description": "[USE THE FULL DESCRIPTION FROM SECTION 3 ABOVE]"
  },
  "destination": {
    "type": "assistant",
    "assistantName": "[Agent B's exact assistant name]"
  },
  "contextEngineeringPlan": {
    "type": "userAndAssistantMessages"
  },
  "variableExtractionPlan": {
    "schema": {
      "type": "object",
      "properties": {
        "caller_first_name": { "type": "string" },
        "caller_phone": { "type": "string" },
        "caller_email": { "type": "string" },
        "qualification_status": { 
          "type": "string",
          "enum": ["qualified", "disqualified", "in_progress"]
        },
        "case_type": { "type": "string" },
        "tools_already_fired": { 
          "type": "array", 
          "items": { "type": "string" } 
        },
        "escalation_reason": { 
          "type": "string",
          "description": "Why you're handing off — be specific about which trigger condition fired"
        },
        "open_objection": { 
          "type": "string",
          "description": "If escalating due to an unresolved objection, summarize what the caller is objecting to and what you've already tried"
        }
      },
      "required": ["escalation_reason"]
    }
  }
}
```

Notes on this configuration:

- **`type: "handoff"`** — this is the VAPI tool type for silent assistant-to-assistant transfers within a squad. Not `transferCall`, which is for external PSTN destinations.
- **`assistantName`** — uses the human-readable name rather than `assistantId` so the squad config is more portable across environments. Make sure Agent B's name in VAPI exactly matches.
- **`contextEngineeringPlan: userAndAssistantMessages`** — passes the full conversation history to Agent B. The other option (`messages` only) doesn't include the system prompt context Agent B needs.
- **`variableExtractionPlan`** — extracts structured state at the moment of handoff. The `escalation_reason` field is critical — it tells Agent B why it was called in, which informs how it should pick up the conversation.
- **`open_objection`** — when the trigger is a stuck objection, Agent B needs to know what the objection is and what's already been tried, so it doesn't repeat 4.1 Mini's failed approach.

### Phase 5: Set the opening context for Agent B

Agent B always enters mid-conversation. There is no fresh-call path for Agent B — Agent A is the only entry point to the squad, and Agent B is only ever invoked via handoff. The full prior conversation history will already be in Agent B's context window when it takes its first turn, courtesy of `contextEngineeringPlan: userAndAssistantMessages` plus the handoff variables.

Given this, the opening of Agent B's Instructions should not ask Agent B to reason about *whether* it's mid-conversation. That conditional doesn't exist in production. It's a wasted cognitive layer and an unnecessary failure surface. Just tell Agent B the truth about the context it's always in, and direct it to continue.

**Important framing principle:** Don't introduce concepts Agent B doesn't need to know about. Words like "front-line counterpart," "supervisor," "Agent A," "escalation," "handoff," and "tier system" should not appear in Agent B's prompt. Agent B isn't part of a tier system from its own perspective — it's an agent that handles calls that come in already underway. Frame the opening from Agent B's point of view, not the system designer's point of view.

Add this as the opening of Agent B's Instructions, before Goal 1:

```
## Opening Context

You are taking this call mid-conversation. The full 
conversation history up to this moment is already in your 
context — read it carefully. The caller has been talking 
to "you" the whole time and does not perceive any change.

You are also receiving structured context from the call:
- escalation_reason: Why this moment in the call needs 
  your attention
- open_objection: What the caller is objecting to (if any) 
  and what's already been tried
- tools_already_fired: What's already been done in the call
- qualification_status: Where the call stands

Your first turn is a direct continuation. Respond to the 
caller's most recent message naturally, as if you've been 
on the call all along. Do not greet, do not introduce 
yourself, do not summarize the call back to them, do not 
acknowledge any change. Just continue the conversation 
from exactly where it left off, without skipping a beat.

If there is an open objection, take a fundamentally 
different angle than what was already tried. Don't repeat 
an approach that already failed — reason about why it 
failed and try something different.
```

This is declarative, not conditional. It tells Agent B what its situation always is, and what to do in that situation. No branching logic, no "if fresh / else mid-conversation" structure, no extra reasoning step before the first turn.

Without this framing, Agent B's default behavior will be to greet — every voice agent prompt's Instructions begin with "Hi, thank you for calling..." and Agent B will pattern-match on that without specific direction otherwise. This opening section overrides that default with the actual operating reality.

### How Agent B Should Respond

Once the Opening Context is set, Agent B needs guidance on *how* to respond — not just to its first turn after entry, but to every turn it handles. This is where the reasoning-model investment pays off. The technique is the central reason 5.4 Mini exists in this pattern: it should think carefully about what the caller is actually concerned with, reach for the simplest response that resolves the concern, and only escalate the explanation strategy if that response doesn't land.

The instruction should give the model the principle and the available tools, then trust the reasoning to handle execution. Reasoning models will mechanically apply mechanical instructions — if you script a sequence ("always answer first, then offer a metaphor, then offer social proof"), the model will execute that sequence on every turn including the ones where it doesn't fit.

Add this section to Agent B's Instructions, after the Opening Context and before Goal 1:

```
## How to Respond

Every time the caller says something, think carefully about 
what they're actually asking for or concerned about. Often 
the surface question and the underlying concern are 
different, and what resolves the conversation is addressing 
the underlying concern.

Respond in a way that feels genuine and personal to this 
specific caller in this specific moment. Avoid scripted or 
canned phrasing. The caller has just told you, in their own 
words, what's on their mind — your response should sound 
like it was built for what they actually said, not for a 
generic version of it.

## Reach for the simplest answer first

Default to the shortest response that fully addresses what 
the caller asked. If a one-sentence direct answer resolves 
their concern, give the one-sentence answer. Do not pad it 
with metaphors, social proof, or additional context that 
the caller didn't ask for. The simplest sufficient response 
is almost always the right response.

If the caller signals that the simple answer didn't land — 
they're confused, they push back, they ask the same thing 
in a different way — then escalate your explanation 
strategy. You have several tools available, in rough order 
of escalation:

- A direct, plain-language answer
- A relatable metaphor or analogy that reframes the idea 
  in terms the caller will recognize from their own life
- Social proof — what other people in similar situations 
  have done, and what they found when they did
- Acknowledging the limits of what you can explain over the 
  phone, and offering the next step (a consultation, a 
  human expert, written follow-up)

Use one of these per turn, not all of them stacked in a 
single response. Each layer is a separate attempt to land 
the same point — if the previous layer didn't work, the 
next one might. If multiple layers don't land, that's a 
signal to move forward rather than keep explaining.

## When the caller's input is unclear, clarify before responding

Phone calls produce noisy input. Callers interrupt 
themselves, use slang, misspeak, lose their train of 
thought, or use vocabulary you can't quite parse. 
Transcription can also garble what they said into something 
nonsensical. When you receive an input that doesn't make 
sense in context, or that you cannot confidently interpret, 
do not guess at what they meant and respond as if your 
guess was right. That sends the conversation down the wrong 
path and the caller has to backtrack to fix it.

Instead, ask them to repeat or clarify. Frame it as your 
issue, not theirs: "Sorry, I think I missed that — could 
you say it again?" or "I want to make sure I understood 
you right — were you asking about X or Y?" The cost of one 
clarifying turn is much lower than the cost of an entire 
exchange built on a misread.

Use this only when input is genuinely unclear. Don't 
clarify when you can reasonably interpret what they said 
— that turns into stalling and feels evasive.

## Complexity, not length, drives pacing

Simple ideas can be delivered completely in one turn. A 
direct answer to a clear question fits in one or two 
sentences and is done. Don't artificially break that into 
multiple turns — the caller asked, give them the answer.

Complex ideas — ones where the caller has to hold multiple 
concepts simultaneously, or where understanding builds on 
prior understanding — should be broken into a sequence of 
short turns. Make one point, see how it lands, then 
continue. People listening on a phone tune out after about 
fifteen seconds of unbroken speech, and they can only hold 
one new idea at a time. A complete answer to a complex 
question delivered in a single sixty-second monologue will 
not be heard.

## When you've explained multiple ways and the caller is still stuck, check whether you're answering the right question

If you've worked through the direct answer, tried a 
different angle like a metaphor, brought in social proof, 
and the caller is still confused or disagreeing, the most 
likely reason is that you've been answering the wrong 
question all along. The caller's surface words pointed you 
toward one concern, but their actual concern is something 
different, and your explanations — however well-crafted — 
have been resolving a problem they didn't have.

Before continuing to escalate or push, pause and state your 
current understanding of their concern back to them. Give 
them a chance to either confirm you've got it right or to 
correct you. Something along the lines of: "I want to make 
sure I'm actually answering what you're asking. It sounds 
to me like the real concern is [your read of their 
underlying concern] — is that right, or am I missing 
something?"

If they confirm, you now know the prior turns just didn't 
land and you can try yet another angle on the same problem. 
If they correct you, you have a different problem to solve 
and your prior responses can be set aside.

This is a fallback for genuinely stuck conversations — 
roughly three rounds on the same unresolved point. Don't 
deploy it as a default check-in pattern. The point is 
diagnostic, not procedural.
```

That's the section. It's longer than earlier versions because it covers five distinct concepts — addressing the underlying concern, simplicity-first with progressive disclosure, clarifying genuinely unclear input, complexity-based pacing, and diagnostic reconfirmation when stuck — but each sub-section is principle-based rather than procedural.

A few notes on why it's structured this way:

- **The principle is "reach for the simplest sufficient response, escalate only when needed."** Everything else — which metaphor to use, when to bring in social proof, when to defer to a human — is one possible *expression* of that principle. The reasoning model will choose appropriately if it knows the available tools and the criterion for escalating ("the previous layer didn't land").

- **The escalation list is unordered in practice.** It's described as "rough order of escalation" rather than a strict sequence so the model has license to skip steps when context demands. A caller asking a factual question should get the direct answer, not a metaphor first. A caller who's emotionally stuck might need social proof before the direct answer. The model should reason about what fits.

- **Check-ins emerge from pacing, not from a rule.** The instruction to "see how it lands" between turns produces natural reaction-reading. There's no separate rule about appending "does that make sense?" to every response, because that would deploy mechanically on simple turns where it isn't needed.

- **Clarification is framed positively but bounded.** The model is told to clarify when input is unclear, and explicitly told *not* to clarify when input is clear. The framing — "frame it as your issue, not theirs" — gives a stylistic direction without scripting the exact words.

- **Complexity vs. length distinction is explicit.** The previous version of this section conflated the two and produced over-correction toward terse responses. The new version says simple ideas can be complete in one turn, complex ideas need pacing. The dimension is *what the caller has to hold in their head*, not how many sentences fit in the response.

- **No mechanical "always end with a question."** Healthy pacing produces natural reaction points without templated check-in language.

- **Diagnostic reconfirmation is bounded as a fallback, not a default.** The "check whether you're answering the right question" sub-section is positioned to fire only after the model has already tried multiple angles and the caller is still stuck. It's framed as a recovery move for genuinely stuck conversations, not as a routine check-in. Without that bounding, the model would deploy reconfirmation on every objection — which would feel patronizing, like a customer service rep who keeps saying "let me make sure I understand your concern" before answering anything. The bound (~three rounds on the same unresolved point, presupposes prior escalation attempts) restricts the behavior to its actual use case.

The general meta-rule: when writing instructions for a reasoning model, give it the principle, the goal, and the tools available — then trust the reasoning to handle execution. Mechanical sub-instructions become mechanical behaviors. Equally important: instructions framed at the extremes (length, frequency, repetition, completeness) will be interpreted at the extremes — every prompt edit needs a sanity check for "what's the worst literal reading of this, and would the model do that?"

### Phase 6: Deploy as a VAPI squad and validate

Follow the standard VAPI squad deployment from SKILL.md Phase 10A:

1. Create both assistants in VAPI (Agent A and Agent B)
2. Create the `handoff_to_reasoning` tool via the VAPI REST API (the MCP doesn't support handoff type as of writing — confirm in `references/vapi-config-reference.md`)
3. Update Agent A's `model.toolIds` to include the handoff tool ID
4. Assign the phone number to **Agent A only** (the entry assistant). Agent B is reachable only via handoff, not directly.
5. Run the VAPI Simulations suite against the squad

**Squad-specific simulation scenarios to add:**

- **Escalation triggers correctly:** Build a scenario where the caller raises a persistent objection. Verify Agent A escalates after the second failed attempt, not before, not on the third.
- **Escalation does not trigger inappropriately:** Build a scenario where the caller is amicable and books on the first ask. Verify Agent A handles it end-to-end without escalating.
- **Voice consistency across handoff:** Listen to recordings of test calls that escalated. Verify the voice sounds identical before and after the handoff. Any audible difference means the voice config doesn't match between the two assistants.
- **Context inheritance works:** Verify Agent B references information collected by Agent A without re-asking ("So you mentioned you were rear-ended in Glendale on Tuesday...").
- **No double-greeting:** Verify Agent B never says "Hi, thank you for calling..." when entering via handoff.
- **One-way escalation:** Verify Agent B never tries to hand back to Agent A.
- **Personalized response quality:** Build a scenario where the caller raises an objection with specific, idiosyncratic phrasing ("I just don't want to feel boxed in"). Verify Agent B's response (a) addresses what the caller is actually concerned with rather than the surface objection type, and (b) sounds custom-crafted rather than templated. The pass criterion is whether the response would have made sense for *this specific caller's words*. If the response could have been pre-written and dropped in for any caller with the same objection category, the model isn't actually reasoning about the caller — it's pattern-matching. Also flag the inverse: if Agent B mechanically restates the caller's words on every utterance, the **How to Respond** section is over-specified and needs to be loosened.
- **Pacing across multi-point answers:** Build a scenario where the caller raises a concern that genuinely requires multiple points to resolve (e.g., "I'm worried about cost AND I don't trust online services AND I'm not sure I have a strong case"). Verify Agent B handles this as a sequence of short turns — addressing one concern, pausing for reaction, continuing — rather than monologuing through all three concerns in a single response. Time the longest individual response: anything over 15 seconds of spoken audio is likely too long for the caller to track.
- **Progressive disclosure on persistent objections:** Build a scenario where the caller raises an objection, Agent B gives a direct answer, and the caller pushes back ("I still don't know..."). Verify Agent B's *next* turn shifts strategy — to a metaphor, an analogy, or social proof — rather than repeating a slightly reworded version of the same direct answer. The escalation should be visible: each layer is a different angle on the same underlying point, not a louder version of the previous layer.
- **Simplicity-first on factual questions:** Build a scenario where the caller asks a simple factual question ("How long does the consultation take?"). Verify Agent B answers with the time and stops, without padding the response with metaphors, social proof, or unsolicited reassurance. If Agent B is over-explaining factual questions, the simplicity-first principle isn't being applied or the progressive disclosure list is being read as a checklist.
- **Clarification on ambiguous input:** Build a scenario where the caller's transcribed input is partially garbled or contains ambiguous slang ("Yeah I'm just kinda iffy on the whole, you know, situation"). Verify Agent B asks a clarifying question rather than guessing at the meaning. Also build the inverse: a scenario where the caller's input is clear but informal ("yeah I think I'm good"). Verify Agent B does NOT clarify in this case — it responds directly.
- **Reconfirms understanding when stuck:** Build a scenario where the caller's surface objection points to one concern but their actual concern is something different. For example, caller says "I just don't think this is for me" — Agent B reads this as a value objection and responds about the firm's track record. Caller pushes back: "no, that's not what I meant." Agent B tries social proof. Caller pushes back again. Verify Agent B's third or fourth response is a reconfirmation of understanding ("It sounds to me like the real concern is...") rather than yet another explanation tool. The pass criterion is that Agent B catches the mismatch by asking instead of continuing to misfire. Also build the inverse: a scenario where Agent B correctly understands the concern from turn one. Verify Agent B does NOT deploy reconfirmation prematurely just because the caller is taking a few turns to be convinced.

---

## 5. The Mirror Prompt Pattern

The single biggest implementation challenge of this pattern is keeping Agent A and Agent B functionally equivalent while their prompts diverge stylistically. This requires discipline.

### The "shared core, divergent style" model

Think of the SCRIPT prompt as having two layers:

**Shared core (identical across A and B):**
- Scenario (S) — same business context
- Character (C) — same persona, voice, speech patterns
- Role (R) — same job description, KPIs
- Tools (T) — same tool inventory (minus the handoff tool on B)
- Knowledge base references — same supporting documents
- Caller information — same variable schema

**Divergent style (different per agent):**
- Instructions (I) — A enumerates, B reasons
- Policies (P) — A is rule-heavy, B is principle-heavy
- Support (s) — A scripts objection responses, B captures objection substance
- Edge cases — A scripts each one, B states principles

When you make changes during ongoing iteration, you have to decide which layer is being changed:

- **Shared core change** → update both A and B identically
- **Style-specific change** → update only the relevant agent

If you update only one agent for what should be a shared-core change, the agents will drift apart and behave differently from the caller's perspective. That's the failure mode this pattern lives or dies by.

### Maintaining mirror discipline during iteration

Every iteration to this squad needs to follow this checklist:

1. **Identify the change layer.** Is this a shared-core change (e.g., new policy, new tool, persona update) or a style-specific change (e.g., better Roughly example for one model)?

2. **For shared-core changes:** Edit both prompts in lockstep. Use the Lossless Conversion Protocol in both directions — verify the change preserves functionality on both sides.

3. **For style-specific changes:** Edit only the relevant prompt, but verify the *outcome* still matches the other side. If you tighten 4.1 Mini's enumeration of objection responses, run sim scenarios on both A and B to confirm B is still producing equivalent outcomes via reasoning.

4. **Always run sim scenarios on both agents independently** before deploying. Run the easy-path Tier 1 scenarios on A, run the hard-path Tier 2 scenarios on B, and run the escalation-trigger scenarios on the squad as a whole.

5. **Voice consistency check on every deploy.** Listen to a test call recording. The voice should be indistinguishable across the handoff. Any drift means the voice config differs.

### Naming convention for clarity

In the squad config, name the agents to make their roles obvious:

- Agent A: `[BaseName] - Frontline (4.1)`
- Agent B: `[BaseName] - Reasoning (5.4)`

Example for a law-firm intake: `Dana - Frontline (4.1)` and `Dana - Reasoning (5.4)`. The caller never sees these names — they're only visible in the VAPI dashboard. They're for your operational sanity when staring at logs and recordings.

---

## 6. Voice and Persona Consistency Requirements

This pattern only works if the caller cannot detect the handoff. That requires obsessive attention to voice and persona consistency.

### Voice configuration must match exactly

In the VAPI assistant config for both A and B:

- `voice.provider` — must be identical (e.g., `11labs` on both)
- `voice.voiceId` — must be identical (e.g., `sarah` on both)
- `voice.model` — must be identical (e.g., `eleven_turbo_v2_5` on both)
- `voice.stability`, `voice.similarityBoost`, etc. — all voice tuning parameters must match

Any difference in these parameters produces an audible voice change at the moment of handoff. Listen to a real test call. If you can hear the change, the caller will hear it too.

### Speech patterns must match

This is where mirror discipline matters most. The Character section's filler word examples, note-taking phrases, empathetic reactions, and softener vocabulary must be identical between A and B. If Agent A says "Mmm hmm... got it..." and Agent B says "Right, so..." after the handoff, the caller perceives a personality change even if the voice is identical.

The 5.4 Mini guide is explicit on this: "Filler word examples, speech output rules — don't cut these even though the model is smarter." The reasoning model can produce natural speech without examples, but the *specific* speech patterns that make Agent A sound like Dana require verbatim preservation.

### Name consistency

Both agents introduce themselves as the same person (e.g., "Dana"). This is enforced by both the Character section's persona description and Agent B's Opening Context (which directs it to never re-introduce since it's always continuing).

The internal VAPI assistant names (`Dana - Frontline (4.1)`, `Dana - Reasoning (5.4)`) are for operational clarity only. The caller-facing name in the prompt is just "Dana" in both.

### Backchanneling and conversational tics

If Agent A is configured with `backchannelingEnabled: true`, Agent B must be too. If Agent A uses "uhm" twice per turn on average, Agent B should too. These small auditory cues are what make the caller perceive continuity.

Run an A/B test: record two test calls, one that stays with Agent A throughout, one that escalates to Agent B. Listen to them blindly. If you can tell which is which from the audio, the consistency isn't tight enough.

---

## 7. Handoff Tool Configuration

The handoff tool is the only structurally new component this pattern adds beyond a standard squad. It deserves its own deep treatment.

### Why VAPI's `handoff` type, not `transferCall`

`transferCall` is for transferring to an external PSTN number (a human, another department). It produces an audible transfer experience — there's typically a brief pause, the caller may hear ringing or hold music, and the new party often introduces themselves.

`handoff` is for silent assistant-to-assistant transfers within a VAPI squad. There's no pause, no audible transition, no re-introduction. The voice synthesis continues seamlessly because the voice config is the same and the conversation context is preserved.

For this pattern, you must use `handoff`. `transferCall` would defeat the entire silent-handoff property.

### `contextEngineeringPlan: userAndAssistantMessages`

This tells VAPI to pass the entire conversation transcript (both user turns and assistant turns) to Agent B when the handoff fires. Agent B's first inference call includes the full history as context.

Alternatives and why we don't use them:

- **`messages` (just user messages)** — Agent B sees what the caller said but not what Agent A said in response. Result: Agent B doesn't know what's already been tried, may repeat failed approaches.
- **`summary` (auto-generated summary)** — Agent B sees a brief recap. Result: lossy. Critical context like the exact wording of an objection or a specific commitment Agent A made gets lost.
- **`none` (no context)** — Agent B starts fresh. Catastrophic for this pattern — Agent B would re-greet the caller.

Always use `userAndAssistantMessages` for this pattern.

### `variableExtractionPlan` schema design

The variable extraction plan defines a JSON schema that VAPI extracts from the conversation at handoff time and passes to Agent B as variables. Design this schema to capture all the structured state Agent B needs to continue intelligently.

Required fields for a tiered escalation pattern:

- **`escalation_reason`** — required. The specific trigger condition that fired. Agent B uses this to decide its approach.
- **`open_objection`** — what the caller is currently objecting to and what Agent A has already tried. Critical for objection-driven escalations.
- **`qualification_status`** — where the call stands in the qualification flow.
- **`tools_already_fired`** — what's already been done (CRM updated, agreement sent, etc.) so Agent B doesn't redo them.

Optional but useful:

- **`caller_emotional_state`** — Agent A's read on the caller's emotional state at the moment of escalation.
- **`turn_count`** — how many turns the call has had so far.
- **`time_elapsed_seconds`** — how long the call has been going.

The schema should not duplicate information that's already in the conversation transcript (Agent B can read the transcript). It should capture *interpretive* information that requires Agent A's running judgment — what the call's actual state is, why this moment requires escalation, what's been tried.

### The handoff tool description as decision logic

This is worth re-emphasizing: the handoff tool's `description` field is the trigger logic. The LLM evaluates this description on every turn to decide whether to call the tool. Make it explicit, behavioral, and pair conditions with turn counts.

See Section 3 for the full description template.

---

## 8. Cost Modeling and Volume Math

The economic case for this pattern depends on the call distribution and the cost differential between models.

### Per-call cost rough estimates

Based on the model profiles in `references/gpt-4.1-mini-voice-guide.md` and `references/gpt-5.4-mini-voice-guide.md`:

- **GPT-4.1 Mini** — roughly $0.06 per minute of conversation (varies with input length, prompt caching, output volume). For a typical 4-minute call, ~$0.24 in LLM costs.
- **GPT-5.4 Mini** — roughly $0.14 per minute of conversation. For a typical 4-minute call, ~$0.56 in LLM costs.

These are LLM costs only. STT (Deepgram), TTS (ElevenLabs), and VAPI infrastructure costs are roughly the same across both agents and don't enter into the optimization decision.

### Distribution scenarios

Assume a typical legal intake call distribution at 1,000 calls per day:

- 40% voicemail or immediate hang-up (avg 30 seconds each)
- 30% quick disqualification (avg 1.5 minutes each)
- 20% qualified, amicable, books on first ask (avg 4 minutes each)
- 10% qualified, requires reasoning (avg 7 minutes each)

**Pure 4.1 Mini scenario (no escalation):**
- Voicemails: 400 × 30s × $0.001/s = $12
- Quick disqualifications: 300 × 90s × $0.001/s = $27
- Amicable books: 200 × 240s × $0.001/s = $48
- Hard calls (handled badly): 100 × 420s × $0.001/s = $42
- Total: $129/day, but with conversion lift problems on the 100 hard calls

**Pure 5.4 Mini scenario (no escalation):**
- Voicemails: 400 × 30s × $0.0023/s = $28
- Quick disqualifications: 300 × 90s × $0.0023/s = $62
- Amicable books: 200 × 240s × $0.0023/s = $110
- Hard calls (handled well): 100 × 420s × $0.0023/s = $97
- Total: $297/day, with full conversion quality but 2.3x cost

**Tiered escalation scenario (this pattern):**
- All calls start on 4.1 Mini
- 90% of calls (voicemails, disqualifications, amicable books) complete on 4.1 Mini at $0.001/s
- 10% of calls escalate to 5.4 Mini after ~2 minutes (the average time to detect a hard call), then continue on 5.4 Mini for the remaining ~5 minutes
- Voicemails: 400 × 30s × $0.001/s = $12
- Quick disqualifications: 300 × 90s × $0.001/s = $27
- Amicable books: 200 × 240s × $0.001/s = $48
- Hard calls: 100 × (120s × $0.001/s + 300s × $0.0023/s) = $12 + $69 = $81
- Total: $168/day, with full conversion quality on hard calls

**Result:** Tiered escalation saves ~43% vs. pure 5.4 Mini ($297 → $168) while preserving full reasoning quality on the 10% of calls that need it. Compared to pure 4.1 Mini, you spend ~30% more ($129 → $168) but recover the conversion losses on the hard calls.

The break-even point depends on your specific call distribution and conversion economics. The pattern wins economically when the percentage of hard calls is meaningful (>5%) and lead values are high enough to justify the engineering complexity.

### Volume thresholds

Below ~500 calls/day, the engineering complexity of maintaining two synchronized prompts and a squad config probably isn't worth the savings. At those volumes, just use 5.4 Mini for everything and pay the premium.

Above ~2,000 calls/day, the cost savings become substantial enough to justify dedicated maintenance. High-volume legal intake programs typically fit this band.

---

## 9. Common Failure Modes & Fixes

### Failure: Voice changes audibly at handoff
**Symptom:** Test call recordings have a noticeable voice shift when escalation happens.
**Fix:** Verify all voice config parameters match exactly between A and B. Check `voice.provider`, `voice.voiceId`, `voice.model`, and all tuning parameters. A common culprit is one agent having an outdated `eleven_turbo_v2` while the other has `eleven_turbo_v2_5`.

### Failure: Agent B re-greets the caller after handoff
**Symptom:** Caller hears "Hi, thank you for calling Summit Law Group..." in the middle of the call.
**Fix:** Agent B is missing or has a malformed Opening Context block. Verify Agent B's Instructions begin with the Opening Context block from Section 5 of this doc — it must explicitly state that Agent B is always taking the call mid-conversation and direct it to never greet or re-introduce. Also verify the handoff tool's `contextEngineeringPlan` is `userAndAssistantMessages` — without prior conversation in context, Agent B has no history to continue from and the Opening Context's reference to "the conversation history" becomes meaningless.

### Failure: Agent A escalates too aggressively
**Symptom:** Most calls escalate to Agent B even when 4.1 Mini could have handled them. Cost savings disappear.
**Fix:** The handoff tool description is too permissive. Tighten the trigger conditions. Add explicit "DO NOT trigger this tool for..." cases (amicable callers, quick disqualifications, voicemail). Add stricter turn-count thresholds (3+ failed objection attempts instead of 2+). Run sim scenarios for amicable callers and verify they don't escalate.

### Failure: Agent A escalates too rarely
**Symptom:** Hard calls fail on Agent A without ever escalating. Conversion quality suffers.
**Fix:** The handoff tool description is too restrictive, or 4.1 Mini isn't recognizing trigger conditions. Add more concrete behavioral examples to the description. Consider adding an explicit complexity classifier as a separate tool — a quick `classify_complexity()` call that runs each turn and returns "simple" or "complex," with the handoff tool description referencing the classifier output.

### Failure: Agent B repeats Agent A's failed approach
**Symptom:** Caller raises an objection, Agent A tries the HEART framework and fails twice, escalates to Agent B, Agent B tries the same HEART framework and fails again.
**Fix:** Two complementary fixes. (1) Verify Agent B's Opening Context is reading the `escalation_reason` and `open_objection` variables — if either is missing or malformed, Agent B has no signal that what it's about to try has already been tried. (2) Verify Agent B has the **How to Respond** section (see Phase 5). Without it, Agent B has no procedural direction to think carefully about the caller's actual concern, and falls back to pattern-matched objection rebuttals that look just like 4.1 Mini's failed attempt. The whole point of the section is to direct Agent B's reasoning toward what the caller is *actually* asking for — which by definition is something Agent A's surface response didn't address. Also verify the `variableExtractionPlan` is capturing what was tried, not just the objection itself, so Agent B can tell at a glance which approaches to avoid.

### Failure: Agent B's responses sound canned or generic
**Symptom:** Even after escalation, Agent B's responses feel like recited objection rebuttals — they're more polished than Agent A's but they don't sound like they were custom-built for what this specific caller said. Caller doesn't feel heard.
**Fix:** This is the failure mode that defeats the entire purpose of using a reasoning model. Verify:
- The **How to Respond** section is present in Agent B's Instructions (see Phase 5). Without it, Agent B will default to template-matching just like 4.1 Mini, just with better grammar.
- `reasoning_effort` is set to `low` or higher — at `none`, Agent B doesn't actually reason about the caller's words, it just generates a response. The reasoning step is what enables the technique to work.
- The (s) Support section in Agent B's prompt does NOT contain scripted objection responses. If it does, Agent B will pattern-match to the script instead of reasoning about the caller's specific concern. Per the 5.4 Mini guide, the (s) section in 5.4-style prompts contains *substance* (key arguments, facts, talking points) — not pre-formed responses. If you copied scripted responses over from Agent A's prompt during the mirror conversion, the Lossless Conversion Protocol failed at the substance-vs-script step. Convert them.
- The **How to Respond** instruction has not been over-specified with mechanical sub-rules ("restate the question first," "always mirror their vocabulary"). Mechanical sub-rules produce mechanical behaviors, which is the opposite of what's wanted. The instruction should give the principle and trust the reasoning to handle execution.

### Failure: Agent B responds confidently to garbled or nonsensical input
**Symptom:** Caller's transcribed input contains a transcription error, slang the model didn't parse, or a confused/incoherent statement. Agent B responds as if its best guess at the meaning was correct, which sends the conversation in the wrong direction. The caller has to backtrack — "no, that's not what I asked" — and trust degrades.
**Fix:** This is the inverse of the over-clarification failure. The How to Respond section directs the model to clarify when input is genuinely unclear, but the model may not be reading "unclear" broadly enough. Verify the section explicitly mentions transcription errors and ambiguous input, not just incomplete questions. If failures persist, you can strengthen the instruction with "If the caller's message doesn't fit the conversation context — for example, if they seem to answer a question you didn't ask, or use words that don't make sense given what you were just discussing — treat that as a signal to clarify rather than an instruction to follow." This bounds the failure mode to the specific cases where clarification is correct without expanding it to all uncertainty.

### Failure: Agent B over-explains simple questions
**Symptom:** Caller asks a simple factual question ("How long does the consultation take?"). Agent B answers with the time, then deploys a metaphor about how short it'll feel, then adds social proof about how other callers found the consultation valuable. Caller didn't ask for any of that and the response feels like a sales pitch where they wanted information.
**Fix:** The progressive disclosure strategy in How to Respond is being applied where it shouldn't be. Verify the section's "Reach for the simplest answer first" instruction is present and unambiguous. The escalation tools (metaphor, social proof) are supposed to be deployed *only* when the simple answer doesn't land — not stacked into the initial response. If the model is stacking, the escalation list is being read as a sequence to execute rather than tools to choose from. Strengthen the wording: "Use one of these per turn, not all of them stacked in a single response. Each layer is a separate attempt to land the same point." Also: factual questions almost never need escalation — the answer is the answer.

### Failure: Agent B mechanically restates everything the caller says
**Symptom:** Agent B opens every response by paraphrasing what the caller just said, even on simple turns. The conversation feels patronizing and over-coached, like a customer service rep who's been told to "show active listening" and is doing it on every utterance.
**Fix:** The **How to Respond** section has been over-specified — it probably contains a rule about restating the caller's message before answering, or enumerated layers to address on every turn. Reasoning models apply mechanical rules mechanically. Strip the mechanics out and leave only the principle: "think carefully about what they're actually asking for and respond in a way that feels genuine and personal." The model will restate when restating fits the moment and not when it doesn't.

### Failure: Agent B mechanically deploys metaphors or social proof
**Symptom:** Agent B reaches for a metaphor or social-proof construction on every objection, regardless of whether the caller signaled they didn't understand the direct answer. The model treats progressive disclosure as a checklist to work through ("first the answer, then the metaphor, then the social proof") rather than as escalation tools to use only when needed.
**Fix:** The progressive disclosure structure in How to Respond is being read as a sequence rather than a toolkit. Verify the prompt language explicitly says "Use one of these per turn, not all of them stacked in a single response. Each layer is a separate attempt to land the same point — if the previous layer didn't work, the next one might." If the model is still mechanically deploying, strengthen with: "Most callers will land on the direct answer. Only escalate to metaphor or social proof if the caller signals they didn't understand or didn't accept the direct answer." This explicitly conditions escalation on caller signal rather than treating it as default behavior.

### Failure: Agent B asks unnecessary clarifying questions
**Symptom:** Caller raises a clear concern that Agent B could have responded to directly, but Agent B instead asks "Can you tell me more about what you mean by that?" or "What specifically are you concerned about?" The model is stalling on input it could have parsed. Note: this is different from the *desired* clarifying behavior on genuinely unclear or garbled input (see the "When the caller's input is unclear" subsection of How to Respond) — the failure is clarifying on input that didn't need clarification.
**Fix:** Reasoning models can over-clarify when uncertain about how to respond. The How to Respond section explicitly bounds clarification to genuinely unclear input ("Use this only when input is genuinely unclear. Don't clarify when you can reasonably interpret what they said — that turns into stalling and feels evasive"). If Agent B is over-clarifying, verify that bounding language is present in the prompt. Also check `reasoning_effort` — at `medium` or higher the model may second-guess itself and ask for confirmation when it should just respond. `low` is the right default for voice. Real test: if a competent human listening to the caller would have responded directly, Agent B should too.

### Failure: Agent B reconfirms understanding on every objection
**Symptom:** Caller raises a concern, Agent B opens with "let me make sure I understand what you're really asking..." — even on the first turn of the objection. The reconfirmation pattern that was supposed to be a fallback for stuck conversations is being deployed as a default check-in. Caller feels condescended to or like the agent is stalling.
**Fix:** The "check whether you're answering the right question" sub-section is being read as a default behavior rather than a fallback. Verify the prompt language explicitly says this is a fallback for genuinely stuck conversations, presupposing prior escalation attempts. The bounding language — "if you've worked through the direct answer, tried a different angle like a metaphor, brought in social proof, and the caller is still confused" — establishes the precondition. If that's present and the model is still misusing, strengthen with: "Do not use this on the first or second turn of an objection. The first attempt is to answer directly. The second is to try a different angle. Reconfirmation is for the case where multiple angles haven't worked."

### Failure: Agent B keeps explaining the wrong thing without ever reconfirming
**Symptom:** Caller raises a concern, Agent B answers with the direct response, gets pushback, escalates to a metaphor, gets more pushback, escalates to social proof, gets more pushback, and just keeps cycling through explanation strategies without ever stepping back to ask whether it understood the question correctly. The conversation drags on with the agent burning explanation tools on the wrong target.
**Fix:** The reconfirmation sub-section is missing or too weak. Verify it's present in How to Respond. The trigger condition needs to be concrete enough that the model recognizes it — "roughly three rounds on the same unresolved point" gives a specific threshold. Without that, the model will keep applying the progressive disclosure tools indefinitely because each one is a "different angle" on the same point. Also verify the simulation suite includes a scenario where the model is correctly answering a question the caller didn't ask — see the "Reconfirms understanding when stuck" scenario in Phase 6.

### Failure: Agent B monologues
**Symptom:** Agent B delivers minute-long speeches packed with multiple points, sub-arguments, and comprehensive coverage of every angle. Caller goes silent, says "uh-huh" a lot, or interrupts to bring it back to one specific thing. Most of the response was wasted because the caller stopped tracking after the first ten or fifteen seconds.
**Fix:** The **How to Respond** section is missing or weak on the one-point-per-turn principle. Verify the section explicitly says "keep each turn focused on one point" and "walk multi-step ideas across several short turns rather than monologuing." Avoid phrasing like "give the answer the length it needs" — that licenses long responses. Also check whether the section is encouraging completeness over pacing. The instruction should frame multi-point answers as a *sequence of short turns with reactions in between*, not as a single comprehensive response.


### Failure: Agents drift in functionality over time
**Symptom:** After a few iteration cycles, Agent A and Agent B start producing meaningfully different outcomes on the same scenarios. Caller perceives inconsistency depending on whether they got escalated.
**Fix:** Mirror discipline broke down. Adopt the change-layer checklist from Section 5: every iteration must declare whether it's a shared-core or style-specific change, and shared-core changes must be applied to both prompts in lockstep. Run the full sim suite on both agents independently after every deploy.

### Failure: Agent B's response feels off-tempo
**Symptom:** Caller experiences a slight pause or unnatural rhythm right after the handoff.
**Fix:** Two possible causes. (1) Agent B's `reasoning_effort` is set too high, adding latency on the first turn after takeover. Reduce to `low` or even `none`. (2) Agent B's first turn is generating too much text trying to "catch up" — set `verbosity: low` and reinforce in the Opening Context: "Your first turn is a single, focused response to the caller's most recent message. Do not summarize, do not catch up, just respond as if you've been on the call all along."

### Failure: Handoff tool doesn't fire (4.1 Mini ignores it)
**Symptom:** Hard calls go unresolved on Agent A and the handoff tool is never called.
**Fix:** Enumerate the trigger conditions more concretely with examples. 4.1 Mini follows instructions literally — if the description says "use this when the caller has complex needs," it won't fire because "complex" is too abstract. Replace with concrete behavioral patterns: "use this when the caller has said the words 'I'm not sure' or 'I need to think about it' two or more times." Also add the handoff tool to the list of tools mentioned in the system prompt's Tools (T) section so 4.1 Mini knows it exists.

### Failure: Agent B treats the handoff as a tier-system context
**Symptom:** Agent B references "the front-line agent," talks to the caller about being "transferred to a supervisor," or otherwise breaks the illusion that it's been the only agent on the call.
**Fix:** Agent B's prompt must contain zero references to the existence of Agent A, the tiered system, or escalation as a concept. From Agent B's perspective, there's no second agent — it's just an agent whose calls always start mid-conversation. The only place Agent B encounters anything tier-related is the `escalation_reason` and `open_objection` variables in the inherited context, which the Opening Context section reads to inform Agent B's approach but does not narrate to the caller. Verify Agent B's prompt: no mention of "front-line," "supervisor," "escalation," "Agent A," "handoff," or any meta-reference to the architecture. The Opening Context block in Section 5 is written in declarative language about Agent B's actual operating reality, not in conditional language about tier transitions.

**Note on omission discipline:** Agent B does not have the `handoff_to_reasoning` tool in its `model.toolIds`. It has no instruction about whether to escalate, hand back, or transfer to other agents. The pattern relies on simple absence — Agent B can't do something if the capability isn't present in its tools and the concept isn't in its prompt. Do NOT add a Policy like "do not hand off to other agents" — this introduces the concept of handing off into Agent B's context window for no benefit. Agents don't attempt behaviors that aren't in their tools and prompts; telling them not to attempt those behaviors is pink-elephant priming.

---

## 10. Reference Doc Cross-Map

This pattern composes several existing skill references. Load them in this order during the build:

| Reference | When to Load | Why |
|-----------|--------------|-----|
| `references/gpt-4.1-mini-voice-guide.md` | Phase 1 of build sequence | Optimize Agent A's prompt for 4.1 Mini's literal instruction following |
| `references/vapi-config-reference.md` | Phase 4 of build sequence | Handoff tool schema, contextEngineeringPlan, variableExtractionPlan options |
| `references/conversion-guide.md` | Phase 3 of build sequence | Goal-based methodology for converting Agent A to Agent B |
| `references/gpt-5.4-mini-voice-guide.md` | Phase 3 of build sequence | 5.4 Mini-specific patterns and the 9-step migration checklist |
| `references/lossless-conversion-protocol.md` | Phase 3 of build sequence (mandatory) | Ensure no functionality is silently dropped when mirroring A → B |
| `references/filler-disfluency-patterns.md` | Phase 3 of build sequence | Maintain voice/persona consistency across both agents |
| `references/vapi-simulations.md` | Phases 2 and 6 of build sequence | Standalone Agent A validation, then squad-level escalation testing |
| `references/cross-platform-migration.md` | When migrating this pattern to FlowForge (Section 11) | Feature parity matrix and platform-specific caveats |

Sub-references for specific situations:

- **Iteration after the squad is live:** Always load `references/lossless-conversion-protocol.md` and apply mirror discipline (Section 5 of this doc) on every change.
- **New trigger condition discovery:** When a real-call failure mode reveals a missing trigger, add it to the handoff tool description AND add a regression scenario to the simulation suite.
- **Voice provider change:** Treat as a major deploy — verify voice consistency obsessively per Section 6.

---

## 11. FlowForge Migration Notes (Future)

FlowForge does not have a first-class equivalent to VAPI's `handoff` tool with `contextEngineeringPlan` and `variableExtractionPlan`. The closest patterns on FlowForge are:

- **`flow_data` graph** — a single FlowForge assistant with a ReactFlow graph that branches based on conversation state. Different nodes can have different prompts (effectively different "personalities"), but they share a single LLM model setting at the assistant level. This means you can't have one branch on 4.1 Mini and another on 5.4 Mini within a single flow-based assistant. Rules out this pattern within a single FlowForge assistant.

- **Multiple FlowForge assistants + telephony-layer transfer** — deploy Agent A and Agent B as separate FlowForge assistants. When Agent A determines escalation is needed, it triggers `system_tools_config.transfer_call: true` to transfer to Agent B's phone number. This is NOT silent — the caller experiences a warm transfer with a brief pause. Defeats the silent-handoff property of this pattern.

**Recommendation as of writing:** Deploy this pattern on VAPI only. If a client requires FlowForge specifically, deploy that client's tiered-escalation agents on VAPI and treat it as the platform exception rather than forcing FlowForge to do something it can't do silently.

If FlowForge adds a silent assistant-to-assistant handoff capability in the future, this section should be expanded with the specific implementation. Until then, see `references/cross-platform-migration.md` for the general migration protocol and the platform exception documentation pattern.

---

## Quick-Start Checklist

For a new tiered-escalation squad build, run through this checklist:

- [ ] **Phase 0:** Confirm volume (>500/day), call distribution variance, and lead value justify the pattern
- [ ] **Phase 1:** Build Agent A as a standard 4.1 Mini single-agent (skill Phases 0-9, single-agent architecture)
- [ ] **Phase 2:** Validate Agent A standalone — Tier 1 sims passing >90%, Tier 2 sims explicitly failing (expected)
- [ ] **Phase 3:** Mirror-convert Agent A → Agent B (5.4 Mini) using conversion guide + 5.4 guide + lossless protocol
- [ ] **Phase 4:** Add `handoff_to_reasoning` tool to Agent A with the full description from Section 3 of this doc
- [ ] **Phase 5:** Add Opening Context block to Agent B's Instructions (declarative, not conditional). Add the How to Respond section with five sub-instructions: think carefully about underlying concern, reach for the simplest answer first, clarify when input is genuinely unclear, pace complex ideas across short turns, reconfirm understanding when stuck. Keep all sub-sections principle-based, not procedural.
- [ ] **Phase 6:** Deploy as VAPI squad, assign phone number to Agent A only, run full sim suite
- [ ] **Validation:** Voice consistency check, Tier 1 + Tier 2 + escalation scenarios all passing
- [ ] **Production:** Monitor escalation rate (should be ~5-15% of calls), escalation success rate (Agent B should resolve >70% of escalated calls), and total cost vs. pure 5.4 Mini baseline
