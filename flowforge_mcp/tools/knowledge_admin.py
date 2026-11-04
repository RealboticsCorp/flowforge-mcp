"""Knowledge-base administration: documents and knowledge bases.

Complements ``knowledge.py`` (search/list). An assistant only searches its
documents at runtime when it has ``knowledge_base_id`` set (or documents
linked) AND ``enable_rag_tool=true`` - remind the user of the flag.
"""

from enum import Enum
from typing import Optional

from pydantic import Field

from ..app import mcp
from ..models import FormatMixin
from ._dispatch import MissingInputError, Route, execute, require
from .uploads import file_part


class DocumentAction(str, Enum):
    GET = "get"
    CONTENT = "content"
    UPLOAD = "upload"
    IMPORT_URL = "import_url"
    DELETE = "delete"
    LIST_FOR_AGENT = "list_for_agent"
    LINK_TO_AGENT = "link_to_agent"
    REINDEX = "reindex"


class ManageDocumentsInput(FormatMixin):
    """Inputs for knowledge-document operations."""

    action: DocumentAction = Field(
        ...,
        description=(
            "'get' (metadata), 'content' (extracted text), 'upload' (local file), "
            "'import_url' (crawl a web page), 'delete', 'list_for_agent', "
            "'link_to_agent', 'reindex' (re-embed; all docs when no IDs given)."
        ),
    )
    document_id: Optional[str] = Field(default=None, description="get/content/delete: document ID.")
    document_ids: Optional[list[str]] = Field(default=None, description="link_to_agent (required) / reindex (optional).")
    agent_id: Optional[str] = Field(default=None, description="list_for_agent/link_to_agent: assistant ID.")
    file_path: Optional[str] = Field(default=None, description="upload: local file path (PDF, DOCX, TXT, MD, ...).")
    url: Optional[str] = Field(default=None, description="import_url: page URL to ingest.")
    knowledge_base_id: Optional[str] = Field(
        default=None, description="upload/import_url: target knowledge base (org default when omitted)."
    )
    title: Optional[str] = Field(default=None, description="upload/import_url: document title.")
    source_url: Optional[str] = Field(default=None, description="upload: original source URL to record.")
    confirm: bool = Field(default=False, description="Required true for 'delete'.")


class KnowledgeBaseAction(str, Enum):
    LIST = "list"
    GET = "get"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class ManageKnowledgeBasesInput(FormatMixin):
    """Inputs for knowledge-base CRUD."""

    action: KnowledgeBaseAction = Field(..., description="'list', 'get', 'create', 'update' or 'delete'.")
    kb_id: Optional[str] = Field(default=None, description="get/update/delete: knowledge base ID.")
    name: Optional[str] = Field(default=None, description="create (required) / update: name (unique; 409 if taken).")
    description: Optional[str] = Field(default=None, description="create/update: description.")
    confirm: bool = Field(default=False, description="Required true for 'delete'.")


@mcp.tool(
    name="flowforge_manage_documents",
    annotations={
        "title": "Manage FlowForge Knowledge Documents",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def flowforge_manage_documents(params: ManageDocumentsInput) -> str:
    """Upload, import, read, delete, link and reindex knowledge documents.

    Typical flow: ``flowforge_manage_knowledge_bases`` create -> upload or
    import_url into it -> set the assistant's ``knowledge_base_id`` and
    ``enable_rag_tool=true`` -> verify with ``flowforge_search_knowledge``.
    """
    action = params.action.value
    try:
        if params.action == DocumentAction.UPLOAD:
            route = Route(
                "POST",
                "knowledge/documents/upload",
                query={
                    "knowledge_base_id": params.knowledge_base_id,
                    "title": params.title,
                    "source_url": params.source_url,
                },
                files=file_part(require(params.file_path, "file_path", action)),
            )
        elif params.action == DocumentAction.IMPORT_URL:
            route = Route(
                "POST",
                "knowledge/documents/import-url",
                body={
                    "url": require(params.url, "url", action),
                    "knowledge_base_id": params.knowledge_base_id,
                    "title": params.title,
                },
            )
        elif params.action == DocumentAction.REINDEX:
            route = Route("POST", "knowledge/reindex", body={"document_ids": params.document_ids})
        elif params.action in (DocumentAction.LIST_FOR_AGENT, DocumentAction.LINK_TO_AGENT):
            agent_docs = f"knowledge/agents/{require(params.agent_id, 'agent_id', action)}/documents"
            route = (
                Route("GET", agent_docs)
                if params.action == DocumentAction.LIST_FOR_AGENT
                else Route(
                    "POST",
                    agent_docs,
                    body={"document_ids": require(params.document_ids, "document_ids", action)},
                )
            )
        else:
            document = f"knowledge/documents/{require(params.document_id, 'document_id', action)}"
            route = {
                DocumentAction.GET: Route("GET", document),
                DocumentAction.CONTENT: Route("GET", f"{document}/content"),
                DocumentAction.DELETE: Route("DELETE", document, gated=True),
            }[params.action]
    except MissingInputError as error:
        return str(error)
    return await execute(route, confirm=params.confirm, response_format=params.response_format, title="Knowledge Documents")


@mcp.tool(
    name="flowforge_manage_knowledge_bases",
    annotations={
        "title": "Manage FlowForge Knowledge Bases",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def flowforge_manage_knowledge_bases(params: ManageKnowledgeBasesInput) -> str:
    """List, read, create, rename or delete knowledge bases (named groups of
    documents an assistant points at via ``knowledge_base_id``)."""
    action = params.action.value
    base = "knowledge/knowledge-bases"
    try:
        if params.action == KnowledgeBaseAction.LIST:
            route = Route("GET", base)
        elif params.action == KnowledgeBaseAction.CREATE:
            route = Route(
                "POST",
                base,
                body={"name": require(params.name, "name", action), "description": params.description},
            )
        else:
            kb = f"{base}/{require(params.kb_id, 'kb_id', action)}"
            route = {
                KnowledgeBaseAction.GET: Route("GET", kb),
                KnowledgeBaseAction.UPDATE: Route(
                    "PATCH",
                    kb,
                    body=require(
                        {k: v for k, v in (("name", params.name), ("description", params.description)) if v is not None},
                        "name or description",
                        action,
                    ),
                ),
                KnowledgeBaseAction.DELETE: Route("DELETE", kb, gated=True),
            }[params.action]
    except MissingInputError as error:
        return str(error)
    return await execute(route, confirm=params.confirm, response_format=params.response_format, title="Knowledge Bases")
