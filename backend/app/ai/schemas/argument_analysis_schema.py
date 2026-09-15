"""
===============================================================================
Argument Analysis Schema
===============================================================================

Module:
    app.ai.schemas.argument_analysis_schema

Purpose:
    Defines the standardized data models (schemas) for the Argument Analysis
    Engine using Pydantic. These schemas act as the contract between the
    Large Language Model (LLM), backend services, APIs, and frontend
    components.
"""

from typing import List, Literal, Any, Dict
from pydantic import BaseModel, Field, model_validator


class ArgumentExtraction(BaseModel):
    """
    Extracted primary argument from the user's speech.
    """

    original_argument: str = Field(
        default="User argument overview.",
        description="Original argument summary."
    )

    extracted_argument: str = Field(
        default="Normalized version of primary argument.",
        description="Normalized version of the user's primary argument."
    )

    @model_validator(mode="before")
    @classmethod
    def flex_parse(cls, v: Any) -> Any:
        if isinstance(v, str):
            return {"original_argument": v, "extracted_argument": v}
        if isinstance(v, dict):
            orig = v.get("original_argument") or v.get("extracted_argument") or "User argument summary."
            ext = v.get("extracted_argument") or orig
            return {"original_argument": str(orig), "extracted_argument": str(ext)}
        return {"original_argument": "User argument summary.", "extracted_argument": "Normalized primary argument."}


class ClaimIdentification(BaseModel):
    """
    Claims identified within the argument.
    """

    primary_claim: str = Field(
        default="Primary claim of the argument.",
        description="Main claim presented in the argument."
    )

    supporting_claims: List[str] = Field(
        default_factory=list,
        description="Supporting claims identified in the argument."
    )

    @model_validator(mode="before")
    @classmethod
    def flex_parse(cls, v: Any) -> Any:
        if isinstance(v, str):
            return {"primary_claim": v, "supporting_claims": []}
        if isinstance(v, dict):
            p_claim = v.get("primary_claim") or "Primary claim."
            s_claims = v.get("supporting_claims") or []
            if isinstance(s_claims, str):
                s_claims = [s_claims]
            return {"primary_claim": str(p_claim), "supporting_claims": [str(x) for x in s_claims]}
        return {"primary_claim": "Primary claim.", "supporting_claims": []}


class EvidenceEvaluation(BaseModel):
    """
    Evaluation of evidence used in the argument.
    """

    evidence_items: List[str] = Field(
        default_factory=list,
        description="Evidence identified in the argument."
    )

    evidence_strength: Literal[
        "Very Weak",
        "Weak",
        "Moderate",
        "Strong",
        "Very Strong",
    ] = Field(
        default="Weak",
        description="Overall quality of supporting evidence."
    )

    evidence_analysis: str = Field(
        default="Analysis of supporting evidence quality.",
        description="Analysis of how effectively the evidence supports the claims."
    )

    @model_validator(mode="before")
    @classmethod
    def flex_parse(cls, v: Any) -> Any:
        if isinstance(v, str):
            return {"evidence_items": [], "evidence_strength": "Weak", "evidence_analysis": v}
        if isinstance(v, dict):
            items = v.get("evidence_items") or []
            if isinstance(items, str):
                items = [items]
            strength = v.get("evidence_strength") if v.get("evidence_strength") in ["Very Weak", "Weak", "Moderate", "Strong", "Very Strong"] else "Weak"
            analysis = v.get("evidence_analysis") or "Evaluation of evidence."
            analysis_lower = str(analysis).lower()
            weak_indicators = ["limited", "no evidence", "unsupported", "overgeneralized", "anecdotal", "weak", "lacks", "absent", "insufficient", "no supporting"]
            if any(ind in analysis_lower for ind in weak_indicators) or not items:
                if strength in ["Strong", "Very Strong"]:
                    strength = "Weak"
            return {"evidence_items": [str(x) for x in items], "evidence_strength": strength, "evidence_analysis": str(analysis)}
        return {"evidence_items": [], "evidence_strength": "Weak", "evidence_analysis": "Evaluation of evidence."}


class ArgumentStrengthAssessment(BaseModel):
    """
    Overall strength assessment.
    """

    strength_level: Literal[
        "Very Weak",
        "Weak",
        "Moderate",
        "Strong",
        "Very Strong",
    ] = Field(
        default="Weak",
        description="Overall strength of the argument."
    )

    justification: str = Field(
        default="Reasoning for assigned strength level.",
        description="Reason for assigning the argument strength."
    )

    @model_validator(mode="before")
    @classmethod
    def flex_parse(cls, v: Any) -> Any:
        if isinstance(v, str):
            return {"strength_level": "Weak", "justification": v}
        if isinstance(v, dict):
            strength = v.get("strength_level") if v.get("strength_level") in ["Very Weak", "Weak", "Moderate", "Strong", "Very Strong"] else "Weak"
            just = v.get("justification") or "Argument strength evaluation."
            return {"strength_level": strength, "justification": str(just)}
        return {"strength_level": "Weak", "justification": "Argument strength evaluation."}


class ReasoningQualityAnalysis(BaseModel):
    """
    Logical reasoning quality assessment.
    """

    reasoning_summary: str = Field(
        default="Evaluation of the reasoning process.",
        description="Evaluation of the reasoning process."
    )

    reasoning_quality: Literal[
        "Poor",
        "Fair",
        "Good",
        "Excellent",
    ] = Field(
        default="Poor",
        description="Overall reasoning quality."
    )

    @model_validator(mode="before")
    @classmethod
    def flex_parse(cls, v: Any) -> Any:
        if isinstance(v, str):
            return {"reasoning_summary": v, "reasoning_quality": "Poor"}
        if isinstance(v, dict):
            summary = v.get("reasoning_summary") or "Evaluation of reasoning process."
            quality = v.get("reasoning_quality") if v.get("reasoning_quality") in ["Poor", "Fair", "Good", "Excellent"] else "Poor"
            return {"reasoning_summary": str(summary), "reasoning_quality": quality}
        return {"reasoning_summary": "Evaluation of reasoning process.", "reasoning_quality": "Poor"}


class EvaluationCriteria(BaseModel):
    """
    Milestone 2 evaluation criteria.
    Scores range from 1 to 10.
    """

    clarity: int = Field(default=5, ge=1, le=10)
    relevance: int = Field(default=5, ge=1, le=10)
    evidence_strength: int = Field(default=5, ge=1, le=10)
    logical_consistency: int = Field(default=5, ge=1, le=10)
    persuasiveness: int = Field(default=5, ge=1, le=10)

    @model_validator(mode="before")
    @classmethod
    def flex_parse(cls, v: Any) -> Any:
        if isinstance(v, dict):
            def clean_score(val, default=5):
                try:
                    s = int(val)
                    return max(1, min(10, s))
                except (ValueError, TypeError):
                    return default
            return {
                "clarity": clean_score(v.get("clarity")),
                "relevance": clean_score(v.get("relevance")),
                "evidence_strength": clean_score(v.get("evidence_strength")),
                "logical_consistency": clean_score(v.get("logical_consistency")),
                "persuasiveness": clean_score(v.get("persuasiveness")),
            }
        return {"clarity": 5, "relevance": 5, "evidence_strength": 5, "logical_consistency": 5, "persuasiveness": 5}


class ArgumentScoring(BaseModel):
    """
    Overall argument scoring based on the evaluation criteria.
    """

    overall_score: float = Field(
        default=50.0,
        ge=0,
        le=100,
        description="Overall argument quality score."
    )

    score_justification: str = Field(
        default="Explanation for assigned overall score.",
        description="Explanation for the assigned overall score."
    )

    @model_validator(mode="before")
    @classmethod
    def flex_parse(cls, v: Any) -> Any:
        if isinstance(v, (int, float)):
            return {"overall_score": float(v), "score_justification": "Overall argument score."}
        if isinstance(v, dict):
            try:
                score = float(v.get("overall_score", 50.0))
                score = max(0.0, min(100.0, score))
            except (ValueError, TypeError):
                score = 50.0
            just = str(v.get("score_justification") or "Overall score explanation.")
            return {"overall_score": score, "score_justification": just}
        return {"overall_score": 50.0, "score_justification": "Overall score explanation."}


class ArgumentAnalysisResponse(BaseModel):
    """
    Complete Argument Analysis Engine response.
    """

    argument_extraction: ArgumentExtraction = Field(
        default_factory=lambda: ArgumentExtraction()
    )

    claim_identification: ClaimIdentification = Field(
        default_factory=lambda: ClaimIdentification()
    )

    evidence_evaluation: EvidenceEvaluation = Field(
        default_factory=lambda: EvidenceEvaluation()
    )

    argument_strength_assessment: ArgumentStrengthAssessment = Field(
        default_factory=lambda: ArgumentStrengthAssessment()
    )

    reasoning_quality_analysis: ReasoningQualityAnalysis = Field(
        default_factory=lambda: ReasoningQualityAnalysis()
    )

    evaluation_criteria: EvaluationCriteria = Field(
        default_factory=lambda: EvaluationCriteria()
    )

    argument_scoring: ArgumentScoring = Field(
        default_factory=lambda: ArgumentScoring()
    )

    executive_summary: str = Field(
        default="Overall summary of argument analysis.",
        description="Overall summary of the argument analysis."
    )

    improvement_recommendations: List[str] = Field(
        default_factory=list,
        description="Suggestions for improving the argument."
    )