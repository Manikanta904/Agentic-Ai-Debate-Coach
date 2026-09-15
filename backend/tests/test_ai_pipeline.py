import sys
import os
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.ai.orchestrator.debate_graph import debate_orchestrator
from app.ai.scoring.scoring_engine import PerformanceScoringEngine
from app.ai.schemas.milestone3_schema import JudgeCategoryScores
from app.ai.agents.judge_agent import JudgeAgent
from app.schemas.ai_analysis import AIAnalysisData


def test_scoring_engine_deterministic_formula():
    """Verify deterministic 30-20-20-15-15 scoring formula."""
    categories = JudgeCategoryScores(
        argument_quality=80.0,
        evidence_usage=70.0,
        logical_consistency=60.0,
        rebuttal_effectiveness=90.0,
        communication_skills=85.0,
        rationale=["Test rationale"]
    )
    score = PerformanceScoringEngine.calculate(categories)
    expected = round((80.0 * 0.30) + (70.0 * 0.20) + (60.0 * 0.20) + (90.0 * 0.15) + (85.0 * 0.15), 2)
    assert score.overall_score == expected
    assert score.overall_score != 82.0 or expected == 82.0


def test_judge_fallacy_deduction():
    """Verify JudgeAgent penalizes logical consistency when fallacies are present."""
    judge = JudgeAgent()

    # Case A: Sound argument without fallacies
    clean_eval = judge.evaluate(
        argument="Well reasoned claim with empirical data.",
        argument_analysis={"evaluation_criteria": {"clarity": 8, "relevance": 8, "evidence_strength": 8, "logical_consistency": 9, "persuasiveness": 8}, "argument_scoring": {"overall_score": 85.0}},
        fallacies={"detected_fallacies": [], "credibility_assessment": {"credibility_score": 90.0}},
        counterargument={"challenge_questions": ["Q1"], "evidence_sources": []}
    )

    # Case B: Argument with critical & high fallacies
    fallacious_eval = judge.evaluate(
        argument="Fallacious claim.",
        argument_analysis={"evaluation_criteria": {"clarity": 6, "relevance": 6, "evidence_strength": 3, "logical_consistency": 8, "persuasiveness": 5}, "argument_scoring": {"overall_score": 50.0}},
        fallacies={
            "detected_fallacies": [
                {"fallacy_type": "Ad Hominem", "severity": "Critical"},
                {"fallacy_type": "False Dilemma", "severity": "High"},
                {"fallacy_type": "Hasty Generalization", "severity": "Medium"}
            ],
            "credibility_assessment": {"credibility_score": 40.0}
        },
        counterargument={"challenge_questions": ["Q1"], "evidence_sources": []}
    )

    assert clean_eval.logical_consistency > fallacious_eval.logical_consistency
    assert fallacious_eval.logical_consistency < 60.0


def test_orchestrator_failure_handling():
    """Verify orchestrator returns structured failure status without fake 82 fallback on errors."""
    with patch("app.ai.orchestrator.graph_nodes.validate_debate_input", side_effect=Exception("LLM API Rate Limit Exceeded")):
        res = debate_orchestrator.invoke(
            session_id=999,
            argument="This is a test debate argument for error validation.",
            debate_format="One-on-One",
            difficulty="Intermediate"
        )

        assert res["execution_status"] == "failed"
        assert "errors" in res
        assert "LLM API Rate Limit Exceeded" in res["errors"][0]
        assert "argument_analysis" not in res
        assert res.get("performance", {}).get("overall_score") != 82.0


def test_complete_pipeline_fallacy_execution():
    """Integration test: Verify 8-agent pipeline execution produces non-static dynamic output."""
    cybersecurity_argument = (
        "Everyone knows that upgrading our firewall is completely useless because the IT manager is incompetent and irresponsible. "
        "Either we replace the entire network infrastructure immediately or our company will go bankrupt tomorrow. "
        "I talked to one employee yesterday who said his laptop was slow, which proves all computers across the entire company are infected with malware."
    )

    res = debate_orchestrator.invoke(
        session_id=1,
        argument=cybersecurity_argument,
        debate_format="One-on-One",
        difficulty="Intermediate",
        user_position="Affirmative",
        current_round=1
    )

    assert res["execution_status"] in ["completed", "in_progress"]
    assert "argument_analysis" in res
    assert "logical_fallacy_analysis" in res
    assert "counterargument" in res
    assert "ai_debate_opponent" in res
    assert "performance" in res
    assert "coaching" in res
    assert "recommendations" in res
    assert "learning_path" in res

    # Verify fallacies detected for clear fallacious input
    fallacies = res["logical_fallacy_analysis"].get("detected_fallacies", [])
    assert len(fallacies) > 0

    # Verify overall score is calculated from formula, not hardcoded 82.0
    overall = res["performance"].get("overall_score")
    cats = res["performance"].get("categories", {})
    expected_score = round(
        (cats["argument_quality"] * 0.30) +
        (cats["evidence_usage"] * 0.20) +
        (cats["logical_consistency"] * 0.20) +
        (cats["rebuttal_effectiveness"] * 0.15) +
        (cats["communication_skills"] * 0.15),
        2
    )
    assert abs(overall - expected_score) < 0.05
