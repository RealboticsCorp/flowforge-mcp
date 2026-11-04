"""Campaign administration: settings, lead removal, dispositions, filtered
call lists.

Complements ``campaigns.py`` (create/get/control/add leads). Key start
prerequisites the API enforces: a phone number or pool, and - for a campaign
that has never run - an outcomes decision (custom dispositions with
``criteria``, or ``keep_platform_defaults``).
"""

from enum import Enum
from typing import Any, Optional

from pydantic import Field

from ..app import mcp
from ..client import FlowForgeHTTPError, api_request, format_error
from ..formatting import render
from ..models import FormatMixin
from ._dispatch import MissingInputError, Route, execute, require


class UpdateCampaignSettingsInput(FormatMixin):
    """Inputs for patching campaign settings."""

    campaign_id: str = Field(..., min_length=1, description="Campaign to update.")
    settings: dict[str, Any] = Field(
        ...,
        description=(
            "Fields to change, e.g. {'agent_id', 'phone_number_id' or "
            "'phone_pool_id', 'schedule': {...}, 'dialer_settings': {...}, "
            "'compliance': {...}, 'voicemail_drop_enabled', "
            "'voicemail_drop_message', 'webhook_url', 'pacing_config', "
            "'enforce_local_calling_hours', 'branch_id', "
            "'prompt_variable_mappings'}. Full schema: flowforge_api_reference "
            "method=PATCH path=/campaigns/x/settings."
        ),
    )


class RemoveLeadsInput(FormatMixin):
    """Inputs for bulk-removing campaign leads."""

    campaign_id: str = Field(..., min_length=1, description="Campaign to prune.")
    status_filter: Optional[list[str]] = Field(
        default=None,
        description=(
            "Only remove leads in these statuses, e.g. ['failed','no_answer','busy']. "
            "OMIT to remove ALL leads. Refused (400) while the campaign is running or scheduled."
        ),
    )
    confirm: bool = Field(default=False, description="Required true to actually delete.")


class DispositionAction(str, Enum):
    LIST = "list"
    CREATE = "create"
    UPDATE = "update"
    OUTCOMES_DECISION = "outcomes_decision"
    KEEP_PLATFORM_DEFAULTS = "keep_platform_defaults"
    ORG_LIST = "org_list"


class ManageDispositionsInput(FormatMixin):
    """Inputs for campaign disposition management."""

    action: DispositionAction = Field(
        ...,
        description=(
            "'list'/'create'/'update' a campaign's dispositions; "
            "'outcomes_decision' (can it start?); 'keep_platform_defaults' "
            "(satisfies the outcomes requirement); 'org_list' (dispositions "
            "across the org, for call filtering)."
        ),
    )
    campaign_id: Optional[str] = Field(default=None, description="Campaign ID (all actions except org_list).")
    disposition_id: Optional[str] = Field(default=None, description="update: disposition ID.")
    fields: Optional[dict[str, Any]] = Field(
        default=None,
        description=(
            "create: {'name'*, 'label'*, 'category'*, 'is_terminal' (true), "
            "'criteria' (plain-English rule the analyser applies), "
            "'retry_strategy', 'actions', 'routing_rules', 'compliance_action', "
            "'color', 'sort_order'}. update: any of those except name."
        ),
    )


class CampaignCallsInput(FormatMixin):
    """Inputs for a campaign's filtered call list."""

    campaign_id: str = Field(..., min_length=1, description="Campaign whose calls to list.")
    status: Optional[str] = Field(default=None, description="Call status filter.")
    disposition_id: Optional[str] = Field(default=None, description="Only calls with this disposition.")
    date_from: Optional[str] = Field(default=None, description="ISO lower bound.")
    date_to: Optional[str] = Field(default=None, description="ISO upper bound.")
    search: Optional[str] = Field(default=None, description="Free-text search (number, name).")
    limit: int = Field(default=25, ge=1, le=100, description="Page size.")
    offset: int = Field(default=0, ge=0, description="Rows to skip.")


@mcp.tool(
    name="flowforge_update_campaign_settings",
    annotations={
        "title": "Update FlowForge Campaign Settings",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowforge_update_campaign_settings(params: UpdateCampaignSettingsInput) -> str:
    """Patch a campaign's settings: assistant, caller number/pool, schedule,
    dialer and compliance rules, voicemail drop, webhook, pacing, branch.
    Only the keys you pass change."""
    return await execute(
        Route("PATCH", f"campaigns/{params.campaign_id}/settings", body=params.settings, keep_nulls=True),
        confirm=False,
        response_format=params.response_format,
        title="Campaign Settings",
    )


@mcp.tool(
    name="flowforge_remove_campaign_leads",
    annotations={
        "title": "Remove FlowForge Campaign Leads",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowforge_remove_campaign_leads(params: RemoveLeadsInput) -> str:
    """Bulk soft-delete a campaign's leads, optionally only those in given
    statuses. Dry run until ``confirm=true``; pause/stop the campaign first."""
    if params.status_filter == []:
        return "Error: status_filter=[] is ambiguous. Omit it to remove ALL leads, or list statuses."
    body = {"status_filter": params.status_filter} if params.status_filter else None
    return await execute(
        Route("DELETE", f"campaigns/{params.campaign_id}/leads/bulk", body=body, gated=True),
        confirm=params.confirm,
        response_format=params.response_format,
        title="Leads Removed",
    )


@mcp.tool(
    name="flowforge_manage_dispositions",
    annotations={
        "title": "Manage FlowForge Dispositions",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def flowforge_manage_dispositions(params: ManageDispositionsInput) -> str:
    """Manage per-campaign dispositions (labels classifying how calls ended)
    and the outcomes decision a never-run campaign needs before it can start.
    """
    action = params.action.value
    try:
        if params.action == DispositionAction.ORG_LIST:
            route = Route("GET", "calls/dispositions")
        else:
            base = f"campaigns/{require(params.campaign_id, 'campaign_id', action)}/dispositions"
            if params.action == DispositionAction.LIST:
                route = Route("GET", base)
            elif params.action == DispositionAction.CREATE:
                route = Route("POST", base, body=require(params.fields, "fields", action))
            elif params.action == DispositionAction.UPDATE:
                route = Route(
                    "PATCH",
                    f"{base}/{require(params.disposition_id, 'disposition_id', action)}",
                    body=require(params.fields, "fields", action),
                    keep_nulls=True,
                )
            elif params.action == DispositionAction.OUTCOMES_DECISION:
                route = Route("GET", f"{base}/outcomes-decision")
            else:
                route = Route("POST", f"{base}/keep-platform-defaults")
    except MissingInputError as error:
        return str(error)
    return await execute(route, confirm=False, response_format=params.response_format, title="Dispositions")


@mcp.tool(
    name="flowforge_list_campaign_calls",
    annotations={
        "title": "List FlowForge Campaign Calls",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowforge_list_campaign_calls(params: CampaignCallsInput) -> str:
    """List one campaign's calls with status/disposition/date/search filters.
    Use ``flowforge_get_call`` on a result for transcript and metrics.

    If the campaign-scoped endpoint fails server-side (it has returned 500 on
    some campaigns), falls back to the org call list filtered by
    ``campaign_id`` and says so in ``source``; ``disposition_id`` is not
    applied on the fallback.
    """
    query = {
        "status": params.status,
        "disposition_id": params.disposition_id,
        "date_from": params.date_from,
        "date_to": params.date_to,
        "search": params.search,
        "limit": params.limit,
        "offset": params.offset,
    }
    try:
        try:
            data = await api_request(f"campaigns/{params.campaign_id}/calls", params=query)
            return render(data, params.response_format, title="Campaign Calls")
        except FlowForgeHTTPError as error:
            if error.result.status < 500:
                raise
            fallback = await api_request(
                "calls/",
                params={
                    "campaign_id": params.campaign_id,
                    "status_filter": params.status,
                    "date_from": params.date_from,
                    "date_to": params.date_to,
                    "search": params.search,
                    "limit": params.limit,
                    "offset": params.offset,
                },
            )
            result = {
                "source": "fallback: GET /calls/?campaign_id= (campaign calls endpoint returned "
                f"{error.result.status}, request_id {error.result.request_id})",
                **(fallback if isinstance(fallback, dict) else {"calls": fallback}),
            }
            return render(result, params.response_format, title="Campaign Calls")
    except Exception as error:  # noqa: BLE001
        return format_error(error)
