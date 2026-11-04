---
type: voice-agent-spec
spec_version: 1
status: draft            # draft | approved
approved_on:             # YYYY-MM-DD when the user approves
industry:
city:
role:
platform: flowforge
demo_type:               # generic | tailored
demo_business:           # made-up name (generic) or the target business (tailored)
playbook: playbook.md
research: ../../research/
---

# AI [role] spec: [Industry] in [City]

> Input contract for the goal-based-voice-agent skill. The section arrows (→) show which SCRIPT phase each section feeds. Keep the headings as they are.

## 1. Summary
Three to five sentences: what the agent does, for whom, the problem it solves (from the reviews), and what the demo shows.

## 2. Scenario → S
- **Business:** [demo business: name, location, services overview, hours]
- **Callers:** [who calls and why, most to least common, with the share if known]
- **Inbound / outbound:**
- **Goal of a call:** [primary and secondary outcomes]

## 3. Character → C
- **Name and persona:**
- **Personality:** [3-5 traits, each tied to a praise theme]
- **Voice:** [gender, age range, accent, pace, energy]
- **Expressiveness:** [subtle / warm / lively; moments where warmth or humour fits, and moments where it never does, e.g. complaints. The builder adds emotion and laughter tags only if the voice is Cartesia Sonic.]
- **Speech style:** [sample phrases from the playbook; words to avoid]

## 4. Role and responsibilities → R
| Responsibility | Playbook ref | In scope for the agent? |
|---|---|---|

## 5. Skills → I (call flows)
### Skill: [name]
- **Trigger:** what the caller says or needs
- **Flow:** 1. … 2. … 3. …
- **Data needed:** [fields collected or looked up]
- **Integration:** [which integration from §7]
- **Success:** [what has to be true at the end]
- **Playbook rules enforced:** [rule refs]
- **Failure / fallback:** [what happens if the tool fails or the caller goes off-path]

(One block per skill: booking, rescheduling, cancellation, service and price questions, pre- and after-care, message taking, transfer, …)

## 6. Principles and guardrails → P
- Rules from the playbook the agent must always follow.
- What the agent must never do (medical advice, guaranteeing results, quoting prices not in the knowledge base, …).
- Escalation triggers and how to hand off.
- Compliance notes (e.g. HIPAA / privacy for medical businesses).
- Always include these three, adapted to the business:
  - **Recording disclosure** in the first message wherever the law requires consent from everyone on the call (e.g. California and other all-party-consent states), and as good practice elsewhere.
  - **AI honesty:** if a caller asks whether they're talking to a real person, the agent says it is the business's AI assistant and offers a human.
  - **No vendor names:** the agent never names the AI, voice or software providers behind it.

## 7. Integrations → T
### Integration: [category, e.g. Booking and practice management]
- **Used by skills:** [list]
- **Operations needed:** [check availability, create booking, …]
- **Ranked apps for this industry:**

| Rank | App | Evidence (tech-stack.md) | API / connection route | Plan |
|---|---|---|---|---|
| 1 | | | | preset |
| 2 | | | | preset |
| 3 | | | | preset / add on demand |
| 4 | | | | add on demand |

(One block per integration: booking, calendar, CRM/marketing, SMS, payments, phone transfer, knowledge base.)

## 8. Knowledge base
What the agent needs to know, and where it comes from: services and prices, policies (deposit, cancellation, age, consultation), pre- and after-care, FAQs from the reviews, location, parking, hours.

For a **generic demo**, prices, policies and staff are made up: set them at typical local levels, and label every price as a demo value in the knowledge base so nobody mistakes the demo for a real quote. For a **tailored demo**, use only what the business publishes, and list anything missing as an open question rather than guessing.

## 9. Demo plan
| Integration | Live in demo? | How (real demo account / real demo calendar) | If not live: why, and what the agent says instead |
|---|---|---|---|

Nothing in the demo pretends to work. A capability that isn't live is either left out or clearly handled as "I'll have the team call you back to book."

**FlowForge has no built-in calendar, booking or texting.** The agent reaches a booking system or SMS provider through webhook tools, and most booking APIs need a small connector in between that turns a simple tool call ("book Maya, Tuesday 3pm") into the vendor's request format: for example an n8n workflow or a small serverless function. Name the connector here, and list any account the user must create themselves (e.g. a free booking-system sandbox) in Open questions, since the build can't create accounts.

## 10. Configuration → Phase 7
- **Model, voice, transcriber:** [preferences or "builder's default"]
- **First message:**
- **Max call length, silence timeout, end-call rules:**
- **Transfer number for the demo:**

## 11. Test scenarios
| # | Scenario | Caller persona | Based on (theme / quote) | Pass criteria |
|---|---|---|---|---|
(10-15, drawn from real complaints and common calls.)

## 12. Success metrics
What "good enough to sell" means: e.g. books correctly in 9/10 test calls, never quotes a wrong price, transfers within 2 turns on request.

## 13. Open questions
Anything the user still has to decide.

## Change log
| Date | Change | Reason (feedback) |
|---|---|---|
