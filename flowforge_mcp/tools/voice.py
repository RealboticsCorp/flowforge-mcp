"""Voice catalog and voice cloning.

Read the provider/voice catalog before setting an assistant's
``tts_settings`` / ``stt_settings`` so provider, model and voice IDs are valid.
"""

from enum import Enum
from typing import Optional

from pydantic import Field

from ..app import mcp
from ..models import FormatMixin
from ._dispatch import MissingInputError, Route, execute, require
from .uploads import file_part


class VoiceCatalog(str, Enum):
    SUMMARY = "summary"
    TTS = "tts"
    STT = "stt"
    PRESETS = "presets"
    AGENT_PRESETS = "agent-presets"
    CLONED = "cloned"


class VoiceCatalogInput(FormatMixin):
    """Inputs for reading the voice catalog."""

    catalog: VoiceCatalog = Field(
        default=VoiceCatalog.SUMMARY,
        description=(
            "'summary' (providers overview - start here), 'tts' (TTS providers, "
            "models, voices), 'stt' (transcription providers/models), 'presets' "
            "(curated voice presets), 'agent-presets' (full agent voice bundles), "
            "'cloned' (your cloned voices)."
        ),
    )
    provider: Optional[str] = Field(default=None, description="'cloned' only: filter by clone provider.")


class CloneAction(str, Enum):
    CREATE = "create"
    DELETE = "delete"


class CloneVoiceInput(FormatMixin):
    """Inputs for creating or deleting a cloned voice."""

    action: CloneAction = Field(..., description="'create' (upload reference audio) or 'delete'.")
    file_path: Optional[str] = Field(default=None, description="create: local path to reference audio (<= 50 MB).")
    name: Optional[str] = Field(default=None, description="create: display name for the voice.")
    provider: str = Field(default="chatterbox", description="create: 'chatterbox' (default) or 'orpheus'.")
    voice_id: Optional[str] = Field(default=None, description="delete: cloned voice ID.")
    confirm: bool = Field(default=False, description="Required true for 'delete'.")


@mcp.tool(
    name="flowforge_voice_catalog",
    annotations={
        "title": "FlowForge Voice Catalog",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowforge_voice_catalog(params: VoiceCatalogInput) -> str:
    """Read the TTS/STT provider catalog, voice presets, or your cloned voices.

    Use it to pick valid ``tts_settings``/``stt_settings`` values for
    ``flowforge_create_assistant`` / ``flowforge_update_assistant``. To hear a
    voice, POST /voice/preview via ``flowforge_api_request``.
    """
    if params.catalog == VoiceCatalog.CLONED:
        route = Route("GET", "voice/cloning/voices", query={"provider": params.provider})
    else:
        route = Route("GET", f"voice/{params.catalog.value}")
    return await execute(route, confirm=False, response_format=params.response_format, title="Voice Catalog")


@mcp.tool(
    name="flowforge_clone_voice",
    annotations={
        "title": "Clone or Delete a FlowForge Voice",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def flowforge_clone_voice(params: CloneVoiceInput) -> str:
    """Create a cloned voice from a local reference-audio file, or delete one.

    Only clone a voice the user has the right to use. The new voice appears
    in ``flowforge_voice_catalog`` catalog='cloned'.
    """
    action = params.action.value
    try:
        if params.action == CloneAction.DELETE:
            route = Route(
                "DELETE",
                f"voice/cloning/voices/{require(params.voice_id, 'voice_id', action)}",
                gated=True,
            )
            return await execute(route, confirm=params.confirm, response_format=params.response_format, title="Cloned Voice")
        route = Route(
            "POST",
            "voice/cloning/voices",
            files=file_part(require(params.file_path, "file_path", action)),
            form={"name": require(params.name, "name", action), "provider": params.provider},
        )
    except MissingInputError as error:
        return str(error)
    return await execute(route, confirm=False, response_format=params.response_format, title="Cloned Voice")
