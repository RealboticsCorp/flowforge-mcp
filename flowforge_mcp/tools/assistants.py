"""Tools for managing FlowForge assistants (voice agents).

An *assistant* is the configured AI agent that handles a phone call: its
prompt/flow, LLM model, voice (TTS) and transcription (STT) settings. These
tools cover the full lifecycle: list, inspect, create, update, delete, and the
clone/publish lifecycle actions.
"""

from enum import Enum
from typing import Any, Optional

from pydantic import Field

from ..app import mcp
from ..client import api_request, format_error
from ..formatting import local_page, render
from ..models import FormatMixin, PaginationParams, StrictModel


class AssistantLifecycleAction(str, Enum):
    """Non-destructive lifecycle action to run against an assistant."""

    CLONE = "clone"
    PUBLISH = "publish"


class AssistantInclude(str, Enum):
    """Assistant sub-resources fetchable alongside the assistant itself."""

    PROMPT_VARIABLES = "prompt-variables"
    FLOW = "flow"
    KNOWLEDGE_BASE = "knowledge-base"
    STATS = "stats"
    EXPORT = "export"


class ListAssistantsInput(PaginationParams):
    """Inputs for listing assistants."""


class GetAssistantInput(FormatMixin):
    """Inputs for retrieving one assistant."""

    assistant_id: str = Field(
        ...,
        min_length=1,
        description="ID of the assistant to retrieve (e.g. a UUID string).",
    )
    detailed: bool = Field(
        default=False,
        description=(
            "When true, fetch the comprehensive configuration (flow, voice, "
            "tools); when false, return the standard summary."
        ),
    )
    include: list[AssistantInclude] = Field(
        default_factory=list,
        description=(
            "Extra sub-resources to fetch in the same step: 'prompt-variables' "
            "({{vars}} the prompt expects), 'flow' (React Flow graph), "
            "'knowledge-base' (linked docs/KB), 'stats' (call stats), 'export' "
            "(portable JSON for flowforge_import_assistant)."
        ),
    )


class CreateAssistantInput(FormatMixin):
    """Inputs for creating an assistant. Only ``name`` is required; the rest map
    directly to optional fields on the FlowForge AssistantCreateRequest."""

    name: str = Field(..., min_length=1, max_length=200, description="Display name for the assistant.")
    description: Optional[str] = Field(default=None, description="Optional human description.")
    system_prompt: Optional[str] = Field(
        default=None,
        description="System prompt for a simple (single-prompt) agent.",
    )
    first_message: Optional[str] = Field(
        default=None,
        description="The first thing the agent says, if it speaks first.",
    )
    agent_speak_first: Optional[bool] = Field(
        default=None,
        description="Whether the agent speaks before the other party.",
    )
    model: Optional[str] = Field(
        default=None,
        description="LLM model to use (e.g. 'gpt-4o-mini', the FlowForge default).",
    )
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="LLM sampling temperature (0.0-2.0).",
    )
    tts_settings: Optional[dict[str, Any]] = Field(
        default=None,
        description="Text-to-speech config, e.g. {'provider': '...', 'voice': '...'}.",
    )
    stt_settings: Optional[dict[str, Any]] = Field(
        default=None,
        description="Speech-to-text config, e.g. {'provider': '...', 'model': '...'}.",
    )
    mcp_servers: Optional[list[str]] = Field(
        default=None,
        description="IDs of MCP tool servers to attach to the assistant.",
    )
    extra_config: Optional[dict[str, Any]] = Field(
        default=None,
        description=(
            "Escape hatch for any other AssistantCreateRequest field not listed "
            "above (e.g. flow_data, backchannels_enabled, webhook_tools). Merged "
            "into the request body verbatim."
        ),
    )


class UpdateAssistantInput(FormatMixin):
    """Inputs for updating an assistant. Provide only the fields to change."""

    assistant_id: str = Field(..., min_length=1, description="ID of the assistant to update.")
    fields: dict[str, Any] = Field(
        ...,
        description=(
            "Object of fields to change, using the same field names as create "
            "(e.g. {'system_prompt': '...', 'temperature': 0.5}). Only the keys "
            "you include are modified."
        ),
    )


class DeleteAssistantInput(StrictModel):
    """Inputs for deleting an assistant."""

    assistant_id: str = Field(..., min_length=1, description="ID of the assistant to delete.")


class AssistantLifecycleInput(FormatMixin):
    """Inputs for a clone/publish lifecycle action."""

    assistant_id: str = Field(..., min_length=1, description="ID of the target assistant.")
    action: AssistantLifecycleAction = Field(
        ...,
        description="'clone' to duplicate the assistant, 'publish' to deploy it live.",
    )


@mcp.tool(
    name="flowforge_list_assistants",
    annotations={
        "title": "List FlowForge Assistants",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowforge_list_assistants(params: ListAssistantsInput) -> str:
    """List the voice assistants (agents) in your FlowForge organization.

    Use this to discover assistant IDs before starting calls, creating
    campaigns, or assigning phone numbers. Returns a page of assistants plus
    pagination metadata.

    Args:
        params: ``limit`` (1-100, default 50), ``offset`` (default 0),
            ``response_format`` ('json' or 'markdown').

    Returns:
        JSON (or Markdown) with ``total``, ``count``, ``offset``, ``has_more``,
        ``next_offset`` and an ``assistants`` array. Each assistant object's
        exact fields are defined by the API but include at least an id and name.

    Error Handling:
        Returns "Error: ..." with the cause (e.g. 401 invalid key) on failure.
    """
    try:
        # The endpoint returns every assistant; page client-side.
        data = await api_request("assistants/")
        envelope = local_page(
            data, preferred_key="assistants", limit=params.limit, offset=params.offset
        )
        return render(envelope, params.response_format, title="FlowForge Assistants")
    except Exception as error:  # noqa: BLE001 - translated for the agent
        return format_error(error)


@mcp.tool(
    name="flowforge_get_assistant",
    annotations={
        "title": "Get FlowForge Assistant",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowforge_get_assistant(params: GetAssistantInput) -> str:
    """Retrieve a single assistant's configuration by ID, optionally with its
    prompt variables, flow, knowledge base, stats, or export bundle.

    Args:
        params: ``assistant_id`` (required), ``detailed`` (full config when
            true), ``include`` (sub-resources), ``response_format``.

    Returns:
        The assistant object; with ``include``, an object keyed ``assistant``
        plus one key per sub-resource (a failed sub-fetch holds its error).

    Error Handling:
        Returns "Error: Resource not found..." if the ID is wrong.
    """
    try:
        suffix = "/detailed" if params.detailed else ""
        data = await api_request(f"assistants/{params.assistant_id}{suffix}")
        if not params.include:
            return render(data, params.response_format, title="Assistant")
        result: dict[str, Any] = {"assistant": data}
        for include in params.include:
            try:
                result[include.value] = await api_request(
                    f"assistants/{params.assistant_id}/{include.value}"
                )
            except Exception as sub_error:  # noqa: BLE001 - isolate per-include failures
                result[include.value] = {"error": format_error(sub_error)}
        return render(result, params.response_format, title="Assistant")
    except Exception as error:  # noqa: BLE001
        return format_error(error)


@mcp.tool(
    name="flowforge_create_assistant",
    annotations={
        "title": "Create FlowForge Assistant",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def flowforge_create_assistant(params: CreateAssistantInput) -> str:
    """Create a new voice assistant (agent).

    Only ``name`` is required. Provide ``system_prompt`` for a simple agent, or
    pass ``extra_config={'flow_data': {...}}`` for a flow-based agent. Voice and
    transcription are configured via ``tts_settings`` / ``stt_settings``.

    Args:
        params: See field descriptions. ``extra_config`` accepts any additional
            AssistantCreateRequest field verbatim.

    Returns:
        The created assistant object (including its new ID) as JSON or Markdown.

    Error Handling:
        Returns "Error: Validation failed..." (422) if fields are malformed.
    """
    try:
        body: dict[str, Any] = {
            "name": params.name,
            "description": params.description,
            "system_prompt": params.system_prompt,
            "first_message": params.first_message,
            "agent_speak_first": params.agent_speak_first,
            "model": params.model,
            "temperature": params.temperature,
            "tts_settings": params.tts_settings,
            "stt_settings": params.stt_settings,
            "mcp_servers": params.mcp_servers,
        }
        if params.extra_config:
            body.update(params.extra_config)
        data = await api_request("assistants/", method="POST", json=body)
        return render(data, params.response_format, title="Created Assistant")
    except Exception as error:  # noqa: BLE001
        return format_error(error)


@mcp.tool(
    name="flowforge_update_assistant",
    annotations={
        "title": "Update FlowForge Assistant",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowforge_update_assistant(params: UpdateAssistantInput) -> str:
    """Update an existing assistant. Only the fields you supply are changed.

    Args:
        params: ``assistant_id`` and a ``fields`` object of changes.

    Returns:
        The updated assistant object as JSON or Markdown.

    Error Handling:
        Returns "Error: Resource not found..." if the ID is wrong.
    """
    try:
        data = await api_request(
            f"assistants/{params.assistant_id}",
            method="PATCH",
            json=params.fields,
            drop_none=False,  # explicit nulls clear fields (e.g. knowledge_base_id)
        )
        return render(data, params.response_format, title="Updated Assistant")
    except Exception as error:  # noqa: BLE001
        return format_error(error)


@mcp.tool(
    name="flowforge_delete_assistant",
    annotations={
        "title": "Delete FlowForge Assistant",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowforge_delete_assistant(params: DeleteAssistantInput) -> str:
    """Permanently delete an assistant. This cannot be undone.

    Args:
        params: ``assistant_id`` of the assistant to delete.

    Returns:
        A confirmation message on success.

    Error Handling:
        Returns "Error: Resource not found..." if the ID is wrong.
    """
    try:
        await api_request(f"assistants/{params.assistant_id}", method="DELETE")
        return f"Deleted assistant {params.assistant_id}."
    except Exception as error:  # noqa: BLE001
        return format_error(error)


@mcp.tool(
    name="flowforge_assistant_lifecycle",
    annotations={
        "title": "Clone or Publish Assistant",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def flowforge_assistant_lifecycle(params: AssistantLifecycleInput) -> str:
    """Run a lifecycle action on an assistant: clone it or publish it live.

    'clone' creates an independent copy (useful for safe iteration); 'publish'
    deploys the current configuration so it answers real calls.

    Args:
        params: ``assistant_id`` and ``action`` ('clone' or 'publish').

    Returns:
        The API result (e.g. the new clone's object, or publish status).

    Error Handling:
        Returns "Error: ..." with the cause on failure.
    """
    try:
        data = await api_request(
            f"assistants/{params.assistant_id}/{params.action.value}", method="POST"
        )
        return render(data, params.response_format, title=f"Assistant {params.action.value.title()}")
    except Exception as error:  # noqa: BLE001
        return format_error(error)
