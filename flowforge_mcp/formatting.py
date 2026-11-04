"""Response formatting helpers shared across all tools.

Provides the ``ResponseFormat`` enum, a generic Markdown renderer that copes
with the FlowForge API's loosely-typed (``additionalProperties``) responses,
JSON serialization, and a uniform pagination wrapper. Centralizing this keeps
every tool's output consistent and prevents duplicated formatting logic.
"""

import json
from enum import Enum
from typing import Any, Optional


class ResponseFormat(str, Enum):
    """Output format for tool responses.

    ``json`` preserves every field for programmatic use (the safe default for
    this API's loosely-typed objects). ``markdown`` produces a compact,
    human-readable summary.
    """

    JSON = "json"
    MARKDOWN = "markdown"


def to_json(data: Any) -> str:
    """Serialize ``data`` to indented JSON with stable key ordering."""
    return json.dumps(data, indent=2, ensure_ascii=False, default=str)


def render(data: Any, response_format: ResponseFormat, *, title: Optional[str] = None) -> str:
    """Render ``data`` as JSON or Markdown.

    Args:
        data: Any JSON-serializable structure returned by the API.
        response_format: Desired output format.
        title: Optional heading used only for the Markdown rendering.

    Returns:
        The formatted string.
    """
    if response_format == ResponseFormat.MARKDOWN:
        return _to_markdown(data, title=title)
    return to_json(data)


def paginated(
    items: list[Any],
    *,
    total: Optional[int],
    limit: int,
    offset: int,
    item_key: str = "items",
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Build a standard pagination envelope around a page of results.

    Args:
        items: The page of results.
        total: Total number of results available (``None`` if unknown).
        limit: Page size that was requested.
        offset: Offset that was requested.
        item_key: Key under which to place ``items`` (e.g. "calls").
        extra: Additional top-level fields to merge in.

    Returns:
        A dict with ``total``, ``count``, ``offset``, ``has_more``,
        ``next_offset`` and the items under ``item_key``.
    """
    count = len(items)
    if total is not None:
        has_more = (offset + count) < total
    else:
        # Heuristic when the API omits a total: a full page implies more.
        has_more = count >= limit
    envelope: dict[str, Any] = {
        "total": total,
        "count": count,
        "offset": offset,
        "has_more": has_more,
        "next_offset": offset + count if has_more else None,
        item_key: items,
    }
    if extra:
        envelope.update(extra)
    return envelope


def local_page(
    response: Any, *, preferred_key: str, limit: int, offset: int
) -> dict[str, Any]:
    """Paginate client-side for endpoints that ignore limit/offset.

    Assistants, campaigns, phone numbers, tests and pools return the whole
    collection in one response (hundreds of rows on busy orgs). Slicing here
    keeps tool output within an agent's context budget while preserving the
    standard ``total``/``has_more``/``next_offset`` envelope.
    """
    items, _ = extract_items(response, preferred_key=preferred_key)
    page = items[offset : offset + limit]
    return paginated(page, total=len(items), limit=limit, offset=offset, item_key=preferred_key)


def extract_items(
    response: Any, *, preferred_key: Optional[str] = None
) -> tuple[list[Any], Optional[int]]:
    """Pull a list of items and a total count out of a list-endpoint response.

    The FlowForge API returns list payloads in a few shapes (a bare array, or a
    dict wrapping the array under a key such as ``calls``/``items``/``data``
    plus a ``total``). This normalizes them so list tools share one code path.

    Args:
        response: The raw decoded API response.
        preferred_key: A resource-specific key to check first (e.g. "calls").

    Returns:
        A ``(items, total)`` tuple. ``total`` is ``None`` when the API does not
        report one.
    """
    if isinstance(response, list):
        return response, len(response)

    if not isinstance(response, dict):
        return [], None

    total = response.get("total")
    total = total if isinstance(total, int) else None

    keys = [preferred_key] if preferred_key else []
    keys += ["items", "data", "results", "records"]
    for key in keys:
        if key and isinstance(response.get(key), list):
            return response[key], total

    # Fall back to the first list-valued field present.
    for value in response.values():
        if isinstance(value, list):
            return value, total
    return [], total


def _to_markdown(data: Any, *, title: Optional[str], depth: int = 0) -> str:
    """Recursively render arbitrary JSON-like data as readable Markdown."""
    lines: list[str] = []
    if title and depth == 0:
        lines.append(f"# {title}")
        lines.append("")

    if isinstance(data, dict):
        lines.append(_dict_to_markdown(data, depth=depth))
    elif isinstance(data, list):
        lines.append(_list_to_markdown(data, depth=depth))
    else:
        lines.append(_scalar(data))

    return "\n".join(line for line in lines if line is not None).strip() or "_(empty)_"


def _dict_to_markdown(data: dict[str, Any], *, depth: int) -> str:
    if not data:
        return "_(empty object)_"
    lines: list[str] = []
    indent = "  " * depth
    for key, value in data.items():
        label = f"**{_humanize(key)}**"
        if isinstance(value, dict):
            lines.append(f"{indent}- {label}:")
            lines.append(_dict_to_markdown(value, depth=depth + 1))
        elif isinstance(value, list):
            lines.append(f"{indent}- {label}:")
            lines.append(_list_to_markdown(value, depth=depth + 1))
        else:
            lines.append(f"{indent}- {label}: {_scalar(value)}")
    return "\n".join(lines)


def _list_to_markdown(data: list[Any], *, depth: int) -> str:
    if not data:
        return "  " * depth + "- _(none)_"
    lines: list[str] = []
    indent = "  " * depth
    for index, item in enumerate(data, start=1):
        if isinstance(item, dict):
            lines.append(f"{indent}- Item {index}:")
            lines.append(_dict_to_markdown(item, depth=depth + 1))
        elif isinstance(item, list):
            lines.append(f"{indent}- Item {index}:")
            lines.append(_list_to_markdown(item, depth=depth + 1))
        else:
            lines.append(f"{indent}- {_scalar(item)}")
    return "\n".join(lines)


def _scalar(value: Any) -> str:
    if value is None:
        return "_null_"
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def _humanize(key: str) -> str:
    """Turn a snake_case API key into a Title Case label."""
    return key.replace("_", " ").strip().title()
