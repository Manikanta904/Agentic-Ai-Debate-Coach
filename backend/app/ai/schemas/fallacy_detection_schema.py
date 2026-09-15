"""
Logical Fallacy Detection Schema

Purpose:
    Defines the authoritative structured output schema for the Logical Fallacy
    Detection Engine using Groq Native Strict JSON Schema compatibility.
"""

from typing import List, Literal
from pydantic import BaseModel, Field


class DetectedFallacy(BaseModel):
    """
    Represents a detected logical fallacy.
    """

    fallacy_type: Literal[
        "Ad Hominem",
        "Straw Man",
        "False Dilemma",
        "Slippery Slope",
        "Appeal to Authority",
        "Circular Reasoning",
        "Hasty Generalization",
        "Red Herring",
    ] = Field(
        description="Supported fallacy taxonomy categories."
    )

    snippet: str = Field(
        default="",
        description="Brief snippet from the argument where the fallacy occurs."
    )

    excerpt: str = Field(
        default="",
        description="Brief excerpt from the argument where the fallacy occurs."
    )

    explanation: str = Field(
        default="",
        description="Why the reasoning is a fallacy."
    )

    severity: Literal["Low", "Medium", "High", "Critical"] = Field(
        default="Medium",
        description="Severity level of the fallacy."
    )

    confidence: float = Field(
        default=0.85,
        ge=0,
        le=1,
        description="Model confidence score between 0.0 and 1.0."
    )

    correction_suggestion: str = Field(
        default="",
        description="Specific recommendation to resolve this fallacy."
    )


class ExplanationGeneration(BaseModel):
    """
    Explanation of detected fallacies.
    """

    explanation: str = Field(
        default="Analysis of reasoning quality and logical fallacies.",
        description="Why the detected reasoning is considered fallacious."
    )


class CorrectionSuggestion(BaseModel):
    """
    Suggestions to improve reasoning.
    """

    suggestions: List[str] = Field(
        default_factory=list,
        description="Recommended corrections."
    )


class ReasoningAnalysis(BaseModel):
    """
    Overall reasoning quality analysis.
    """

    reasoning_summary: str = Field(
        default="Evaluation of overall logical flow and consistency.",
        description="Summary of overall reasoning quality."
    )

    reasoning_quality: Literal["Excellent", "Good", "Fair", "Poor"] = Field(
        default="Poor",
        description="Overall quality level."
    )


class CredibilityAssessment(BaseModel):
    """
    Overall credibility assessment.
    """

    credibility_level: Literal["High", "Medium", "Low"] = Field(
        default="Low",
        description="Level of credibility."
    )

    credibility_score: float = Field(
        default=30.0,
        ge=0,
        le=100,
        description="Numerical score between 0 and 100."
    )

    justification: str = Field(
        default="Credibility assessment based on argument logic and evidence.",
        description="Justification for the credibility score."
    )


class FallacyDetectionResponse(BaseModel):
    """
    Complete logical fallacy detection result.
    """

    detected_fallacies: List[DetectedFallacy] = Field(
        default_factory=list,
        description="Detected logical fallacies systematically evaluated against taxonomy."
    )

    explanation_generation: ExplanationGeneration = Field(
        default_factory=ExplanationGeneration,
        description="Explanation of detected reasoning issues."
    )

    correction_suggestions: CorrectionSuggestion = Field(
        default_factory=CorrectionSuggestion,
        description="Suggestions to fix fallacies."
    )

    reasoning_analysis: ReasoningAnalysis = Field(
        default_factory=ReasoningAnalysis,
        description="Overall reasoning quality evaluation."
    )

    credibility_assessment: CredibilityAssessment = Field(
        default_factory=CredibilityAssessment,
        description="Credibility score and justification."
    )

    executive_summary: str = Field(
        default="Logical fallacy detection analysis complete.",
        description="Executive summary of fallacy detection."
    )