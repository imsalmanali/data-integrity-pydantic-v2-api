from typing import Any, Dict, List, Literal, Optional
from pydantic import Field
from .base import TimestampedModel


class DataIntegrityReport(TimestampedModel):
    """Integrity audit generated for every ingested external batch."""
    total_received: int = Field(..., ge=0)
    valid_count: int = Field(..., ge=0)
    invalid_count: int = Field(..., ge=0)
    quarantine_errors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Detailed Pydantic validation error traces for rejected records"
    )
    status: Literal["SUCCESS", "PARTIAL", "FAILED"] = Field(...)


class AgentToolPayload(TimestampedModel):
    """
    Standard envelope format passed into an AI Agent's Context Window.
    Guarantees that LLM prompts only receive clean, schema-validated facts.
    """
    tool_name: str = Field(..., description="Name of the calling tool/API")
    source_url: str = Field(..., description="API endpoint queried")
    status: Literal["SUCCESS", "DEGRADED", "ERROR"] = Field(...)
    data: Dict[str, Any] = Field(default_factory=dict, description="Clean validated entity payload")
    audit: DataIntegrityReport = Field(..., description="Validation audit record")
    agent_summary: Optional[str] = Field(default=None, description="Concise synopsis prepared for LLM prompts")
