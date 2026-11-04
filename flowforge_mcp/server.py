"""Entry point for the FlowForge MCP server.

Importing ``flowforge_mcp.tools`` registers every tool on the shared ``mcp``
instance; ``main`` then runs the server over stdio (the standard transport for
local MCP clients such as Claude Desktop / Claude Code).

``flowforge-mcp --check`` verifies the install instead: it counts the tools and
reads the organization the API key belongs to, then exits (0 = ok).
"""

import asyncio
import json
import logging
import sys

from .app import API_BASE_URL, mcp
from . import tools  # noqa: F401 - import triggers tool registration
from .client import api_request, format_error


async def _check() -> int:
    """Print tool count and the key's organization; return a process exit code."""
    logging.disable(logging.CRITICAL)  # keep output to the one JSON line the installer parses
    tool_count = len(await mcp.list_tools())
    try:
        org = await api_request("organisation/")
    except Exception as error:  # noqa: BLE001 - report any failure and exit non-zero
        print(json.dumps({"ok": False, "base_url": API_BASE_URL, "tools": tool_count, "error": format_error(error)}))
        return 1
    print(
        json.dumps(
            {
                "ok": True,
                "base_url": API_BASE_URL,
                "tools": tool_count,
                "organization": org.get("name") if isinstance(org, dict) else None,
                "organization_id": org.get("id") if isinstance(org, dict) else None,
            }
        )
    )
    return 0


def main() -> None:
    """Run the FlowForge MCP server over stdio, or verify the install with --check."""
    if "--check" in sys.argv[1:]:
        sys.exit(asyncio.run(_check()))
    mcp.run()


if __name__ == "__main__":
    main()
