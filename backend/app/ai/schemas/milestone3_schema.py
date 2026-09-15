"""Strict Pydantic contracts for Milestone 3 graph outputs."""
from typing import Literal, List, Dict, Optional
from pydantic import BaseModel, Field

Difficulty = Literal["Beginner", "Intermediate", "Advanced", "Master"]

class EvidenceSource(BaseModel):
    content: str = Field(default="")
    source: str = Field(default="knowledge_base")

class CounterargumentResponse(BaseModel):
    logical_rebuttal: str = Field(default="Logical rebuttal to user argument.")
    evidence_rebuttal: str = Field(default="Evidence rebuttal to user argument.")
    ethical_rebuttal: str = Field(default="Ethical rebuttal to user argument.")
    practical_or_policy_rebuttal: str = Field(default="Practical policy rebuttal.")
    challenge_questions: List[str] = Field(default_factory=list)
    debate_strategies: List[str] = Field(default_factory=list)
    evidence_sources: List[EvidenceSource] = Field(default_factory=list)

class AIDebateOpponentResponse(BaseModel):
    opponent_response: str = Field(default="AI debate opponent response.")
    opponent_position: str = Field(default="Opposing position.")
    challenge: str = Field(default="Key challenge question.")
    next_turn_guidance: str = Field(default="Guidance for the next round.")

class JudgeCategoryScores(BaseModel):
    argument_quality: float = Field(default=50.0, ge=0, le=100)
    evidence_usage: float = Field(default=50.0, ge=0, le=100)
    logical_consistency: float = Field(default=50.0, ge=0, le=100)
    rebuttal_effectiveness: Optional[float] = Field(default=None, ge=0, le=100)
    communication_skills: float = Field(default=50.0, ge=0, le=100)
    rationale: List[str] = Field(default_factory=list)

class PerformanceScore(BaseModel):
    categories: JudgeCategoryScores = Field(default_factory=JudgeCategoryScores)
    overall_score: float = Field(default=50.0, ge=0, le=100)

class CoachingResponse(BaseModel):
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    rewrite_suggestions: List[str] = Field(default_factory=list)
    practice_advice: List[str] = Field(default_factory=list)
    next_actions: List[str] = Field(default_factory=list)

class RecommendationResponse(BaseModel):
    debate_topics: List[str] = Field(default_factory=list)
    exercises: List[str] = Field(default_factory=list)
    resources: List[str] = Field(default_factory=list)
    practice_plan: List[str] = Field(default_factory=list)

class LearningPathResponse(BaseModel):
    level: str = Field(default="Intermediate")
    milestones: List[str] = Field(default_factory=list)
    target_skills: List[str] = Field(default_factory=list)
    next_review_after_debates: int = Field(default=3, ge=1)

class ObservabilityMetadata(BaseModel):
    model_used: str = Field(default="openai/gpt-oss-20b")
    latency_ms: int = Field(default=0, ge=0)
    execution_time_ms: int = Field(default=0, ge=0)
    token_usage: Dict[str, int] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
