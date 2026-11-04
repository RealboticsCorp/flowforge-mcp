"""Assistant configuration beyond the core record: pronunciations, branches,
and export/import.

* Pronunciations - per-assistant TTS dictionary (written -> spoken / IPA).
* Branches - named config variants with their own version history (Main plus
  forks used for A/B tests and safe iteration).
* Import - recreate an assistant from ``flowforge_get_assistant`` with
  ``include=['export']`` output (e.g. to copy between orgs/keys).
"""

from enum import Enum
from typing import Any, Optional

from pydantic import Field

from ..app import mcp
from ..models import FormatMixin
from ._dispatch import MissingInputError, Route, execute, require

_WRITE = {
    "readOnlyHint": False,
    "destructiveHint": True,
    "idempotentHint": False,
    "openWorldHint": True,
}


class PronunciationAction(str, Enum):
    LIST = "list"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class ManagePronunciationsInput(FormatMixin):
    """Inputs for the pronunciation dictionary of one assistant."""

    assistant_id: str = Field(..., min_length=1, description="Assistant whose dictionary to manage.")
    action: PronunciationAction = Field(..., description="'list', 'create', 'update' or 'delete'.")
    pronunciation_id: Optional[str] = Field(default=None, description="Entry ID (update/delete).")
    fields: Optional[dict[str, Any]] = Field(
        default=None,
        description=(
            "create/update body: {'written'*: 'FlowForge', 'spoken'*: 'flow forge', "
            "'ipa', 'case_sensitive' (false), 'match_whole_word' (true), "
            "'priority' (0), 'enabled' (true)}. * = required on create. "
            "A duplicate 'written' word returns 409."
        ),
    )
    confirm: bool = Field(default=False, description="Required true for 'delete'.")


class BranchAction(str, Enum):
    LIST = "list"
    GET = "get"
    CREATE = "create"
    UPDATE = "update"


class ManageBranchesInput(FormatMixin):
    """Inputs for assistant branches."""

    assistant_id: str = Field(..., min_length=1, description="Assistant whose branches to manage.")
    action: BranchAction = Field(..., description="'list', 'get', 'create' or 'update'.")
    branch_id: Optional[str] = Field(default=None, description="Branch ID (get/update).")
    version: Optional[str] = Field(
        default=None, description="get: version number to read, or 'tip' (default) for the latest."
    )
    fields: Optional[dict[str, Any]] = Field(
        default=None,
        description=(
            "create: {'name'*, 'description', 'source_branch_id', 'source_version'} "
            "(forks Main when no source given). update: any assistant config "
            "field to change on that branch (system_prompt, model, temperature, "
            "tts_settings, stt_settings, first_message, webhook_tools, "
            "knowledge_base_id, enable_rag_tool, ...)."
        ),
    )


class ImportAssistantInput(FormatMixin):
    """Inputs for importing an exported assistant bundle."""

    data: dict[str, Any] = Field(
        ...,
        description=(
            "The exported assistant JSON (from flowforge_get_assistant "
            "include=['export']). Requires name, slug, model at minimum."
        ),
    )
    name_override: Optional[str] = Field(default=None, description="Name for the new assistant.")
    slug_override: Optional[str] = Field(default=None, description="Slug for the new assistant.")
    import_character: bool = Field(default=True, description="Recreate the embedded character.")
    import_role: bool = Field(default=True, description="Recreate the embedded role.")
    import_flow: bool = Field(default=True, description="Recreate the embedded flow.")


@mcp.tool(name="flowforge_manage_pronunciations", annotations={"title": "Manage Assistant Pronunciations", **_WRITE})
async def flowforge_manage_pronunciations(params: ManagePronunciationsInput) -> str:
    """List, create, update or delete an assistant's pronunciation entries
    (how TTS should say a written word - brand names, acronyms, surnames).

    Returns:
        The API result; ``delete`` without ``confirm=true`` returns a dry run.
    """
    base = f"assistants/{params.assistant_id}/pronunciations"
    action = params.action.value
    try:
        if params.action == PronunciationAction.LIST:
            route = Route("GET", base)
        elif params.action == PronunciationAction.CREATE:
            route = Route("POST", base, body=require(params.fields, "fields", action))
        else:
            entry = f"{base}/{require(params.pronunciation_id, 'pronunciation_id', action)}"
            route = (
                Route("PATCH", entry, body=require(params.fields, "fields", action), keep_nulls=True)
                if params.action == PronunciationAction.UPDATE
                else Route("DELETE", entry, gated=True)
            )
    except MissingInputError as error:
        return str(error)
    return await execute(route, confirm=params.confirm, response_format=params.response_format, title="Pronunciations")


@mcp.tool(name="flowforge_manage_branches", annotations={"title": "Manage Assistant Branches", **_WRITE, "destructiveHint": False})
async def flowforge_manage_branches(params: ManageBranchesInput) -> str:
    """List, read, create (fork) or update an assistant's branches.

    Use a branch to change prompt/voice/model without touching Main, then run
    tests against it (``flowforge_run_test`` with ``branch_id``) before
    promoting. Updating a branch creates a new version on it.
    """
    base = f"assistants/{params.assistant_id}/branches"
    action = params.action.value
    try:
        if params.action == BranchAction.LIST:
            route = Route("GET", base)
        elif params.action == BranchAction.CREATE:
            route = Route("POST", base, body=require(params.fields, "fields", action))
        else:
            branch = f"{base}/{require(params.branch_id, 'branch_id', action)}"
            route = (
                Route("GET", branch, query={"version": params.version})
                if params.action == BranchAction.GET
                else Route("PATCH", branch, body=require(params.fields, "fields", action), keep_nulls=True)
            )
    except MissingInputError as error:
        return str(error)
    return await execute(route, confirm=False, response_format=params.response_format, title="Assistant Branches")


@mcp.tool(
    name="flowforge_import_assistant",
    annotations={"title": "Import FlowForge Assistant", **_WRITE, "destructiveHint": False},
)
async def flowforge_import_assistant(params: ImportAssistantInput) -> str:
    """Create a new assistant from an exported bundle (with its character,
    role and flow). Pair with ``flowforge_get_assistant`` include=['export']
    to copy an assistant - including across orgs, using a different server
    (e.g. export from ``flowforge``, import via ``flowforge-acme``).

    Returns:
        The created assistant (with its new ID).
    """
    body = {
        "data": params.data,
        "name_override": params.name_override,
        "slug_override": params.slug_override,
        "import_character": params.import_character,
        "import_role": params.import_role,
        "import_flow": params.import_flow,
    }
    return await execute(
        Route("POST", "assistants/import", body=body),
        confirm=False,
        response_format=params.response_format,
        title="Imported Assistant",
    )
