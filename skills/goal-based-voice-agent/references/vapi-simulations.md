# VAPI Simulations — API Reference

How to use VAPI Simulations to roleplay caller scenarios against a deployed assistant, evaluate the result programmatically, and iterate.

**Sources (the only two pages you need):**
- https://docs.vapi.ai/observability/simulations-quickstart
- https://docs.vapi.ai/observability/simulations-advanced

---

## Resource model

VAPI Simulations is built on five resource types. Create them in this order:

1. **Personality** — the AI tester's persona. Defines model, voice, and a system prompt that controls how the tester behaves (impatient, skeptical, hostile, confused, etc.). Reusable across many scenarios.
2. **Scenario** — instructions for the tester ("call to book an appointment for next Monday at 2pm") plus evaluations (pass/fail criteria as structured outputs).
3. **Simulation** — a pairing of one Personality + one Scenario. This is the unit that actually runs.
4. **Simulation Suite** — a group of Simulations executed together as a batch.
5. **Run** — an execution of a Suite against a target Assistant or Squad, on a given transport.

You don't have to go through all five every time — Personalities and Scenarios are reusable. Build a library once per agent, then add new Simulations as new failure modes are discovered.

---

## Auth

Bearer token from the org's VAPI API key. Header on every request:

```
Authorization: Bearer $VAPI_API_KEY_<ORG>
Content-Type: application/json
```

Keep one key per VAPI org in an untracked `.env`, for example:
- `VAPI_API_KEY_ACME` — Acme's inbound agents
- `VAPI_API_KEY_GLOBEX_SALES` — Globex outbound BDR agents

---

## API surface

All endpoints are on `https://api.vapi.ai`.

### 1. Create a Personality

`POST /eval/simulation/personality`

```bash
curl -X POST "https://api.vapi.ai/eval/simulation/personality" \
  -H "Authorization: Bearer $VAPI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Skeptical New LLC Owner",
    "assistant": {
      "model": {
        "provider": "openai",
        "model": "gpt-4o",
        "messages": [{
          "role": "system",
          "content": "You are a new LLC owner who picked up the call. You are skeptical and slow to commit. You do not know what attorney consultations are. When asked about scheduling you press for concrete examples of what you would actually talk about. You only agree to book after the agent gives you something specific."
        }]
      },
      "voice": {
        "provider": "cartesia",
        "voiceId": "sonic-english"
      }
    }
  }'
```

Response: `{ "id": "personality-uuid", ... }` — capture `id` as `personalityId`.

### 2. Create a Scenario

`POST /eval/simulation/scenario`

```bash
curl -X POST "https://api.vapi.ai/eval/simulation/scenario" \
  -H "Authorization: Bearer $VAPI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Book Appointment",
    "instructions": "Call the agent. Your goal is to book an attorney consultation, but only if the agent gives you a concrete example of what to talk about. If the agent asks Does this sound familiar, say no. If the agent presses you about scheduling without explaining what you would discuss, ask what would I actually talk about. Eventually agree to book.",
    "evaluations": [
      {
        "structuredOutput": {
          "name": "appointment_booked",
          "schema": {
            "type": "boolean",
            "description": "Did the agent confirm a specific day, date, time, AND callback number with the caller before ending the call?"
          }
        },
        "comparator": "=",
        "value": true,
        "required": true
      },
      {
        "structuredOutput": {
          "name": "first_name_used_on_close",
          "schema": {
            "type": "boolean",
            "description": "Did the agent address the caller by their first name in the scheduled close (e.g., Thank you so much, John)?"
          }
        },
        "comparator": "=",
        "value": true,
        "required": false
      }
    ]
  }'
```

Response: `{ "id": "scenario-uuid", ... }` — capture as `scenarioId`.

**Evaluation rules:**
- `comparator` supports: `=`, `!=`, `>`, `<`, `>=`, `<=`. Numeric operators only work on `number` and `integer` schema types.
- Schema `type` is restricted to **primitives only**: `"string"`, `"number"`, `"integer"`, `"boolean"`. No objects or arrays.
- `required: true` means failing this evaluation fails the scenario. `required: false` records the result but doesn't fail the run.

### 3. Create a Simulation (Personality + Scenario pair)

`POST /eval/simulation`

```bash
curl -X POST "https://api.vapi.ai/eval/simulation" \
  -H "Authorization: Bearer $VAPI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Skeptical caller — what would I talk about?",
    "scenarioId": "scenario-uuid",
    "personalityId": "personality-uuid"
  }'
```

Response: `{ "id": "simulation-uuid", ... }` — capture as `simulationId`.

### 4. Create a Simulation Suite

`POST /eval/simulation/suite`

```bash
curl -X POST "https://api.vapi.ai/eval/simulation/suite" \
  -H "Authorization: Bearer $VAPI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Riley Regression Suite",
    "simulationIds": [
      "simulation-uuid-1",
      "simulation-uuid-2",
      "simulation-uuid-3"
    ]
  }'
```

Response: `{ "id": "suite-uuid", ... }` — capture as `suiteId`.

### 5. Run the Suite

`POST /eval/simulation/run`

**Chat mode** (faster, lower cost — recommended for iteration):

```bash
curl -X POST "https://api.vapi.ai/eval/simulation/run" \
  -H "Authorization: Bearer $VAPI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "simulations": [{
      "type": "simulationSuite",
      "simulationSuiteId": "suite-uuid"
    }],
    "target": {
      "type": "assistant",
      "assistantId": "<assistant-id>"
    },
    "transport": {
      "provider": "vapi.webchat"
    }
  }'
```

**Voice mode** (full TTS/STT pipeline, audible recording, slower, costs minutes):

```bash
curl -X POST "https://api.vapi.ai/eval/simulation/run" \
  -H "Authorization: Bearer $VAPI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "simulations": [{
      "type": "simulationSuite",
      "simulationSuiteId": "suite-uuid"
    }],
    "target": {
      "type": "assistant",
      "assistantId": "..."
    },
    "transport": {
      "provider": "vapi.websocket"
    }
  }'
```

**Targeting a squad instead of a single assistant:**

```json
"target": { "type": "squad", "squadId": "squad-uuid" }
```

**Re-running each simulation N times** (useful when the agent has natural variation):

```json
{
  "simulations": [...],
  "target": {...},
  "transport": {...},
  "iterations": 3
}
```

Response: `{ "id": "run-uuid", "status": "running", ... }` — capture as `runId`.

### 6. Check Results

`GET /eval/simulation/run/{runId}`

```bash
curl -X GET "https://api.vapi.ai/eval/simulation/run/$RUN_ID" \
  -H "Authorization: Bearer $VAPI_API_KEY"
```

Response:

```json
{
  "id": "run-uuid",
  "status": "running" | "ended",
  "endedReason": "...",
  "itemCounts": {
    "total": 3,
    "passed": 3,
    "failed": 0
  }
}
```

`GET /eval/simulation/run/{runId}/item` — lists individual scenario executions within the run, with full transcripts and per-evaluation pass/fail details.

---

## Tool mocks (advanced)

When the assistant under test would normally call a real tool (booking API, CRM lookup), you can intercept the call and return a predetermined response. Define on the Scenario:

```json
"toolMocks": [
  {
    "toolName": "bookAppointment",
    "result": "{\"status\": \"success\", \"confirmationId\": \"APT-12345\"}",
    "enabled": true
  }
]
```

Use this to test both success and failure paths deterministically — one Scenario with a success mock, another with an error mock. Mocks are inert without `enabled: true`.

---

## Hooks (websocket transport only)

Trigger webhooks on simulation lifecycle events. Define on the Scenario:

```json
"hooks": [
  {
    "on": "simulation.run.started" | "simulation.run.ended",
    "do": [
      {
        "type": "webhook",
        "server": { "url": "https://your-server.com/webhooks/vapi-sim" },
        "include": { "transcript": true, "messages": true, "recordingUrl": true }
      }
    ]
  }
]
```

**Webhook payloads:**

```json
// simulation.run.started
{
  "event": "simulation.run.started",
  "simulationId": "...",
  "runId": "...",
  "timestamp": "..."
}

// simulation.run.ended
{
  "event": "simulation.run.ended",
  "simulationId": "...",
  "runId": "...",
  "duration": 145,
  "status": "passed" | "failed",
  "transcript": "...",
  "messages": [...],
  "recordingUrl": "https://..."
}
```

**Critical limitation:** hooks only fire on `vapi.websocket` transport. They do NOT fire on `vapi.webchat`. If you need lifecycle webhooks, run on websocket.

---

## Transports

- **`vapi.webchat`** — text-based, fast, lower cost. No calling minutes consumed. Hooks do NOT fire. Use for iteration and CI/CD.
- **`vapi.websocket`** — full voice pipeline (TTS/STT), audible recording produced, hooks fire. Slower, consumes calling minutes. Use for canonical-final-pass before shipping, and for any voice-specific verification (TTS pronunciation of phone numbers, interruption handling, fillers as actually spoken).

Recommended pattern: **iterate on webchat, certify on websocket.**

---

## Building the Personality library

Personalities are the AI testers' personas. They're reusable across many Scenarios — you build the library **once per agent type**, then mix and match against scenario instructions. The right library covers three concentric tiers: **ICP, ICP-adjacent, and non-ICP**.

### Why three tiers

- **ICP (Ideal Customer Profile)** — the people the agent is actually built to convert. Most simulations should run against this tier. Failures here directly correlate to lost revenue.
- **ICP-adjacent** — close-but-not-quite callers who realistically end up on the line: wrong-fit decision-maker, partial-fit business stage, related-but-different intent. The agent shouldn't waste effort on them, but it also shouldn't burn the relationship. These scenarios test **graceful handling** more than conversion.
- **Non-ICP** — out-of-scope callers (wrong number, hostile, DNC, voicemail, minor, gatekeeper). These test **disqualification, compliance, and exit hygiene**. Failures here are reputational and legal risks.

A suite without all three tiers tests only the happy market and misses entire categories of failure.

### Step 1: Extract ICP from the prompt's S — SCENARIO and R — ROLE sections

Read the source prompt's S and R sections. The ICP is everything the prompt says the caller IS. For Riley: "new LLC owners who recently formed their business through FormFast... overwhelmed with setup tasks... haven't used the attorney consultation benefit." That's the spine of every ICP personality.

From that spine, generate **3-5 ICP variations** that differ on personality dimensions, NOT demographic dimensions. The agent doesn't behave differently based on who the caller is demographically — it behaves differently based on how the caller engages. So vary on engagement style:

- **Cooperative-fast** — picks up engaged, says yes early, easy book. Stress-tests the "Stage 1 lands → don't over-explain" path.
- **Cooperative-slow** — willing but slow to commit, asks several clarifying questions before agreeing. Stress-tests the agent's patience and the "answer questions without re-spamming times" rule.
- **Skeptical-curious** — engaged but pushes back on every gate. Stress-tests progressive-disclosure depth (Stages 2, 3, 4 in sequence) and rebuttal handlers.
- **Distracted-busy** — picked up but multitasking, gives short answers, occasional non-sequiturs. Stress-tests "read the room, tighten up" and recovery from incomplete answers.
- **Stressed-overwhelmed** — explicitly stressed about business setup. Stress-tests the warmth/empathy register without crossing into fabricated emotional projection (Riley's "I bet you're juggling" anti-pattern).

Each Personality's system prompt should be 2-4 sentences. Specific, behavioral, and **rooted in what the SCENARIO says is true about ICP callers** — not invented demographics.

```json
{
  "name": "ICP — Skeptical-curious LLC owner",
  "assistant": {
    "model": {
      "provider": "openai",
      "model": "gpt-4o",
      "messages": [{
        "role": "system",
        "content": "You are a new LLC owner who formed your business through FormFast recently. You're engaged on the call but skeptical — you push back on every claim and ask for specifics. You don't agree to anything unless the agent gives you a concrete answer. You're not hostile, just careful with your time."
      }]
    },
    "voice": { "provider": "cartesia", "voiceId": "sonic-english" }
  }
}
```

### Step 2: Build ICP-adjacent variations

Extract these from the prompt's "Not the right person" / sentiment-routing branches in Goal 2 and the (s) handlers that decline gracefully. Each adjacency type usually maps 1:1 to a handler in the prompt:

- **Already-served** — caller has the product but doesn't need this specific outreach. Maps to "I already have an attorney" handler. Tests: agent acknowledges without competing.
- **Wrong-fit decision-maker** — answered the call but is not the account holder (spouse, employee, business partner). Maps to the "spouse / family member" branch. Tests: agent doesn't disclose account details, captures availability for the right person.
- **Wrong-stage** — partial fit (e.g., LLC formed but caller is the accountant, not the owner). No exact handler — agent should improvise gracefully. Tests: graceful redirect without burning the contact.
- **Wrong-intent** — picked up assuming the call is something else (support call, billing question). Tests: agent corrects the framing without losing warmth.
- **Future-fit** — right ICP but wrong moment ("I'm in a meeting" / "call me back next month"). Maps to "Not a good time" / "Not ready right now" handlers. Tests: agent honors the constraint, captures preferred callback, exits cleanly.

ICP-adjacent personalities should NOT be "easy converts who book anyway." That's lying to yourself about the agent's behavior. They should test that the agent **disqualifies efficiently and ends warmly** — exactly the behavior the prompt's Policies prescribe.

```json
{
  "name": "ICP-adjacent — Wrong decision-maker (spouse)",
  "assistant": {
    "model": {
      "provider": "openai",
      "model": "gpt-4o",
      "messages": [{
        "role": "system",
        "content": "You answered your spouse's phone. The agent asks for them by name. You confirm you are not them and offer to take a message. Do not reveal you know anything about their business or their FormFast account. You are friendly but protective of their information."
      }]
    },
    "voice": { "provider": "cartesia", "voiceId": "sonic-english" }
  }
}
```

### Step 3: Build non-ICP variations

These are the disqualification and compliance tests. They map directly to the prompt's redline policies and Error Handling section. Required non-ICP personalities for any goal-based agent:

- **DNC requester** — "stop calling me" / "remove me from your list." Tests: Policy #13 (immediate honor, no pushback, no email offer).
- **Hostile / suspicious** — "is this a scam?" / "how'd you get my number?" Tests: hostile reassurance handler, no "nothing's wrong" usage.
- **Wrong number entirely** — "I don't have an LLC" / "you have the wrong person." Tests: agent apologizes and ends without pitching.
- **Voicemail** — answers with a recorded greeting. Tests: Goal 1 voicemail detection, immediate end-call without message.
- **Minor / unauthorized contact** — answered the phone but isn't authorized to discuss the account. Tests: Policy #2 (no account disclosure to unauthorized contacts).
- **Distressed caller** — clearly upset, frustrated, possibly in crisis. Tests: Error Handling "clearly upset or frustrated" branch — graceful exit, no pushing.
- **Off-topic talker** — keeps the agent on the phone with unrelated chatter. Tests: agent's ability to gracefully steer back without being rude, and the call-duration target (Policy #9).

```json
{
  "name": "Non-ICP — DNC request",
  "assistant": {
    "model": {
      "provider": "openai",
      "model": "gpt-4o",
      "messages": [{
        "role": "system",
        "content": "You answered the call. You are tired of marketing calls. As soon as the agent identifies their company, you say 'please remove me from your list, I don't want any more calls.' If the agent tries to explain or offer alternatives, you firmly repeat the request. You are not hostile, but you are immovable."
      }]
    },
    "voice": { "provider": "cartesia", "voiceId": "sonic-english" }
  }
}
```

### Personality coverage targets

For a mature suite:
- **5-6 ICP personalities** — most volume runs against these.
- **3-5 ICP-adjacent personalities** — one per adjacency type the prompt actually handles.
- **5-7 non-ICP personalities** — one per disqualification / compliance redline.

Total: ~15 personalities in the library. Each Scenario picks the right Personality for what it tests. Most ICP-tier Scenarios will pair with multiple ICP personalities (run the same booking Scenario against cooperative-fast AND skeptical-curious — same passing criteria, different tester behaviors).

### Personality writing rules

- **Behavior, not demographics.** "You are skeptical and slow to commit" is useful. "You are a 45-year-old male in Texas" is not.
- **Concrete trigger conditions where they matter.** For non-ICP, instruct exactly when the personality fires the disqualifying behavior ("As soon as the agent identifies their company, say 'please remove me'"). For ICP, leave more room ("agree to book once the agent gives you a concrete example").
- **Don't quote the agent's exact phrases.** If the personality is told to react to "Does this sound familiar?", it'll miss when the agent varies to "ring a bell?" Match by intent ("any version of asking whether you recognize this").
- **One behavior per personality.** A personality that's both skeptical AND hostile AND distracted will produce muddy transcripts. Split into separate personalities, each isolating one dimension.
- **Don't lie about ICP fit.** A "cooperative ICP caller" should still behave like the actual ICP — overwhelmed, distracted by setup tasks, vague memory of what they bought. Optimistic personalities that book the agent regardless of agent quality test nothing.

---

## Reverse-engineering Scenarios from the system prompt

The prompt itself is the spec. Every goal, gate, handler, and redline implies at least one Scenario the agent must handle correctly. This section is the methodology for systematically extracting that scenario inventory — so you ship with coverage instead of guessing what to test.

The reverse-engineering pass takes about 30 minutes for a mature SCRIPT-framework prompt and produces a complete scenario list before you write a single one.

### Step 1: Inventory every "must-pass" path through the call flow

Read the prompt's I — INSTRUCTIONS section and list every path that ends in either a confirmed booking or a graceful-decline. For a goal-based agent with N stages, that's:

- **N happy paths** — one per stage gate. Caller passes the gate, skips remaining stages, books.
- **The "all stages NO" graceful path** — caller passes no gates, agent accepts gracefully and offers self-service.
- **The "soft hesitation post-stage-3" path** — caller agrees through Stage 3 but hesitates at scheduling, agent fires the closer (Stage 4), caller agrees.

Write each as a one-sentence Scenario brief: "Caller agrees on Stage 1 → books." Don't fill in the full instructions yet — just enumerate.

For Riley (4 stages + closer): 4 happy + 1 all-no + 1 closer-rescue = **6 must-pass scenarios** from this step.

### Step 2: One Scenario per (s) handler

Open the (s) — SUPPORT section. Every named handler is a real caller behavior the prompt expects, which means it deserves a regression Scenario. List them:

For Riley, the (s) handlers in Objection Handling and Customer Questions:
- "Not ready right now / I'll do it later"
- "I'm too busy"
- "Is this a scam? / Who is this?"
- "I already have an attorney"
- "I'll schedule it myself online"
- "I need to talk to my spouse first"
- "Why would I want to do that?"
- "I don't need this" (the friend-who-happens-to-be-a-lawyer rebuttal)
- "Are you AI?" — pre-booking
- "Are you AI?" — post-booking (different code path, see Policy #33)
- "What would I talk about?"
- "Does what sound familiar?" (gate-recovery)
- "Tax-specific or legal-specific questions"
- Plan/billing redirect

That's **~14 Scenarios** from the (s) section alone. Pre/post-booking variants count as separate Scenarios when the prompt branches them.

Pattern for the brief: "Caller raises [trigger phrase]. Agent fires [handler name]. Pass criteria: handler-specific behavior preserved (e.g., 'paid for' anchor in gate-recovery, three concrete examples in friend-who-happens-to-be-a-lawyer)."

### Step 3: One Scenario per redline Policy

Open the P — POLICIES section. Each numbered policy is a redline the agent must NOT cross. Most policies need a Scenario specifically designed to **bait the agent into crossing it** — and the evaluation passes if the agent doesn't.

Walk the policy list, asking for each one: "What caller behavior would make a weak agent violate this?" If the answer is concrete, that's a Scenario. If the policy is a structural rule the agent enforces internally (like "use the caller's name sparingly"), it becomes an evaluation criterion across all scenarios rather than its own Scenario.

Examples from Riley:
- **Policy #13 (DNC immediate honor)** → Scenario: caller demands DNC.
- **Policy #14 ("nothing's wrong" forbidden)** → Scenario: caller answers warily ("what's this about?"), evaluation checks the phrase "nothing's wrong" never appears.
- **Policy #19 (don't append times to follow-ups)** → Scenario: caller asks a product question after times offered, evaluation checks no time-slots in the answer turn.
- **Policy #20 (no repeat slot pairs)** → Scenario: caller rejects first pair, evaluation checks the second pair is different from the first.
- **Policy #30 (gate-phrase exclusivity)** → universal evaluation across all scenarios (no separate Scenario needed).
- **Policy #32 ("write that down" narrow trigger)** → Scenario: caller asks about value-uncertainty (NOT legal advice), evaluation checks "write that down" did not fire.
- **Policy #33 (booking-confirmed locked state)** → Scenario: caller asks a question post-booking, evaluation checks no re-offer of times.
- **Policy #34 (no clinical cleanness)** → universal evaluation.
- **Policy #35 ("you know" only for shared-experience)** → universal evaluation.
- **Policy #36 (close fires once)** → Scenario: caller interjects after the close, evaluation checks no second full close.
- **Policy #37 (no inbound channel offered)** → Scenario: caller asks "how do I reach you?", evaluation checks no "let me know" / "reach out to me."

Roughly half of policies become individual Scenarios, half become universal evaluations.

### Step 4: One Scenario per Error Handling branch

Open the Error Handling section in P. Each enumerated branch is a failure mode the agent must handle. For Riley:

- "Caller is clearly upset or frustrated" → distressed-caller Scenario.
- "Technical issues on the call" → hard to simulate; mark as "skip in webchat, manual on websocket."
- "They ask a question you can't answer" → already covered by tax/legal Scenario above.
- "You misheard something critical" → Scenario: caller's name comes through as garbled in the transcript (you can simulate this via instructions: "you mumble your name once, the agent should ask you to repeat").

### Step 5: Failure-mode regression Scenarios from real-call iteration

Every prompt edit driven by a real-call failure should produce a corresponding Scenario. This is how the suite grows with the agent. From Riley's iteration history:

- **Sign-off loop** (Policy #36 source) — Scenario: caller interjects with question post-booking, then again, then again. Evaluation: only one full close pattern in the transcript.
- **"Let me know" fabrication** (Policy #37 source) — Scenario: caller asks how to follow up if they have questions later. Evaluation: agent did not say "let me know" or "reach out to me."
- **Gate orphaning** ("Does what sound familiar?" handler source) — Scenario: caller asks for clarification on the Stage 1 gate. Evaluation: agent re-anchors with "paid for" preserved (don't drop the sunk-cost anchor).
- **Fabricated emotional state** — Scenario: caller answers "yeah, no, it's fine" with no shared content. Evaluation: agent did not say "I bet you're juggling" or any version of projecting an emotion the caller didn't claim.
- **YES + question swallowing** — Scenario: caller passes a gate AND asks a question in the same turn. Evaluation: agent answers the question before pivoting to scheduling.
- **Fake interruption apology** — Scenario: caller pauses normally between agent's gate and their answer. Evaluation: agent did not preemptively say "sorry, I didn't mean to jump in" when no interruption occurred.

These are the most valuable Scenarios in the suite — they encode hard-won lessons from production calls. **Every fix to the prompt that came from a real-call transcript should leave behind a regression Scenario that catches the same pattern in CI.**

### Step 6: Coverage check — map Scenarios back to the prompt

After enumerating, walk the prompt one more time and confirm:
- Every **goal stage** has at least one happy-path Scenario hitting it.
- Every **(s) handler** has at least one Scenario triggering it.
- Every **policy** is either a Scenario or a universal evaluation.
- Every **Error Handling branch** has a Scenario or an explicit "manual test only" note.
- Every **failure-mode fix** in the prompt's edit history has a regression Scenario.

Anywhere the prompt has content with no corresponding Scenario, you have either: (a) a coverage gap, or (b) dead content in the prompt that should be deleted.

### Output: the Scenario manifest

The reverse-engineering pass produces a flat list like this:

```
HAPPY PATHS (6)
  H1. Stage 1 YES → book
  H2. Stage 2 YES → book
  H3. Stage 3 YES → book
  H4. Stage 4 YES (closer) → book
  H5. All stages NO → graceful accept
  H6. Stage 3 YES + scheduling hesitation → closer rescue → book

(s) HANDLERS (14)
  S1. "Not ready right now"
  S2. "I'm too busy"
  ...

POLICY-DRIVEN (8)
  P1. DNC immediate honor (Policy #13)
  P2. "Nothing's wrong" forbidden (Policy #14)
  ...

ERROR HANDLING (2)
  E1. Distressed caller
  E2. Misheard name

REGRESSION (6)
  R1. Sign-off loop
  R2. "Let me know" fabrication
  ...

UNIVERSAL EVALUATIONS (no separate scenarios)
  U1. Gate-phrase exclusivity (Policy #30)
  U2. No clinical cleanness (Policy #34)
  ...
```

For Riley, that's roughly **35 Scenarios** total, plus ~6 universal evaluations applied across all of them. Build this manifest before writing any Scenario JSON — it tells you exactly what to build, what Personality to pair each with, and which universal evaluations to attach.

### Pairing Scenarios with Personalities

Once both inventories exist, pair them deliberately:

- **Happy paths** → run against multiple ICP personalities (cooperative-fast, skeptical-curious, distracted-busy). Each pairing is a separate Simulation.
- **(s) handlers** → run against the personality whose behavior naturally triggers that handler. "I already have an attorney" pairs with an ICP personality scripted to mention their attorney. "Are you AI?" pairs with ICP-skeptical.
- **Policy-driven** → run against the personality designed to bait the policy violation. DNC pairs with the non-ICP DNC requester. "Nothing's wrong" trap pairs with non-ICP hostile.
- **Error Handling** → run against non-ICP distressed, non-ICP off-topic.
- **Regression** → pair with the personality that originally triggered the failure in production (if known) plus one ICP variant.

A single Scenario paired with N Personalities = N Simulations in the suite. That's how a 35-scenario manifest grows into a 60-80 simulation suite.

---

## Designing the suite for a goal-based agent

For any agent built with this skill, structure the suite to exercise **one Scenario per goal stage and one per redline policy**. The SCRIPT framework gives you the inventory automatically.

### Mandatory scenario set

**Happy-path scenarios** — one per shortest possible YES path:
- Stage 1 YES — caller recognizes the benefit immediately, books on first slot offered.
- Stage 2 YES — caller doesn't recognize it but accepts after the explanation + dollar anchor.
- Stage 3 YES — caller resists at "why a lawyer?" but agrees after the lawsuit-stakes pitch.
- Stage 4 YES — caller hesitates after Stage 3, agrees after the doctor metaphor + "try it once" close.

**Resistance scenarios** — one per objection handler in (s).

**Customer Question scenarios** — one per question handler (e.g., "Are you AI?" pre-booking and post-booking are different code paths).

**Edge / hostile / compliance scenarios** — DNC, hostile/scam reaction, wrong person answers, voicemail detection, legal-advice request.

**Failure-mode regression scenarios** — designed to catch the patterns real-call iterations have exposed:
- Caller agrees AND asks a substantive question in the same turn — agent must address the question before pivoting.
- Caller asks a clarification on the gate phrase ("Does what sound familiar?") — agent must fire the gate-recovery handler with "paid for" preserved.
- Caller interjects post-booking — agent must NOT re-fire the full close (sign-off loop check).
- Caller asks for an inbound contact path — agent must NOT offer "let me know."
- Agent must NOT project an emotional state ("I bet you're juggling a lot") onto a caller who didn't share one.

A mature suite for a goal-based agent runs ~25 scenarios. Ship in increments — start with the four happy paths plus DNC plus three top objections, expand from there.

### Personality library

Build a library of reusable Personalities once per agent type:
- Cooperative caller (says yes early, easy book)
- Skeptical caller (presses for specifics)
- Curt / busy caller (short answers, low patience)
- Confused caller (doesn't track gate phrases, asks "what?")
- Hostile / suspicious caller ("is this a scam?")
- Post-booking interrupter (raises questions after the booking is locked)
- Composite-response caller (delivers YES + question in the same turn)

Each Personality is reusable across many Scenarios. The Scenario controls *what to test*; the Personality controls *who's calling*.

### Evaluation patterns

Define evaluations as structured outputs whose schema description is a precise yes/no question. The AI judge reads the transcript and produces the answer.

**Evaluation hygiene:**
- Schema description must be precise. "Did the agent book a time?" is too vague. "Did the agent state back a specific day, date, AND time AND get caller confirmation on the callback number, all before saying goodbye?" gets a reliable yes/no.
- One behavior per evaluation. Don't AND multiple checks into one — split them.
- Schema type must be `string`, `number`, `integer`, or `boolean`. Most goal-based evaluations are boolean.
- Mark only the load-bearing evaluations as `required: true`. Use `required: false` to track signals that shouldn't fail the run.

**Universal evaluations** (apply to every scenario):
- `booking_confirmed_or_graceful_decline` — call ended in either a confirmed booking or a graceful accept.
- `no_clinical_cleanness` — agent's responses showed natural fillers/contractions per Character placement rules.
- `no_fabrication` — agent did NOT respond to content the caller didn't share (no "good to hear you're doing well" when they didn't say that, no "you must be juggling" when they didn't say that, no apology for an interruption that didn't happen).
- `gate_phrase_exclusivity` — Stage gate phrases ("Does this sound familiar?", "Sound good?", etc.) appeared only in their assigned stage.

**Booked-call evaluations** (apply to scenarios that should book):
- `first_name_used_on_close` — Goal 6 mandatory name use.
- `time_specifics_clean` — agent did not insert fillers inside the day/date/time read-back.
- `single_close_only` — the full close pattern fired once, not multiple times in a sign-off loop.
- `no_inbound_channel_offered` — agent did not say "let me know," "reach out to me," or imply a callback path.

**Resistance-handling evaluations:**
- `objection_addressed_before_pivot` — when caller raised an objection, agent handled it (with the matching handler) before pivoting back to scheduling.
- `closer_fired_before_objection_fallback` — if caller hesitated at scheduling pre-Stage-4, agent fired Stage 4 before falling to objection handlers.

---

## Iteration workflow

```
Edit local prompt.md
  ↓
Phase 0.5 — Lossless Conversion Protocol diff-check
  ↓
Push to VAPI (mcp__vapi-mcp__update_assistant or curl PATCH)
  ↓
Run sim suite — POST /eval/simulation/run with vapi.webchat transport
  ↓
Poll until ended — GET /eval/simulation/run/{runId}
  ↓
Inspect failed items — GET /eval/simulation/run/{runId}/item
  ↓
Read transcript + which evaluation failed
  ↓
Fix: surgical prompt edit OR new policy/handler
  ↓
Repeat from "Phase 0.5"
  ↓
When all webchat scenarios pass: re-run on vapi.websocket for voice-specific verification
  ↓
Ship
```

**Don't iterate against live calls when sim coverage exists.** Real-call transcripts are gold for finding NEW failure modes — that's how every Policy in Riley's prompt got discovered. But once a failure mode is identified, the fix lands in (a) the prompt, (b) a regression Scenario in the sim suite, and (c) a new evaluation criterion if applicable. After that, regression is caught in CI, not in production.

---

## CI/CD pattern

Block deploys when sim pass rate drops below threshold:

```bash
#!/usr/bin/env bash
set -euo pipefail

SUITE_ID="suite-uuid-for-this-agent"
ASSISTANT_ID="$1"
KEY="$VAPI_API_KEY_ACME"

RUN=$(curl -sS -X POST https://api.vapi.ai/eval/simulation/run \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"simulations\": [{\"type\": \"simulationSuite\", \"simulationSuiteId\": \"$SUITE_ID\"}],
    \"target\": {\"type\": \"assistant\", \"assistantId\": \"$ASSISTANT_ID\"},
    \"transport\": {\"provider\": \"vapi.webchat\"}
  }")

RUN_ID=$(echo "$RUN" | jq -r '.id')

# Poll until ended
until [ "$(curl -sS -H "Authorization: Bearer $KEY" \
  https://api.vapi.ai/eval/simulation/run/$RUN_ID | jq -r '.status')" = "ended" ]; do
  sleep 5
done

RESULT=$(curl -sS -H "Authorization: Bearer $KEY" \
  https://api.vapi.ai/eval/simulation/run/$RUN_ID)

PASSED=$(echo "$RESULT" | jq '.itemCounts.passed')
TOTAL=$(echo "$RESULT" | jq '.itemCounts.total')

echo "Sim run $RUN_ID: $PASSED / $TOTAL passed"

if [ "$PASSED" -lt "$TOTAL" ]; then
  echo "FAIL — failure details:"
  curl -sS -H "Authorization: Bearer $KEY" \
    https://api.vapi.ai/eval/simulation/run/$RUN_ID/item | jq '.items[] | select(.status == "failed")'
  exit 1
fi
```

Drop into a pre-deploy hook so a failing sim blocks the iterative push.

---

## Pitfalls

**Webchat doesn't fire hooks.** If you depend on `simulation.run.ended` webhooks, use websocket. For pure pass/fail polling, webchat is fine.

**Voice mode costs calling minutes.** Each websocket scenario consumes the same minutes as a real call. For a 25-scenario suite, keep websocket runs to canonical-final-pass — not iterative.

**Tool mocks must be enabled per Scenario.** A `toolMocks` entry without `enabled: true` is inert. Booking-success vs. booking-failure paths need distinct Scenarios with distinct mocks.

**Schema descriptions must be precise.** The AI judge extracts pass/fail from the description. Vague descriptions produce flaky evaluations.

**Don't quote the gate phrase verbatim in Scenario instructions.** If the tester is told "say yes when she asks 'Does this sound familiar?'", the tester will look for that exact phrase. The agent might naturally vary to "ring a bell?" — and the tester will fail to recognize the gate. Match by intent: "When the agent asks any version of 'do you recognize this benefit', say yes."

**Don't run sims against an empty assistant config.** If `toolIds` aren't set on the assistant, `toolMocks` have nothing to intercept and results will be misleading. Confirm tool attachments in Phase 0.5 inventory before running.

**Treat Personalities, Scenarios, Simulations, and Suites as code.** Store the JSON definitions in `vapi-agents/{agent}/sims/`, version-control them, and re-create rather than patch through the dashboard. The dashboard is for ad-hoc; the suite-of-record is in the repo.

---

## Quick checklist

Before shipping a goal-based agent:
- [ ] Personality library defined (cooperative, skeptical, curt, confused, hostile, composite-response).
- [ ] Suite contains at least the four happy-path Scenarios (one per Stage YES).
- [ ] Suite contains one Scenario per (s) objection handler.
- [ ] Suite contains one Scenario per Customer Question handler.
- [ ] Suite contains the failure-mode regression Scenarios (sign-off loop, "let me know" fabrication, gate-orphaning, fabricated emotional state, YES+question swallowing).
- [ ] Universal evaluations defined (no_clinical_cleanness, no_fabrication, gate_phrase_exclusivity, booking_confirmed_or_graceful_decline).
- [ ] Booked-call evaluations defined where applicable.
- [ ] All webchat scenarios pass.
- [ ] Canonical happy-path scenarios pass on websocket transport.
- [ ] Suite definitions checked into the repo, not just the dashboard.
- [ ] CI/CD hook in place to block deploys on regression failures.
