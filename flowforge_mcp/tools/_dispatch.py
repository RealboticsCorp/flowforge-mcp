"""Shared plumbing for the action-style "manage" tools.

Each manage tool maps an ``action`` to a :class:`Route` (method, path, query,
body). :func:`execute` sends it, rendering the result or a dry-run preview when
the route is gated and the caller has not set ``confirm=true``.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ..client import api_request, format_error
from ..formatting import ResponseFormat, render, to_json


class MissingInputError(ValueError):
    """An action was requested without a field it needs."""


@dataclass(frozen=True)
class Route:
    """One concrete API call an action resolves to."""

    method: str
    path: str
    query: Optional[dict[str, Any]] = None
    body: Any = None
    gated: bool = False
    files: Optional[dict[str, Any]] = field(default=None, compare=False)
    form: Optional[dict[str, Any]] = None
    # True when ``body`` is caller-supplied passthrough: explicit nulls are
    # sent (e.g. unlinking a knowledge base) instead of being stripped.
    keep_nulls: bool = False


def require(value: Any, name: str, action: str) -> Any:
    """Return ``value`` or raise a message naming the missing input."""
    if value is None or value == "" or value == [] or value == {}:
        raise MissingInputError(f"Error: action '{action}' requires '{name}'.")
    return value


async def execute(
    route: Route,
    *,
    confirm: bool,
    response_format: ResponseFormat,
    title: str,
) -> str:
    """Send ``route`` (or preview it if gated and unconfirmed) and render."""
    if route.gated and not confirm:
        return to_json(
            {
                "dry_run": True,
                "would_send": {
                    "method": route.method,
                    "path": route.path,
                    "query": route.query,
                    "body": route.body if route.files is None else "<multipart upload>",
                },
                "why": "Destructive or real-world side effect. Confirm with the user, then re-call with confirm=true.",
            }
        )
    try:
        data = await api_request(
            route.path,
            route.method,
            params=route.query,
            json=route.body,
            files=route.files,
            data=route.form,
            drop_none=not route.keep_nulls,
        )
    except Exception as error:  # noqa: BLE001 - translated for the agent
        return format_error(error)
    if data == {} and route.method == "DELETE":
        return f"Done: {route.method} {route.path}."
    return render(data, response_format, title=title)
