"""Organization settings and MCP-server tooling for assistants.

* ``flowforge_update_organization`` - org fields, concurrency caps, and the
  org test phone number.
* ``flowforge_manage_mcp_servers`` - registry MCP servers enabled for the org,
  and custom MCP servers (add/test/call/delete) that assistants can attach via
  their ``mcp_servers`` list.
"""

from enum import Enum
from typing import Any, Optional

from pydantic import Field

from ..app import mcp
from ..models import FormatMixin
from ._dispatch import MissingInputError, Route, execute, require


def _server_ids(server_ids: Optional[list[str]], action: str) -> list[str]:
    """org_set accepts an empty list (disable all), so only None is missing."""
    if server_ids is None:
        raise MissingInputError(f"Error: action '{action}' requires 'server_ids' ([] disables all).")
    return server_ids


class OrgAction(str, Enum):
    UPDATE = "update"
    UPDATE_CONCURRENCY = "update_concurrency"
    GET_TEST_PHONE_NUMBER = "get_test_phone_number"
    SET_TEST_PHONE_NUMBER = "set_test_phone_number"


class UpdateOrganizationInput(FormatMixin):
    """Inputs for organization settings."""

    action: OrgAction = Field(..., description="Which org setting to read/change.")
    fields: Optional[dict[str, Any]] = Field(
        default=None,
        description=(
            "update: any of {'name','slug','mcp_servers','analytics_timezone',"
            "'max_outbound_concurrent','max_inbound_concurrent'}. "
            "update_concurrency: any of {'max_outbound_concurrent',"
            "'max_inbound_concurrent','max_web_concurrent'}."
        ),
    )
    test_phone_number_id: Optional[str] = Field(
        default=None, description="set_test_phone_number: owned number ID (null clears it)."
    )


class McpAction(str, Enum):
    CATALOG = "catalog"
    SERVER_TOOLS = "server_tools"
    ORG_LIST = "org_list"
    ORG_SET = "org_set"
    ORG_REMOVE = "org_remove"
    CUSTOM_LIST = "custom_list"
    CUSTOM_ADD = "custom_add"
    CUSTOM_TEST = "custom_test"
    CUSTOM_CALL = "custom_call"
    CUSTOM_DELETE = "custom_delete"


class ManageMcpServersInput(FormatMixin):
    """Inputs for MCP-server management."""

    action: McpAction = Field(
        ...,
        description=(
            "'catalog' (registry servers), 'server_tools' (tools of one server), "
            "'org_list'/'org_set'/'org_remove' (registry servers enabled for the "
            "org; org_set REPLACES the whole list), 'custom_list'/'custom_add'/"
            "'custom_test'/'custom_call'/'custom_delete' (your own MCP servers)."
        ),
    )
    server_id: Optional[str] = Field(
        default=None, description="server_tools/org_remove/custom_test/custom_call/custom_delete: server ID."
    )
    server_ids: Optional[list[str]] = Field(default=None, description="org_set: full list of enabled server IDs.")
    url: Optional[str] = Field(default=None, description="custom_add: MCP server URL (HTTP/SSE).")
    name: Optional[str] = Field(default=None, description="custom_add: display name.")
    prefix: Optional[str] = Field(default=None, description="custom_add: tool-name prefix exposed to assistants.")
    description: Optional[str] = Field(default=None, description="custom_add: description.")
    tool_name: Optional[str] = Field(default=None, description="custom_call: tool to invoke.")
    arguments: Optional[dict[str, Any]] = Field(default=None, description="custom_call: tool arguments.")
    confirm: bool = Field(
        default=False, description="Required true for org_set, org_remove, custom_call and custom_delete."
    )


@mcp.tool(
    name="flowforge_update_organization",
    annotations={
        "title": "Update FlowForge Organization",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowforge_update_organization(params: UpdateOrganizationInput) -> str:
    """Change organization settings and concurrency caps, or read/set the org
    test phone number (the number test calls ring). Read current values first
    with ``flowforge_get_organization`` include_concurrency=true."""
    action = params.action.value
    try:
        if params.action == OrgAction.UPDATE:
            route = Route("PATCH", "organisation/", body=require(params.fields, "fields", action), keep_nulls=True)
        elif params.action == OrgAction.UPDATE_CONCURRENCY:
            route = Route("PATCH", "organisation/concurrency", body=require(params.fields, "fields", action))
        elif params.action == OrgAction.GET_TEST_PHONE_NUMBER:
            route = Route("GET", "organisation/test-phone-number")
        else:
            route = Route(
                "PUT",
                "organisation/test-phone-number",
                body={"test_phone_number_id": params.test_phone_number_id},
                keep_nulls=True,  # null clears the test number
            )
    except MissingInputError as error:
        return str(error)
    return await execute(route, confirm=False, response_format=params.response_format, title="Organization")


@mcp.tool(
    name="flowforge_manage_mcp_servers",
    annotations={
        "title": "Manage FlowForge MCP Servers",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def flowforge_manage_mcp_servers(params: ManageMcpServersInput) -> str:
    """Manage the MCP servers FlowForge assistants can call mid-conversation.

    Attach a server to an assistant by adding its ID to the assistant's
    ``mcp_servers`` (``flowforge_update_assistant``). Use ``custom_test`` and
    ``custom_call`` to verify a custom server before attaching it.
    """
    action = params.action.value
    try:
        if params.action == McpAction.CATALOG:
            route = Route("GET", "mcp-tools/servers")
        elif params.action == McpAction.ORG_LIST:
            route = Route("GET", "mcp-tools/orgs/mcp-servers")
        elif params.action == McpAction.ORG_SET:
            route = Route(
                "PUT",
                "mcp-tools/orgs/mcp-servers",
                body=_server_ids(params.server_ids, action),
                gated=True,
            )
        elif params.action == McpAction.CUSTOM_LIST:
            route = Route("GET", "mcp-tools/custom")
        elif params.action == McpAction.CUSTOM_ADD:
            route = Route(
                "POST",
                "mcp-tools/custom",
                body={
                    "url": require(params.url, "url", action),
                    "name": params.name,
                    "prefix": params.prefix,
                    "description": params.description,
                },
            )
        else:
            server = require(params.server_id, "server_id", action)
            route = {
                McpAction.SERVER_TOOLS: lambda: Route("GET", f"mcp-tools/servers/{server}/tools"),
                McpAction.ORG_REMOVE: lambda: Route("DELETE", f"mcp-tools/orgs/mcp-servers/{server}", gated=True),
                McpAction.CUSTOM_TEST: lambda: Route("POST", f"mcp-tools/custom/{server}/test"),
                McpAction.CUSTOM_DELETE: lambda: Route("DELETE", f"mcp-tools/custom/{server}", gated=True),
                McpAction.CUSTOM_CALL: lambda: Route(
                    "POST",
                    f"mcp-tools/custom/{server}/call",
                    body={
                        "tool_name": require(params.tool_name, "tool_name", action),
                        "arguments": params.arguments or {},
                    },
                    gated=True,
                ),
            }[params.action]()
    except MissingInputError as error:
        return str(error)
    return await execute(route, confirm=params.confirm, response_format=params.response_format, title="MCP Servers")
