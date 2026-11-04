"""Tool modules for the FlowForge MCP server.

Importing this package imports every tool module, which registers all tools on
the shared ``mcp`` instance via their ``@mcp.tool`` decorators.
"""

from . import (
    account,
    api,
    assistant_config,
    assistants,
    calls,
    campaign_admin,
    campaigns,
    knowledge,
    knowledge_admin,
    org_admin,
    phone_admin,
    phone_numbers,
    tests_admin,
    voice,
)

__all__ = [
    "account",
    "api",
    "assistant_config",
    "assistants",
    "calls",
    "campaign_admin",
    "campaigns",
    "knowledge",
    "knowledge_admin",
    "org_admin",
    "phone_admin",
    "phone_numbers",
    "tests_admin",
    "voice",
]
