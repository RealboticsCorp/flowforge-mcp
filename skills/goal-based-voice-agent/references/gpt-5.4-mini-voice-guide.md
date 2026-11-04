# GPT-5.4 Mini — Voice Agent Prompting Guide

> **Source:** This guide distills OpenAI's official prompting guidance for voice agent use cases. For the canonical reference, see:
> - [Prompt Guidance for GPT-5.4](https://developers.openai.com/api/docs/guides/prompt-guidance) (OpenAI API docs — primary reference)
> - [Introducing GPT-5.4](https://openai.com/index/introducing-gpt-5-4/) (announcement post with benchmarks)
> - [GPT-5 Prompting Guide](https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide) (foundational concepts: reasoning_effort, verbosity)
> - [GPT-5.1 Prompting Guide](https://cookbook.openai.com/examples/gpt-5/gpt-5-1_prompting_guide) (introduced `reasoning: none` for 4.1 migration)
> - [GPT-5.2 Prompting Guide](https://cookbook.openai.com/examples/gpt-5/gpt-5-2_prompting_guide) (output contracts, migration patterns)
> - [GPT-5 New Params and Tools](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5_new_params_and_tools) (verbosity, custom tools, CFG)
> - [GPT-5 Troubleshooting Guide](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5_troubleshooting_guide) (common failure modes)

## Table of Contents
1. Model Profile
2. Why 5.4 Mini for Voice Agents
3. The Core Shift: Reasoning Changes Everything
4. The Two Controls That Matter Most
5. Prompt Architecture for Voice
6. Tool Calling Patterns
7. Converting 4.1 Mini Prompts to 5.4 Mini
8. Common Failure Modes & Fixes
9. When to Use 5.4 Mini vs. Other Models

---

## 1. Model Profile

| Attribute | Value |
|---|---|
| Model | gpt-5.4-mini |
| Type | Reasoning model (adjustable reasoning_effort) |
| Pricing | $0.75/M input, $4.50/M output |
| TTFT | ~180-190ms (sub-200ms reported) |
| Output speed | ~180-190 TPS |
| IFBench | 73.3% |
| τ²-Bench | 83.3% |
| Toolathlon | 42.9% (up from 26.9% on GPT-5 Mini) |
| GPQA Diamond | 87.5% |
| Best for | High-value intake calls, complex qualification logic, branching conversations, agents that need emotional intelligence and genuine conversational presence |

---

## 2. Why 5.4 Mini for Voice Agents

GPT-5.4 Mini is a reasoning model that can think before it speaks. For voice agents, this means the model can reason through ambiguous caller statements, navigate complex decision trees without explicit enumeration, and maintain conversational coherence across long, emotionally charged calls.

The practical impact: you write shorter prompts that produce smarter behavior. Instead of scripting every possible branching path, you define the goal and let the model reason about how to get there. This is especially powerful for intake calls where callers are emotional, information comes in unpredictable order, and the agent needs to exercise judgment.

The tradeoff is cost. At $0.75/$4.50, it's roughly 2.5x more expensive per token than GPT-4.1 Mini. This is only justified when the value per call is high enough — legal intake, enterprise sales, medical triage — where a 10% improvement in conversion quality pays for the model difference many times over.

**Use 5.4 Mini when:**
- Lead values are high enough to absorb the cost premium ($100+ per qualified lead)
- The agent needs to reason through complex qualification criteria
- Conversations are emotionally complex and require adaptive tone
- The call flow has many possible paths that can't all be enumerated
- You want shorter prompts that are easier to maintain
- Conversational presence and emotional intelligence matter for conversion

**Don't use 5.4 Mini when:**
- You're running thousands of concurrent calls at razor-thin margins
- The call flow is simple and well-defined (routing, appointment setting)
- Every decision path is known in advance and can be scripted
- Cost-per-call is your primary optimization target

---

## 3. The Core Shift: Reasoning Changes Everything

The fundamental difference between 4.1 Mini and 5.4 Mini for voice prompts is this: **4.1 Mini follows instructions literally. 5.4 Mini reasons about intent.**

This changes how you write every section of the prompt.

### Instructions become outcomes, not procedures

WITH 4.1 MINI (procedural):
```
Ask these 4 qualifying questions in order:
1. Have you been injured in an accident?
   - Yes/Maybe → continue to question 2
   - No → disqualified. Say: "I'm sorry, but based on your 
     answer it doesn't look like our firm would be the best 
     fit." End the call politely.
2. When did the accident occur?
   - If more than 2 years ago → note statute of limitations
   - If they don't remember → ask for approximate month/year
3. What type of accident?
   - Motor vehicle → continue
   - Premises liability → continue  
   - Workers' comp → disqualified, refer out
   [... 15 more lines of branching ...]
```

WITH 5.4 MINI (outcome-based):
```
Determine whether this is a personal injury case the firm 
can represent. You need to establish: whether someone was 
injured, when it happened, what kind of accident it was, and 
whether they already have representation.

If they clearly don't have a PI case (no injury, workers' 
comp, already represented and satisfied), let them know 
compassionately that the firm isn't the right fit.

If they qualify, let them know it sounds like the firm can 
help and ask to continue gathering details.
```

The 5.4 version is 60% shorter but produces equivalent or better behavior because the model reasons about edge cases (e.g., "what if they're not sure if they were injured?") instead of needing them enumerated.

### Edge cases become principles, not scripts

WITH 4.1 MINI (scripted edge cases):
```
Edge Case #4: Poor clarity or incoherent speech
If you're having trouble understanding the caller, say:
"I'm so sorry, I can barely hear you. It might be the 
reception on your end. You're cutting in and out, so could 
you please repeat that for me again?"

If you've already asked once and still can't hear them:
"I'm really sorry, but I'm still having trouble hearing 
you clearly. Would you mind repeating that one more time?"
```

WITH 5.4 MINI (principle-based):
```
If you can't hear or understand the caller, blame the 
connection, not them. Ask them to repeat or speak up. 
Be patient — never guess at what they said.
```

The model reasons about the appropriate response based on context. First occurrence gets a lighter touch; repeated issues get escalated naturally. The principle is enough.

### Character descriptions replace behavioral rules

WITH 4.1 MINI (rule list):
```
1. Maintain a professional and engaging yet highly empathetic 
   and personable tone
2. Detect the caller's emotions and adjust
3. Speak slowly and keep explanations clear
4. Ensure responses are personalized and context-aware
5. Prioritize the caller's comfort
6. Address objections thoughtfully
7. Keep responses to 2-3 sentences
[... 15 more rules ...]
```

WITH 5.4 MINI (character description):
```
You treat every caller like family. You're warm, empathetic, 
and genuinely motivated to help people through difficult 
situations. Your constant smile and positive energy come 
through in every word. You speak casually — no corporate 
stiffness, no legal jargon unless you explain it.
```

The reasoning model inhabits the character description and generates behavior that follows from it. The rule list tells a non-reasoning model what to do step by step. Both produce similar output, but the character description is more maintainable and produces more varied, natural phrasing across calls.

---

## 4. The Two Controls That Matter Most

GPT-5.4 Mini has two API-level parameters that replace large chunks of what used to live in the prompt: `reasoning_effort` and `verbosity`.

### reasoning_effort

This controls how much the model thinks before responding. For voice agents, this is the single most important parameter to get right.

| Level | Use for voice when... | Latency impact |
|---|---|---|
| `none` | Simple routing, FAQ, transfers. No reasoning needed. Behaves like 4.1 Mini. | Minimal — fastest |
| `low` | Standard intake, qualification, objection handling. The model reasons about caller intent and next steps but doesn't over-think. | Small — good for voice |
| `medium` | Complex qualification with ambiguous criteria, multi-path decision trees, emotionally nuanced conversations. | Moderate — still viable for voice |
| `high` | Not recommended for real-time voice. Use for async tasks like post-call analysis, compliance review, or case summarization. | Significant — too slow |
| `xhigh` | Never for voice. Background processing only. | Very high |

**For legal intake, start with `low`.** This gives the model enough reasoning to navigate qualification logic, handle objections intelligently, and adapt its emotional tone — without adding perceptible latency. Move to `medium` only if you observe the agent making poor judgment calls on complex branching.

OpenAI's guidance: "For GPT-5.4 workloads, `none` can already perform well on action-selection and tool-discipline tasks. If your workload depends on nuanced interpretation, such as implicit requirements, ambiguity, or cancelled-tool-call recovery, start with `low` or `medium` instead."

Legal intake is exactly the "nuanced interpretation" and "implicit requirements" case.

### verbosity

This controls the length and density of the model's final response — separate from how much it thinks.

| Level | Voice usage |
|---|---|
| `low` | **Default for voice.** Concise, phone-natural responses. 1-2 sentences per turn. |
| `medium` | Case summaries, explaining next steps. Use for specific contexts only. |
| `high` | Never for voice conversation. May be useful for post-call notes. |

Set `verbosity: low` at the API level. This replaces prompt-level instructions like "keep responses to 2-3 sentences" and "don't ramble." The model produces concise spoken responses while its internal reasoning can be as thorough as needed.

You can override verbosity in the prompt for specific contexts:

```
When summarizing the full case back to the caller, use more 
detail than your usual responses. Walk through the key 
points so they can confirm everything is accurate.
```

This tells the model to expand for summaries while keeping everything else tight.

---

## 5. Prompt Architecture for Voice

### System Prompt Structure

The SCRIPT framework works with 5.4 Mini, but sections can be significantly shorter:

```
# S — SCENARIO    (2-3 sentences of context)
# C — CHARACTER   (persona description + speech patterns)
# R — ROLE        (job description with accountability metrics)
# I — INSTRUCTIONS (goal-based checklist — the core section)
# P — POLICIES    (hard constraints only — cut ~50% from 4.1 version)
# T — TOOLS       (function definitions)
# (s) — SUPPORT   (objection substance + caller data)
```

### The Goal-Based Checklist

This is the defining pattern for 5.4 Mini voice agents. Instead of enumerated steps, the agent tracks a mental checklist of outcomes to achieve:

```
Your call has 4 goals. Complete them in order, but use your 
own words every time. The example phrasing shows roughly how 
it should sound — never repeat it verbatim. Adapt your 
language to what just happened in the conversation. If a goal 
gets accomplished naturally during another step, check it off 
and move on.

Maintain a mental checklist:
☐ Warm transfer received, caller greeted
☐ Contact info captured (full name, phone, email)
☐ Qualification complete
☐ Case interview complete
☐ Agreement sent via text
```

Each goal then describes the **outcome** to achieve, not the **procedure** to follow:

```
### Goal 2: Qualify the Lead

Determine whether this is a personal injury case the firm 
can represent. You need to establish four things: whether 
someone was injured, when it happened, what kind of accident, 
and whether they already have representation.

[... outcome criteria, not step-by-step script ...]
```

### Speech Patterns Still Need Examples

Even though 5.4 Mini is a reasoning model, TTS-specific patterns (filler words, verbal nods, thinking-aloud phrases) still benefit from explicit examples. The model can reason about *what* to say but benefits from examples of *how* it should sound:

```
Conversational Speech Patterns:

- Filler words: "uhm," "uh," "umm" — mid-sentence at natural 
  pauses, never at start or end
- Thinking out loud: "Alright…" "Mmm hmm…" "Oh-kaaay, got it…"
- Casual confirmations: "Got it." "Okay." "Sure thing."

Examples:
- "Sure, I can definitely help with that. To get started uhm 
  can I have your full name please?"
- "And umm what type of accident was it?"
```

Without these examples, even reasoning models tend to produce "clean" speech that sounds robotic via TTS.

### Objection Handling: Substance Over Scripts

With 4.1 Mini, objection handling requires scripted responses for each objection. With 5.4 Mini, you provide the *substance* of the rebuttal and trust the model to phrase it naturally:

4.1 MINI (scripted response):
```
"I need to think about it"
Response: "I completely understand. This is a big decision. 
But let me explain why moving forward now can actually help 
you. Every day we wait, there's a chance that crucial 
evidence could be lost..."
```

5.4 MINI (substance only):
```
"I need to think about it" — Every day of delay risks losing 
evidence (footage, reports, witnesses). Signing doesn't lock 
them in, it protects their position. They can keep thinking 
while the firm starts working.
```

The reasoning model takes the substance — evidence loss, no lock-in, parallel protection — and constructs a natural response that fits the emotional context of the specific call. Different callers get different phrasing, all hitting the same key points.

### Output Contract Pattern

5.4 Mini responds especially well to explicit definitions of what "done" looks like. OpenAI calls this the "output contract" — a clear specification of the expected outcome:

```
<output_contract>
- Respond in 1-2 sentences per turn unless summarizing
- Always end your turn with a question
- Ask one question at a time
- Never use lists, bullets, or formatted text
- All responses will be spoken via TTS — write as speech
</output_contract>
```

This replaces scattered formatting rules throughout the prompt with a single, referenced contract.

---

## 6. Tool Calling Patterns

### Improved tool discipline

GPT-5.4 Mini reasons about *whether* to call a tool before calling it. This is a meaningful improvement over 4.1 Mini, which tends to call tools eagerly whenever they're available.

For voice agents, this means:
- The agent won't prematurely trigger a CRM write before finishing qualification
- The agent won't attempt a transfer before addressing the caller's concern
- The agent reasons about readiness ("do I have all the required parameters?") before making the call

You can reinforce this with a lightweight prompt:

```
Before calling any tool, verify you have all required 
information. If you're missing a parameter, ask the caller 
for it first. Never call a tool with placeholder or 
assumed values.
```

With 4.1 Mini, you'd need to spell out every scenario where a tool should NOT be called. With 5.4 Mini, the principle is sufficient.

### Reasoning effort and tool calling

At `reasoning_effort: none`, 5.4 Mini handles tool calling similarly to 4.1 Mini — fast, literal, reliable for simple actions. OpenAI's guidance: custom function-calling performance is "substantially improved" at `none` compared to earlier models.

At `reasoning_effort: low`, the model adds a reasoning step before tool calls — checking whether the call is appropriate, whether parameters are complete, whether the timing is right. This small overhead produces noticeably more disciplined tool usage with minimal latency impact.

At `reasoning_effort: medium+`, the model may over-deliberate on tool calls, adding latency without proportional benefit for simple voice agent actions. Reserve medium for complex multi-tool orchestration tasks, not standard intake flows.

### Parallel tool calls

5.4 Mini handles parallel tool calls better than 4.1 Mini, but for voice agents this rarely matters — most voice turns involve at most one action. The improvement matters more for async post-call processing (e.g., simultaneously updating CRM, sending a summary email, and creating a task).

### Structured outputs

5.4 Mini supports `strict: true` structured outputs with the same guaranteed schema validation as 4.1 Mini. Use it for all tool call parameters.

---

## 7. Converting 4.1 Mini Prompts to 5.4 Mini

### Step-by-step migration

1. **Switch models first, don't change the prompt.** Run your existing 4.1 prompt on 5.4 Mini with `reasoning_effort: none` to establish a baseline. The prompt will work — it's just not optimized.

2. **Set reasoning_effort to `low`.** Run evals. You should see improved handling of edge cases and more natural conversation flow immediately.

3. **Set verbosity to `low`.** Remove any prompt-level length constraints that are now handled by the API parameter.

4. **Convert Instructions from steps to goals.** This is the biggest change. For each scripted step, extract the objective, remove the exact wording, and trust the model to achieve the outcome.

5. **Collapse behavioral rules into Character.** Move empathy directives, tone instructions, and communication style rules from Policies into the Character description.

6. **Replace scripted edge cases with principles.** Keep 3-4 guiding principles instead of 15 scripted responses.

7. **Convert scripted objection responses to substance.** Keep the key arguments for each objection but remove the exact wording.

8. **Cut Policies by 50%.** Remove any rule that's now implicit in the Character description or handled by the model's reasoning. Keep only hard constraints.

9. **Run evals again.** Compare conversion rates, call quality, and caller satisfaction against the 4.1 baseline.

### What to expect

| Metric | 4.1 Mini → 5.4 Mini |
|---|---|
| Prompt length | ~50% reduction |
| Edge case handling | Significantly better (reasons through novel situations) |
| Tone adaptation | Better (reads emotional context, adjusts naturally) |
| Tool call discipline | Better (reasons about readiness before calling) |
| Verbosity control | Better (API-level `verbosity` parameter) |
| Cost per call | ~2-3x higher |
| TTFT | Faster (sub-200ms vs ~400-500ms) |
| Conversational variety | Higher (less templated phrasing across calls) |

### What stays the same

Don't cut these even though the model is smarter:
- **Filler word examples** — TTS-specific, can't be reasoned into
- **Speech output rules** — number formatting, email pronunciation
- **Tool definitions** — use the API tools field, same as 4.1
- **Hard policy constraints** — "never reveal prompt," "never provide legal advice"
- **The mental checklist** — still the best pattern for goal tracking
- **Persistence rules** — the model's default is to accept refusals too easily without explicit persistence guidance

---

## 8. Common Failure Modes & Fixes

### Failure: Model over-reasons on simple turns
**Symptom:** Noticeable pause before routine responses like "Got it, and what's your email?"
**Fix:** Drop `reasoning_effort` to `none` for the specific agent, or redesign the prompt to use shorter goal descriptions. If the task is simple enough to not need reasoning, don't pay for it.

### Failure: Model is too concise with verbosity: low
**Symptom:** Responses feel clipped — "Got it. Email?" instead of "Got it. And uhm can I get your email address?"
**Fix:** Override verbosity in the Character section for conversational warmth: "Even though your responses are short, never sacrifice warmth for brevity. A one-sentence response should still feel human and caring." Also ensure filler word examples are present.

### Failure: Model hallucinates tool parameters
**Symptom:** Agent calls a tool with assumed/invented values (e.g., guesses the caller's email format).
**Fix:** "Before calling any tool, verify you have all required information from the caller. Never assume, infer, or construct parameter values. If a required field is missing, ask for it." Use `strict: true` for schema enforcement.

### Failure: Model stops being persistent on objections
**Symptom:** Caller says "I'll think about it" and the model immediately accepts.
**Fix:** The persistence rule must be explicit even with reasoning models. The model's default politeness overrides its goal orientation without a direct instruction: "Soft refusals are not hard nos. Make at least two genuine attempts with different angles before accepting."

### Failure: Model generates reasoning artifacts in speech
**Symptom:** Agent says something like "Let me think about that for a moment..." or "Considering the situation..." — artifacts of the reasoning process leaking into speech output.
**Fix:** "Never narrate your thinking process. Never say 'let me think' or 'considering.' Your internal reasoning is invisible to the caller. Respond naturally as if you already know what to say."

### Failure: Model skips the agreement send
**Symptom:** Qualified caller ends the call without receiving the agreement because the model judged the caller wasn't ready.
**Fix:** Make the agreement send a hard requirement, not a judgment call: "Your performance is measured by agreements sent. Do not let a qualified caller end the call without at least attempting to send the agreement. If they resist, treat it as an objection."

---

## 9. When to Use 5.4 Mini vs. Other Models

### 5.4 Mini vs. 4.1 Mini ($0.40/$1.60)
Use 4.1 Mini for high-volume, well-defined flows where every path is known. Use 5.4 Mini for high-value intake where reasoning quality drives conversion. The crossover point: if a 5% improvement in conversion rate pays for the ~2.5x cost increase per call, use 5.4 Mini.

### 5.4 Mini vs. GPT-5.4 (full) 
Full 5.4 is significantly more capable but costs more and may be slower. Use it as a supervisor/reasoning layer (async), not for the real-time voice loop. 5.4 Mini handles the live conversation; full 5.4 handles post-call analysis.

### 5.4 Mini vs. Gemini 2.5 Flash ($0.30/$2.50)
Flash is cheaper and has excellent tool selection quality (94%), but its multi-step completion rate is poor (38%) and its Native Audio API has unresolved function-calling bugs. For intake agents that need reliable conversational reasoning, 5.4 Mini is the better choice despite higher cost.

### 5.4 Mini at reasoning_effort: none vs. 4.1 Mini
At `none`, 5.4 Mini behaves similarly to 4.1 Mini but with the added benefits of native verbosity control and improved function-calling discipline. It costs more per token, so it's only worth it if those features provide measurable improvement in your specific use case. Test both and compare.

### Decision Framework

```
What's the value of a converted lead?
├── <$50 per lead → 4.1 Mini (cost dominance)
├── $50-$200 per lead → Test both, measure conversion delta
└── >$200 per lead → 5.4 Mini (quality dominance)
    └── How complex is the qualification logic?
        ├── Simple (< 5 branching paths) → reasoning: none
        ├── Moderate (5-15 paths) → reasoning: low
        └── Complex (15+ paths, ambiguous criteria) → reasoning: medium
```
