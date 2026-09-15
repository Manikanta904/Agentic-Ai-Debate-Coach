from typing import Any, List, Optional
from pydantic import BaseModel, Field


class DebateReport(BaseModel):
    """
    Represents a single debate analysis report stored in MongoDB.
    """

    report_id: str = Field(
        ...,
        description="MongoDB ObjectId of the report."
    )

    session_id: int = Field(
        ...,
        description="Debate session ID."
    )

    user_id: Optional[int] = Field(
        None,
        description="User ID."
    )

    topic_id: Optional[int] = Field(
        None,
        description="Debate topic ID."
    )

    input_type: str = Field(
        "text",
        description="Type of debate input."
    )

    media_filename: Optional[str] = Field(
        None,
        description="Uploaded media filename."
    )

    transcript: Optional[dict] = Field(
        default_factory=dict,
        description="Speech transcription."
    )

    argument_analysis: Optional[dict] = Field(
        default_factory=dict,
        description="Argument analysis results."
    )

    logical_fallacy_analysis: Optional[dict] = Field(
        default_factory=dict,
        description="Logical fallacy analysis results."
    )

    counterargument: Optional[dict] = Field(
        default_factory=dict,
        description="Counterargument analysis results."
    )

    ai_debate_opponent: Optional[dict] = Field(
        default_factory=dict,
        description="AI debate opponent results."
    )

    judge_evaluation: Optional[dict] = Field(
        default_factory=dict,
        description="Judge evaluation results."
    )

    performance: Optional[dict] = Field(
        default_factory=dict,
        description="Performance score results."
    )

    coaching: Optional[dict] = Field(
        default_factory=dict,
        description="Coaching recommendations."
    )

    recommendations: Optional[dict] = Field(
        default_factory=dict,
        description="Actionable recommendations."
    )

    learning_path: Optional[dict] = Field(
        default_factory=dict,
        description="Personalized learning path."
    )

    observability: Optional[dict] = Field(
        default_factory=dict,
        description="Observability and timing metadata."
    )

    created_at: Optional[str] = Field(
        None,
        description="ISO timestamp of creation."
    )

    updated_at: Optional[str] = Field(
        None,
        description="ISO timestamp of last update."
    )


class DebateReportResponse(BaseModel):
    """
    Response model for a single report.
    """

    success: bool

    message: str

    data: DebateReport


class DebateReportListResponse(BaseModel):
    """
    Response model for multiple reports.
    """

    success: bool

    message: str

    data: List[DebateReport]
