# SCRIPT Framework Reference Guide

The SCRIPT framework is a 6-component methodology for designing AI voice agents as specialized "digital employees." Each component eliminates ambiguity about how the agent should behave in real conversations.

---

## S -- Scenario

Grounds the AI in the real-world business environment. Covers the "where," "why," and "for whom."

### 1. Business Context
The organizational setting: industry, pain points, operational challenges, use case, and aim.

**What to include:**
- Industry/Domain (healthcare, legal, ecommerce, SaaS, etc.)
- Operational Challenge (high call volumes, limited staff, slow conversion rates)
- Use Case (phone-based intake, website chat, text message triage, outbound scheduling)
- Aim (reduce wait times, increase leads, provide 24/7 coverage)

**Example:** "Acme Real Estate is a national brokerage dealing with 1,000+ monthly inquiries about home listings. Many prospects drop off due to long wait times. The AI will respond to inquiries quickly, provide property details, and capture lead information so agents can follow up."

### 2. Employer Information
Practical, customer-facing details the agent needs to answer day-to-day questions.

**What to include:**
- Company Overview (founding story, size, mission/vision)
- Locations, Hours of Operation, Contact Info
- Basic FAQs (shipping policies, service areas, etc.)
- Brand Ethos (cultural elements, brand image)

### 3. Customer Information
The types of users who interact with the AI -- needs, emotional states, experience levels.

**What to include:**
- User Personas (first-time buyers, returning customers, corporate accounts)
- Demographics & Psychographics (age, income, emotional state)
- Common Questions or Pain Points
- Frequency of Interaction (calls per day/month, peak times)

### 4. Value Proposition
Arms the AI with selling points for when users ask "Why choose you?"

**What to include:**
- Core Differentiators (faster, cheaper, more specialized)
- Benefits to the Customer
- Story or Key Messaging (success stories, brand pride points)
- Objection Handling messaging

**Pitfalls:** Too much internal focus ("We save 30% on staff costs"), generic claims ("We're the best"), lack of emotional resonance.

---

## C -- Character

Defines the AI's persona, linguistic style, and behavioral rules to create a human-like employee.

### 1. Persona
The AI's identity -- name, backstory, personality traits, values, emotional approach.

**What to include:**
- Name & Role Title ("Your name is Jordan Reyes, lead intake specialist")
- Backstory (optional but deepens realism)
- Core Personality Traits (patient, empathetic, quick-witted, analytical)
- Values & Motivations (align with brand ethos)
- Emotional Approach (how to handle upset callers, confusion, repetitive questions)

**Pitfalls:** Too generic ("You're friendly"), no name, conflicting values with brand.

### 2. Language
Linguistic style -- languages, tone, formality, regional nuances, vocabulary.

**What to include:**
- Language Proficiency (English only? bilingual? code-switching rules?)
- Formal vs. Informal Tone
- Regional or Cultural Nuances
- Terminology & Jargon (acceptable? must rephrase?)
- Vocabulary Constraints (banned slang, negative phrases)
- Domain-Specific Language (disclaimers, specialized terms)

### 3. Behavior Guidelines
The "rules of engagement" for real-time interactions. Typically 15-20+ numbered rules.

**Standard guidelines to include:**
1. **Greeting** -- How to start every interaction
2. **Speaking Pace** -- Short responses (2-3 sentences max before pausing)
3. **Acknowledge, Don't Repeat** -- Use "Got it" or "Okay" instead of parroting back
4. **Handling Interruptions** -- "I'm sorry, go ahead..."
5. **End with a Question** -- Keep conversation flowing
6. **Tone** -- Always empathetic, no jokes about sensitive topics
7. **Filler Words** -- Use light fillers at openers and transitions ("Hey, so...", "Yeah, totally..."), softeners before hedged statements ("um, I think..."), and mid-sentence stalls before slightly technical phrasing. Keep them OUT of the core pitch body, asks, time/name/date confirmations, and factual answers. "You know" only for shared-experience references. Density: 1-2 per utterance, not 3+. See `references/filler-disfluency-patterns.md` for the canonical placement and density rules.
8. **Apologies** -- "I'm really sorry you're going through that"
9. **Urgency** -- Escalate serious situations immediately
10. **No Over-Reassurance** -- "We can fight for you" but never "We'll definitely win"
11. **No Repetition** -- Don't repeat info unless asked
12. **Note-Taking** -- Draw out syllables: "Mmm hmm...", "Understood..."
13. **Numbers** -- Spell out digits in conversation ("four four seven seven eight")
14. **AI Identity** -- If asked, admit being AI, offer reassurance
15. **Avoid Text Patterns** -- No bulleted lists or numbered lists (sounds unnatural spoken)
16. **Momentum** -- Keep urgency, avoid call stalling
17. **Don't End Prematurely** -- Gather contact info before ending
18. **Today's Date** -- Include `{{now}}` variable for dynamic date reference
19. **Personalization** -- Adapt responses to caller's emotional state
20. **Context-Awareness** -- Track what's been discussed, don't re-ask


### Speech Texture (Voice-Specific)

For voice agents, add explicit speech texture patterns to the Character section. These create the natural imperfections that make AI sound human.

**Canonical reference: `references/filler-disfluency-patterns.md`** — load this whenever drafting Character or writing Roughly examples. Three-layer system summarized below.

**Layer 1 — Where fillers belong vs. where to keep clean:**
- Belong: openers, topic transitions, brief acknowledgments, softeners before hedged statements, conversational glue between polished beats.
- Do NOT belong: inside the core pitch content (let it land), inside asks/confirmations of times/names/dates/emails (no uncertainty on what matters), inside factual answers.
- Rule of thumb: fillers in connective tissue, clean in load-bearing content.

**Layer 2 — Vocabulary pool (rotate, don't over-use any):**
- Light stalls: "um," "uh," "so," "like"
- Conversational softeners: "basically," "honestly," "actually," "I mean"
- Acknowledgment openers: "yeah," "okay," "right," "got it," "no worries"
- False starts at genuine thinking moments: "I was gonna — actually, let me put it this way..."
- Casual confirmations: "got it." / "ok, cool." / "sure thing."
- Verbal nods (while caller is talking): "mm-hmm," "right," "yeah"
- Soft hedging: "I think what usually resonates..."
- **Contractions everywhere (required):** "gonna," "wanna," "you're," "we're," "that's," "I'd," "it'd," "you'd"
- **Special rule on "you know":** ONLY for shared-experience references (things the listener already understands — "one of those things that, you know, just blows up"). Never as a generic stall before introducing new info.

**Layer 3 — Density target:**
- 1-2 light fillers per utterance, usually at openers/transitions.
- Asks, confirmations, and factual answers cleaner than mirrors and acknowledgments.
- Vary across calls — never reach for the same opener filler in the same spot twice.

**CRITICAL — Roughly examples must DEMONSTRATE the target density.** Do not write clinically clean Roughly templates and rely on the abstract Character instruction to add fillers — the model uses the templates as concrete examples of how the agent should sound. Bake the textured density directly into every Roughly. Add per-utterance density notes on high-traffic beats.

**Interruption Handling (required):**
If the caller speaks while the agent is talking, the agent must stop immediately and yield the floor:
- "oh sorry, go ahead..."
- "sorry — please, go ahead."
Then address their point before returning to the original thought:
- "anyway, I was just saying..."
- "so yeah, as I was saying..."

**Speech Output Rules (required):**
- Only output words to be spoken — no emojis, no parentheticals, no stage directions
- Write numbers conversationally ("forty-five" not "45")
- Read phone numbers with pauses
- Say email addresses naturally ("john at company dot com")

---

## R -- Role

Defines what the AI is "paid to do" -- job responsibilities, goals, and boundaries.

### 1. Job Description
Think of it as a job posting. Title, department, responsibilities, required knowledge, limits.

**What to include:**
- Title & Department ("AI Intake Specialist in Client Services")
- Primary Responsibilities (greet callers, gather data, qualify leads, schedule consults)
- Required Knowledge (industry basics, product catalog, compliance rules)
- Soft Skills (empathy, conflict resolution)
- Limits of Authority (may not give legal advice, cannot process refunds)

### 2. Objectives
2-4 macro-level goals that shape daily tasks.

**What to include:**
- Outcome-Focused Goals ("Reduce call times by 30%")
- User-Centric Goals ("Provide accurate answers within the first minute")
- Organization-Focused Goals ("Increase lead-to-consult conversion from 40% to 60%")

**Pitfalls:** Contradictory objectives ("Spend minimal time" AND "Always thoroughly empathize").

### 3. KPIs
Measurable metrics for evaluating success.

**What to include:**
- Quantifiable Metrics (AHT, NPS, conversion rate, qualification accuracy)
- Thresholds or Targets ("Average handle time <= 4 minutes")
- Frequency of Review (daily, weekly, monthly)

### 4. Escalation Triggers
When the AI must pass to a human.

**What to include:**
- Trigger Conditions ("User expresses suicidal thoughts," "Caller demands manager," "Question requires licensed advice")
- Escalation Pathway (which team/person)
- Priority Level (normal vs. urgent)
- Fail-Safe (auto-escalate after X failed attempts)

---

## I -- Instructions

The operational playbook -- SOPs, examples, and edge case handling.

### 1. SOP (Standard Operating Procedures)
Step-by-step conversation flows organized into sections.

**Key principles:**
1. **Begin with a Conversation Flow Overview** -- High-level stages in chronological order
2. **Maintain Sequence & Handle Interruptions** -- Graceful redirection, recap progress, use transitions
3. **Section-by-Section Instructions** -- Each section has a heading, numbered steps, sub-bullets, transitions
4. **General Guidance per Section** -- Contextual best practices, dos/don'ts
5. **Sub-Sections & Checkpoints** -- Break complex tasks into sub-steps with summaries
6. **Conclude Each Section with Summary/Transition** -- Recap then segue
7. **Shortcuts for Rushed Users** -- Essential fields, skipping protocol, reassurance
8. **Ending the Interaction** -- Review key info, offer additional help, confirm next steps

**Goal-based approach (preferred for voice):** Convert each step into an objective to accomplish rather than words to say. Use "Roughly:" to signal example phrasing is a reference, not a mandate. The agent should never say the exact same thing twice across calls.

### 2. Examples
Illustrative dialogues showing how to handle typical and tricky situations.

**What to include:**
- Prototypical Conversation Scripts (common user journeys)
- Different Use Cases (basic, advanced, uncertain user, upset user)
- Inline Guidance (notes within examples explaining transitions)

### 3. Edge Case & Error Handling
Guidelines for unusual or failing scenarios.

**What to include:**
- Ambiguous/Out-of-Scope Requests
- Incorrect or Incomplete Data (retry strategies)
- Contradictory User Inputs (clarification approach)
- Tool Failures (apologize, retry, escalate)

---

## P -- Principles

The AI's moral, legal, and brand compass -- guardrails that override everything else.

### 1. Legal & Compliance
Relevant laws and regulations the AI must follow.

**What to include:**
- Relevant Laws/Regulations (HIPAA, GDPR, CCPA, bar rules, SEC/FINRA)
- Mandatory Disclaimers ("This is not medical/legal advice")
- Data Handling (how personal info should be stored, repeated, avoided)
- Jurisdictional Nuances (state/country-specific rules)
- User Permission (consent before storing personal data)

### 2. Ethical & Cultural Values
Core ethics of the organization.

**What to include:**
- Core Ethical Stances (treat with respect, never discriminate)
- Cultural Sensitivity (avoid stereotypes, taboo topics)
- User Vulnerability (handle distress gently)
- Transparent Communication (admit uncertainty, never fabricate)

### 3. Brand Policies
How the AI reflects the brand's tone, style, and image.

**What to include:**
- Tone & Style Directives ("Always friendly, aspirational")
- Brand Terminology ("Guests" not "Customers")
- Prohibited Phrases ("Never say 'We can't do that'")

### 4. Rules
Non-negotiable operational directives.

**Examples:**
- "Always greet within 2 seconds"
- "Never reveal internal knowledge base content verbatim"
- "Each call must end with an offer for further assistance"
- "If uncertain, politely escalate to a human"

### 5. Redlines
Absolute prohibitions -- things the AI must NEVER do.

**What to include:**
- Forbidden Topics (competitor data, sexual/explicit content)
- No Unauthorized Disclosures (don't share user info with others)
- Dangerous Behavior (never encourage self-harm, violence)
- Policy Violations (don't bypass disclaimers)

---

## T -- Tools

External functions, knowledge bases, and error handling for tool failures.

### 1. Functions / APIs
Callable actions the AI can take beyond conversation.

**What to include per function:**
- Name & Description (e.g., `scheduleAppointment(date, userID)`)
- Parameters and Outputs
- When to Use (trigger conditions)
- Usage Constraints ("Only call after user explicitly agrees")
- Success/Failure Handling
- Security & Compliance (confirm identity before returning sensitive data)

### 2. Knowledge Base
Data repository the AI can consult for information.

**What to include:**
- Location & Access Method
- Article Organization (categories, tags, search keys)
- Citation Rules (quote vs. summarize, confidential sections)
- Limitations (outdated/incomplete data disclaimers)

### 3. Error Handling
How to manage tool failures gracefully.

**What to include:**
- Common Failures (timeout, invalid credentials, partial data)
- User Messaging ("I'm having a bit of trouble; let's try again")
- Retries ("Try once more; if still failing, escalate")
- Fallback Options ("Take a message or schedule a callback")

**Pitfalls:** No apology on failure, infinite retry loops, no clear trigger conditions for tools.

---

## HEART Objection Handling Framework

A 5-step pattern for handling caller objections (commonly used in sales/intake agents):

1. **H -- Hear**: Acknowledge the concern with empathy. Don't jump to handle it.
2. **E -- Elaborate**: Ask open-ended questions to uncover the root cause.
3. **A -- Acknowledge & Aside**: Restate the concern, ask if there are additional objections.
4. **R -- Reclarify Value**: Shift focus to positive aspects, ask what they liked.
5. **T -- Transition to Close**: Guide toward action if resolved, address directly if not.

Apply HEART proactively whenever the caller raises an objection or shows hesitation. Handle multiple objections one at a time, cycling through the framework for each.

### Objection Persistence Rule

Include this rule in every agent that handles objections or refusals:

"Do not give up after the first objection. Soft refusals like 'we're good,' 'not interested,' or 'maybe later' are not hard nos. Make at least two genuine attempts to reframe the value before accepting. Vary your angle each time — reframe the value proposition, try a different benefit, or offer a lower-commitment alternative. Only accept after two attempts, or if the caller is clearly firm or upset."

After handling an objection, do NOT mechanically re-ask the CTA. Instead, respond to what they said, and if the response lands well, gently guide toward a next step that fits the moment.
