"""Deterministic weighted debate performance scoring."""
from app.ai.schemas.milestone3_schema import JudgeCategoryScores, PerformanceScore

class PerformanceScoringEngine:
    WEIGHTS = {
        "argument_quality": 0.30,
        "evidence_usage": 0.20,
        "logical_consistency": 0.20,
        "rebuttal_effectiveness": 0.15,
        "communication_skills": 0.15,
    }

    @classmethod
    def calculate(cls, categories: JudgeCategoryScores) -> PerformanceScore:
        weighted_sum = 0.0
        total_weight = 0.0
        for name, weight in cls.WEIGHTS.items():
            val = getattr(categories, name, None)
            if val is not None:
                weighted_sum += float(val) * weight
                total_weight += weight

        overall = (weighted_sum / total_weight) if total_weight > 0 else 0.0
        return PerformanceScore(categories=categories, overall_score=round(overall, 2))
