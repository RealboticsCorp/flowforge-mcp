"""Shared async HTTP client and error handling for the FlowForge API.

All tools route their network access through :func:`api_request` (or
:func:`api_send` when they need the status code and headers) so that
authentication, timeouts, redirects, read retries and error translation live in
exactly one place.
"""

import asyncio
import os
from dataclasses import dataclass
from typing import Any, Optional

import httpx

from .app import API_BASE_URL, API_KEY_ENV, REQUEST_TIMEOUT_SECONDS


# Maximum redirect hops to follow before giving up (guards against loops).
_MAX_REDIRECTS = 5

# Read retries for transient server errors (docs: retry reads on 500/502/503
# with backoff). Writes are never retried: FlowForge has no Idempotency-Key, so
# a retried POST /calls/start places a second real call.
_READ_RETRY_STATUSES = frozenset({500, 502, 503})
_READ_RETRY_DELAYS_SECONDS = (1.0, 2.0)


class FlowForgeConfigError(RuntimeError):
    """Raised when the server is missing required configuration (e.g. API key)."""


@dataclass(frozen=True)
class ApiResponse:
    """A completed API exchange: status, request id, and decoded body."""

    status: int
    request_id: Optional[str]
    body: Any


def _get_api_key() -> str:
    """Return the FlowForge API key from the environment.

    Raises:
        FlowForgeConfigError: If the key is not configured. The message tells
            the user exactly which variable to set and where to get a key.
    """
    api_key = os.environ.get(API_KEY_ENV, "").strip()
    if not api_key:
        raise FlowForgeConfigError(
            f"Missing API key. Set the {API_KEY_ENV} environment variable to a "
            f"FlowForge key (format: ff_live_...). Create one in the FlowForge "
            f"dashboard under Settings -> API Keys."
        )
    return api_key


async def api_send(
    path: str,
    method: str = "GET",
    *,
    params: Optional[dict[str, Any]] = None,
    json: Any = None,
    files: Optional[dict[str, Any]] = None,
    data: Optional[dict[str, Any]] = None,
    drop_none: bool = True,
) -> ApiResponse:
    """Send an authenticated request and return status + body WITHOUT raising
    on HTTP error statuses.

    Args:
        path: Endpoint path relative to the API base, e.g. ``"calls/start"``.
            A leading slash and a leading ``api/v1/external/`` are both optional.
        method: HTTP method (GET, POST, PATCH, PUT, DELETE).
        params: Query-string parameters. ``None`` values are dropped.
        json: JSON body. For dicts, ``None`` values are dropped (unless
            ``drop_none=False``) so the API only receives fields the caller
            set. Lists are sent verbatim.
        files: Multipart file parts, as accepted by httpx (``{"file": (name,
            bytes, content_type)}``).
        data: Multipart form fields sent alongside ``files``.
        drop_none: Pass False for caller-supplied passthrough bodies, so an
            explicit ``null`` (e.g. unlinking a knowledge base) reaches the API.

    Raises:
        UnsafePathError: If ``path`` contains dot segments or URL syntax.
        httpx.TimeoutException / httpx.RequestError: network failures.
        FlowForgeConfigError: If the API key is not configured.
    """
    api_key = _get_api_key()
    method = method.upper()
    headers = {"X-API-Key": api_key, "Accept": "application/json"}
    body = _drop_none(json) if (drop_none and isinstance(json, dict)) else json
    url = _build_url(path, _drop_none(params))

    attempts = 1 + (len(_READ_RETRY_DELAYS_SECONDS) if method == "GET" else 0)
    response: Optional[httpx.Response] = None
    for attempt in range(attempts):
        response = await _request_following_redirects(
            method, url, headers=headers, json=body, files=files, data=data
        )
        if response.status_code not in _READ_RETRY_STATUSES or attempt == attempts - 1:
            break
        await asyncio.sleep(_READ_RETRY_DELAYS_SECONDS[attempt])

    assert response is not None  # loop always runs at least once
    return ApiResponse(
        status=response.status_code,
        request_id=response.headers.get("x-request-id"),
        body=_decode(response),
    )


async def api_request(
    path: str,
    method: str = "GET",
    *,
    params: Optional[dict[str, Any]] = None,
    json: Any = None,
    files: Optional[dict[str, Any]] = None,
    data: Optional[dict[str, Any]] = None,
    drop_none: bool = True,
) -> Any:
    """Perform an authenticated request and return the decoded body.

    Same arguments as :func:`api_send`.

    Returns:
        The parsed JSON body; ``{}`` for empty (204) responses; ``{"raw": text}``
        for non-JSON success bodies (e.g. the CSV ledger).

    Raises:
        FlowForgeHTTPError: For non-2xx responses (translated by
            :func:`format_error`).
        httpx.TimeoutException / httpx.RequestError: network failures.
        FlowForgeConfigError: If the API key is not configured.
    """
    result = await api_send(
        path, method, params=params, json=json, files=files, data=data, drop_none=drop_none
    )
    # A 3xx that was not followed (cross-host, or a write the client refused
    # to downgrade) is a failure, not a success.
    if result.status >= 300:
        raise FlowForgeHTTPError(result)
    return result.body


class UnsafePathError(ValueError):
    """A path that could escape its intended endpoint (dot segments, URL syntax)."""


_FORBIDDEN_PATH_CHARS = frozenset("?#%\\")


def _validate_path(path: str) -> str:
    """Reject dot segments and URL syntax before the path reaches httpx.

    httpx normalizes ``..`` away, so an ID like ``../../calls/<id>/end``
    interpolated into an ungated route would otherwise reach a different (and
    possibly gated) endpoint. Real IDs never contain these characters.
    """
    if any(char in _FORBIDDEN_PATH_CHARS for char in path):
        raise UnsafePathError(f"Path contains a forbidden character (?, #, %, \\): {path!r}")
    if any(segment in (".", "..") for segment in path.split("/")):
        raise UnsafePathError(f"Path contains a '.' or '..' segment: {path!r}")
    return path


class FlowForgeHTTPError(Exception):
    """A non-2xx FlowForge response, carrying the decoded error envelope."""

    def __init__(self, result: ApiResponse) -> None:
        super().__init__(f"HTTP {result.status}")
        self.result = result


def _build_url(path: str, params: Optional[dict[str, Any]]) -> httpx.URL:
    """Join ``path`` onto the API base, tolerating a pasted full API path."""
    clean = _validate_path(path.strip()).lstrip("/")
    if clean.startswith("api/v1/external/"):
        clean = clean[len("api/v1/external/"):]
    # Bake params into the URL so they survive redirects without being
    # re-appended on each hop.
    return httpx.URL(f"{API_BASE_URL}/{clean}", params=params or None)


async def _request_following_redirects(
    method: str,
    url: httpx.URL,
    *,
    headers: dict[str, str],
    json: Any,
    files: Optional[dict[str, Any]],
    data: Optional[dict[str, Any]],
) -> httpx.Response:
    """Issue a request, following redirects manually and forcing HTTPS.

    The API 307-redirects bare collection paths to their trailing-slash form
    (/assistants -> /assistants/) and has historically built the Location with
    an http:// scheme. Letting httpx auto-follow would transmit X-API-Key over
    plaintext on that hop, so every hop is upgraded to https before re-request.

    Redirects to another host are never followed (the key would go with them),
    and a 301/302 on PUT/PATCH/DELETE is returned rather than silently turned
    into a GET that would look like a successful write.
    """
    origin_host = url.host
    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT_SECONDS, follow_redirects=False
    ) as client:
        for _ in range(_MAX_REDIRECTS + 1):
            response = await client.request(
                method, url, json=json, files=files, data=data, headers=headers
            )
            if not (response.is_redirect and response.headers.get("location")):
                return response
            target = httpx.URL(response.url).join(response.headers["location"])
            if target.host != origin_host:
                return response
            if target.scheme == "http":
                target = target.copy_with(scheme="https", port=None)
            status = response.status_code
            if status in (301, 302) and method not in ("GET", "POST"):
                return response
            # 303 (and 301/302 on POST) downgrade to GET without a body;
            # 307/308 preserve method and body.
            if status == 303 or (status in (301, 302) and method == "POST"):
                method, json, files, data = "GET", None, None, None
            url = target
        raise httpx.TooManyRedirects("Exceeded redirect limit.", request=response.request)


def _decode(response: httpx.Response) -> Any:
    """Decode a response body: JSON when possible, else raw text."""
    if not response.content:
        return {}
    try:
        return response.json()
    except ValueError:
        return {"raw": response.text}


def _drop_none(data: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """Return a copy of ``data`` with ``None`` values removed, or ``None``."""
    if not data:
        return None
    return {key: value for key, value in data.items() if value is not None}


_STATUS_HINTS = {
    400: "The request is invalid for the resource's current state (e.g. starting a running campaign, or a caller number not active in this org).",
    401: "Authentication failed. Verify FLOWFORGE_API_KEY is a valid, non-expired key (ff_live_...) for this host.",
    402: "Prepaid balance is used up. Add funds in Billing before placing calls or starting campaigns; do not retry until then.",
    403: "Permission denied. The key's scopes (or its owner's dashboard permissions) don't cover this request, or the call was refused.",
    404: "Not found, or it belongs to another org. Re-list to get the right ID; never guess IDs.",
    409: "Conflict: the name/word already exists. Pick another name or update the existing object.",
    413: "Upload too large (voice cloning caps at 50 MB).",
    422: "Validation failed. Fix the fields listed in Details (use flowforge_api_reference for the schema).",
    429: "Rate limited by an intermediary. Back off and retry.",
    500: "FlowForge server error (GETs were already retried 3x). Quote the request_id to FlowForge. Never blindly retry call-starting writes: check flowforge_list_calls first (no idempotency keys).",
    502: "An upstream service FlowForge depends on failed (e.g. Vapi during vapi-import). Retry shortly.",
    503: "FlowForge is temporarily unable to serve this (e.g. calls cannot be placed right now). Retry after a short wait.",
}


def format_error(error: Exception) -> str:
    """Translate an exception into a clear, actionable message for the agent.

    The message names the likely cause, the API's own detail, and the request
    id (quote it to FlowForge support), so the agent can self-correct.
    """
    if isinstance(error, FlowForgeConfigError):
        return f"Error: {error}"

    if isinstance(error, FlowForgeHTTPError):
        result = error.result
        hint = _STATUS_HINTS.get(
            result.status,
            "Unfollowed redirect (cross-host, or a write the client will not downgrade)."
            if 300 <= result.status < 400
            else f"The API returned HTTP {result.status}.",
        )
        detail = extract_detail(result.body)
        parts = [f"Error: HTTP {result.status}. {hint}"]
        if detail:
            parts.append(f"Details: {detail}")
        if result.request_id:
            parts.append(f"request_id: {result.request_id}")
        return " ".join(parts)

    if isinstance(error, UnsafePathError):
        return f"Error: {error}. Pass plain IDs, not paths."

    if isinstance(error, httpx.TooManyRedirects):
        return "Error: The API redirected in a loop; check FLOWFORGE_BASE_URL."

    if isinstance(error, httpx.TimeoutException):
        return (
            "Error: The request timed out. If it was a call-starting write, check "
            "flowforge_list_calls (search=<number>) before retrying; otherwise retry."
        )

    if isinstance(error, httpx.RequestError):
        return (
            "Error: Could not reach the FlowForge API "
            f"({type(error).__name__}). Check network connectivity and the "
            "FLOWFORGE_BASE_URL setting (flowforge_health checks the host)."
        )

    return f"Error: Unexpected {type(error).__name__}: {error}"


def extract_detail(body: Any) -> str:
    """Pull a human-readable detail out of a FlowForge error envelope.

    Envelopes are ``{"error": str|object, "request_id": ...}`` plus, for 422,
    a ``detail`` list of ``{loc, msg, type}`` field errors.
    """
    if not isinstance(body, dict):
        return ""
    detail = body.get("detail")
    if isinstance(detail, list) and detail:
        return "; ".join(_field_error(item) for item in detail[:10])
    for key in ("detail", "error", "message"):
        value = body.get(key)
        if isinstance(value, str) and value:
            return value
        if value:
            return str(value)[:500]
    if "raw" in body:
        return str(body["raw"])[:300].strip()
    return ""


def _field_error(item: Any) -> str:
    """Render one 422 field error as ``body.phone_number: Field required``."""
    if not isinstance(item, dict):
        return str(item)
    location = ".".join(str(part) for part in item.get("loc", []))
    return f"{location}: {item.get('msg', '')}".strip(": ")
