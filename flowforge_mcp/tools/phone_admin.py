"""Phone-number administration and phone pools.

Complements ``phone_numbers.py`` (list/search/assign): read one number,
rename, buy, release, look up supported countries/area codes, and manage
pools that rotate caller ID across a campaign's calls.
"""

from enum import Enum
from typing import Any, Optional

from pydantic import Field

from ..app import mcp
from ..models import FormatMixin
from ._dispatch import MissingInputError, Route, execute, require


class PhoneNumberAction(str, Enum):
    GET = "get"
    RENAME = "rename"
    PURCHASE = "purchase"
    RELEASE = "release"
    COUNTRIES = "countries"
    AREA_CODES = "area_codes"


class ManagePhoneNumberInput(FormatMixin):
    """Inputs for single phone-number administration."""

    action: PhoneNumberAction = Field(
        ...,
        description=(
            "'get', 'rename' (friendly name), 'purchase' (buys a number - costs "
            "money), 'release' (gives the number up - irreversible), "
            "'countries' (supported countries), 'area_codes' (for one country)."
        ),
    )
    phone_number_id: Optional[str] = Field(default=None, description="Owned number ID (get/rename/release).")
    phone_number: Optional[str] = Field(
        default=None, description="purchase: E.164 number from flowforge_search_phone_numbers."
    )
    capabilities: list[str] = Field(
        default_factory=lambda: ["voice"],
        description="purchase: capabilities to buy, e.g. ['voice'] or ['voice', 'sms'].",
    )
    friendly_name: Optional[str] = Field(default=None, description="purchase/rename: display label.")
    country_code: Optional[str] = Field(default=None, description="area_codes: ISO country code, e.g. 'US'.")
    confirm: bool = Field(default=False, description="Required true for 'purchase' and 'release'.")


class PoolAction(str, Enum):
    LIST = "list"
    GET = "get"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ADD_MEMBER = "add_member"
    REMOVE_MEMBER = "remove_member"
    NEXT_PHONE = "next_phone"
    STATISTICS = "statistics"


class ManagePhonePoolsInput(FormatMixin):
    """Inputs for phone-pool management."""

    action: PoolAction = Field(..., description="Pool operation to perform.")
    pool_id: Optional[str] = Field(default=None, description="Pool ID (all actions except list/create).")
    phone_number_id: Optional[str] = Field(default=None, description="add_member/remove_member: owned number ID.")
    weight: int = Field(default=1, ge=1, description="add_member: weight for 'weighted' distribution.")
    priority: int = Field(default=0, description="add_member: priority within the pool.")
    fields: Optional[dict[str, Any]] = Field(
        default=None,
        description=(
            "create: {'name'*, 'description', 'distribution_strategy' "
            "(round_robin|weighted|least_used|random|local_presence), "
            "'custom_sip_trunk_id', 'phone_number_ids': [...]}. update: any of "
            "name, description, distribution_strategy, custom_sip_trunk_id, is_active."
        ),
    )
    confirm: bool = Field(default=False, description="Required true for 'delete' and 'remove_member'.")


@mcp.tool(
    name="flowforge_manage_phone_number",
    annotations={
        "title": "Manage FlowForge Phone Number",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def flowforge_manage_phone_number(params: ManagePhoneNumberInput) -> str:
    """Read, rename, buy or release one phone number; list supported countries
    and area codes. Buying and releasing return a dry run until
    ``confirm=true`` - confirm the number and cost with the user first.
    """
    action = params.action.value
    try:
        if params.action == PhoneNumberAction.COUNTRIES:
            route = Route("GET", "phone-numbers/countries")
        elif params.action == PhoneNumberAction.AREA_CODES:
            route = Route("GET", f"phone-numbers/area-codes/{require(params.country_code, 'country_code', action)}")
        elif params.action == PhoneNumberAction.PURCHASE:
            route = Route(
                "POST",
                "phone-numbers/purchase",
                body={
                    "phone_number": require(params.phone_number, "phone_number", action),
                    "capabilities": params.capabilities,
                    "friendly_name": params.friendly_name,
                },
                gated=True,
            )
        else:
            number = f"phone-numbers/{require(params.phone_number_id, 'phone_number_id', action)}"
            if params.action == PhoneNumberAction.GET:
                route = Route("GET", number)
            elif params.action == PhoneNumberAction.RENAME:
                route = Route("PATCH", number, body={"friendly_name": require(params.friendly_name, "friendly_name", action)})
            else:
                route = Route("DELETE", number, gated=True)
    except MissingInputError as error:
        return str(error)
    return await execute(route, confirm=params.confirm, response_format=params.response_format, title="Phone Number")


@mcp.tool(
    name="flowforge_manage_phone_pools",
    annotations={
        "title": "Manage FlowForge Phone Pools",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def flowforge_manage_phone_pools(params: ManagePhonePoolsInput) -> str:
    """List/create/update/delete phone pools, add or remove member numbers,
    peek the next number the pool would dial from, or read pool statistics.

    Attach a pool to a campaign via ``flowforge_update_campaign_settings``
    (``phone_pool_id``) to rotate caller ID.
    """
    action = params.action.value
    try:
        if params.action == PoolAction.LIST:
            route = Route("GET", "phone-pools/")
        elif params.action == PoolAction.CREATE:
            route = Route("POST", "phone-pools/", body=require(params.fields, "fields", action))
        else:
            pool = f"phone-pools/{require(params.pool_id, 'pool_id', action)}"
            routes = {
                PoolAction.GET: lambda: Route("GET", pool),
                PoolAction.UPDATE: lambda: Route(
                    "PATCH", pool, body=require(params.fields, "fields", action), keep_nulls=True
                ),
                PoolAction.DELETE: lambda: Route("DELETE", pool, gated=True),
                PoolAction.NEXT_PHONE: lambda: Route("GET", f"{pool}/next-phone"),
                PoolAction.STATISTICS: lambda: Route("GET", f"{pool}/statistics"),
                PoolAction.ADD_MEMBER: lambda: Route(
                    "POST",
                    f"{pool}/members",
                    body={
                        "phone_number_id": require(params.phone_number_id, "phone_number_id", action),
                        "weight": params.weight,
                        "priority": params.priority,
                    },
                ),
                PoolAction.REMOVE_MEMBER: lambda: Route(
                    "DELETE",
                    f"{pool}/members/{require(params.phone_number_id, 'phone_number_id', action)}",
                    gated=True,
                ),
            }
            route = routes[params.action]()
    except MissingInputError as error:
        return str(error)
    return await execute(route, confirm=params.confirm, response_format=params.response_format, title="Phone Pools")
