import sys
import os
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.ai.orchestrator.debate_graph import debate_orchestrator
from app.ai.scoring.scoring_engine import PerformanceScoringEngine
from app.ai.schemas.milestone3_schema import JudgeCategoryScores
from app.ai.agents.judge_agent import JudgeAgent


class TestAIPipeline(unittest.TestCase):
    def test_scoring_engine_deterministic_formula(self):
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
        self.assertEqual(score.overall_score, expected)
        self.assertNotEqual(score.overall_score, 82.0)

    def test_judge_fallacy_deduction(self):
        """Verify JudgeAgent penalizes logical consistency when fallacies are present."""
        judge = JudgeAgent()

        clean_eval = judge.evaluate(
            argument="Well reasoned claim with empirical data.",
            argument_analysis={"evaluation_criteria": {"clarity": 8, "relevance": 8, "evidence_strength": 8, "logical_consistency": 9, "persuasiveness": 8}, "argument_scoring": {"overall_score": 85.0}},
            fallacies={"detected_fallacies": [], "credibility_assessment": {"credibility_score": 90.0}},
            counterargument={"challenge_questions": ["Q1"], "evidence_sources": []}
        )

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

        self.assertGreater(clean_eval.logical_consistency, fallacious_eval.logical_consistency)
        self.assertLess(fallacious_eval.logical_consistency, 60.0)

    def test_orchestrator_failure_handling(self):
        """Verify orchestrator returns structured failure status without fake 82 fallback on errors."""
        with patch("app.ai.orchestrator.debate_graph.validate_debate_input", side_effect=Exception("LLM API Rate Limit Exceeded")):
            res = debate_orchestrator.invoke(
                session_id=999,
                argument="This is a test debate argument for error validation.",
                debate_format="One-on-One",
                difficulty="Intermediate"
            )

            self.assertEqual(res["execution_status"], "failed")
            self.assertIn("errors", res)
            self.assertIn("LLM API Rate Limit Exceeded", res["errors"][0])
            self.assertNotIn("argument_analysis", res)
            self.assertNotEqual(res.get("performance", {}).get("overall_score"), 82.0)



if __name__ == "__main__":
    unittest.main()
