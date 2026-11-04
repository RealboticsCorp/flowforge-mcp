"""Shared Pydantic building blocks for tool input validation.

Tool-specific input models live alongside their tools; this module holds the
common configuration and the pagination/format mixins reused everywhere.
"""


from pydantic import BaseModel, ConfigDict, Field

from .formatting import ResponseFormat

# Re-exported so tool modules import a single name.
__all__ = ["StrictModel", "PaginationParams", "FormatMixin", "ResponseFormat"]


class StrictModel(BaseModel):
    """Base model: strips string whitespace, validates on assignment, forbids extras."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )


class FormatMixin(StrictModel):
    """Adds a standard ``response_format`` field to a model."""

    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description=(
            "Output format. 'json' (default) returns every field for further "
            "processing; 'markdown' returns a compact human-readable summary."
        ),
    )


class PaginationParams(FormatMixin):
    """Standard pagination inputs matching the FlowForge list endpoints."""

    limit: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of items to return per page (1-100).",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of items to skip, for paging through results.",
    )
