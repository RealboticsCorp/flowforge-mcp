"""Index over the bundled FlowForge OpenAPI spec.

The spec (``data/openapi.json``, fetched from the Fern docs site) is the
authoritative list of External API endpoints. It powers two things:

* ``flowforge_api_reference`` - lets an agent search endpoints and read the
  exact query params and request-body schema before calling or coding against
  the API.
* ``flowforge_api_request`` - validates that a raw (method, path) pair is a
  documented endpoint before sending it.

Refresh the bundled copy with ``scripts/refresh_spec.py`` when the docs change.
"""

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

SPEC_PATH = Path(__file__).parent / "data" / "openapi.json"
API_PREFIX = "/api/v1/external"
_HTTP_METHODS = ("get", "post", "put", "patch", "delete")
# Nested $ref depth to expand when describing schemas; deeper refs are named.
_MAX_SCHEMA_DEPTH = 3


@dataclass(frozen=True)
class Endpoint:
    """One documented operation, with its path relative to the API prefix."""

    method: str
    path: str
    summary: str
    tag: str
    operation: dict[str, Any]
    pattern: "re.Pattern[str]"

    @property
    def key(self) -> str:
        return f"{self.method} {self.path}"


@lru_cache(maxsize=1)
def load_spec() -> dict[str, Any]:
    """Load and cache the bundled OpenAPI document."""
    with SPEC_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def endpoints() -> tuple[Endpoint, ...]:
    """Every documented operation, in spec order."""
    found: list[Endpoint] = []
    for raw_path, operations in load_spec().get("paths", {}).items():
        path = raw_path[len(API_PREFIX):] if raw_path.startswith(API_PREFIX) else raw_path
        for method, operation in operations.items():
            if method not in _HTTP_METHODS:
                continue
            found.append(
                Endpoint(
                    method=method.upper(),
                    path=path,
                    summary=operation.get("summary", ""),
                    tag=_group(path),
                    operation=operation,
                    pattern=_path_pattern(path),
                )
            )
    return tuple(found)


def _group(path: str) -> str:
    """Resource group = first path segment (the spec tags everything
    ``externalApi``, which is useless for navigation)."""
    return path.strip("/").split("/", 1)[0] or "root"


def spec_version() -> str:
    """Version string recorded in the bundled spec."""
    return str(load_spec().get("info", {}).get("version", "unknown"))


def _path_pattern(path: str) -> "re.Pattern[str]":
    """Compile ``/calls/{call_id}/end`` into a regex matching concrete paths."""
    escaped = re.escape(path.rstrip("/"))
    return re.compile("^" + re.sub(r"\\\{[^}]+\\\}", "[^/]+", escaped) + "/?$")


def normalize_path(path: str) -> str:
    """Strip host, API prefix and query string; ensure one leading slash."""
    clean = re.sub(r"^https?://[^/]+", "", path.strip()).split("?", 1)[0]
    if clean.startswith(API_PREFIX):
        clean = clean[len(API_PREFIX):]
    return "/" + clean.lstrip("/")


def match(method: str, path: str) -> Optional[Endpoint]:
    """Find the documented endpoint for a concrete method + path, if any.

    Literal segments win over templated ones (``/calls/live/active`` before
    ``/calls/{call_id}``).
    """
    concrete = normalize_path(path)
    candidates = [
        endpoint
        for endpoint in endpoints()
        if endpoint.method == method.upper() and endpoint.pattern.match(concrete)
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda endpoint: endpoint.path.count("{"))


def search(query: Optional[str], tag: Optional[str], limit: int) -> list[Endpoint]:
    """Endpoints whose method/path/summary/tag contain every query word."""
    words = [word.lower() for word in (query or "").split()]
    results = []
    for endpoint in endpoints():
        if tag and tag.lower() not in endpoint.tag.lower():
            continue
        haystack = f"{endpoint.key} {endpoint.summary} {endpoint.tag}".lower()
        if all(word in haystack for word in words):
            results.append(endpoint)
    return results[:limit]


def tags() -> dict[str, int]:
    """Resource group -> number of endpoints, for orientation."""
    counts: dict[str, int] = {}
    for endpoint in endpoints():
        counts[endpoint.tag] = counts.get(endpoint.tag, 0) + 1
    return counts


def describe(endpoint: Endpoint, *, include_response: bool) -> dict[str, Any]:
    """Compact, $ref-resolved description of one endpoint for an agent."""
    operation = endpoint.operation
    described: dict[str, Any] = {
        "method": endpoint.method,
        "path": endpoint.path,
        "summary": endpoint.summary,
        "tag": endpoint.tag,
        "description": (operation.get("description") or "").strip()[:2000],
    }
    parameters = [
        {
            "name": param.get("name"),
            "in": param.get("in"),
            "required": bool(param.get("required")),
            "schema": _resolve(param.get("schema", {})),
            "description": (param.get("description") or "")[:300],
        }
        for param in operation.get("parameters", [])
        if param.get("in") != "header"  # X-API-Key is injected by the server
    ]
    if parameters:
        described["parameters"] = parameters
    content = operation.get("requestBody", {}).get("content", {})
    if content:
        content_type, media = next(iter(content.items()))
        described["request_body"] = {
            "content_type": content_type,
            "required": bool(operation.get("requestBody", {}).get("required")),
            "schema": _resolve(media.get("schema", {})),
        }
    if include_response:
        described["responses"] = {
            code: _resolve(
                next(iter(body.get("content", {}).values()), {}).get("schema", {})
            )
            for code, body in operation.get("responses", {}).items()
        }
    return described


def _resolve(schema: Any, depth: int = 0) -> Any:
    """Inline $refs (to a bounded depth) and flatten nullable anyOf unions.

    Output convention: object properties map to their schema; a trailing ``*``
    on a property name marks it required.
    """
    if not isinstance(schema, dict):
        return schema
    if "$ref" in schema:
        name = schema["$ref"].rsplit("/", 1)[-1]
        if depth >= _MAX_SCHEMA_DEPTH:
            return f"<{name}>"
        target = load_spec().get("components", {}).get("schemas", {}).get(name, {})
        return _resolve(target, depth + 1)
    for union in ("anyOf", "oneOf"):
        if union in schema:
            options = [
                _resolve(option, depth)
                for option in schema[union]
                if option.get("type") != "null"
            ]
            return options[0] if len(options) == 1 else {union: options}
    if "enum" in schema:
        return {"enum": schema["enum"], **_default(schema)}
    if schema.get("type") == "array":
        return [_resolve(schema.get("items", {}), depth)]
    if "properties" in schema:
        required = set(schema.get("required", []))
        return {
            (name + "*" if name in required else name): _resolve(prop, depth)
            for name, prop in schema["properties"].items()
        }
    resolved: dict[str, Any] = {"type": schema.get("type", "any"), **_default(schema)}
    if schema.get("description"):
        resolved["description"] = schema["description"][:200]
    return resolved if len(resolved) > 1 else resolved["type"]


def _default(schema: dict[str, Any]) -> dict[str, Any]:
    return {"default": schema["default"]} if "default" in schema else {}
