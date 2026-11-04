"""Tools for FlowForge account-level data: organization, billing, and tests.

Grouped together because each is a small, read-mostly surface: organization
settings/concurrency, billing usage and balance, and the agent-test suite
(list and run LLM-scored tests against an assistant).
"""

from enum import Enum
from typing import Any, Optional

from pydantic import Field

from ..app import mcp
from ..client import FlowForgeHTTPError, api_request, format_error
from ..formatting import local_page, render
from ..models import FormatMixin, PaginationParams


class UsageBreakdown(str, Enum):
    """Which billing report to fetch."""

    TOTAL = "current-month"
    BY_COMPONENT = "by-component"
    BY_RESOURCE = "by-resource"
    BY_DISPOSITION = "by-disposition"
    FORECAST = "forecast"
    INSIGHTS = "insights"
    AGENTS_EFFICIENCY = "agents-efficiency"
    IDLE_PHONES = "idle-phones"
    LEDGER = "ledger"


# Report -> endpoint path under /billing.
_USAGE_PATHS = {
    UsageBreakdown.TOTAL: "billing/usage/current-month",
    UsageBreakdown.BY_COMPONENT: "billing/usage/by-component",
    UsageBreakdown.BY_RESOURCE: "billing/usage/by-resource",
    UsageBreakdown.BY_DISPOSITION: "billing/usage/by-disposition",
    UsageBreakdown.FORECAST: "billing/forecast",
    UsageBreakdown.INSIGHTS: "billing/insights",
    UsageBreakdown.AGENTS_EFFICIENCY: "billing/agents/efficiency",
    UsageBreakdown.IDLE_PHONES: "billing/phones/idle",
    UsageBreakdown.LEDGER: "billing/ledger",
}


class OrganizationInput(FormatMixin):
    """Inputs for fetching organization info."""

    include_concurrency: bool = Field(
        default=False,
        description="Also fetch call concurrency limits alongside the org record.",
    )


class UsageInput(FormatMixin):
    """Inputs for the billing usage report."""

    breakdown: UsageBreakdown = Field(
        default=UsageBreakdown.TOTAL,
        description=(
            "Report: 'current-month' (total), 'by-component', 'by-resource', "
            "'by-disposition', 'forecast' (month-end projection), 'insights' "
            "(cost anomalies/tips), 'agents-efficiency' (cost per assistant), "
            "'idle-phones' (numbers costing money without calls), 'ledger' "
            "(line-item charges/credits)."
        ),
    )
    date_from: Optional[str] = Field(
        default=None,
        description="ISO date/time lower bound (by-component, by-resource: 'from'; ledger: 'since').",
    )
    date_to: Optional[str] = Field(
        default=None,
        description="ISO date/time upper bound (by-component, by-resource: 'to'; ledger: 'until').",
    )
    period_days: Optional[int] = Field(
        default=None, ge=1, le=365, description="Look-back window for by-disposition, insights, agents-efficiency (default 30)."
    )
    threshold_days: Optional[int] = Field(
        default=None, ge=1, le=365, description="idle-phones: days without calls to count as idle (default 30)."
    )
    limit: Optional[int] = Field(
        default=None, ge=1, le=5000, description="agents-efficiency (default 50) or ledger (default 500) row cap."
    )


class BalanceInput(FormatMixin):
    """Inputs for fetching the account balance."""


class ListTestsInput(PaginationParams):
    """Inputs for listing agent tests."""

    assistant_id: Optional[str] = Field(default=None, description="Only tests attached to this assistant.")
    folder_id: Optional[str] = Field(default=None, description="Only tests in this folder.")
    test_type: Optional[str] = Field(
        default=None, description="Filter by type: 'scenario', 'tool_call', 'simulation', 'span_replay'."
    )


class RunTestInput(FormatMixin):
    """Inputs for running an agent test."""

    test_id: str = Field(..., min_length=1, description="ID of the agent test to run.")
    assistant_id: str = Field(..., min_length=1, description="Assistant to run the test against (required by the API).")
    branch_id: Optional[str] = Field(default=None, description="Run against this assistant branch instead of Main.")
    n_iterations: int = Field(default=1, ge=1, le=20, description="How many times to run it (for flakiness).")
    draft: bool = Field(default=False, description="Run against the unpublished draft configuration.")


@mcp.tool(
    name="flowforge_get_organization",
    annotations={
        "title": "Get FlowForge Organization",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowforge_get_organization(params: OrganizationInput) -> str:
    """Get your FlowForge organization's settings, optionally with concurrency
    limits.

    Args:
        params: ``include_concurrency`` flag, ``response_format``.

    Returns:
        JSON/Markdown with an ``organisation`` object and, if requested, a
        ``concurrency`` object.

    Error Handling:
        Returns "Error: ..." on failure.
    """
    try:
        result = {"organisation": await api_request("organisation")}
        if params.include_concurrency:
            try:
                result["concurrency"] = await api_request("organisation/concurrency")
            except Exception as sub_error:  # noqa: BLE001
                result["concurrency"] = {"error": format_error(sub_error)}
        return render(result, params.response_format, title="Organization")
    except Exception as error:  # noqa: BLE001
        return format_error(error)


@mcp.tool(
    name="flowforge_get_usage",
    annotations={
        "title": "Get FlowForge Usage",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowforge_get_usage(params: UsageInput) -> str:
    """Get a billing report: current-month usage (total or broken down by
    component/resource/disposition), forecast, insights, per-assistant
    efficiency, idle phone numbers, or the ledger.

    Args:
        params: ``breakdown`` (report name), optional ``date_from``/``date_to``,
            ``period_days``, ``threshold_days``, ``limit``, ``response_format``.

    Returns:
        JSON/Markdown with the usage report for the selected breakdown.

    Error Handling:
        Returns "Error: ..." on failure.
    """
    try:
        query = _usage_query(params)
        try:
            data = await api_request(_USAGE_PATHS[params.breakdown], params=query)
        except FlowForgeHTTPError as error:
            if params.breakdown != UsageBreakdown.LEDGER or error.result.status < 500:
                raise
            data = await _ledger_csv_fallback(params, error)
        return render(data, params.response_format, title="Usage Report")
    except Exception as error:  # noqa: BLE001
        return format_error(error)


@mcp.tool(
    name="flowforge_get_balance",
    annotations={
        "title": "Get FlowForge Balance",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowforge_get_balance(params: BalanceInput) -> str:
    """Get the current account balance.

    Args:
        params: ``response_format`` only.

    Returns:
        JSON/Markdown with the account balance.

    Error Handling:
        Returns "Error: ..." on failure.
    """
    try:
        data = await api_request("billing/balance")
        return render(data, params.response_format, title="Account Balance")
    except Exception as error:  # noqa: BLE001
        return format_error(error)


@mcp.tool(
    name="flowforge_list_tests",
    annotations={
        "title": "List FlowForge Agent Tests",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowforge_list_tests(params: ListTestsInput) -> str:
    """List the agent tests defined in your organization.

    Agent tests are LLM-scored scenarios used to evaluate assistant behavior.

    Args:
        params: ``limit`` (1-100), ``offset``, ``response_format``.

    Returns:
        JSON/Markdown with pagination metadata and a ``tests`` array.

    Error Handling:
        Returns "Error: ..." on failure.
    """
    try:
        # Server filters but returns a bare, unpaginated array; page client-side.
        data = await api_request(
            "tests/",
            params={
                "assistant_id": params.assistant_id,
                "folder_id": params.folder_id,
                "test_type": params.test_type,
            },
        )
        envelope = local_page(data, preferred_key="tests", limit=params.limit, offset=params.offset)
        return render(envelope, params.response_format, title="Agent Tests")
    except Exception as error:  # noqa: BLE001
        return format_error(error)


@mcp.tool(
    name="flowforge_run_test",
    annotations={
        "title": "Run FlowForge Agent Test",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def flowforge_run_test(params: RunTestInput) -> str:
    """Start an agent test run against an assistant.

    Runs are asynchronous: this returns the run row (status ``queued``). Poll
    ``flowforge_get_test_run`` with the returned run id for status and
    per-iteration results.

    Args:
        params: ``test_id``, ``assistant_id``, optional ``branch_id``,
            ``n_iterations``, ``draft``, ``response_format``.

    Returns:
        JSON/Markdown with the queued run (including its id).

    Error Handling:
        Returns "Error: Resource not found..." if the test_id is wrong.
    """
    try:
        data = await api_request(
            f"tests/{params.test_id}/run",
            method="POST",
            json={
                "assistant_id": params.assistant_id,
                "branch_id": params.branch_id,
                "n_iterations": params.n_iterations,
                "draft": params.draft,
            },
        )
        return render(data, params.response_format, title="Test Run")
    except Exception as error:  # noqa: BLE001
        return format_error(error)


def _usage_query(params: UsageInput) -> dict[str, Any]:
    """Map the generic report inputs onto each endpoint's own query names."""
    report = params.breakdown
    if report in (UsageBreakdown.BY_COMPONENT, UsageBreakdown.BY_RESOURCE):
        return {"from": params.date_from, "to": params.date_to}
    if report == UsageBreakdown.LEDGER:
        return {"since": params.date_from, "until": params.date_to, "limit": params.limit}
    if report == UsageBreakdown.AGENTS_EFFICIENCY:
        return {"period_days": params.period_days, "limit": params.limit}
    if report in (UsageBreakdown.BY_DISPOSITION, UsageBreakdown.INSIGHTS):
        return {"period_days": params.period_days}
    if report == UsageBreakdown.IDLE_PHONES:
        return {"threshold_days": params.threshold_days}
    return {}


async def _ledger_csv_fallback(params: UsageInput, error: FlowForgeHTTPError) -> dict[str, Any]:
    """The JSON ledger has returned 500 while the CSV export works; serve the
    first ``limit`` CSV rows instead (default 200) and say so."""
    csv = await api_request(
        "billing/ledger.csv", params={"from": params.date_from, "to": params.date_to}
    )
    lines = str(csv.get("raw", "") if isinstance(csv, dict) else csv).splitlines()
    row_cap = params.limit or 200
    return {
        "source": f"fallback: ledger.csv (JSON ledger returned {error.result.status}, "
        f"request_id {error.result.request_id})",
        "total_rows": max(len(lines) - 1, 0),
        "csv": "\n".join(lines[: row_cap + 1]),
    }
