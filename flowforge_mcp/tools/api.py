"""Full-coverage tools: endpoint reference, raw API access, and health.

The curated tools cover the common workflows. These three make the *entire*
External API (every endpoint in the bundled OpenAPI spec) reachable and
self-describing, which is what coding agents need:

* ``flowforge_api_reference`` - search endpoints / read exact schemas.
* ``flowforge_api_request`` - call any documented endpoint, with a confirm
  gate on operations that cost money, dial phones, or delete data.
* ``flowforge_health`` - unauthenticated host check.
"""

import re
from typing import Any, Literal, Optional

import httpx
from pydantic import Field

from .. import spec
from ..app import API_BASE_URL, REQUEST_TIMEOUT_SECONDS, mcp
from ..client import api_send, extract_detail, format_error
from ..formatting import to_json
from ..models import StrictModel

# Operations with real-world side effects (phones ring, money is spent, live
# calls drop, org-wide config is replaced). Matched against the spec template.
_GATED_OPERATIONS = frozenset(
    {
        "POST /calls/start",
        "POST /calls/batch",
        "POST /calls/end-all",
        "POST /campaigns/{campaign_id}/start",
        "POST /campaigns/{campaign_id}/resume",
        "POST /phone-numbers/purchase",
        "PUT /mcp-tools/orgs/mcp-servers",
        "POST /mcp-tools/custom/{server_id}/call",
        "POST /characters/instant-test",
        "POST /roles/instant-test",
    }
)

_DEFAULT_MAX_CHARS = 40_000


class ApiReferenceInput(StrictModel):
    """Inputs for searching / describing FlowForge endpoints."""

    query: Optional[str] = Field(
        default=None,
        description=(
            "Words that must all appear in the method, path or summary, e.g. "
            "'pronunciation', 'POST campaigns', 'ledger'. Omit to list a group "
            "(or, with no group, the group index)."
        ),
    )
    group: Optional[str] = Field(
        default=None,
        description=(
            "Restrict to a resource group (first path segment): assistants, "
            "calls, campaigns, phone-numbers, phone-pools, knowledge, voice, "
            "tests, billing, organisation, mcp-tools, characters, roles, "
            "vapi-import, health."
        ),
    )
    method: Optional[str] = Field(
        default=None, description="With 'path': the HTTP method of one endpoint to describe in full."
    )
    path: Optional[str] = Field(
        default=None,
        description=(
            "With 'method': describe one endpoint in full (params + resolved "
            "request-body schema). Concrete paths work: '/calls/abc123/events'."
        ),
    )
    include_response_schema: bool = Field(
        default=False, description="When describing one endpoint, also include its response schemas."
    )
    limit: int = Field(default=40, ge=1, le=160, description="Max endpoints to list in search mode.")


class ApiRequestInput(StrictModel):
    """Inputs for a raw FlowForge External API request."""

    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] = Field(..., description="HTTP method.")
    path: str = Field(
        ...,
        min_length=1,
        description=(
            "Endpoint path relative to /api/v1/external, with IDs filled in, "
            "e.g. '/assistants/<id>/pronunciations'. Collection roots may keep "
            "their trailing slash ('/campaigns/')."
        ),
    )
    query: Optional[dict[str, Any]] = Field(
        default=None, description="Query-string parameters, e.g. {'period_days': 7}."
    )
    body: Optional[Any] = Field(
        default=None,
        description="JSON request body (object or array). Check the schema with flowforge_api_reference first.",
    )
    confirm: bool = Field(
        default=False,
        description=(
            "Required true for DELETEs and side-effect operations (start/batch/"
            "end-all calls, start/resume campaigns, buy numbers, replace org MCP "
            "servers, invoke custom MCP tools, instant tests, and any "
            "undocumented write). Without it the "
            "tool returns a dry-run preview instead of sending."
        ),
    )
    allow_undocumented: bool = Field(
        default=False,
        description="Send even if (method, path) is not in the bundled spec. Use only when the docs are newer than the bundle.",
    )
    max_chars: int = Field(
        default=_DEFAULT_MAX_CHARS,
        ge=1000,
        le=400_000,
        description="Truncate the rendered response body beyond this many characters.",
    )


class HealthInput(StrictModel):
    """No inputs."""


@mcp.tool(
    name="flowforge_api_reference",
    annotations={
        "title": "FlowForge API Reference",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def flowforge_api_reference(params: ApiReferenceInput) -> str:
    """Search the FlowForge External API (all 160 endpoints) or read one
    endpoint's exact contract. Offline - reads the bundled OpenAPI spec.

    Use before ``flowforge_api_request`` and before writing code that calls
    FlowForge, so field names and required params are right the first time.

    Modes:
      * no args -> resource-group index with endpoint counts.
      * ``query`` and/or ``group`` -> matching endpoints (method, path, summary).
      * ``method`` + ``path`` -> full description: path/query params and the
        $ref-resolved request body. In schemas a trailing ``*`` on a property
        name means required.

    Returns:
        JSON. Base URL and auth are included in the index for code generation.
    """
    if params.method and params.path:
        endpoint = spec.match(params.method, params.path)
        if endpoint is None:
            return (
                f"Error: {params.method.upper()} {params.path} is not in the bundled spec "
                f"(v{spec.spec_version()}). Search with 'query' to find the right path."
            )
        return to_json(spec.describe(endpoint, include_response=params.include_response_schema))

    if not params.query and not params.group:
        return to_json(
            {
                "base_url": API_BASE_URL,
                "auth": "X-API-Key: ff_live_... header on every request",
                "spec_version": spec.spec_version(),
                "endpoint_count": len(spec.endpoints()),
                "groups": spec.tags(),
                "next": "Call again with group=<name> or query=<words>.",
            }
        )

    matches = spec.search(params.query, params.group, params.limit)
    return to_json(
        {
            "count": len(matches),
            "endpoints": [
                {"method": e.method, "path": e.path, "summary": e.summary} for e in matches
            ],
            "next": "Describe one with method + path.",
        }
    )


@mcp.tool(
    name="flowforge_api_request",
    annotations={
        "title": "FlowForge Raw API Request",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def flowforge_api_request(params: ApiRequestInput) -> str:
    """Call any documented FlowForge External API endpoint directly.

    Use for operations without a curated tool (characters, roles, vapi-import,
    voice preview, MCP-server attachment, analytics variants, ...) or when you
    need exact control of the body. Auth, host, HTTPS-safe redirects and read
    retries are handled for you.

    Safety: unknown endpoints are refused (unless ``allow_undocumented``), and
    DELETEs plus side-effect operations return a dry-run preview until called
    again with ``confirm=true``. Never auto-confirm calls that dial real
    phones or spend money without the user's go-ahead.

    Returns:
        JSON ``{"status", "request_id", "endpoint", "body"}``. Non-2xx responses
        are returned the same way with an ``error`` summary (not raised), so
        you can read the 422 field errors and fix the request.
    """
    if "?" in params.path or "#" in params.path:
        return "Error: put query parameters in 'query', not in 'path'."
    endpoint = spec.match(params.method, params.path)
    if endpoint is None and not params.allow_undocumented:
        nearby = spec.search(_path_words(params.path), None, 8)
        return to_json(
            {
                "error": f"{params.method} {params.path} is not a documented endpoint.",
                "did_you_mean": [e.key for e in nearby],
                "hint": "Fix the path, or set allow_undocumented=true if the live docs are newer.",
            }
        )

    template = endpoint.key if endpoint else f"{params.method} {spec.normalize_path(params.path)}"
    if _requires_confirmation(params.method, template, documented=endpoint is not None) and not params.confirm:
        return to_json(
            {
                "dry_run": True,
                "would_send": {
                    "method": params.method,
                    "path": spec.normalize_path(params.path),
                    "query": params.query,
                    "body": params.body,
                },
                "endpoint": template,
                "why": "DELETE or real-world side effect. Confirm with the user, then re-call with confirm=true.",
            }
        )

    try:
        result = await api_send(
            spec.normalize_path(params.path),
            params.method,
            params=params.query,
            json=params.body,
            drop_none=False,  # the caller's body is sent exactly as given
        )
    except Exception as error:  # noqa: BLE001 - translated for the agent
        return format_error(error)

    payload: dict[str, Any] = {
        "status": result.status,
        "request_id": result.request_id,
        "endpoint": template,
    }
    if result.status >= 400:
        payload["error"] = extract_detail(result.body) or f"HTTP {result.status}"
    payload["body"] = result.body
    return _truncate(to_json(payload), params.max_chars)


@mcp.tool(
    name="flowforge_health",
    annotations={
        "title": "FlowForge API Health",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowforge_health(params: HealthInput) -> str:
    """Check the FlowForge host is up (unauthenticated GET /health) and report
    which base URL this server targets and which spec version it bundles.

    Use first when other tools return connection errors.
    """
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.get(f"{API_BASE_URL}/health")
        try:
            body: Any = response.json()
        except ValueError:
            body = response.text[:300]
        return to_json(
            {
                "base_url": API_BASE_URL,
                "status": response.status_code,
                "body": body,
                "bundled_spec_version": spec.spec_version(),
            }
        )
    except Exception as error:  # noqa: BLE001
        return format_error(error)


def _requires_confirmation(method: str, template: str, *, documented: bool) -> bool:
    """DELETEs, listed side-effect operations, and any undocumented write."""
    if method == "DELETE" or template in _GATED_OPERATIONS:
        return True
    return not documented and method != "GET"


def _path_words(path: str) -> str:
    """Non-ID path segments, used to suggest the closest documented endpoints."""
    segments = spec.normalize_path(path).strip("/").split("/")
    words = [s for s in segments if s and not re.search(r"\d", s)]
    return " ".join(words[:2])


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return (
        text[:max_chars]
        + f"\n... [truncated {len(text) - max_chars} chars; narrow the query or raise max_chars]"
    )
