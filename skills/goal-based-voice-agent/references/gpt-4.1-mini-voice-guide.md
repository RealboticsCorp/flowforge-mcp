# GPT-4.1 Mini — Voice Agent Prompting Guide

> **Source:** This guide distills OpenAI's official prompting guidance for voice agent use cases. For the canonical reference, see:
> - [GPT-4.1 Prompting Guide](https://cookbook.openai.com/examples/gpt4-1_prompting_guide) (OpenAI Cookbook)
> - [Introducing GPT-4.1 in the API](https://openai.com/index/gpt-4-1/) (announcement post)
> - [Prompt Migration Guide](https://cookbook.openai.com/examples/prompt_migration_guide) (OpenAI Cookbook) — useful when migrating prompts from earlier models to GPT-4.1
> - [OpenAI Prompt Engineering Guide](https://developers.openai.com/api/docs/guides/prompt-engineering) (general best practices)

## Table of Contents
1. Model Profile
2. Why 4.1 Mini for Voice Agents
3. The Core Principle: Literal Instruction Following
4. Prompt Architecture for Voice
5. Tool Calling Patterns
6. Common Failure Modes & Fixes
7. When to Use 4.1 Mini vs. Other Models

---

## 1. Model Profile

| Attribute | Value |
|---|---|
| Model | gpt-4.1-mini-2025-04-14 |
| Type | Non-reasoning (no thinking tokens) |
| Context window | 1,000,000 tokens |
| Max output | 32,768 tokens |
| Pricing | $0.40/M input, $1.60/M output, $0.10/M cached |
| TTFT (voice-realistic) | ~400–500ms (short prompts) |
| Output speed | ~71 TPS |
| IFEval | 84.1% |
| Tool selection quality | 0.79/1.0 (Galileo) |
| Best for | High-volume voice agents with single-tool-per-turn patterns, cost-sensitive deployments, agents where every decision path is known in advance |

---

## 2. Why 4.1 Mini for Voice Agents

GPT-4.1 Mini was explicitly optimized by OpenAI for three capabilities that voice agents demand: instruction following, tool calling, and low-latency streaming. It's the first "mini" model where those three things converge at production quality.

The tradeoff is clear: 4.1 Mini does exactly what you tell it. Nothing more, nothing less. For voice agents with well-defined flows and known edge cases, this is a strength — the agent behaves predictably across thousands of calls. For agents that need to reason through ambiguous situations or improvise qualification logic, the literalness becomes a constraint.

**Use 4.1 Mini when:**
- The call flow is well-defined with known branching paths
- Tool calls are simple (1 tool per turn, not chained)
- You can enumerate every edge case in the prompt
- Cost and volume matter (thousands of concurrent calls)
- You need battle-tested production reliability

**Don't use 4.1 Mini when:**
- The agent needs to reason through complex qualification logic
- Conversations are highly variable and can't be pre-scripted
- You need the agent to infer intent from ambiguous caller statements
- Multi-step tool orchestration is required in a single turn

---

## 3. The Core Principle: Literal Instruction Following

This is the single most important thing to understand about 4.1 Mini for voice. OpenAI's own prompting guide states it clearly: the model follows instructions "more closely and more literally" than its predecessors. Previous models would "liberally infer intent" — 4.1 Mini does not.

**What this means for voice prompts:**

If you don't say it, the agent won't do it. If you say it ambiguously, the agent will pick one interpretation and commit to it. If you say it once, the agent will follow it. If you say it in a way that conflicts with something else in the prompt, the agent will follow whichever instruction it encounters last or most prominently.

**Example — the verbosity problem:**

4.1 Mini tends toward verbose completions. For text applications this is fine. For voice, it's a dealbreaker — a 4-sentence response when the caller expects 1 sentence breaks conversational rhythm.

PROBLEM (implicit):
```
Keep responses conversational.
```

The model interprets "conversational" as "chatty" and produces 3-4 sentences per turn.

FIX (explicit):
```
Respond in 1-2 sentences maximum per turn. Never more than 
three sentences unless you are summarizing the full case. 
This is a phone call — short turns keep momentum.
```

One firm, explicit instruction fixes the behavior. This pattern repeats for every aspect of the voice agent's behavior.

---

## 4. Prompt Architecture for Voice

### System Prompt Structure

4.1 Mini responds best to a layered prompt with clear section boundaries. The SCRIPT framework maps directly to how the model processes instructions:

```
# S — SCENARIO   (processed first, sets context)
# C — CHARACTER   (defines communication style)
# R — ROLE        (defines accountability)
# I — INSTRUCTIONS (the call flow — this is the longest section)
# P — POLICIES    (hard constraints, checked throughout)
# T — TOOLS       (function definitions)
# (s) — SUPPORT   (reference material: objections, talking points)
```

**Key architectural rules for 4.1 Mini:**

1. **Put the most important instructions at the top and bottom of each section.** 4.1 Mini has strong attention across its full context window, but instructions at section boundaries get stronger adherence.

2. **Use explicit section headers.** The model uses headers as organizational anchors. Unlabeled instructions in the middle of a block are more likely to be deprioritized.

3. **Be exhaustive in Instructions.** Unlike reasoning models that can infer missing steps, 4.1 Mini needs every branching path spelled out. If the caller might say X, your prompt needs to handle X.

4. **Separate behavioral rules from hard constraints.** Behavioral guidance ("be empathetic") goes in Character. Hard stops ("never provide legal advice") go in Policies. Mixing them weakens both.

### The Enumeration Pattern

For 4.1 Mini, every decision the agent might face should be enumerated in the prompt. This is the opposite of goal-based prompting — it's rule-based prompting that produces predictable behavior.

```
### Section 2: Qualifying Questions

Ask these 4 questions in order:

1. Have you or someone you know been injured in an accident?
   - Yes or Maybe → continue to question 2
   - No → disqualified. Say: "I'm sorry, but based on your 
     answer it doesn't look like our firm would be the best 
     fit." End the call politely.

2. When did the accident occur?
   - If more than 2 years ago → note this as a potential 
     statute of limitations issue but continue qualifying
   - If they don't remember the exact date → ask for 
     approximate month and year

3. What type of accident was it?
   - Motor vehicle → continue
   - Premises liability → continue
   - Wrongful death → continue
   - Workers' compensation → disqualified. Say: "We 
     specialize in personal injury rather than workers' comp, 
     but I can refer you to a firm that handles those cases."
   - Medical malpractice → continue but note for attorney 
     review

4. Are you currently represented by an attorney?
   - No → continue
   - Yes → ask why they're considering a change, then continue
```

Every path is explicit. The model doesn't need to reason about what to do — it pattern-matches against the enumerated options. This produces extremely reliable behavior but requires the prompt author to anticipate every scenario.

### Transition Scripting

4.1 Mini doesn't generate natural transitions between topics on its own the way reasoning models do. You need to provide transition templates:

```
After completing Group 1 (Accident Info), transition:
Roughly: "Thanks for sharing all that. Now let's uhm talk 
about the vehicles involved."

After completing Group 2 (Vehicle Info), transition:
Roughly: "Got it. Next, let's go over the insurance details 
so we know what we're working with."
```

Without these, 4.1 Mini tends to jump abruptly: "Now I need to ask about insurance." The transition templates give it a natural bridge pattern to reference.

### Filler Words and Natural Speech

4.1 Mini follows filler word instructions reliably, but only if they're specific:

WEAK:
```
Use filler words to sound natural.
```

STRONG:
```
Include filler words such as "uhm", "uh", or "umm" in every 
response. Place them mid-sentence at natural pauses, never at 
the start or end. Aim for at least one every other sentence.

Examples:
- "Sure, I can definitely help with that. To get started uhm 
  can I have your full name please?"
- "And umm what type of accident was it?"
- "Was there anyone else in the uh in the car with you?"
```

The examples are critical. Without them, 4.1 Mini places fillers awkwardly or forgets them entirely. With 3-4 examples, it learns the placement pattern and generalizes well.

---

## 5. Tool Calling Patterns

### Use the API tools field

4.1 Mini has been specifically trained on the `tools` parameter in the OpenAI API. Do not inject tool descriptions manually into the system prompt — use the structured tools field. The model handles tool selection and parameter construction more reliably when tools are defined through the API.

### Keep tool sets small

Each additional tool definition increases the chance of incorrect selection. For voice agents, keep the active tool set to 3-5 tools maximum per agent. If you have more tools, use conditional loading — only include tools relevant to the current conversation state.

### Single-turn tool calls

4.1 Mini excels at single-tool-per-turn calls: "look up this account," "send this text," "transfer this call." This matches most voice agent patterns where each turn involves at most one action.

For multi-tool turns (e.g., "look up the account AND check availability"), 4.1 Mini supports parallel tool calls but accuracy drops. If your flow requires sequential tool chains, design the conversation so each tool call happens in a separate turn with user interaction in between.

### Structured outputs for reliability

Use `strict: true` in structured output mode for guaranteed schema-valid JSON. This is 4.1 Mini's strongest tool-calling feature — constrained decoding means zero malformed function calls reaching your backend.

```json
{
  "tools": [{
    "type": "function",
    "function": {
      "name": "send_agreement",
      "strict": true,
      "parameters": {
        "type": "object",
        "properties": {
          "phone_number": {"type": "string"},
          "caller_name": {"type": "string"}
        },
        "required": ["phone_number", "caller_name"],
        "additionalProperties": false
      }
    }
  }]
}
```

### Silent tool execution

Voice agents should never narrate tool actions. Add this to Policies:

```
Tool calls are silent. Never describe what you are doing. 
Never say the tool name. While waiting for a tool response, 
use natural pauses: "ok... give me just a second here..." 
or "one moment please..."
```

---

## 6. Common Failure Modes & Fixes

### Failure: Agent is too verbose for voice
**Symptom:** 4-5 sentence responses that feel like monologues.
**Fix:** Add explicit length constraints: "Respond in 1-2 sentences per turn. Maximum 3 sentences for case summaries only." Also: "This is a phone call. Keep the back-and-forth going. Always end with a question."

### Failure: Agent repeats the caller's answers back
**Symptom:** Caller says "I was in a car accident." Agent says "I'm sorry to hear you were in a car accident. Can you tell me more about the car accident?"
**Fix:** "Never repeat the caller's answers back to them. Use a short affirmation — 'Got it,' 'Okay,' 'Understood' — then ask the next question. Repetition breaks call flow."

### Failure: Agent asks multiple questions at once
**Symptom:** "Can you tell me your name, phone number, and email?"
**Fix:** "Ask one question at a time. Wait for a full response before asking the next question. Never combine questions."

### Failure: Agent uses the caller's name too often
**Symptom:** "Thank you, John. So John, can you tell me... That's helpful, John."
**Fix:** Specify exact usage: "Use the caller's first name exactly twice: once in the greeting, once when ending the call. Never in between."

### Failure: Agent skips steps when caller volunteers info
**Symptom:** Caller mentions their email during the greeting, agent skips the email collection step and later can't recall it.
**Fix:** 4.1 Mini doesn't handle out-of-order information well. Two options: (a) add explicit instructions for early volunteering ("If the caller provides information before you ask, note it and skip that question when you reach it"), or (b) design the flow so all questions are asked regardless ("Confirm their email even if they mentioned it earlier").

### Failure: Agent breaks character after correction
**Symptom:** Caller corrects the agent's pronunciation, agent becomes overly apologetic and formal.
**Fix:** Script the correction response: "If the caller corrects you on anything, respond casually: 'Sorry about that — my phone's been acting weird today.' Don't make it a big deal. Move on."

### Failure: Agent generates text formatting in speech
**Symptom:** Agent says "Here are three things: 1) first thing, 2) second thing..."
**Fix:** "Never use lists, bullets, numbered sequences, or any text-based formatting. Everything you say will be spoken aloud via TTS. Write as spoken language only."

---

## 7. When to Use 4.1 Mini vs. Other Models

### 4.1 Mini vs. 4.1 Nano ($0.10/$0.40)
Nano is 75% cheaper but drops quality on complex system prompts. Use Nano for simple routing agents (detect intent, transfer call). Use Mini for anything with qualification logic, objection handling, or data capture.

### 4.1 Mini vs. Gemini 2.5 Flash ($0.30/$2.50)
Flash has better instruction following (IFBench 44% vs 38%) and faster TTFT (0.37s vs 0.42s), but weaker multi-step task completion (38% vs 56% on Galileo) and documented bugs in Native Audio function calling. For single-LLM agents with simple tool patterns, they're comparable. For tool-heavy agents, 4.1 Mini is safer.

### 4.1 Mini vs. GPT-5.4 Mini ($0.75/$4.50)
5.4 Mini is a reasoning model with dramatically better IFBench (73% vs 38%), native verbosity control, and better tool-calling discipline. But it costs ~2.5x more on output tokens. Use 5.4 Mini for high-value intake calls where conversion quality justifies the cost. Use 4.1 Mini for high-volume routing where cost-per-call matters.

### 4.1 Mini vs. Llama 4 Scout on Groq ($0.11/$0.34)
Groq delivers sub-200ms TTFT — fastest available. But Scout has weaker instruction following and no structured output guarantees. Use Groq for simple outbound campaigns where speed and cost dominate. Use 4.1 Mini when reliability on complex prompts matters.

### Decision Framework

```
Is the call flow well-defined with <10 branching paths?
├── Yes → Is cost the primary constraint?
│   ├── Yes → 4.1 Mini (or Nano for very simple routing)
│   └── No → 4.1 Mini
└── No → Does the agent need to reason through ambiguous 
         qualification logic?
    ├── Yes → GPT-5.4 Mini with reasoning_effort: low
    └── No → 4.1 Mini with more exhaustive enumeration
```
