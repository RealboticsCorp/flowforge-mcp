"""Tools for managing FlowForge phone numbers.

Covers searching for purchasable numbers, listing owned numbers, and
assigning/unassigning an assistant to a number so inbound calls are answered.
"""

from typing import Optional

from pydantic import Field

from ..app import mcp
from ..client import api_request, format_error
from ..formatting import local_page, render
from ..models import FormatMixin, PaginationParams


class ListPhoneNumbersInput(PaginationParams):
    """Inputs for listing owned phone numbers."""


class SearchPhoneNumbersInput(FormatMixin):
    """Inputs for searching purchasable phone numbers."""

    country_code: str = Field(
        default="US",
        description="ISO country code to search within, e.g. 'US', 'GB' (see flowforge_manage_phone_number action='countries').",
    )
    contains: Optional[str] = Field(
        default=None, description="Digits the number must contain, e.g. '777'."
    )
    area_code: Optional[str] = Field(
        default=None,
        description="Area code / prefix to narrow the search, e.g. '415'.",
    )
    limit: int = Field(
        default=10, ge=1, le=100, description="Maximum candidate numbers to return."
    )


class AssignPhoneNumberInput(FormatMixin):
    """Inputs for assigning or unassigning an assistant to a phone number."""

    phone_number_id: str = Field(..., min_length=1, description="ID of the owned phone number.")
    agent_id: Optional[str] = Field(
        default=None,
        description=(
            "Assistant/agent ID to assign so it answers this number's inbound "
            "calls. Omit and set unassign=true to detach the current assistant."
        ),
    )
    unassign: bool = Field(
        default=False,
        description="When true, unassign the current assistant from the number.",
    )


@mcp.tool(
    name="flowforge_list_phone_numbers",
    annotations={
        "title": "List FlowForge Phone Numbers",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowforge_list_phone_numbers(params: ListPhoneNumbersInput) -> str:
    """List the phone numbers your organization owns.

    Use this to find a ``phone_number_id`` for assigning an assistant or for
    use as a campaign caller ID.

    Args:
        params: ``limit`` (1-100), ``offset``, ``response_format``.

    Returns:
        JSON/Markdown with pagination metadata and a ``phone_numbers`` array.

    Error Handling:
        Returns "Error: ..." on failure.
    """
    try:
        # The endpoint returns every owned number; page client-side.
        data = await api_request("phone-numbers/")
        envelope = local_page(
            data, preferred_key="phone_numbers", limit=params.limit, offset=params.offset
        )
        return render(envelope, params.response_format, title="FlowForge Phone Numbers")
    except Exception as error:  # noqa: BLE001
        return format_error(error)


@mcp.tool(
    name="flowforge_search_phone_numbers",
    annotations={
        "title": "Search Purchasable Phone Numbers",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowforge_search_phone_numbers(params: SearchPhoneNumbersInput) -> str:
    """Search for available phone numbers that can be purchased.

    Args:
        params: ``country_code``, optional ``area_code`` and ``contains``, ``limit``.

    Returns:
        JSON/Markdown listing candidate numbers available to buy.

    Error Handling:
        Returns "Error: ..." on failure.
    """
    try:
        data = await api_request(
            "phone-numbers/search",
            params={
                "country_code": params.country_code,
                "area_code": params.area_code,
                "contains": params.contains,
                "limit": params.limit,
            },
        )
        return render(data, params.response_format, title="Available Phone Numbers")
    except Exception as error:  # noqa: BLE001
        return format_error(error)


@mcp.tool(
    name="flowforge_assign_phone_number",
    annotations={
        "title": "Assign Assistant to Phone Number",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowforge_assign_phone_number(params: AssignPhoneNumberInput) -> str:
    """Assign an assistant to a phone number (so it answers inbound calls), or
    unassign the current one.

    Provide ``agent_id`` to assign, or set ``unassign=true`` to detach.

    Args:
        params: ``phone_number_id``, plus either ``agent_id`` or ``unassign``.

    Returns:
        The API result, or a confirmation message.

    Error Handling:
        Returns "Error: ..." if neither agent_id nor unassign is supplied, or on
        an API failure.
    """
    try:
        if params.unassign:
            data = await api_request(
                f"phone-numbers/{params.phone_number_id}/unassign-agent", method="POST"
            )
            return render(data, params.response_format, title="Assistant Unassigned")
        if not params.agent_id:
            return (
                "Error: Provide 'agent_id' to assign an assistant, or set "
                "'unassign=true' to remove the current assignment."
            )
        data = await api_request(
            f"phone-numbers/{params.phone_number_id}/assign-agent",
            method="POST",
            json={"agent_id": params.agent_id},
        )
        return render(data, params.response_format, title="Assistant Assigned")
    except Exception as error:  # noqa: BLE001
        return format_error(error)
