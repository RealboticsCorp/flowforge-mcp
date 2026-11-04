"""Tools for the FlowForge knowledge base.

Assistants can ground their answers in uploaded documents. These tools let an
agent search that knowledge (semantic or full-text) and list the available
documents.
"""

from typing import Optional

from pydantic import Field

from ..app import mcp
from ..client import api_request, format_error
from ..formatting import extract_items, paginated, render
from ..models import FormatMixin, PaginationParams


class SearchKnowledgeInput(FormatMixin):
    """Inputs for searching the knowledge base."""

    query: str = Field(
        ...,
        min_length=1,
        description="Semantic query text, or (with full_text=true) the literal/regex pattern to grep for.",
    )
    agent_id: Optional[str] = Field(
        default=None,
        description="Semantic mode only: restrict to documents linked to this assistant.",
    )
    document_ids: Optional[list[str]] = Field(
        default=None, description="Restrict the search to these document IDs."
    )
    full_text: bool = Field(
        default=False,
        description=(
            "When false (default), use semantic/vector search. When true, use "
            "exact full-text (grep-style) search."
        ),
    )
    limit: int = Field(default=8, ge=1, le=50, description="Semantic mode: maximum matches to return.")
    context_lines: int = Field(
        default=3, ge=0, le=20, description="Full-text mode: lines of context around each hit."
    )
    case_sensitive: bool = Field(default=False, description="Full-text mode: case-sensitive match.")


class ListDocumentsInput(PaginationParams):
    """Inputs for listing knowledge-base documents."""

    knowledge_base_id: Optional[str] = Field(
        default=None, description="Only documents in this knowledge base."
    )


@mcp.tool(
    name="flowforge_search_knowledge",
    annotations={
        "title": "Search FlowForge Knowledge Base",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowforge_search_knowledge(params: SearchKnowledgeInput) -> str:
    """Search the knowledge base by meaning (semantic) or exact text.

    Use semantic search (default) to find conceptually relevant passages, or
    set ``full_text=true`` for literal keyword matches. Optionally scope to one
    assistant's linked documents.

    Args:
        params: ``query`` (required), optional ``agent_id``, ``full_text`` flag,
            and ``limit``.

    Returns:
        JSON/Markdown with the matching passages/documents.

    Error Handling:
        Returns "Error: ..." on failure.
    """
    try:
        if params.full_text:
            endpoint = "knowledge/text-search"
            body = {
                "pattern": params.query,
                "document_ids": params.document_ids,
                "context_lines": params.context_lines,
                "case_sensitive": params.case_sensitive,
            }
        else:
            endpoint = "knowledge/search"
            body = {
                "query": params.query,
                "agent_id": params.agent_id,
                "document_ids": params.document_ids,
                "limit": params.limit,
            }
        data = await api_request(endpoint, method="POST", json=body)
        return render(data, params.response_format, title="Knowledge Search Results")
    except Exception as error:  # noqa: BLE001
        return format_error(error)


@mcp.tool(
    name="flowforge_list_documents",
    annotations={
        "title": "List FlowForge Knowledge Documents",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowforge_list_documents(params: ListDocumentsInput) -> str:
    """List documents in the knowledge base.

    Args:
        params: optional ``knowledge_base_id``, ``limit`` (1-100), ``offset``
            (rounded down to a multiple of ``limit``; the API pages by page
            number), ``response_format``.

    Returns:
        JSON/Markdown with pagination metadata and a ``documents`` array.

    Error Handling:
        Returns "Error: ..." on failure.
    """
    try:
        page = params.offset // params.limit + 1
        data = await api_request(
            "knowledge/documents",
            params={
                "knowledge_base_id": params.knowledge_base_id,
                "page": page,
                "page_size": params.limit,
            },
        )
        items, total = extract_items(data, preferred_key="documents")
        envelope = paginated(
            items,
            total=total,
            limit=params.limit,
            offset=(page - 1) * params.limit,
            item_key="documents",
        )
        return render(envelope, params.response_format, title="Knowledge Documents")
    except Exception as error:  # noqa: BLE001
        return format_error(error)
