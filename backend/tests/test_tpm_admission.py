"""
Unit tests for process-wide TPMAdmissionController, rolling 60s token budgeting,
semaphore concurrency control, usage reconciliation, and TPD vs TPM error classification.
"""

import time
import unittest
from unittest.mock import MagicMock, patch

from app.ai.llm.structured_output import (
    TPMAdmissionController,
    STRUCTURED_OUTPUT_MAX_TOKENS,
    invoke_structured,
)
from app.ai.schemas.milestone3_schema import CoachingResponse


class TestTPMAdmissionController(unittest.TestCase):

    def test_token_budgets(self):
        """Verify explicit per-schema token budgets."""
        self.assertEqual(STRUCTURED_OUTPUT_MAX_TOKENS["FallacyDetectionResponse"], 4096)
        self.assertEqual(STRUCTURED_OUTPUT_MAX_TOKENS["ArgumentAnalysisResponse"], 2560)
        self.assertEqual(STRUCTURED_OUTPUT_MAX_TOKENS["CounterargumentResponse"], 1536)
        self.assertEqual(STRUCTURED_OUTPUT_MAX_TOKENS["AIDebateOpponentResponse"], 1536)
        self.assertEqual(STRUCTURED_OUTPUT_MAX_TOKENS["CoachingResponse"], 1536)
        self.assertEqual(STRUCTURED_OUTPUT_MAX_TOKENS["RecommendationResponse"], 1024)
        self.assertEqual(STRUCTURED_OUTPUT_MAX_TOKENS["LearningPathResponse"], 1024)

    def test_immediate_admission_within_ceiling(self):
        """Verify requests within safe ceiling (e.g. 5000 used + 1500 request <= 7000 ceiling) are admitted immediately."""
        controller = TPMAdmissionController(tpm_limit=8000, safety_margin=1000)
        # Simulate 5000 tokens consumed in history
        controller.consumed_history.append((time.time(), 5000))

        t0 = time.time()
        req_id = controller.admit_and_reserve(1500)
        t1 = time.time()

        self.assertIsNotNone(req_id)
        # Execution time should be < 0.1s (no wait)
        self.assertLess(t1 - t0, 0.5)

        # Reconcile actual usage (e.g. 1200 tokens)
        controller.reconcile(req_id, 1200, 1500)
        self.assertEqual(len(controller.active_reservations), 0)

    def test_admission_delay_above_ceiling(self):
        """Verify requests exceeding safe ceiling (e.g. 6800 used + 1500 request > 7000 ceiling) wait for window."""
        controller = TPMAdmissionController(tpm_limit=8000, safety_margin=1000)
        old_time = time.time() - 59.8  # Will expire in ~0.2 seconds
        controller.consumed_history.append((old_time, 6800))

        t0 = time.time()
        req_id = controller.admit_and_reserve(1500)
        t1 = time.time()

        self.assertIsNotNone(req_id)
        # Execution should have waited ~0.2-0.5s for old history to expire
        self.assertGreaterEqual(t1 - t0, 0.15)
        controller.release(req_id)

    @patch("app.ai.llm.structured_output.get_groq_client")
    def test_daily_quota_immediate_exit(self, mock_get_client):
        """Verify TPD daily quota error aborts immediately (0 retries)."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception(
            "Rate limit reached for model openai/gpt-oss-20b on tokens per day (TPD): Limit 200000, Used 199990"
        )

        with self.assertRaises(Exception) as ctx:
            invoke_structured([("user", "test")], CoachingResponse, max_retries=2)

        self.assertIn("tokens per day", str(ctx.exception).lower())
        # Ensure create() was called exactly 1 time (0 retries)
        self.assertEqual(mock_client.chat.completions.create.call_count, 1)

    @patch("app.ai.llm.structured_output.get_groq_client")
    def test_tpm_rate_limit_single_retry(self, mock_get_client):
        """Verify TPM rate limit error pauses controller and retries once."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"strengths":["Good logic"],"weaknesses":["Short"],"rewrite_suggestions":["Add facts"],"practice_advice":["Drill"],"next_actions":["Practice"]}'
        mock_response.usage.total_tokens = 250

        # First call fails with TPM 429, second call succeeds
        mock_client.chat.completions.create.side_effect = [
            Exception("Rate limit reached on tokens per minute (TPM): try again in 0.1s"),
            mock_response
        ]

        res = invoke_structured([("user", "test")], CoachingResponse, max_retries=2)
        self.assertIsInstance(res, CoachingResponse)
        self.assertEqual(mock_client.chat.completions.create.call_count, 2)


if __name__ == "__main__":
    unittest.main()
