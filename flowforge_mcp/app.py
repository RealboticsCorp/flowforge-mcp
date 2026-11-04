"""Shared FastMCP application instance and module-level constants.

Tool modules import ``mcp`` from here and register themselves with the
``@mcp.tool`` decorator. ``server.py`` imports every tool module to trigger
registration, then runs the server. Keeping the instance in its own module
avoids circular imports between the tool modules and the entry point.
"""

import os

from mcp.server.fastmcp import FastMCP

# Server name follows the {service}_mcp convention.
mcp = FastMCP("flowforge_mcp")

# Current FlowForge API host. Earlier hosts are retired; set FLOWFORGE_BASE_URL
# to override when it changes.
DEFAULT_BASE_URL = "https://api.realbotics.ai/api/v1/external"
API_BASE_URL = os.environ.get("FLOWFORGE_BASE_URL", DEFAULT_BASE_URL).rstrip("/")

# Name of the environment variable holding the API key (format: ff_live_...).
API_KEY_ENV = "FLOWFORGE_API_KEY"

# Default network timeout for all API calls, in seconds.
REQUEST_TIMEOUT_SECONDS = 30.0
