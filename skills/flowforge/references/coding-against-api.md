# Writing code against the FlowForge External API

Read this before writing or reviewing code (services, n8n Code nodes, scripts,
webhook receivers) that talks to FlowForge. Use `flowforge_api_reference` for the
exact schema of any endpoint; this file covers the rules the schema doesn't show.
Source of truth: https://flowforge.docs.buildwithfern.com (append `.md` to any page
for Markdown; full index at `/llms.txt`; OpenAPI at `/openapi.json`).

## Basics

- Base: `https://api.realbotics.ai/api/v1/external`
- Auth: `X-API-Key: ff_live_…` on every request. Keys are org-scoped; read from an
  env var / secret manager, never hard-code or commit. The dashboard bearer token
  does NOT work here (401 `API key required`).
- JSON in/out. Uploads (knowledge documents, voice clones) are multipart with a
  `file` part.

## Trailing slashes (the #1 integration bug)

Collection routes take a trailing slash; item and action routes don't:

```
GET/POST /assistants/   /campaigns/   /phone-numbers/   /calls/   /tests/   /phone-pools/
GET      /campaigns/{id}/leads/
no slash /assistants/{id}  /calls/start  /calls/batch  /campaigns/{id}/start  /campaigns/{id}/leads/bulk
```

Missing the slash returns a 307 whose `Location` has historically used `http://`;
most clients drop `X-API-Key` on redirect (→ 401) or, worse, resend it over
plaintext. Use the slash; if you must follow redirects, force https and re-attach
the header yourself.

## Pagination is inconsistent

| Endpoint | Behaviour |
| --- | --- |
| `GET /calls/` | `limit`/`offset`; returns `total`, `page`, `page_size`, `total_pages` |
| `GET /knowledge/documents` | `page`/`page_size` (not limit/offset) |
| `GET /campaigns/{id}/leads/`, `/campaigns/{id}/calls` | `limit`/`offset` |
| `GET /assistants/`, `/campaigns/`, `/phone-numbers/`, `/tests/`, `/phone-pools/` | **no paging** — whole collection in one response (100s of rows) |

Response wrappers differ too: `{assistants:[…], total}`, `{success, phone_numbers,
count}`, bare arrays for tests/pools. Normalize at the client boundary.

## Errors

Envelope: `{"error": string|object, "request_id": "…"}` (+ `x-request-id` header).
422 adds `detail: [{loc, msg, type}]`. Always log `request_id`; send your own
`x-request-id` to correlate.

| Status | Meaning | Retry? |
| --- | --- | --- |
| 400 | invalid for current state (campaign already running, caller ID not active) | no — fix state |
| 401 / 403 | key missing/invalid / scope or call refused | no |
| 402 | prepaid balance empty (calls, batch, campaign start) | no — add funds |
| 404 | missing or other org's object | no |
| 409 | name/word already exists | no |
| 413 | upload > 50 MB | no |
| 422 | field validation | no — fix fields |
| 500 / 502 / 503 | server / upstream / temporarily unavailable | reads: backoff 1,2,4,8s ≤5 tries |

No rate-limit headers and no per-key rate limit; practical limits are org
concurrency (`GET /organisation/concurrency`), campaign `parallel_lines` (≤100),
batch size (≤100), leads per bulk add (≤1000).

## No idempotency

There is no `Idempotency-Key`. A retried `POST /calls/start` places a second call.
- Store every returned `call_id`; never retry a request that returned one.
- On timeout: `GET /calls/?search=<destination>&date_from=<send time>` before retrying.
- Put your own correlation id in `template_variables` (e.g. `client_request_id`);
  it returns in the end-of-call report under `capturedVariables`.
- Batch: `reference_id` per item is echoed in that item's result only.

## Webhooks you receive

**End-of-call report** — set on the assistant via PATCH:
`end_of_call_report_config: {enabled: true, server_url, headers: [{key, value}], timeout_seconds: 30}`.
- One attempt, never re-sent on failure; occasionally delivered twice → dedupe on `call.call_id`.
- Not signed: authenticate with a secret in `headers`, verify it on receipt.
- `server_url` must be public (private/internal addresses refused).
- Post-call analysis (`structuredData`, `successEvaluation`, captured variables)
  arrives ONLY here — persist it; no endpoint returns it later.
- Return any 2xx fast (body ignored).

**Webhook tools** — endpoints the agent calls mid-conversation, declared in the
assistant's `webhook_tools` (array replaced wholesale on PATCH):

```json
{
  "name": "lookup_order",
  "description": "Look up an order by ID. Use when the caller asks about order status.",
  "method": "GET",
  "url": "https://your-app.example.com/orders/lookup",
  "headers": [{"name": "Authorization", "value": "Bearer {{shared_secret}}"}],
  "bodyParams": [{"name": "order_id", "type": "string", "description": "Customer order ID", "required": true}],
  "preToolSpeech": "auto",
  "responseTimeout": 20,
  "responseFields": ["status", "items.sku"]
}
```

- `{{template_variables}}` substitute into url/headers/body at call time.
- Retried up to 3× (≈0.5 s, 1 s) on 5xx/timeout/connection error, not on 4xx →
  make writes idempotent.
- Redirects are not followed; the model sees status + body verbatim, so return a
  clear JSON error body on failure. Not signed — use a header secret.
- Copy the exact current shape from a live assistant
  (`flowforge_get_assistant detailed=true`) before writing new ones.

## Agent config essentials

- Knowledge: PATCH `knowledge_base_id` + `enable_rag_tool: true` (create ignores the
  flags); `enable_search_tool` for literal search. Tell the agent in its prompt when to
  search.
- Flows: send `flow_data` (React Flow JSON) on create or set `flow_id`; nodes can
  override prompt/voice per turn.
- Template variables: `{{name}}` in prompt / first message / tool URLs; supplied per
  call, per batch item, or per lead (`custom_fields`).
- Branches: `/assistants/{id}/branches` — fork, edit, test, then promote.

## Campaign start checklist

`POST /campaigns/{id}/start` refuses until: agent (or squad) set; `phone_number_id`
or `phone_pool_id` set; outbound has schedule (start date, times, days, timezone);
a never-run campaign has an outcomes decision
(`POST /campaigns/{id}/dispositions/keep-platform-defaults` or dispositions with
`criteria`). Starting a running campaign → 400. Lead deletes are refused while
running or scheduled.

## Minimal Python client

```python
import os, time, httpx

BASE = "https://api.realbotics.ai/api/v1/external"
HEADERS = {"X-API-Key": os.environ["FLOWFORGE_API_KEY"]}

def ff(method: str, path: str, *, retry_reads: bool = True, **kwargs) -> httpx.Response:
    """Call FlowForge. Retries only GETs on 5xx; never retries call-starting writes."""
    attempts = 5 if (retry_reads and method == "GET") else 1
    for attempt in range(attempts):
        response = httpx.request(method, f"{BASE}{path}", headers=HEADERS, timeout=30, **kwargs)
        if response.status_code < 500 or attempt == attempts - 1:
            return response
        time.sleep(min(2 ** attempt, 8))
    return response

assistants = ff("GET", "/assistants/").json()["assistants"]   # note the slash
```
