"""Tools for FlowForge outbound campaigns.

A *campaign* drives many calls (or messages) to a list of leads using an
assistant, with its own dialing settings and analytics. These tools cover
creating campaigns, adding leads, controlling run state (start/stop/pause/
resume/clone), and inspecting a campaign with its analytics in one step.
"""

from enum import Enum
from typing import Any, Optional

from pydantic import Field

from ..app import mcp
from ..client import api_request, format_error
from ..formatting import local_page, render
from ..models import FormatMixin, PaginationParams, StrictModel


class CampaignAction(str, Enum):
    """Run-state action for a campaign."""

    START = "start"
    STOP = "stop"
    PAUSE = "pause"
    RESUME = "resume"
    CLONE = "clone"


class CampaignInclude(str, Enum):
    """Related campaign data foldable into a single get request."""

    ANALYTICS = "analytics"
    STATUS = "status"
    LEADS = "leads"
    CALLS = "calls"


class ListCampaignsInput(PaginationParams):
    """Inputs for listing campaigns."""

    status: Optional[str] = Field(
        default=None, description="Filter by status, e.g. 'draft', 'running', 'paused', 'completed'."
    )
    direction: Optional[str] = Field(default=None, description="Filter by 'outbound' or 'inbound'.")
    agent_id: Optional[str] = Field(default=None, description="Only campaigns using this assistant.")


class CreateCampaignInput(FormatMixin):
    """Inputs for creating a campaign. Only ``name`` is required."""

    name: str = Field(..., min_length=1, max_length=200, description="Campaign name.")
    description: Optional[str] = Field(default=None, description="Optional description.")
    agent_id: Optional[str] = Field(
        default=None, description="Assistant/agent UUID used to run the campaign."
    )
    campaign_type: Optional[str] = Field(
        default=None, description="Channel type (default 'phone')."
    )
    direction: Optional[str] = Field(
        default=None, description="Call direction (default 'outbound')."
    )
    phone_number_id: Optional[str] = Field(
        default=None, description="Specific phone number UUID to dial from."
    )
    phone_pool_id: Optional[str] = Field(
        default=None, description="Phone pool UUID to rotate caller IDs from."
    )
    parallel_lines: Optional[int] = Field(
        default=None, ge=1, description="Number of simultaneous lines (default 1)."
    )
    total_dial_attempts: Optional[int] = Field(
        default=None, ge=1, description="Max dial attempts per lead (default 3)."
    )
    recipients: Optional[list[dict[str, Any]]] = Field(
        default=None,
        description="Optional initial leads, each a LeadItem object (e.g. {'phone_number': '+1...'}).",
    )
    extra_config: Optional[dict[str, Any]] = Field(
        default=None,
        description=(
            "Any other CreateCampaignRequest field (e.g. message_template, "
            "send_rate_per_hour, min_retry_interval_minutes). Merged verbatim."
        ),
    )


class CampaignControlInput(FormatMixin):
    """Inputs for changing a campaign's run state."""

    campaign_id: str = Field(..., min_length=1, description="Target campaign ID.")
    action: CampaignAction = Field(
        ...,
        description="One of: start, stop, pause, resume, clone.",
    )


class AddLeadsInput(FormatMixin):
    """Inputs for bulk-adding leads to a campaign."""

    campaign_id: str = Field(..., min_length=1, description="Target campaign ID.")
    leads: list[dict[str, Any]] = Field(
        ...,
        min_length=1,
        description=(
            "Leads to add: [{'phone_number': '+14155551234' (E.164, required), "
            "'first_name', 'last_name', 'email', 'custom_fields': {...}}]. "
            "custom_fields feed the assistant's {{template variables}}."
        ),
    )
    allow_duplicates: bool = Field(
        default=False, description="Add numbers already present in the campaign instead of skipping them."
    )
    allow_self_dial: bool = Field(
        default=False, description="Allow leads whose number is one of your own FlowForge numbers."
    )


class GetCampaignInput(FormatMixin):
    """Inputs for fetching a campaign with optional related data."""

    campaign_id: str = Field(..., min_length=1, description="Target campaign ID.")
    include: list[CampaignInclude] = Field(
        default_factory=list,
        description=(
            "Related data to include in one step: any of 'analytics', 'status', "
            "'leads', 'calls'. Omit for the base campaign record."
        ),
    )


class DeleteCampaignInput(StrictModel):
    """Inputs for deleting a campaign."""

    campaign_id: str = Field(..., min_length=1, description="Campaign ID to delete.")


@mcp.tool(
    name="flowforge_list_campaigns",
    annotations={
        "title": "List FlowForge Campaigns",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowforge_list_campaigns(params: ListCampaignsInput) -> str:
    """List outbound campaigns in your organization.

    Args:
        params: ``limit`` (1-100), ``offset``, ``response_format``.

    Returns:
        JSON/Markdown with pagination metadata and a ``campaigns`` array.

    Error Handling:
        Returns "Error: ..." on failure.
    """
    try:
        # Server filters but does not paginate; page client-side.
        data = await api_request(
            "campaigns/",
            params={
                "status": params.status,
                "direction": params.direction,
                "agent_id": params.agent_id,
            },
        )
        envelope = local_page(
            data, preferred_key="campaigns", limit=params.limit, offset=params.offset
        )
        return render(envelope, params.response_format, title="FlowForge Campaigns")
    except Exception as error:  # noqa: BLE001
        return format_error(error)


@mcp.tool(
    name="flowforge_create_campaign",
    annotations={
        "title": "Create FlowForge Campaign",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def flowforge_create_campaign(params: CreateCampaignInput) -> str:
    """Create an outbound campaign.

    Provide an ``agent_id`` to bind an assistant, a dialing source
    (``phone_number_id`` or ``phone_pool_id``), and optionally seed
    ``recipients``. Use ``extra_config`` for any other campaign setting.

    Args:
        params: See field descriptions.

    Returns:
        The created campaign object (with its ID) as JSON or Markdown.

    Error Handling:
        Returns "Error: Validation failed..." if fields are malformed.
    """
    try:
        body: dict[str, Any] = {
            "name": params.name,
            "description": params.description,
            "agent_id": params.agent_id,
            "campaign_type": params.campaign_type,
            "direction": params.direction,
            "phone_number_id": params.phone_number_id,
            "phone_pool_id": params.phone_pool_id,
            "parallel_lines": params.parallel_lines,
            "total_dial_attempts": params.total_dial_attempts,
            "recipients": params.recipients,
        }
        if params.extra_config:
            body.update(params.extra_config)
        data = await api_request("campaigns/", method="POST", json=body)
        return render(data, params.response_format, title="Created Campaign")
    except Exception as error:  # noqa: BLE001
        return format_error(error)


@mcp.tool(
    name="flowforge_get_campaign",
    annotations={
        "title": "Get FlowForge Campaign",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowforge_get_campaign(params: GetCampaignInput) -> str:
    """Fetch a campaign and, in one step, any of its analytics, status, leads,
    or calls.

    Args:
        params: ``campaign_id`` and optional ``include`` list.

    Returns:
        JSON/Markdown with a ``campaign`` object plus one key per requested
        include. A failed include yields an ``{"error": ...}`` note rather than
        failing the whole request.

    Error Handling:
        Returns "Error: Resource not found..." if the ID is wrong.
    """
    try:
        result: dict[str, Any] = {"campaign": await api_request(f"campaigns/{params.campaign_id}")}
        for include in params.include:
            try:
                result[include.value] = await api_request(
                    f"campaigns/{params.campaign_id}/{include.value}"
                )
            except Exception as sub_error:  # noqa: BLE001 - isolate per-include failures
                result[include.value] = {"error": format_error(sub_error)}
        return render(result, params.response_format, title="Campaign Details")
    except Exception as error:  # noqa: BLE001
        return format_error(error)


@mcp.tool(
    name="flowforge_control_campaign",
    annotations={
        "title": "Control FlowForge Campaign",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def flowforge_control_campaign(params: CampaignControlInput) -> str:
    """Change a campaign's run state: start, stop, pause, resume, or clone it.

    Args:
        params: ``campaign_id`` and ``action``.

    Returns:
        The API result (e.g. updated status, or the clone object).

    Error Handling:
        Returns "Error: ..." on failure (e.g. resuming a non-paused campaign).
    """
    try:
        data = await api_request(
            f"campaigns/{params.campaign_id}/{params.action.value}", method="POST"
        )
        return render(data, params.response_format, title=f"Campaign {params.action.value.title()}")
    except Exception as error:  # noqa: BLE001
        return format_error(error)


@mcp.tool(
    name="flowforge_add_campaign_leads",
    annotations={
        "title": "Add FlowForge Campaign Leads",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def flowforge_add_campaign_leads(params: AddLeadsInput) -> str:
    """Bulk-add leads (contacts) to a campaign.

    Args:
        params: ``campaign_id`` and a ``leads`` array of contact objects.

    Returns:
        The API result summarizing how many leads were added.

    Error Handling:
        Returns "Error: ..." on failure.
    """
    try:
        data = await api_request(
            f"campaigns/{params.campaign_id}/leads/bulk",
            method="POST",
            json={
                "leads": params.leads,
                "allow_duplicates": params.allow_duplicates,
                "allow_self_dial": params.allow_self_dial,
            },
        )
        return render(data, params.response_format, title="Leads Added")
    except Exception as error:  # noqa: BLE001
        return format_error(error)


@mcp.tool(
    name="flowforge_delete_campaign",
    annotations={
        "title": "Delete FlowForge Campaign",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowforge_delete_campaign(params: DeleteCampaignInput) -> str:
    """Permanently delete a campaign. This cannot be undone.

    Args:
        params: ``campaign_id`` to delete.

    Returns:
        A confirmation message on success.

    Error Handling:
        Returns "Error: Resource not found..." if the ID is wrong.
    """
    try:
        await api_request(f"campaigns/{params.campaign_id}", method="DELETE")
        return f"Deleted campaign {params.campaign_id}."
    except Exception as error:  # noqa: BLE001
        return format_error(error)
