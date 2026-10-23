from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field


class AgentBaseModel(BaseModel):
    """
    Strict base model for all Agentic AI entities.
    Enforces extra field prohibition and string stripping.
    """
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
    )


class TimestampedModel(AgentBaseModel):
    """Base model with UTC timestamp auditing."""
    ingested_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the record was validated and ingested into agent memory."
    )
