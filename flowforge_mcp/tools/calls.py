"""Tools for placing and inspecting FlowForge phone calls.

Covers the core calling workflow: start a single call, start a batch (up to
100), list/filter call history, fetch one call together with its transcript /
recordings / metrics in a single step, list live calls, and end calls.
"""

from enum import Enum
from typing import Any, Optional

from pydantic import Field, field_validator

from ..app import mcp
from ..client import api_request, format_error
from ..formatting import ResponseFormat, extract_items, paginated, render
from ..models import FormatMixin, StrictModel

# Sub-resources that can be folded into a single get-call request.
_CALL_DETAIL_ENDPOINTS = {
    "transcript": "transcript",
    "recordings": "recordings",
    "metrics": "metrics",
    "events": "events",
}


class CallDetail(str, Enum):
    """Optional related data to include when fetching a call."""

    TRANSCRIPT = "transcript"
    RECORDINGS = "recordings"
    METRICS = "metrics"
    EVENTS = "events"


class StartCallInput(FormatMixin):
    """Inputs for starting a single outbound call."""

    phone_number: str = Field(
        ...,
        description="Destination phone number in E.164 format, e.g. '+14155551234'.",
    )
    assistant_id: str = Field(
        ..., min_length=1, description="ID of the assistant/agent that will handle the call."
    )
    caller_phone_number: Optional[str] = Field(
        default=None,
        description="Specific org phone number to call from (E.164). Optional.",
    )
    template_variables: Optional[dict[str, Any]] = Field(
        default=None,
        description=(
            "Key/value variables injected into the assistant's prompt for "
            "personalization, e.g. {'customer_name': 'Alex'}."
        ),
    )

    @field_validator("phone_number", "caller_phone_number")
    @classmethod
    def _check_e164(cls, value: Optional[str]) -> Optional[str]:
        if value and not value.startswith("+"):
            raise ValueError("Phone number must be in E.164 format and start with '+'.")
        return value


class BatchCallItem(StrictModel):
    """One recipient within a batch call request."""

    phone_number: str = Field(..., description="Destination number in E.164 format.")
    template_variables: Optional[dict[str, Any]] = Field(
        default=None, description="Per-call personalization variables."
    )
    reference_id: Optional[str] = Field(
        default=None, description="Your own ID for correlating this call in the results."
    )

    @field_validator("phone_number")
    @classmethod
    def _check_e164(cls, value: str) -> str:
        if not value.startswith("+"):
            raise ValueError("Phone number must be in E.164 format and start with '+'.")
        return value


class BatchCallInput(FormatMixin):
    """Inputs for starting up to 100 outbound calls in one request."""

    assistant_id: str = Field(
        ..., min_length=1, description="Assistant/agent used for every call in the batch."
    )
    calls: list[BatchCallItem] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of recipients (1-100 items).",
    )
    caller_phone_number: Optional[str] = Field(
        default=None, description="Specific org phone number to call from (E.164)."
    )
    delay_between_calls_ms: int = Field(
        default=500,
        ge=0,
        le=5000,
        description="Delay between successive calls in milliseconds (0-5000).",
    )


class ListCallsInput(FormatMixin):
    """Inputs for listing/filtering call history."""

    limit: int = Field(default=50, ge=1, le=100, description="Page size (1-100).")
    offset: int = Field(default=0, ge=0, description="Pagination offset.")
    status_filter: Optional[str] = Field(
        default=None,
        description="Comma-separated statuses, e.g. 'completed,no_answer'.",
    )
    direction_filter: Optional[str] = Field(
        default=None, description="Call direction: 'inbound' or 'outbound'."
    )
    agent_id: Optional[str] = Field(default=None, description="Filter by assistant/agent UUID.")
    campaign_id: Optional[str] = Field(default=None, description="Filter by campaign UUID.")
    date_from: Optional[str] = Field(
        default=None, description="ISO date/datetime lower bound on start time."
    )
    date_to: Optional[str] = Field(
        default=None, description="ISO date/datetime upper bound on start time."
    )
    search: Optional[str] = Field(
        default=None, description="Substring search across call_id, from/to numbers."
    )
    disposition_name: Optional[str] = Field(
        default=None,
        description="Filter by disposition template name; pass 'none' for undispositioned calls.",
    )
    sort_by: Optional[str] = Field(
        default=None,
        description=(
            "Sort field: start_time, duration_seconds, cost_cents, estimated_cost, "
            "average_latency_ms, or status."
        ),
    )
    sort_order: Optional[str] = Field(
        default=None, description="Sort direction: 'asc' or 'desc' (default desc)."
    )


class GetCallInput(FormatMixin):
    """Inputs for fetching one call, optionally with related data."""

    call_id: str = Field(..., min_length=1, description="ID of the call to fetch.")
    include: list[CallDetail] = Field(
        default_factory=list,
        description=(
            "Related data to fetch alongside the call in one step: any of "
            "'transcript', 'recordings', 'metrics', 'events'. Omit for status only."
        ),
    )


class EndCallInput(StrictModel):
    """Inputs for ending one call or all active calls."""

    call_id: Optional[str] = Field(
        default=None,
        description="ID of the call to end. Omit and set all_calls=true to end every active call.",
    )
    all_calls: bool = Field(
        default=False,
        description="When true, terminate ALL active calls (ignores call_id).",
    )


class ActiveCallsInput(FormatMixin):
    """Inputs for listing currently active calls."""


@mcp.tool(
    name="flowforge_start_call",
    annotations={
        "title": "Start FlowForge Call",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def flowforge_start_call(params: StartCallInput) -> str:
    """Place a single outbound phone call using a FlowForge assistant.

    Args:
        params: ``phone_number`` (E.164), ``assistant_id``, optional
            ``caller_phone_number`` and ``template_variables``.

    Returns:
        JSON/Markdown with ``call_id`` (use it with flowforge_get_call),
        ``room_name``, ``job_id`` and SIP identifiers.

    Examples:
        - "Call +14155551234 with assistant abc" -> phone_number + assistant_id.
        - To personalize: template_variables={'customer_name': 'Alex'}.

    Error Handling:
        Returns "Error: ..." (e.g. 404 if the assistant_id is unknown).
    """
    try:
        body = {
            "phone_number": params.phone_number,
            "assistant_id": params.assistant_id,
            "caller_phone_number": params.caller_phone_number,
            "template_variables": params.template_variables,
        }
        data = await api_request("calls/start", method="POST", json=body)
        return render(data, params.response_format, title="Call Started")
    except Exception as error:  # noqa: BLE001
        return format_error(error)


@mcp.tool(
    name="flowforge_start_batch_calls",
    annotations={
        "title": "Start FlowForge Batch Calls",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def flowforge_start_batch_calls(params: BatchCallInput) -> str:
    """Place up to 100 outbound calls in a single batch with one assistant.

    Each recipient may carry its own ``template_variables`` and a
    ``reference_id`` you can match against the results.

    Args:
        params: ``assistant_id``, ``calls`` (1-100 BatchCallItem objects),
            optional ``caller_phone_number`` and ``delay_between_calls_ms``.

    Returns:
        JSON/Markdown with ``total_requested``, ``successful``, ``failed`` and a
        ``results`` array (each item has phone_number, success, call_id, error,
        reference_id).

    Error Handling:
        Returns "Error: Validation failed..." if any recipient is malformed.
    """
    try:
        body = {
            "assistant_id": params.assistant_id,
            "calls": [item.model_dump(exclude_none=True) for item in params.calls],
            "caller_phone_number": params.caller_phone_number,
            "delay_between_calls_ms": params.delay_between_calls_ms,
        }
        data = await api_request("calls/batch", method="POST", json=body)
        return render(data, params.response_format, title="Batch Calls Started")
    except Exception as error:  # noqa: BLE001
        return format_error(error)


@mcp.tool(
    name="flowforge_list_calls",
    annotations={
        "title": "List FlowForge Calls",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowforge_list_calls(params: ListCallsInput) -> str:
    """List and filter call history with rich filters and sorting.

    Filter by status, direction, agent, campaign, date range, disposition, or a
    freeform search across numbers/IDs. Use this to audit outcomes or find a
    specific call_id.

    Args:
        params: pagination plus optional filters (see field descriptions).

    Returns:
        JSON/Markdown with ``total``, ``count``, ``offset``, ``has_more``,
        ``next_offset`` and a ``calls`` array.

    Error Handling:
        Returns "Error: ..." on failure.
    """
    try:
        query = {
            "limit": params.limit,
            "offset": params.offset,
            "status_filter": params.status_filter,
            "direction_filter": params.direction_filter,
            "agent_id": params.agent_id,
            "campaign_id": params.campaign_id,
            "date_from": params.date_from,
            "date_to": params.date_to,
            "search": params.search,
            "disposition_name": params.disposition_name,
            "sort_by": params.sort_by,
            "sort_order": params.sort_order,
        }
        data = await api_request("calls", params=query)
        items, total = extract_items(data, preferred_key="calls")
        envelope = paginated(
            items, total=total, limit=params.limit, offset=params.offset, item_key="calls"
        )
        return render(envelope, params.response_format, title="FlowForge Calls")
    except Exception as error:  # noqa: BLE001
        return format_error(error)


@mcp.tool(
    name="flowforge_get_call",
    annotations={
        "title": "Get FlowForge Call",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowforge_get_call(params: GetCallInput) -> str:
    """Fetch one call and, in the same step, any of its transcript, recordings,
    metrics, or events.

    This consolidates what would otherwise be several API calls: pass
    ``include=['transcript','metrics']`` to get the call status plus those
    sub-resources together.

    Args:
        params: ``call_id`` and optional ``include`` list.

    Returns:
        JSON/Markdown with a ``call`` object and one key per requested include
        (e.g. ``transcript``, ``recordings``, ``metrics``, ``events``). If an
        include fails, its key holds an ``{"error": ...}`` note instead of
        failing the whole request.

    Error Handling:
        Returns "Error: Resource not found..." if the call_id is wrong.
    """
    try:
        result: dict[str, Any] = {"call": await api_request(f"calls/{params.call_id}")}
        for detail in params.include:
            endpoint = _CALL_DETAIL_ENDPOINTS[detail.value]
            try:
                result[detail.value] = await api_request(f"calls/{params.call_id}/{endpoint}")
            except Exception as sub_error:  # noqa: BLE001 - isolate per-include failures
                result[detail.value] = {"error": format_error(sub_error)}
        return render(result, params.response_format, title="Call Details")
    except Exception as error:  # noqa: BLE001
        return format_error(error)


@mcp.tool(
    name="flowforge_list_active_calls",
    annotations={
        "title": "List Active FlowForge Calls",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowforge_list_active_calls(params: ActiveCallsInput) -> str:
    """List calls that are live right now (in progress).

    Args:
        params: ``response_format`` only.

    Returns:
        JSON/Markdown listing the currently active calls.

    Error Handling:
        Returns "Error: ..." on failure.
    """
    try:
        data = await api_request("calls/live/active")
        return render(data, params.response_format, title="Active Calls")
    except Exception as error:  # noqa: BLE001
        return format_error(error)


@mcp.tool(
    name="flowforge_end_call",
    annotations={
        "title": "End FlowForge Call(s)",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowforge_end_call(params: EndCallInput) -> str:
    """End an in-progress call, or end every active call at once.

    Provide ``call_id`` to end one call, or set ``all_calls=true`` to terminate
    all running calls. This immediately hangs up; it cannot be undone.

    Args:
        params: ``call_id`` (optional) and ``all_calls`` (default false).

    Returns:
        A confirmation message or the API result.

    Error Handling:
        Returns "Error: ..." if neither call_id nor all_calls is provided, or on
        an API failure.
    """
    try:
        if params.all_calls:
            data = await api_request("calls/end-all", method="POST")
            return render(data, ResponseFormat.JSON, title="All Calls Ended")
        if not params.call_id:
            return (
                "Error: Provide a 'call_id' to end a specific call, or set "
                "'all_calls=true' to end all active calls."
            )
        await api_request(f"calls/{params.call_id}/end", method="DELETE")
        return f"Ended call {params.call_id}."
    except Exception as error:  # noqa: BLE001
        return format_error(error)
