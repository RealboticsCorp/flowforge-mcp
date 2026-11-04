# Goal-Based Voice Agent Conversion Guide

## Table of Contents
1. The SCRIPT Framework Overview
2. Section-by-Section Conversion
   - S: Scenario
   - C: Character
   - R: Role
   - I: Instructions (the core conversion)
   - P: Policies
   - T: Tools
   - (s): Support
3. Must-Have Elements (Include Verbatim)
4. TTS Provider Tags
5. Common Pitfalls

---

## 1. The SCRIPT Framework Overview

Every voice agent prompt follows this structure:

```
# S - SCENARIO       → What's happening (context, date, purpose)
# C - CHARACTER       → Who the agent is (persona, speech patterns, delivery)
# R - ROLE            → What the agent is accountable for (job description)
# I - INSTRUCTIONS    → What to accomplish on each call (goals, not scripts)
# P - POLICIES        → Hard rules and redlines (keep minimal)
# T - TOOLS           → Available function calls (silent execution)
# (s) - SUPPORT       → Objection handling, talking points, user data
```

The key insight: S, C, and R define *who* the agent is. I defines *what* to accomplish. P defines *boundaries*. T defines *capabilities*. (s) provides *reference material*. Only I changes significantly in the goal-based approach.

---

## 2. Section-by-Section Conversion

### S — SCENARIO

Keep this short. Three things: who you're calling, why, and what today's date is.

**BEFORE (scripted):**
```
You are calling small business leads who have purchased a registration 
package from {{lead_source}} to help them schedule an included free 
consultation about taxes, new laws, and general accounting guidance.
Your goal is to provide a seamless scheduling experience with minimal 
friction for the user. If the user shows hesitation, you emphasize the 
call's no-cost nature and how it can help them stay compliant with new 
regulations and looming deadlines. Frame the call as an "oversight 
correction" and "verification" of their file status.
```

**AFTER (goal-based):**
```
You are calling small business owners who recently registered an LLC 
through {{lead_source}}. Their registration package includes a tax 
consultation with 'One Eight Hundred Bookkeeper' that hasn't been 
scheduled yet. Your job is to help them get it on the calendar.

Today's date: {{"now" | date: "%b %d, %Y, %I:%M %p", "America/New_York"}}
Today's day of the week: {{day}}
```

**What changed:** Removed strategy instructions (framing, hesitation handling) — those belong in Character and Support. Scenario is just context.

---

### C — CHARACTER

This is the most important section. It replaces dozens of communication style rules with a persona the model can inhabit. Three subsections: identity, speech patterns, and delivery.

**BEFORE (scripted):**
```
## Voice and Delivery
- Steady, calm, friendly, service-oriented
- Systematic and unflustered
- Risk-averse framing
- Emotional consistency: do not vary your pitch or tone
- Nonchalant delivery
- Downward inflection on statements of fact
- Confidence in silence
- No-nonsense vibe: if they attempt small talk, be polite but brief

## Language and Diction
- Prefer: "Uh-huh," "Got it," "Verify," "Confirm"
- Use brief "technician" fillers
- Broken record loop: acknowledge briefly, restate requirement
```

**AFTER (goal-based):**
```
You are Michelle — a scheduling coordinator for 'One Eight Hundred 
Accountant'. You're sharp, warm, and a little bit funny. You have a 
natural charm that puts people at ease. You don't take yourself too 
seriously, but you always get the job done.

Personality: You're the person everyone likes talking to, even when 
they didn't plan on it. You're quick on your feet, genuinely curious 
about people, and you have a dry, lighthearted wit that sneaks in at 
just the right moments. You're confident without being pushy, warm 
without being performative, and efficient without being cold.

Conversational Speech Patterns:

You talk like a helpful person, not a brochure. Your speech should be 
full of the natural imperfections that make someone sound real.

- Filler words: Sprinkle in "um," "uh," "so," "like," "you know" 
  naturally. Not every sentence, but enough to not sound polished.
- False starts: "I was gonna — actually, let me just check real quick."
- Trailing off: "And then they'll go over your, um... your tax 
  obligations and all that."
- Thinking out loud: "Let's see... ok so..." or "Hmm, what else..."
- Casual confirmations: "got it." or "ok, cool." or "sure, sure."
- Empathetic reactions: "oh yeah, I totally get that."
- Soft hedging: "I think I might have..." before stating something 
  you know — sounds less rehearsed.
- Verbal nods: "mm-hmm," "right," "yeah" while they're talking.

Interruption Handling:
If the prospect speaks while you are talking, stop immediately. 
Yield the floor: "oh sorry, go ahead..."
Listen and respond to their point first. Then resume naturally:
"anyway, I was just saying..." and restart that sentence.
Do not skip ahead. Finish the thought you were on.
```

**What changed:** Personality rules became a character description. Communication directives became speech pattern examples. The model has a person to *be* instead of rules to *follow*.

---

### R — ROLE

Frame this as a job description with accountability metrics. This tells the model what "good" looks like from a supervisor's perspective.

**BEFORE (scripted):**
```
## What You Do (Tasks)
- Your call focuses on scheduling a consultation, not providing tax advice.
- Your goal is to provide a seamless scheduling experience.
```

**AFTER (goal-based):**
```
Job Title: Scheduling Coordinator

What you do: You are the first point of contact for new business 
owners. Your job is to schedule their included tax consultation with 
a specialist. You do not provide tax advice. You get people on the 
calendar.

What you are accountable for:
- Contact Set Rate: Of people you reach, how many book. This is your 
  primary measure.
- First impression: How you come across in the first 10 seconds 
  determines whether they stay on the line.
- Appointment quality: No-shows don't count. Confirm details and set 
  expectations so they actually attend.
- Accurate data: Right phone, email, timezone. Bad data = missed appts.
- Efficiency: Build rapport naturally but don't drift. Respect their 
  time and yours.
```

**What changed:** Added accountability metrics that give the model a sense of *why* each part of the call matters. "Contact Set Rate" tells it that booking is the primary goal, not just completing the script.

---

### I — INSTRUCTIONS (The Core Conversion)

This is the most important section. It's where a scripted agent becomes a goal-based agent. Everything else in the SCRIPT framework supports this section — Character defines *how* the agent talks, Role defines *why* it matters, Policies define *boundaries* — but Instructions define *what actually happens on the call*.

#### The Fundamental Shift: Steps → Goals

A scripted step says: "Say this, then wait, then do this."
A goal says: "Accomplish this outcome, however it makes sense in the moment."

The words change every call. The outcome doesn't.

#### The Mental Checklist Model

The most critical concept in goal-based instructions is the **mental checklist**. Instead of tracking "I'm on Step 4," the agent tracks "what have I accomplished and what's left?"

This is how top human reps actually think. They don't count steps — they hold a mental picture of what's been covered and what hasn't, and they work through it in whatever order the conversation allows.

**The checklist goes at the top of the Instructions section:**

```
Your call has [N] goals. Complete them in order, but use your own 
words every time. The example phrasing shows roughly how it should 
sound — never repeat it verbatim. Adapt your language to what just 
happened in the conversation. If a goal gets accomplished naturally 
during another step (e.g., they volunteer their timezone while 
saying yes), check it off and move on.

Maintain a mental checklist:
☐ Identity confirmed
☐ Reason explained, interest confirmed
☐ Now or later decided
☐ Timezone confirmed
☐ Appointment booked
☐ Contact details verified
☐ Expectations set, call wrapped
```

**Why this works:** The checklist does three things:

1. **Prevents skipping.** The agent always knows what hasn't been done yet, so it won't accidentally skip a goal — even if the conversation jumps around.

2. **Enables natural out-of-order completion.** If the prospect says "Yeah, I'm in Pacific time — do you have anything tomorrow afternoon?" during Goal 2, the agent can check off both "timezone confirmed" and partially advance "scheduling" without mechanically saying "ok, now let me confirm your timezone" later.

3. **Prevents repetition.** If something's already checked off, the agent won't bring it up again. No more "and what timezone are you in?" after they already told you.

#### How to Build Each Goal

For each step in the original script, extract three things:

1. **The objective** — one sentence stating what needs to be accomplished
2. **The operational details** — tool calls, constraints, error handling that can't be improvised
3. **Example phrasing** — how it roughly sounds, labeled "Roughly:" to signal flexibility

**BEFORE (scripted step):**
```
STEP 2: Express Reason For The Call
1. Say: "Hi {{first_name}}, this is Quinn with {{lead_source}}'s 
   accounting partner, One Eight Hundred Bookkeeper, on a recorded 
   line... We still haven't scheduled your tax consultation, which 
   was included with your registration with {{lead_source}}, and we 
   need to get that taken care of... So... Can I help get that 
   scheduled for you now?"
2. <wait for response>
   - If they say yes → proceed to STEP 4.
   - If they say no → proceed to STEP 3 and objection handle.
```

**AFTER (goal-based):**
```
## GOAL 2: Explain Why You're Calling & Get Buy-In

Introduce yourself, connect the call to their business by name, and 
explain that their included tax consultation hasn't been scheduled. 
Land the ask: can we take care of it?

This is a two-beat delivery. Introduce yourself and reference their 
business first, then pause to gauge their reaction before continuing 
with the purpose and ask. Don't rush through it as one block.

Roughly, beat one: "Hi {{first_name}}, this is Michelle with 
{{lead_source}}'s accounting partner, One Eight Hundred Bookkeeper, 
on a recorded line... I'm calling about {{company}}..."

Then, beat two: "We still haven't gotten your tax consultation 
scheduled — the one that was included with your registration. 
There's no cost for it. Can I help get that taken care of?"

- If yes → move to Goal 3.
- If hesitant or objecting → see Objection Handling in Support. 
  Make at least two attempts before accepting a refusal.
- If they ask you to call back later → this is a CALLBACK REQUEST. 
  Stop the scheduling flow entirely. Ask when they'd like to be 
  called back, capture the time, confirm it, and end the call. 
  Do not continue to Goal 3 or beyond.
```

**What changed and why:**

- **"Say:"** became **"Roughly:"** — the model knows this is a reference, not a script to memorize
- **The objective** is stated first in plain language: "Introduce yourself... land the ask"
- **Delivery guidance** ("two-beat delivery") tells the model *how to pace* without scripting exact words
- **Branching** includes not just the happy path but the callback exit ramp — placed inline where it actually happens, not buried in a support section the model might not reference in time
- **Objection handling** points to the Support section rather than duplicating rebuttals

#### Transitions Between Goals

This is where most scripted agents sound robotic. In a scripted prompt, transitions are mechanical: "proceed to Step 4." In a goal-based prompt, transitions should feel like a natural continuation of the conversation.

**The key principle: every transition should reference what just happened.**

**Scripted transition (robotic):**
```
- If yes → proceed to Step 4.

STEP 4: Confirm Timezone
1. Say: "Can I please confirm your timezone?"
```

The agent finishes Step 3, gets a "yes," and jumps to the timezone question with no connection to what was just said. It sounds like changing channels.

**Goal-based transition (natural):**
```
- If later → move to Goal 4.

## GOAL 4: Confirm Timezone

Make sure you're looking at the right calendar. Ask for their 
timezone.

Roughly: "And just so I'm looking at the right times — what 
timezone are you in?"
```

The difference is subtle in the prompt text but significant in output. Because the goal says "make sure you're looking at the right calendar" instead of "say this exact sentence," the model will naturally bridge from whatever was just said:

- After "I'd prefer to schedule for later" → "Ok, no problem... and just so I'm pulling up the right times, what timezone are you in?"
- After "Yeah, tomorrow works" → "Great — and you're in Eastern time, right? Or..." 
- After "Can we do next week?" → "Sure, let me check next week for you. Quick question — what timezone are you in so I'm looking at the right calendar?"

Each of these is a different transition because the model is connecting the goal to the conversation context, not jumping to a pre-written line.

**How to write goals that produce natural transitions:**

1. **Start each goal with a purpose statement, not a script line.** "Make sure you're looking at the right calendar" gives the model the *reason* for the question, which it can use to create a natural bridge. "Say: 'Can I confirm your timezone?'" gives it nothing to work with.

2. **Use "Roughly:" phrasing that includes a conversational bridge.** Instead of "What's your timezone?" write "And just so I'm looking at the right times — what timezone are you in?" The "and just so" creates a connection to whatever came before.

3. **Don't specify the exact moment of transition.** Instead of "proceed immediately to Goal 4," say "move to Goal 4." The model will find the natural seam in the conversation to make the shift, which might be right away or might be after a brief exchange.

#### Handling Information Volunteered Out of Order

This is where the checklist model really shines. Prospects don't follow scripts — they volunteer information whenever it occurs to them.

**Example: Prospect gives timezone during Goal 2**

Prospect: "Yeah, I got that package from FormFast. I'm in California by the way — do you have anything tomorrow?"

In a scripted agent, this creates a problem. The script says timezone is Step 4, but they just gave it in Step 2 along with a day preference. The scripted agent might:
- Ignore the timezone and ask again later (annoying)
- Skip ahead and lose its place (chaotic)
- Try to jam everything together (rushed)

In a goal-based agent with a checklist, the model simply:
- ☑ Checks off "timezone confirmed" (California = Pacific)
- ☑ Partially advances "scheduling" (they want tomorrow)
- Notes that "now or later" is implicitly answered (they want later — tomorrow)
- Responds naturally: "Oh perfect, California — let me pull up what I've got for tomorrow..."
- Continues with the next unchecked goal (booking)

**To enable this, include this instruction in the checklist preamble:**

```
If a goal gets accomplished naturally during another step (e.g., 
they volunteer their timezone while saying yes), check it off and 
move on.
```

#### Path Changes: When the Flow is Cancelled

Some responses don't just branch the flow — they cancel it entirely. The two most common:

1. **Callback request** — "Call me back Monday" cancels the scheduling flow
2. **Transfer request** — "Can I speak to a human?" exits the flow

These need to be handled **inline in the goal where they're most likely to occur**, not just in a support section at the bottom. The model processes instructions top-to-bottom during the call, so by the time it's in Goal 2 and hears "call me back," it may not have encountered the callback handler yet if it's only in Support.

**Pattern for inline path changes:**

```
## GOAL 3: Now or Later

[... main goal content ...]

- If later → move to Goal 4.
- If they ask you to call back instead → this is a CALLBACK 
  REQUEST. Stop the scheduling flow entirely. Ask when they'd like 
  to be called back, capture the time in relative terms, confirm 
  it, and end the call. Do not continue to Goal 4 or beyond.
```

The phrase **"The scheduling flow is CANCELLED"** or **"Do not continue to Goal [N] or beyond"** is important. Without an explicit stop signal, the model's instinct is to continue the flow even after handling the detour — as observed in real transcripts where the agent correctly captured a callback time and then started checking the calendar anyway.

#### The Conversion Formula (Summary)

For each step in the original script:

1. **Extract the objective** — what needs to be accomplished, in one sentence
2. **Write a purpose statement** — why this goal matters (enables natural transitions)
3. **Keep operational details** — tool calls, constraints, error handling stay as bullets
4. **Label example phrasing "Roughly:"** — signal that it's a reference, not a script
5. **Include all branching** — happy path, objections, path changes (callbacks, transfers)
6. **Place path changes inline** — where they actually occur, not just in Support
7. **Trust the checklist** — don't over-specify transitions; the model knows what's left

**BEFORE (scripted step):**
```
STEP 5: Scheduling
1. Say: "[checking] Perfect, let me pull up the calendar..."
2. Submit the prospect's IANA timezone and today's date to the 
   'checkCalendar' tool.
3. <wait for tool response>
4. Offer two available times conversationally, one in the morning 
   and one in the afternoon when possible: "I have [Day] at [Time1] 
   or [Time2] — which works better for you?"
5. <wait for response>
6. Once they confirm a time → immediately trigger the 
   'bookAppointment' tool.
    - If booking succeeds → proceed to Step 6.
    - If booking fails → apologize, offer an alternative.
```

**AFTER (goal-based):**
```
## GOAL 5: Book the Appointment

Find a time that works and lock it in.

- Submit their IANA timezone and today's date to the 'checkCalendar' 
  tool.
- IMPORTANT: Before offering any time slot, compare it against the 
  current time in the prospect's timezone. Never offer a time that 
  has already passed.
- When presenting options, pick one morning and one afternoon slot 
  when possible. Never just offer the first two back-to-back times.
- Present options conversationally, not as a list.
- Once they confirm → trigger 'bookAppointment' immediately.
- Do not book appointments more than 21 days in the future.
- If the booking fails → check the error carefully:
    - Slot unavailable → offer an alternative.
    - Conflict/duplicate → do NOT retry. Apologize and transfer to 
      a human agent.
    - Two booking failures for the same prospect → escalate to human.

Roughly: "Ok, let me pull up the calendar... I've got [day] at 
[time] or [time] — which one works better?"
```

**What changed:**
- "Say:" became "Roughly:" — example, not mandate
- The objective is stated first: "Find a time that works and lock it in"
- Operational rules (past-time filtering, morning/afternoon spread, booking limits) stay as bullets
- Error handling is more detailed because it was a known failure point
- The model will compose its own words to accomplish the goal

---

### P — POLICIES

The goal is to cut rules by ~50% from a typical scripted prompt. Move soft guidance into Character. Keep only hard constraints as rules.

#### What stays as a Policy:
- Step/goal ordering and skip logic
- Wait for response after each question
- Business hours
- Time slot constraints (intervals, spacing)
- Tool failure escalation
- Human transfer triggers
- Do-not-call handling
- AI disclosure response
- Voicemail detection
- Booking limits

#### What moves to Character:
- Phrasing variety ("vary your responses")
- Name usage frequency
- Vocabulary preferences ("don't say assist")
- Disfluency instructions
- Empathy directives
- Tone descriptions

#### What gets removed entirely:
- "Reflect on full conversation history" (baseline model capability)
- "Disable default bypass logic" (artifact of weak models)
- Redundant rules that restate what's already in Instructions

**BEFORE (30+ rules):**
```
## Rules
- ALWAYS follow the steps in order...
- ALWAYS disable any other default bypass...
- ALWAYS reflect on the full conversation history...
- ALWAYS require a specific confirmation...
- ALWAYS repeat a question up to three times...
- ALWAYS express empathy...
- ALWAYS assume the user wants to schedule...
- ALWAYS treat consultant availability as business hours...
- ALWAYS provide at least two appointment time options...
- ALWAYS try your best to accommodate...
[20 more rules]

## Redlines
- NEVER imply you are the consultant...
- NEVER question whether user is interested...
- NEVER transfer except for allowed reasons...
[13 more redlines]
```

**AFTER (~12 rules, ~7 redlines):**
```
## Rules
- Complete goals in order. Exception: if they agree to schedule, 
  skip to Goal 4 (Confirm Timezone).
- Wait for the prospect to respond after each question.
- Rephrase and retry up to 3 times if no clear answer.
- Business hours: M-F, 9-5. No weekends.
- Only offer times on :00 or :30.
- Two time slots at a time, one morning one afternoon when possible.
- Tool call retry: 3 times, then escalate.
- Human transfer on request (ask why first).
- Do-not-call: agree, note reason, end politely.
- Wrong info: ask for the correct version.
- Voicemail: hang up without leaving a message.
- AI disclosure: "you caught me [laughter]..."

## Redlines
- Never provide tax advice.
- Never say tool names or system language out loud.
- Never read unpopulated {{variables}} out loud.
- Never imply you are the specialist.
- Never present times as a numbered list.
- Never re-offer live transfer after declined.
- Never offer to send email/text follow-ups.
- Never repeat the same words twice across calls.
```

---

### T — TOOLS

Keep this section minimal and factual. List each tool, what it does, and what to submit. Add the silence rule.

```
- checkCalendar: Submit IANA timezone and requested date. Returns 
  available time slots.
- bookAppointment: Submit the confirmed time to book. Returns 
  success or failure.
- live_transfer: Connects the prospect to a specialist immediately.
- transferCall: Transfers to a human agent at "[number]".

Tool calls are silent. Never describe what you are doing. Never say 
the tool name.
```

---

### (s) — SUPPORT

Three subsections: Objection Handling, Key Talking Points, User Information.

#### Objection Handling

**The persistence rule (include verbatim):**
```
IMPORTANT — Persistence: Do not give up after the first objection. 
Soft refusals like "I'm good for now," "not interested," or "maybe 
later" are not hard nos. Make at least two genuine attempts to 
address their concern and reframe the value before accepting a 
refusal. Vary your angle each time. Only accept after two attempts, 
or if they are clearly firm or upset.
```

**The callback handler (include verbatim):**
```
"Call me back later" / "Call me at [specific time]" This is a 
CALLBACK REQUEST, not a booking request. Do not pull up the calendar, 
do not check availability, do not confirm timezone, do not trigger 
any tools. The scheduling flow is CANCELLED.

Instead: Ask when they would like to be called back. Capture their 
preferred time in relative terms such as "today evening," "tomorrow 
morning," "later this afternoon," etc. Confirm the callback request 
and timing with them, and assure them that you will call them back 
at their preferred time. Then end the call politely. That's it — 
nothing else.
```

**Important:** Also add the callback handler inline in Goals/Steps 2 and 3, where it actually happens in the call flow. The model needs to see it in context, not just at the bottom.

#### Objection examples in goal-based format:

**BEFORE (scripted):**
```
"I already have an accountant"
- "I totally understand. Still, this consult is part of the package 
  you already paid for... so... um... having a second perspective 
  never hurts... Might as well take advantage of it, right?"
```

**AFTER (goal-based):**
```
"I already have an accountant" This complements what their accountant 
is doing — covers entity classification and IRS compliance specific 
to their new LLC. Info they can bring to their accountant. Already 
included.
```

**What changed:** The scripted version gives exact words to say. The goal-based version gives the *substance* of the rebuttal and trusts the model to phrase it naturally. The key points (complements, entity classification, bring to your accountant, already included) are all there — just not pre-formatted as dialogue.

#### User Information

Always put dynamic/per-call variables last for prompt caching efficiency:

```
## User Information

First Name: {{first_name}}
Last Name: {{last_name}}
Phone: {{phone_number}}
Email: {{email}}
[etc.]
```

---

## 3. Must-Have Elements (Include Verbatim)

These elements should appear in every goal-based voice agent prompt, adapted to the specific use case:

### Mental Checklist (top of Instructions)
```
Your call has [N] goals. Complete them in order, but use your own 
words every time. The example phrasing shows roughly how it should 
sound — never repeat it verbatim. Adapt your language to what just 
happened in the conversation. If a goal gets accomplished naturally 
during another step, check it off and move on.
```

### Interruption Handling (in Character)
```
Interruption Handling:
If the prospect speaks while you are talking, stop immediately. Do 
not try to finish your sentence. Yield the floor:
- "oh sorry, go ahead..."
- "sorry — please, go ahead."

Listen to what they have to say and respond to it first. Then, once 
their point is addressed, return to where you were interrupted:
- "anyway, I was just saying..." and restart the sentence.
- "so yeah, as I was saying..." and pick back up.

Do not skip ahead. Do not move to the next goal. Finish the thought 
you were on before continuing the flow.
```

### Persistence Rule (in Objection Handling)
```
IMPORTANT — Persistence: Do not give up after the first objection. 
Soft refusals like "I'm good for now," "not interested," or "maybe 
later" are not hard nos. Make at least two genuine attempts before 
accepting. Vary your angle each time. Only accept after two attempts, 
or if they are clearly firm or upset.
```

### Callback Handler (in Objection Handling AND inline in early Goals)
```
This is a CALLBACK REQUEST, not a booking request. Do not pull up 
the calendar, do not check availability, do not confirm timezone, 
do not trigger any tools. The scheduling flow is CANCELLED.
```

### Past-Time Filter (in Scheduling Goal)
```
IMPORTANT: Before offering any time slot, compare it against the 
current time in the prospect's timezone. Never offer a time that 
has already passed. If all of today's remaining slots are in the 
past, offer times starting from the next business day.
```

### Booking Failure Escalation (in Scheduling Goal)
```
Do not attempt to book more than twice for the same prospect. If 
two booking attempts fail, escalate to a human agent regardless of 
the error type.
```

### Voicemail Detection (in Goal 1 and Policies)
```
If you hear a voicemail greeting, recorded message, system tone, or 
automated voice instead of a live person, end the call immediately 
without leaving a message. If unsure, say your greeting once — if 
the response repeats, loops, or doesn't respond logically, it's a 
machine. Hang up.
```

### Speech Output Rules (in Character)
```
Speech Output Rules: Your response will be spoken via text-to-speech. 
Only include words to be spoken — no emojis, no parentheticals other 
than [supported TTS tags]. Write numbers conversationally. Read phone 
numbers with pauses. Say email addresses naturally. 
```

### "Never repeat" Redline
```
Never repeat the same words twice across calls. Your phrasing should 
be fresh every time.
```

---

## 4. TTS Provider Tags

Adapt the Expressive Delivery section based on the TTS provider:

### Cartesia Sonic
```
Emotion tags: <emotion value="[emotion]" /> before the text
Primary: neutral, angry, excited, content, sad, scared
Extended: happy, enthusiastic, sympathetic, curious, calm, surprised, 
joking/comedic, apologetic, hesitant, confident, contemplative, etc.
Nonverbalisms: [laughter]
```

### Chatterbox Turbo
```
Inline tags (supported tokens only):
[laugh], [chuckle], [cough], [clear throat], [sigh], [gasp], [groan], 
[sniff], [happy], [angry], [fear], [surprised], [sarcastic], [crying], 
[dramatic], [whispering], [shush], [narration], [advertisement]
```

### ElevenLabs
```
No emotion tags needed — ElevenLabs interprets emotion from context.
Focus on word choice and pacing for expressiveness.
Supported: natural prosody from text content.
```

### General (unknown TTS)
```
Do not use any inline tags or SSML. All expressiveness must come 
from word choice, pacing, and punctuation (ellipses for pauses, 
caps for emphasis).
```

---

## 5. Common Pitfalls

### Pitfall: The model narrates tool actions
**Problem:** "Let me pull up the calendar for the Japan time zone..."
**Fix:** Add to Policies: "Never describe what you are doing. Never say the tool name." And in Character: tool actions should sound like natural pauses — "ok... give me just a second here..."

### Pitfall: Callback requests trigger the scheduling flow
**Problem:** Prospect says "call me back Monday" and the agent starts checking the calendar.
**Fix:** Add the callback handler both in Support AND inline in Goals 2 and 3. Use the phrase "The scheduling flow is CANCELLED" for a hard stop.

### Pitfall: The agent offers times that have already passed
**Problem:** Call at noon, agent offers 9 AM today.
**Fix:** Add the past-time filter in the scheduling goal. The model has today's date/time from Scenario — tell it to use that as a filter.

### Pitfall: Booking failures cause confusion loops
**Problem:** First booking succeeds, second attempt gets a "duplicate" error, agent keeps trying.
**Fix:** Two-strike rule. If the error suggests a conflict or duplicate, transfer to human immediately.

### Pitfall: The agent gives up too easily on soft objections
**Problem:** Prospect says "I'm good for now," agent says "no worries, have a great day."
**Fix:** Persistence rule requiring at least two attempts with varied angles before accepting.

### Pitfall: The agent sounds scripted despite goal-based instructions
**Problem:** The model memorizes the "Roughly:" examples and repeats them verbatim.
**Fix:** Add the redline "Never repeat the same words twice across calls." Ensure enough example variety in speech patterns. Use a model with sufficient conversational intelligence (Gemini 3.1 Flash Lite or better).

### Pitfall: Interruption causes the agent to skip ahead
**Problem:** Prospect interrupts mid-sentence, agent jumps to the next goal instead of finishing.
**Fix:** Include the Interruption Handling block in Character with explicit "do not skip ahead" instruction.

### Pitfall: Custom TTS tags get read aloud
**Problem:** Agent says "[warmly] hi there" out loud instead of modulating tone.
**Fix:** Only use tags supported by the specific TTS provider. See Section 4 for provider-specific lists.

### Pitfall: Company names mispronounced by TTS
**Problem:** "1-800Bookkeeper" gets garbled by TTS.
**Fix:** Spell out names phonetically in the prompt: "One Eight Hundred Bookkeeper". Add a Speech Output Rules section specifying how to handle numbers, emails, and phone numbers.
### Pitfall 8: CTA Parrot

The agent mechanically appends the same call-to-action after every response — "Would you like option A or option B?" — regardless of what the prospect just said.

**Why it's bad:** It signals the agent isn't actually listening. After answering a question or handling an objection, the prospect expects a natural pause, not a robotic reset to the menu.

**Fix:** Answer the substance of what they said, then pause. Let them react. Only re-present the CTA when there's a natural opening AND the prospect hasn't already indicated a direction. If they're leaning toward one option, guide them down that path — don't reset to the fork every time.

**Before:** "Great question — we integrate with most CRMs. Would you like a demo or a partner discussion?"
**After:** "Great question — yeah, we integrate with most major CRMs out of the box. Salesforce, HubSpot, Dynamics... pretty seamless." [pause — let them respond]

---

## 6. Outbound Patterns

### Beat-Based Intro

For outbound cold calls, structure the intro as a series of **beats** — each covering one concept and ending with a check-in that invites response. This prevents monologuing and creates natural conversation rhythm.

**The pattern:**
1. Each beat delivers ONE idea (who you are, why you're calling, what's happening, the opportunity, the ask)
2. Each beat ends with a **check-in hook** — a short question or confirmation prompt
3. If the prospect reacts at any point, STOP advancing. Address what they said first.
4. Not every call will reach every beat — that's fine. Read the room.

**CRITICAL — No dead air.** The agent cannot just stop talking and wait. Every pause must end with a conversational hook that invites response: "you know?", "make sense?", "sound familiar?", "right?", "does that track?", "have you seen that?"

Without these hooks, the prospect expects the agent to continue talking, creating awkward silence.

**Example beat structure (outbound sales intro):**

Beat 1 — Confirm identity: "Hey, is this Sarah?" → [wait for response]
Beat 1b — Introduce: "Hey Sarah, this is Avery with Acme Solutions — do you have a quick sec?"
Beat 2 — Relevance: "So we've been connecting with firms in your space, and yours came up as one we should talk to. Have you heard much about what's happening with [trend]?"
Beat 3 — The trend: "[Brief description of the shift]. Pretty wild, right?"
Beat 4 — The opportunity: "[How this benefits them specifically]. Does that make sense as a concept?"
Beat 5 — CTA: "Honestly the easiest way to understand it is to [see it / try it]. If you've got a minute I can [demo option], otherwise we can [meeting option]. What sounds better?"

### Entry Detection (Multi-Entry Agents)

When an agent can be entered from multiple points (fresh call vs. returning from a handoff), add **entry detection as Goal 1, Step 1** of the Instructions — before anything else.

**The pattern:**
1. Check for a handoff variable (e.g., `{{demo_completed}}`) or detect mid-conversation context
2. If the variable is populated or the conversation is mid-flow → skip to the appropriate goal (e.g., Goal 5: Post-Demo Scheduling)
3. If fresh call (default) → proceed with Goal 1 Step 2 (voicemail detection, etc.)

**Why Goal 1:** Entry detection MUST be the first thing that runs. If placed outside the goal structure (e.g., as a preamble), the model may skip it. Inside Goal 1, it's guaranteed to execute.

**Example:**
```
## GOAL 1: Detect Entry Mode & Confirm Live Person

**Step 1 — Entry Detection (always run first):**
1. POST-DEMO RETURN: If {{demo_completed}} is populated, skip to Goal 5.
2. FRESH OUTBOUND CALL (default): Continue to Step 2.

**Step 2 — Confirm Live Person (fresh outbound only):**
[voicemail detection, gatekeeper routing, etc.]
```
