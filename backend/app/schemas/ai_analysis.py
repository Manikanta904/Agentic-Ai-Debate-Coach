"""
AI Analysis API Schemas

Purpose:
    Defines the request and response models for the AI Analysis API.

Responsibilities:
    - Validate incoming API requests.
    - Standardize API responses.
    - Aggregate results from multiple AI engines.

Note:
    These schemas belong to the API layer and should not contain
    any AI processing logic.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.ai.schemas.argument_analysis_schema import (
    ArgumentAnalysisResponse,
)
from app.ai.schemas.fallacy_detection_schema import (
    FallacyDetectionResponse,
)
from app.ai.schemas.milestone3_schema import (
    CounterargumentResponse,
    AIDebateOpponentResponse,
    JudgeCategoryScores,
    PerformanceScore,
    CoachingResponse,
    RecommendationResponse,
    LearningPathResponse,
)


class ArgumentAnalysisRequest(BaseModel):
    """
    Request model for AI analysis.
    """

    session_id: int = Field(
        ...,
        gt=0,
        description="Debate session identifier."
    )

    argument: str = Field(
        ...,
        min_length=10,
        description="User's debate argument."
    )
    debate_format: str = Field(default="One-on-One", max_length=50)
    difficulty: str = Field(default="Intermediate", max_length=20)
    user_position: str = Field(default="Affirmative", max_length=20)
    current_round: int = Field(default=1, ge=1)


class AIAnalysisData(BaseModel):
    """
    Combined AI analysis results across the complete 8-agent pipeline.
    """

    session: Optional[Dict[str, Any]] = None

    argument: Optional[str] = None

    transcript: Optional[Dict[str, Any]] = None

    argument_analysis: Optional[ArgumentAnalysisResponse] = None

    logical_fallacy_analysis: Optional[FallacyDetectionResponse] = None

    counterargument_analysis: Optional[CounterargumentResponse] = None

    debate_simulation: Optional[AIDebateOpponentResponse] = None

    judge_evaluation: Optional[JudgeCategoryScores] = None

    performance_score: Optional[PerformanceScore] = None

    coaching: Optional[CoachingResponse] = None

    recommendations: Optional[RecommendationResponse] = None

    learning_path: Optional[LearningPathResponse] = None

    execution_status: str = Field(default="completed")

    errors: List[str] = Field(default_factory=list)

    metadata: Optional[Dict[str, Any]] = None


class AIAnalysisAPIResponse(BaseModel):
    """
    Standard API response returned to the frontend.
    """

    success: bool

    message: str

    data: AIAnalysisData
