# Filler & Disfluency Patterns for Voice Agents

How to make voice agents sound like real humans by using fillers, disfluencies, and softeners deliberately — not as decoration, but as load-bearing speech texture. This is the single biggest difference between a voice agent that feels human and one that feels like a polished narrator reading a script.

## The core principle

**Roughly: examples must DEMONSTRATE the filler density, not just describe it.**

Clean Roughly templates produce clean output. The model uses the templates as concrete examples of how the agent should sound — including filler placement, contractions, and softeners. If your Roughly examples are clinically clean, the agent will be clinically clean. If they're naturalistically textured, the agent will be too.

This is the most under-applied insight in voice-agent design. Most prompts include a "use fillers naturally" instruction in Character, then write all the Roughly examples in immaculate written prose. The model follows the examples, not the abstract instruction. Result: a clinically clean agent.

The fix: treat every Roughly template as a target for filler density, contraction usage, and naturalistic phrasing. If a Roughly example reads cleaner than how a polished human SDR would actually say it, it's wrong.

## Three layers working together

This system has three layers that must all be present for it to work:

1. **Where fillers belong vs. where to keep clean** — placement rules.
2. **Vocabulary pool** — what filler patterns are available, with the special "you know" rule.
3. **Density target** — 1-2 fillers per utterance, placed at openers/transitions, varied across calls.

Plus per-utterance density notes baked into worked examples for high-traffic beats, and redlines that prevent clinical cleanness.

---

## Layer 1: Where fillers belong (use them)

- **Openers and topic transitions** — "Hey, so...", "Okay, um, real quick...", "So, yeah..."
- **Brief acknowledgments between turns** — "Yeah, totally," "Got it," "No worries," "Oh, um, right"
- **Before a softened or hedged statement** — "um, I think..." / "I mean, honestly..."
- **Mid-sentence thinking moments before slightly technical phrasing** — "the whole, uh, framework around..."
- **Conversational glue between polished beats** — "right, right", "oh yeah"

## Layer 1: Where fillers do NOT belong (keep these clean)

- **Inside the core pitch content** — the value prop must land cleanly. "Um, basically, like, this saves you a lot of money" undermines the message.
- **Inside the ask or confirmation of specific details** — times, names, dates, phone numbers, emails. "Tuesday at, um, three thirty" sounds uncertain about the booking itself.
- **Inside factual answers to product questions** — "yeah so, basically, you can use it, you know, anytime" reads as evasive when the caller wants a clean answer.
- **Anywhere they'd make you sound uncertain about what matters** — if a filler before a load-bearing word makes the agent seem unsure, drop it.

The rule of thumb: **fillers belong in the connective tissue, not the load-bearing content.** Openers, transitions, and acknowledgments are connective tissue. Pitches, asks, confirmations, and facts are load-bearing.

---

## Layer 2: Vocabulary pool

Rotate across these — don't over-use any single one within a call or across calls.

**Light stalls at transitions:**
- "um," "uh," "so," "like"

**Conversational softeners (introduce a hedged or honest statement):**
- "basically," "honestly," "actually," "I mean"

**Acknowledgment openers:**
- "yeah," "okay," "right," "got it," "no worries"

**Self-corrections and false starts at genuine thinking moments:**
- "I was gonna — actually, let me put it this way..."
- "Yeah, so — sorry, let me back up..."

**Contractions everywhere (not optional — required):**
- "gonna," "wanna," "you're," "we're," "that's," "I'd," "it'd," "you'd," "I'll," "won't," "can't," "don't"

### The "you know" rule — special

"You know" is the most abused filler in voice agents. Most prompts treat it as a generic stall. It isn't.

**"You know" is exclusively a shared-experience marker.** It means "the listener already understands what I'm referring to." It works when invoking something universally understood:

- *Right:* "...one of those things that, you know, just blows up if you're not careful." (Universally understood: things that blow up.)
- *Right:* "It's like, you know, having a friend who happens to be a lawyer." (Universally understood: having a friend.)

It does NOT work as a stall before introducing new info:

- *Wrong:* "So, you know, your plan includes unlimited consultations." (The plan content is new info; "you know" implies they already know it. Confusing.)
- *Wrong:* "You know, the way it works is..." (Stall before new content. Drop the "you know" — use "so, basically..." or just start.)

If the agent is about to introduce information the caller doesn't already have, "you know" is wrong. Use a different filler.

---

## Layer 3: Density target

**On average, one or two light fillers per utterance.** Usually at the opener or a transition. Not three per sentence.

- **After-mirror utterances** (responding to what the caller just said) may have a touch more — they're naturally more reactive.
- **Asks, confirmations, and factual answers** should be cleaner — fewer fillers, often zero in the load-bearing portion.
- **Pitch beats and stage utterances** should land with one filler at the opener, otherwise clean through the body.

### Density should match utterance type

| Utterance type | Density |
|---|---|
| Greeting / opener | Light (1 filler max, often zero) |
| Mirror + transition | Standard (1-2 fillers, typically at opener and one mid-sentence softener) |
| Pitch body | Light (1 filler at opener; clean through body) |
| Probe / ask | Clean (zero fillers in the question itself) |
| Factual answer | Light (1 filler at opener; clean through fact) |
| Acknowledgment | Standard (1 filler — "yeah, totally" / "oh, right" / "got it, yeah") |
| Closer / commitment ask | Clean on the ask itself; may have an opener filler before |
| Time / name / date confirmation | Zero fillers inside the specifics |

### Variation across calls

**Never reach for the exact same opener filler in the exact same spot twice across calls.** If the agent always opens its pitch with "So, um," that becomes a tell. Vary openers, acknowledgments, and bridges. The Roughly examples in the prompt show *placement and density* — not *specific words to copy*.

The model achieves this naturally if the Roughly examples themselves rotate across openers ("So, yeah..." / "Okay so..." / "Yeah, basically..." / "Right, so..."). If every Roughly example in the prompt opens with the same phrase, the agent will too.

---

## How to bake density into Roughly templates

The principle: **make the Roughly text read the way you want the agent to sound.** Don't write clean templates and rely on the abstract Character instruction to add fillers. The model follows the examples.

Bad (clinically clean — agent will mirror this):

> Roughly: "When you formed your LLC with FormFast, one of the benefits included is access to unlimited consultations with a business attorney. These consultations usually run two hundred fifty dollars and up, but as a FormFast member you get them at no extra charge."

Good (textured — agent will mirror this):

> Roughly: "So, basically, when you formed your LLC with FormFast, one of the benefits that came with it is access to unlimited consultations with a business attorney. These usually run, like, two hundred fifty dollars and up, but as a FormFast member you get them at no extra charge — which, honestly, is an amazing deal if you take advantage of it."

Note in the "good" example:
- Opener filler: "So, basically"
- Light mid-sentence stall: "like"
- Conversational softener: "honestly" (introducing the hedged value claim)
- Contractions throughout: "you're," "they're"
- Clean on the dollar anchor itself: "two hundred fifty dollars and up" — no filler inside the number
- Density: 3 fillers across a ~50-word utterance — well within target

### Per-utterance density notes (for high-traffic beats)

For beats that get heavy use (the main pitch, the recognition gate, key probes), include a **density note** alongside the Roughly template. This gives the LLM an explicit target.

Example pattern:

> **Stage 1 — Opening pitch + recognition gate**
>
> Roughly: "Hey, so — I'm reaching out because I noticed you haven't taken advantage of the attorney consultations that are, basically, already included and paid for in your plan. I honestly think this is, like, our most valuable benefit. Does this sound familiar?"
>
> **Filler density target:** Opener filler ("Hey, so —" or equivalent), one mid-sentence softener ("basically"), one mid-sentence stall ("like"). Keep the gate question itself clean.

Without the density note, the LLM may treat the fillers as ornamental and drop them. With it, the LLM treats the density as part of the contract.

---

## Worked examples — good and bad

### Greeting

**Bad (too clean):**
> "Hi, this is Riley with FormFast. Did I catch you at an okay time?"

**Bad (over-stuffed):**
> "Hey there, um, so, this is, uh, Riley with, like, FormFast, and I was just, you know, wondering if I, um, caught you at an okay time?"

**Good:**
> "Hey, this is Riley with FormFast on a recorded line. Did I catch you at an okay time?"
>
> Density: light. One soft "Hey" opener. Clean through the disclosure (it's a compliance line). The ask at the end is clean. Three fillers would feel uncertain at first impression.

### Mirror + transition

**Bad (clean):**
> "Great. Let's get this on your calendar."

**Good:**
> "Yeah, totally — and that's exactly why I think this is gonna be useful for you. So what do you say we get this on your calendar real quick?"
>
> Density: opener acknowledgment ("Yeah, totally"), conversational connector ("and that's exactly why"), contraction ("gonna"). Clean on the ask itself.

### Probe / ask

**Bad (over-stuffed):**
> "So, um, basically, like, do you, you know, want me to find you a time?"

**Good:**
> "So — want me to find you a time?"
>
> Density: zero fillers inside the question. One soft opener. The question lands cleanly.

### Factual answer

**Bad (clean and stiff):**
> "It is thirty minutes long, and the attorney calls you."

**Bad (over-fillered):**
> "So, um, it's, like, basically, you know, thirty minutes long, and, uh, the attorney calls you."

**Good:**
> "Yeah, so it's just thirty minutes — and the attorney calls you, so you don't have to call in."
>
> Density: opener acknowledgment ("Yeah, so"), one casual softener ("just"). Clean through the facts.

---

## How to use this in the SCRIPT prompt

### In Character

Replace generic "use fillers naturally" with explicit placement rules. Reference this doc inline. Sample text:

> **Conversational Speech Patterns — USE FILLERS**
>
> You talk like a helpful person, not a brochure. Your speech MUST have natural imperfections. The "Roughly:" examples throughout this prompt show the TARGET filler density — do not clean them up. If your responses sound clinically clean or scripted, you're under-using fillers.
>
> Where fillers belong: openers, topic transitions, brief acknowledgments, softeners before hedged statements, conversational glue between polished beats.
>
> Where fillers do NOT belong: inside the core pitch content (let it land), inside asks and confirmations of times/names/dates (no uncertainty on what matters), inside factual answers.
>
> Vocabulary pool: "um, uh, so, like" (light stalls), "basically, honestly, actually, I mean" (softeners), "yeah, okay, right, got it" (acknowledgments). Contractions everywhere. "You know" ONLY for shared-experience references — never to introduce new info.
>
> Density target: one or two light fillers per utterance, usually at openers or transitions. Not three per sentence. Asks and confirmations are cleaner than mirrors and acknowledgments.
>
> Variation: never reach for the same opener filler in the same spot twice across calls. The Roughly examples show placement and density — not specific words to copy.

### In Role

Add a one-line natural-speech expectation:

> **Natural Speech:** Calls should sound like a warm, polished human SDR — not a scripted reader. Light fillers at openers and transitions are part of the job, not a defect.

### In Instructions (per-beat density notes)

For high-traffic beats, add a density target right under the Roughly template. Treat it like the semantic-elements list in progressive disclosure — it's a contract on what must survive into the agent's actual speech.

> **Stage 1 — Opening pitch + recognition gate**
>
> Roughly: "[textured example with target density]"
>
> Filler density target: [specific guidance for this utterance type]

For greeting, ask, and confirmation beats, the density note can be terse: "Keep the opener clean. Fillers stay light here — you don't want to sound uncertain on the opener." / "Clean on specifics — no fillers inside the time itself."

### In Principles → Redlines

Add a redline to prevent clinical cleanness:

> **Never sound clinically clean.** If an utterance has zero fillers, softeners, or contractions where the Roughly example suggests them, you're under-using. Add a light opener filler ("so, um" / "yeah" / "honestly") or mid-sentence softener ("basically" / "like") in the right spot.
>
> **Never use "you know" to introduce new info** — reserve for shared-experience references.

---

## Pitfalls

**Generic Character instruction with clean Roughly examples.** The instruction says "use fillers naturally," the examples are immaculate prose. Result: agent reads from the examples, not the instruction. Clinically clean output.

**Over-stuffed Roughly examples.** Three fillers in every sentence. Agent mirrors that and sounds drunk or hesitant. Density target prevents this.

**Fillers inside load-bearing content.** "Um, the booking is on, like, Tuesday at, uh, three thirty." Sounds like the agent isn't sure about the booking. Fix: clean specifics, fillers only in connective tissue.

**Same opener filler every utterance.** "So, um..." every single turn. Becomes a tell. Variation rule prevents this — but only if the Roughly examples themselves rotate across openers.

**"You know" abuse.** Used as a generic stall before new information. Sounds patronizing because it implies the listener already knows what's coming. Fix: reserve for genuine shared-experience references.

**Density notes missing on high-traffic beats.** The pitch beat has a clean Roughly with no density note; the LLM strips fillers thinking it's "being professional." Result: the most-spoken utterance sounds the most robotic. Fix: density notes on every high-traffic beat.

---

## Quick checklist for reviewing filler usage in a prompt

- [ ] Character section explicitly distinguishes where fillers belong vs. where to keep clean.
- [ ] Vocabulary pool listed with rotation guidance.
- [ ] "You know" rule is explicit — shared-experience marker only.
- [ ] Density target stated (1-2 per utterance, not 3+).
- [ ] Roughly examples DEMONSTRATE the target density — they're not clinically clean.
- [ ] High-traffic beats have per-utterance density notes.
- [ ] Greeting, asks, and confirmations are explicitly called out as cleaner.
- [ ] Redline preventing clinical cleanness exists in Principles.
- [ ] Redline on "you know" misuse exists.
- [ ] Roughly examples vary their openers across stages — not all "So, um..."
- [ ] Contractions are present throughout examples (not just instructions).
