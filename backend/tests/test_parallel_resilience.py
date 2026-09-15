"""
Unit tests for parallel DAG resilience, schema token budgets, error isolation, and 429 immediate abort policies.
"""

import unittest
from unittest.mock import MagicMock, patch

from app.ai.llm.structured_output import STRUCTURED_OUTPUT_MAX_TOKENS, invoke_structured
from app.ai.scoring.scoring_engine import PerformanceScoringEngine
from app.ai.schemas.milestone3_schema import JudgeCategoryScores, CoachingResponse
from app.ai.schemas.fallacy_detection_schema import FallacyDetectionResponse


class TestParallelResilience(unittest.TestCase):

    def test_schema_token_budgets(self):
        """Verify schema-specific max token budgets are set appropriately."""
        self.assertEqual(STRUCTURED_OUTPUT_MAX_TOKENS.get("FallacyDetectionResponse"), 4096)
        self.assertEqual(STRUCTURED_OUTPUT_MAX_TOKENS.get("ArgumentAnalysisResponse"), 2560)
        self.assertEqual(STRUCTURED_OUTPUT_MAX_TOKENS.get("CounterargumentResponse"), 1536)
        self.assertEqual(STRUCTURED_OUTPUT_MAX_TOKENS.get("AIDebateOpponentResponse"), 1536)
        self.assertEqual(STRUCTURED_OUTPUT_MAX_TOKENS.get("CoachingResponse"), 1536)

    @patch("app.ai.llm.structured_output.get_groq_client")
    def test_http_429_tpd_daily_immediate_abort(self, mock_get_client):
        """Verify TPD daily quota 429 rate limit error aborts immediately without retry."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception(
            "Error code: 429 - Rate limit reached on tokens per day (TPD): Limit 200000, Used 199990"
        )

        with self.assertRaises(Exception) as ctx:
            invoke_structured([("user", "test")], CoachingResponse, max_retries=2)
        
        self.assertIn("tokens per day", str(ctx.exception).lower())
        # Ensure create() was called exactly 1 time (0 retries)
        self.assertEqual(mock_client.chat.completions.create.call_count, 1)

    @patch("app.ai.llm.structured_output.get_groq_client")
    def test_transient_error_single_retry(self, mock_get_client):
        """Verify transient/json_validate_failed errors are retried once."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # First call fails with json_validate_failed, second call succeeds
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"strengths":["Good structure"],"weaknesses":["Lacks data"],"rewrite_suggestions":["Add stats"],"practice_advice":["Practice"],"next_actions":["Debate"]}'
        
        mock_client.chat.completions.create.side_effect = [
            Exception("json_validate_failed"),
            mock_response
        ]

        res = invoke_structured([("user", "test")], CoachingResponse, max_retries=2)
        self.assertIsInstance(res, CoachingResponse)
        self.assertEqual(mock_client.chat.completions.create.call_count, 2)

    def test_deterministic_scoring_renormalization(self):
        """Verify opening argument formula (AQ=45, EU=17.5, LC=12, RE=None, CS=60) = 33.41."""
        cats = JudgeCategoryScores(
            argument_quality=45.0,
            evidence_usage=17.5,
            logical_consistency=12.0,
            rebuttal_effectiveness=None,
            communication_skills=60.0,
            rationale=["Test rationale"]
        )
        perf = PerformanceScoringEngine.calculate(cats)
        expected_score = round((45.0 * 0.30 + 17.5 * 0.20 + 12.0 * 0.20 + 60.0 * 0.15) / 0.85, 2)
        self.assertEqual(expected_score, 33.41)
        self.assertEqual(perf.overall_score, 33.41)

    @patch("app.ai.orchestrator.graph_nodes.fallacy_agent")
    @patch("app.ai.orchestrator.graph_nodes.argument_agent")
    @patch("app.ai.orchestrator.graph_nodes.counter_agent")
    @patch("app.ai.orchestrator.graph_nodes.opponent_agent")
    def test_preserved_parallel_outputs_on_branch_failure(self, mock_opp, mock_counter, mock_arg, mock_fallacy):
        """
        Verify that when fallacy_detection fails permanently, successful parallel outputs
        (argument_analysis, counterargument, opponent) are preserved in state, while
        execution_status is set to 'failed' and no fake fallacies are created.
        """
        from app.ai.orchestrator.debate_graph import debate_orchestrator
        
        # Mocks
        mock_arg.analyze_argument.return_value = {"executive_summary": "Good arg"}
        mock_counter.generate.return_value = MagicMock(
            logical_rebuttal="Rebuttal", evidence_rebuttal="", ethical_rebuttal="",
            practical_or_policy_rebuttal="", challenge_questions=[], debate_strategies=[],
            evidence_sources=[]
        )
        mock_opp.respond.return_value = MagicMock(
            opponent_response="Opponent text", opponent_position="Con", challenge="Q", next_turn_guidance="N"
        )
        # Fallacy agent raises an exception permanently
        mock_fallacy.detect_fallacies.side_effect = Exception("json_validate_failed permanently")

        result = debate_orchestrator.invoke(
            session_id=999,
            argument="Subsidies should be mandatory for green technology.",
            user_id=1
        )

        # 1. Successful outputs must be preserved
        self.assertIsNotNone(result.get("argument_analysis"))
        self.assertIsNotNone(result.get("counterargument"))
        self.assertIsNotNone(result.get("ai_debate_opponent"))

        # 2. Failed branch must NOT create fake fallacies
        self.assertIsNone(result.get("logical_fallacy_analysis"))

        # 3. Execution status must be 'failed'
        self.assertEqual(result.get("execution_status"), "failed")

        # 4. Error must be logged
        self.assertTrue(any("fallacy_detection" in err for err in result.get("errors", [])))


if __name__ == "__main__":
    unittest.main()
