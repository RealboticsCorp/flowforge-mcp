"""Refresh the bundled FlowForge OpenAPI spec from the docs site.

Usage:  .venv/bin/python scripts/refresh_spec.py

Prints which endpoints were added or removed so you can decide whether a new
curated tool is worth adding (every endpoint is already reachable through
flowforge_api_request once the spec is refreshed).
"""

import json
import sys
from pathlib import Path

import httpx

SPEC_URL = "https://flowforge.docs.buildwithfern.com/openapi.json"
SPEC_PATH = Path(__file__).resolve().parent.parent / "flowforge_mcp" / "data" / "openapi.json"
METHODS = ("get", "post", "put", "patch", "delete")


def operation_keys(document: dict) -> set[str]:
    return {
        f"{method.upper()} {path}"
        for path, operations in document.get("paths", {}).items()
        for method in operations
        if method in METHODS
    }


def main() -> int:
    try:
        response = httpx.get(SPEC_URL, timeout=30, follow_redirects=True)
        response.raise_for_status()
        fresh = response.json()
    except (httpx.HTTPError, ValueError) as error:
        print(f"Could not fetch {SPEC_URL}: {error}", file=sys.stderr)
        return 1

    old = json.loads(SPEC_PATH.read_text(encoding="utf-8")) if SPEC_PATH.exists() else {}
    added = sorted(operation_keys(fresh) - operation_keys(old))
    removed = sorted(operation_keys(old) - operation_keys(fresh))
    SPEC_PATH.write_text(json.dumps(fresh, indent=1), encoding="utf-8")

    print(f"Spec saved: {len(operation_keys(fresh))} endpoints.")
    for key in added:
        print(f"  + {key}")
    for key in removed:
        print(f"  - {key}")
    if not added and not removed:
        print("  (no endpoint changes)")
    print("Restart the MCP server (or your Claude/Codex session) to load it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
