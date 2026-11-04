"""Agent-test administration and run results.

Complements ``account.py`` (list/run). Test runs are asynchronous: start one
with ``flowforge_run_test`` (or ``run_all`` here), then poll
``flowforge_get_test_run`` until its status is terminal.
"""

from enum import Enum
from typing import Any, Optional

from pydantic import Field

from ..app import mcp
from ..client import api_request, format_error
from ..formatting import render
from ..models import FormatMixin
from ._dispatch import MissingInputError, Route, execute, require


class TestAction(str, Enum):
    GET = "get"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ATTACH = "attach"
    DETACH = "detach"
    LIST_RUNS = "list_runs"
    RUN_ALL = "run_all"
    LIST_FOLDERS = "list_folders"
    CREATE_FOLDER = "create_folder"


class ManageTestsInput(FormatMixin):
    """Inputs for agent-test management."""

    action: TestAction = Field(..., description="Test operation to perform.")
    test_id: Optional[str] = Field(default=None, description="get/update/delete/attach/detach/list_runs: test ID.")
    assistant_id: Optional[str] = Field(
        default=None, description="attach/detach/run_all: assistant ID."
    )
    branch_id: Optional[str] = Field(default=None, description="run_all: run against this branch.")
    n_iterations: int = Field(default=1, ge=1, le=20, description="run_all: iterations per test.")
    folder_name: Optional[str] = Field(default=None, description="create_folder: folder name (unique).")
    fields: Optional[dict[str, Any]] = Field(
        default=None,
        description=(
            "create: {'name'*, 'test_type'* (scenario|tool_call|simulation|"
            "span_replay), 'config'* {...}, 'folder_id', 'attach_to_assistant_id'}. "
            "update: {'name', 'config', 'folder_id'}. Read an existing test with "
            "action='get' to copy a valid config shape."
        ),
    )
    limit: int = Field(default=20, ge=1, le=200, description="list_runs: max runs.")
    confirm: bool = Field(default=False, description="Required true for 'delete' and 'detach'.")


class GetTestRunInput(FormatMixin):
    """Inputs for reading (or retrying) a test run."""

    run_id: str = Field(..., min_length=1, description="Run ID returned by flowforge_run_test / run_all.")
    include_results: bool = Field(default=True, description="Also fetch per-iteration results.")
    retry: bool = Field(default=False, description="Retry the run instead of reading it.")
    retry_iterations: Optional[list[int]] = Field(
        default=None, description="retry: only these iteration numbers (all failed ones when omitted)."
    )


@mcp.tool(
    name="flowforge_manage_tests",
    annotations={
        "title": "Manage FlowForge Agent Tests",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def flowforge_manage_tests(params: ManageTestsInput) -> str:
    """Create/read/update/delete agent tests, attach them to assistants, list
    a test's runs, run every attached test for an assistant, and manage test
    folders. Tests are the regression suite for prompt/flow changes - run
    them on a branch before publishing."""
    action = params.action.value
    try:
        if params.action == TestAction.LIST_FOLDERS:
            route = Route("GET", "tests/folders")
        elif params.action == TestAction.CREATE_FOLDER:
            route = Route("POST", "tests/folders", body={"name": require(params.folder_name, "folder_name", action)})
        elif params.action == TestAction.CREATE:
            route = Route("POST", "tests/", body=require(params.fields, "fields", action))
        elif params.action == TestAction.RUN_ALL:
            route = Route(
                "POST",
                "tests/run-all",
                body={
                    "assistant_id": require(params.assistant_id, "assistant_id", action),
                    "branch_id": params.branch_id,
                    "n_iterations": params.n_iterations,
                },
            )
        else:
            test = f"tests/{require(params.test_id, 'test_id', action)}"
            if params.action == TestAction.GET:
                route = Route("GET", test)
            elif params.action == TestAction.UPDATE:
                route = Route("PATCH", test, body=require(params.fields, "fields", action), keep_nulls=True)
            elif params.action == TestAction.DELETE:
                route = Route("DELETE", test, gated=True)
            elif params.action == TestAction.LIST_RUNS:
                route = Route("GET", f"{test}/runs", query={"limit": params.limit})
            elif params.action == TestAction.ATTACH:
                route = Route(
                    "POST",
                    f"{test}/attach",
                    body={"assistant_id": require(params.assistant_id, "assistant_id", action)},
                )
            else:
                route = Route(
                    "DELETE",
                    f"{test}/attach/{require(params.assistant_id, 'assistant_id', action)}",
                    gated=True,
                )
    except MissingInputError as error:
        return str(error)
    return await execute(route, confirm=params.confirm, response_format=params.response_format, title="Agent Tests")


@mcp.tool(
    name="flowforge_get_test_run",
    annotations={
        "title": "Get FlowForge Test Run",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def flowforge_get_test_run(params: GetTestRunInput) -> str:
    """Read a test run's status (and per-iteration results), or retry it.

    Poll this after ``flowforge_run_test`` until the status is terminal
    (completed/failed); results include scores and failure reasons.
    """
    if params.retry:
        return await execute(
            Route("POST", f"tests/runs/{params.run_id}/retry", body={"iterations": params.retry_iterations}),
            confirm=False,
            response_format=params.response_format,
            title="Test Run Retry",
        )
    try:
        result: dict[str, Any] = {"run": await api_request(f"tests/runs/{params.run_id}")}
        if params.include_results:
            try:
                result["results"] = await api_request(f"tests/runs/{params.run_id}/results")
            except Exception as sub_error:  # noqa: BLE001 - isolate the sub-fetch
                result["results"] = {"error": format_error(sub_error)}
        return render(result, params.response_format, title="Test Run")
    except Exception as error:  # noqa: BLE001
        return format_error(error)
