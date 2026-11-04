# VAPI Configuration Reference

Reference for voice, LLM, transcriber, tool, observability, and advanced configuration when deploying agents to VAPI.

---

## API Structure

The VAPI assistant config uses a **nested model object**. The system prompt goes inside `model.messages` and tool IDs go inside `model.toolIds`:

```json
{
  "name": "Agent Name",
  "firstMessage": "Hello...",
  "firstMessageMode": "assistant-speaks-first",
  "model": {
    "provider": "openai",
    "model": "gpt-4.1",
    "messages": [{ "role": "system", "content": "Full SCRIPT prompt here..." }],
    "toolIds": ["tool-id-1", "tool-id-2"]
  },
  "voice": { "provider": "11labs", "voiceId": "sarah", "model": "eleven_turbo_v2_5" },
  "transcriber": { "provider": "deepgram", "model": "flux-general-en" },
  "backchannelingEnabled": true,
  "backgroundSound": "off"
}
```

**Key:** `model.messages` (not a flat `instructions` field) and `model.toolIds` (not top-level).

---

## Voice (TTS) Providers

| Provider | Key Voices | Best For | Notes |
|----------|-----------|----------|-------|
| **vapi** | Elliot, Lily, Rohan, Paola, Kian + 12 new voices | Low latency | Vapi-native optimized. Adjustable speed controls. |
| **11labs** | sarah, rachel, adam, josh, emily | Rich expression (Recommended) | Infers emotion from context. Wide library. Custom clones. Models: `eleven_turbo_v2_5`, `eleven_flash_v2_5`. |
| **cartesia** | Sonic 3 voices | Emotion control | Inline tags: `<emotion value="happy" />`. Models: `sonic-3`. |
| **openai** | alloy, echo, fable, onyx, nova, shimmer | Speed, simplicity | Fast, clean output. Limited expressiveness. |
| **deepgram** | aura-asteria, aura-luna, aura-stella | Low latency | Very fast time-to-first-byte. |
| **hume** | EVI2 voices | Emotional intelligence | Reads user emotion and adapts tone. Premium. |
| **playht** | PlayDialog model | Voice cloning | Clone custom voices. Brand-specific delivery. |
| **inworld** | inworld-tts-1.5-max, 1.5-mini | Game/interactive | Expressive, character-driven. |
| **wellsaid** | Caruso + legacy | Studio quality | High-fidelity narration-style voices. |
| **rime-ai** | (various) | Multilingual | Strong non-English support. |
| **azure** | (various) | Enterprise, SSML | SSML markup. Enterprise-grade. |

### Recommended Defaults by Use Case

| Use Case | Voice Provider | Voice / Model | Rationale |
|----------|---------------|---------------|-----------|
| General (recommended) | 11labs | sarah / eleven_turbo_v2_5 | Best expression, natural tone, proven in production |
| Speed-critical (high volume) | vapi or deepgram | Elliot / aura-asteria | Fastest response times |
| Emotion-heavy (healthcare, legal) | hume | EVI2 | Reads and adapts to caller emotion |
| Multilingual | rime-ai | (varies) | Strongest non-English support |
| Brand-specific voice | playht or 11labs | (custom clone) | Clone an existing voice |

---

## LLM Providers

| Provider | Model | Best For | Notes |
|----------|-------|----------|-------|
| **openai** | gpt-4.1 | General use (Recommended) | Best balance of quality, speed, and instruction following |
| **openai** | gpt-4.1-mini | Cost-sensitive, high volume | Faster, cheaper, strong capability |
| **openai** | gpt-4o | General use (legacy) | Still widely used, proven |
| **openai** | gpt-5 / gpt-5-mini | Frontier | Latest capabilities, higher cost |
| **anthropic** | claude-4.6-sonnet | Complex reasoning, nuance | Excellent at following detailed multi-step instructions |
| **anthropic** | claude-4.5-sonnet | Complex reasoning | Strong alternative, slightly older |
| **google** | gemini-2.5-flash-lite | Ultra-low latency + cost | Best speed-to-cost ratio. Great for high-volume outbound. |
| **google** | gemini-2.5-flash | Speed + quality | Good balance for general use |
| **google** | gemini-3-flash | Latest Google | Frontier speed model |
| **groq** | grok-4-fast | Ultra-low latency | Fastest inference available |
| **deepseek** | deepseek-chat | Budget | Open-source, cost-effective |

### Recommended Stacks

| Stack | LLM | Voice | Transcriber | Best For |
|-------|-----|-------|-------------|----------|
| **Low latency / cost** | gemini-2.5-flash-lite | 11labs turbo v2.5 | deepgram flux-general-en | High-volume outbound |
| **Highest quality** | gpt-4.1 | 11labs v2.5 | deepgram nova-3 | Complex conversations |
| **Complex reasoning** | claude-4.6-sonnet | 11labs v2.5 | deepgram nova-3 | Nuanced decision-making |
| **Ultra-fast** | groq/grok-4-fast | vapi native | deepgram flux-general-en | Simple IVR-like flows |

### Configuration Format
```json
{
  "model": {
    "provider": "openai",
    "model": "gpt-4.1",
    "messages": [{ "role": "system", "content": "..." }],
    "toolIds": []
  }
}
```

---

## Transcriber (STT) Providers

| Provider | Model | Best For | Notes |
|----------|-------|----------|-------|
| **deepgram** | flux-general-en | General use (Recommended) | Best speed + accuracy for English |
| **deepgram** | nova-3 | High accuracy | Best accuracy, slightly slower |
| **cartesia** | ink-whisper | Low latency | Fast, good for real-time |
| **soniox** | stt-rt-v4 | Real-time | Optimized for streaming |
| **elevenlabs** | scribe-v2 | High accuracy | Premium tier |

---

## First Message Mode

| Mode | When to Use |
|------|-------------|
| `assistant-speaks-first` | **Outbound calls** -- agent initiates with a static `firstMessage` |
| `assistant-waits-for-user` | **Inbound calls** -- agent waits for caller to speak |
| `assistant-speaks-first-with-model-generated-message` | LLM generates the opening dynamically (see warning below) |

**Warning:** `model-generated-message` is unreliable when the opening must use specific dynamic variables (e.g., `{{first_name}}`). The LLM may use the wrong variable or generate an unexpected greeting. Use a static `firstMessage` with `{{variables}}` when the opening must be precise.

---

## Advanced Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `backchannelingEnabled` | boolean | false | Agent says "mm-hmm", "uh-huh" while user speaks. Recommended for natural feel. |
| `backgroundSound` | string | "off" | Ambient sound: `"off"`, `"office"`, `"cafe"` |
| `compliancePlan.hipaaEnabled` | boolean | false | HIPAA compliance. Restricts logging and data retention. |
| `compliancePlan.pciEnabled` | boolean | false | PCI compliance for payment data. |
| `silenceTimeoutSeconds` | number | 30 | Seconds of silence before auto-ending call |
| `maxDurationSeconds` | number | 600 | Maximum call duration |
| `endCallMessage` | string | null | Message spoken before auto-ending |

**Note:** `hipaaEnabled` at the top level is deprecated. Use `compliancePlan` instead.

---

## Tool Types

### Handoff Tool (for Squad Transfers)

The `handoff` tool is VAPI's dedicated tool type for **agent-to-agent transfers within squads**. It is distinct from `transferCall` (which is for external phone numbers). Handoff tools support context engineering and variable extraction during transfers.

```json
{
  "type": "handoff",
  "destinations": [
    {
      "type": "assistant",
      "assistantName": "Demo Agent",
      "description": "Transfer when the prospect agrees to see a live demo. Do not announce the transfer.",
      "contextEngineeringPlan": {
        "type": "userAndAssistantMessages"
      },
      "variableExtractionPlan": {
        "schema": {
          "type": "object",
          "properties": {
            "demo_type": {
              "type": "string",
              "description": "The type of demo requested",
              "enum": ["sales", "service", "support", "assistant"]
            },
            "prospect_context": {
              "type": "string",
              "description": "Summary of relevant details from the conversation"
            }
          },
          "required": ["demo_type"]
        }
      }
    }
  ]
}
```

**Destination types:** `assistant` (by `assistantId` or `assistantName`), `squad` (by `squadId` or inline), `number`, `sip`

**Destination properties:**

| Property | Type | Description |
|----------|------|-------------|
| `type` | string | Required. `"assistant"`, `"squad"`, `"number"`, `"sip"` |
| `assistantId` | string | Reference a saved assistant by ID |
| `assistantName` | string | Reference by name (only works within a squad) |
| `description` | string | Tells the LLM when to choose this destination |
| `contextEngineeringPlan` | object | Controls conversation history transfer (see below) |
| `variableExtractionPlan` | object | Extracts structured data during handoff (see below) |
| `assistantOverrides` | object | Override settings on the destination assistant |

**LLM-specific pattern:**
- **OpenAI models:** Use separate handoff tools, one per destination (multiple tools)
- **Anthropic models:** Use a single handoff tool with multiple destinations in the array

### Context Engineering Plan

Controls what conversation history is passed to the destination agent during a handoff:

| Type | Description | When to Use |
|------|-------------|-------------|
| `all` | Entire conversation history (default) | Destination needs full context including tool calls |
| `userAndAssistantMessages` | Only user + assistant messages, no system/tool messages | **Recommended for most squad handoffs.** Clean view, lower tokens. |
| `lastNMessages` | Only the most recent N messages (requires `maxMessages`) | Context-window-constrained models |
| `none` | Blank conversation | Agent should start completely fresh |

### Variable Extraction Plan

Automatically extracts structured data from the conversation at the moment of handoff. Uses OpenAI structured outputs to pull values matching a JSON schema. Extracted variables are available in subsequent agents via `{{variableName}}` (Liquid template syntax).

```json
{
  "variableExtractionPlan": {
    "schema": {
      "type": "object",
      "properties": {
        "customerName": { "type": "string", "description": "Full name of the customer" },
        "email": { "type": "string", "format": "email", "description": "Customer email" },
        "issueType": { "type": "string", "description": "Type of issue reported" }
      },
      "required": ["customerName"]
    }
  }
}
```

When a handoff extracts a variable with the same name as an existing one, the new value replaces the previous value.

### Transfer Call Tool

Transfers the call to an **external phone number** or department. For agent-to-agent squad transfers, use the `handoff` tool type instead.

```json
{
  "type": "transferCall",
  "destinations": [
    {
      "type": "number",
      "number": "+15557654321",
      "description": "Main office manager",
      "callerId": "+15551234567"
    }
  ]
}
```

### End Call Tool

Allows the agent to hang up the call programmatically.

```json
{ "type": "endCall" }
```

**Warning:** The `endCall` tool type does NOT accept `name` or `description` fields. Create it with `{"type": "endCall"}` only. The LLM understands when to use it from the system prompt's tool descriptions.

### SMS Tool

Sends text messages during calls (agreements, confirmations, links).

```json
{
  "type": "sms",
  "name": "SendAgreement",
  "description": "Sends the retainer agreement to the caller via text message",
  "sms": {
    "metadata": {
      "from": "+15551234567"
    }
  }
}
```

**Requirements:** `from` number must be a Twilio number in E.164 format.

### DTMF Tool

Sends touch-tone signals (for IVR navigation, entering PINs).

```json
{ "type": "dtmf" }
```

### Voicemail Tool

Detects and handles voicemail.

```json
{ "type": "voicemail" }
```

### Function Tool

Custom server-side function called during the conversation.

```json
{
  "type": "function",
  "name": "lookupAppointment",
  "description": "Looks up a customer's upcoming appointment by phone number",
  "function": {
    "parameters": {
      "type": "object",
      "properties": {
        "phoneNumber": { "type": "string", "description": "Customer phone number" }
      },
      "required": ["phoneNumber"]
    },
    "server": {
      "url": "https://api.example.com/webhook/vapi",
      "headers": { "Authorization": "Bearer {{token}}" }
    }
  }
}
```

### API Request Tool

Direct HTTP API call without a custom server.

```json
{
  "type": "apiRequest",
  "name": "checkInventory",
  "description": "Checks product inventory via the store API",
  "apiRequest": {
    "url": "https://api.store.com/inventory",
    "method": "GET",
    "headers": { "X-API-Key": "{{apiKey}}" },
    "body": {
      "type": "object",
      "properties": { "productId": { "type": "string" } },
      "required": ["productId"]
    },
    "timeoutSeconds": 20,
    "backoffPlan": { "type": "fixed", "maxRetries": 3, "baseDelaySeconds": 1 }
  }
}
```

### Integration Tools

| Type | Purpose |
|------|---------|
| `google.calendar` | Create/read/update calendar events |
| `google.sheets` | Read/write spreadsheet data |
| `slack` | Send messages to Slack channels |
| `mcp` | Connect to any MCP server |

---

## Async Tools & Tool Messages

For tools that take time, configure messages the agent says while waiting:

```json
{
  "type": "function",
  "name": "lookupRecord",
  "description": "Look up the customer's record",
  "messages": [
    { "type": "request-start", "content": "Let me pull that up for you..." },
    { "type": "request-complete", "content": "Got it!" },
    { "type": "request-failed", "content": "I'm having trouble looking that up. Let me try another way." }
  ],
  "async": true
}
```

---

## Hooks

Hooks trigger automated actions on call events. Configure at the assistant level:

| Hook Event | Description |
|-----------|-------------|
| `call.ending` | Fires when the call is about to end. Can trigger transfers (e.g., to a summary agent). |
| `assistant.speechStarted` | Fires when the assistant begins speaking. |
| Low-confidence speech | Fires when the transcriber returns low-confidence results. |
| Time elapsed | Fires at specified time intervals during the call. |

```json
{
  "hooks": [
    {
      "on": "call.ending",
      "do": [
        {
          "type": "transfer",
          "destination": { "type": "assistant", "assistantId": "asst_summary" }
        }
      ]
    }
  ]
}
```

**`sayHook`:** Intercepts and modifies text before it's spoken by the assistant. Useful for real-time content filtering or transformation.

---

## Scorecards (Automated Call Grading)

Scorecards automatically grade calls against KPIs using structured outputs. After a call ends, scorecards compute scores by comparing structured output values to conditions.

**Setup:**
1. Create structured outputs (boolean or number) on the assistant via `artifactPlan.structuredOutputIds`
2. Create a scorecard with metrics referencing those structured output IDs
3. Attach scorecard to the assistant via `artifactPlan.scorecardIds`

```bash
# Create scorecard
curl -X POST https://api.vapi.ai/observability/scorecard \
  -H "Authorization: Bearer $VAPI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Outbound Sales Scorecard",
    "description": "Grades calls on demo conversion and data capture",
    "metrics": [
      {
        "structuredOutputId": "UUID-boolean-demo-booked",
        "conditions": [{ "type": "comparator", "comparator": "=", "value": true, "points": 40 }]
      },
      {
        "structuredOutputId": "UUID-boolean-contact-captured",
        "conditions": [{ "type": "comparator", "comparator": "=", "value": true, "points": 30 }]
      },
      {
        "structuredOutputId": "UUID-number-csat",
        "conditions": [{ "type": "comparator", "comparator": ">=", "value": 8, "points": 30 }]
      }
    ],
    "assistantIds": ["your-assistant-id"]
  }'
```

**Rules:**
- Points across all metrics must sum to **100**
- Supported comparators: `=`, `!=`, `>`, `<`, `>=`, `<=`
- Boolean metrics support only `=`
- Scores available at `call.artifact.scorecards` after the call ends

**Tie scorecards to KPIs from the Role (R) section** — the metrics you define in Phase 3 should map directly to scorecard metrics.

---

## Monitoring (Automated Issue Detection)

VAPI's monitoring system tracks call quality, detects issues, and alerts your team automatically.

**Components:**
- **Monitors** — what to watch and which assistants to target
- **Triggers** — evaluate call data against thresholds on a schedule
- **Issues** — created when thresholds are exceeded
- **Notifiers** — alert channels (email, Slack, webhook)

**Monitor categories:**

| Category | Tracks |
|----------|--------|
| Technical | API errors, provider outages, timeouts |
| Infrastructure | Latency, capacity, resource utilization |
| Effectiveness | Task completion, user satisfaction |
| Compliance | Regulatory and policy adherence |

```bash
# Create a monitor
curl -X POST https://api.vapi.ai/monitoring/monitor \
  -H "Authorization: Bearer $VAPI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Error Rate Monitor",
    "category": "technical",
    "status": "active",
    "targets": "*",
    "triggers": [{
      "insightId": "insight-uuid",
      "interval": { "every": 60 },
      "threshold": { "type": "number", "comparator": "gt", "value": 5 },
      "severity": "error",
      "alert": { "status": "enabled", "credentialIds": ["notifier-uuid"] }
    }]
  }'
```

**Recommended default monitors for every agent:**
- Error rate > 5% (technical, severity: error)
- Task completion < 80% (effectiveness, severity: warning)
- Call duration > max expected (infrastructure, severity: info)

**AI root cause analysis:** `POST /monitoring/issue/{issueId}/analyze` returns summary, root cause (with confidence), impact assessment, and actionable fix suggestions.

Use `"targets": "*"` for org-wide monitoring, or pass specific `assistantIds` for per-agent monitors.

---

## Dynamic Variables

Use `{{variableName}}` syntax in the system prompt for per-call dynamic data. Populate via `assistantOverrides.variableValues` when creating a call:

```json
{
  "assistantId": "asst_123",
  "customer": { "number": "+15551234567" },
  "assistantOverrides": {
    "variableValues": {
      "customerName": "John Smith",
      "appointmentDate": "2026-04-15",
      "now": "April 19, 2026"
    }
  }
}
```

Common variables: `{{now}}`, `{{customerName}}`, `{{appointmentDate}}`, `{{caseId}}`

Variables extracted during handoffs (via `variableExtractionPlan`) are also accessible via the same `{{variableName}}` syntax in subsequent agents.

---

## Deployment Sequence

1. **Create tools first** -- Each tool must exist before the assistant (assistant references `toolIds`)
2. **Create assistant** -- With full SCRIPT prompt in `model.messages[0].content` and tool IDs in `model.toolIds`
3. **For squads** -- Create each agent, then create `handoff` tools referencing the target `assistantId` or `assistantName`, then update each agent's `model.toolIds`
4. **Assign phone number** -- Route inbound number to the entry assistant
5. **Test with outbound call** -- Use `create_call` with the assistant ID and a test phone number
6. **Set up scorecards** -- Create structured outputs, create scorecard, attach to assistant
7. **Set up monitoring** -- Create notifiers, create monitors with triggers and thresholds
8. **Iterate** -- Use the fetch → modify → PATCH pattern to update prompts and settings

### Prompt Sync Pattern (Update Existing Agent)

When updating an agent's prompt after initial deployment:

```bash
# 1. Fetch current state (preserve model, tools, voice)
CURRENT=$(curl -s "https://api.vapi.ai/assistant/$ASSISTANT_ID" \
  -H "Authorization: Bearer $VAPI_API_KEY")

# 2. Modify only the prompt in the complete model object
# 3. PATCH with the COMPLETE model object (never partial)
curl -X PATCH "https://api.vapi.ai/assistant/$ASSISTANT_ID" \
  -H "Authorization: Bearer $VAPI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": { <complete model object with updated messages> }}'
```

### Direct API

```bash
# Create endCall tool (no name or description allowed)
curl -X POST https://api.vapi.ai/tool \
  -H "Authorization: Bearer $VAPI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "type": "endCall" }'

# Create handoff tool (use REST API — MCP create_tool does not support handoff type)
curl -X POST https://api.vapi.ai/tool \
  -H "Authorization: Bearer $VAPI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "type": "handoff", "destinations": [{ "type": "assistant", "assistantName": "...", "description": "...", "contextEngineeringPlan": { "type": "userAndAssistantMessages" } }] }'

# Create assistant
curl -X POST https://api.vapi.ai/assistant \
  -H "Authorization: Bearer $VAPI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "name": "Agent", "model": { ... }, "voice": { ... } }'
```

---

## API Gotchas

| Issue | Details |
|-------|---------|
| **Name max length** | Assistant `name` field has a **40-character maximum**. Plan names accordingly. |
| **endCall has no name/description** | The `endCall` tool type does NOT accept `name` or `description` fields. Create with `{"type": "endCall"}` only. |
| **PATCH replaces model** | `PATCH` on `model` **replaces the entire model object**. Always fetch current state, modify, and send the complete model back. Never partial-PATCH. |
| **Model-generated firstMessage** | `assistant-speaks-first-with-model-generated-message` is unreliable for variable-dependent greetings. Use static `firstMessage` with `{{variables}}` when the opening must use specific data. |
| **MCP doesn't support handoff** | The MCP `create_tool` does not support the `handoff` tool type. Use the REST API directly for handoff tools. |
| **Squad voice consistency** | All squad members MUST use the exact same voice provider, voiceId, and model for seamless single-persona experience. Verify after deployment. |
