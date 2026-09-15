import sys
import os
import json
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.main import app
from app.ai.scoring.scoring_engine import PerformanceScoringEngine
from app.ai.schemas.milestone3_schema import JudgeCategoryScores
from app.ai.schemas.argument_analysis_schema import EvidenceEvaluation
from app.ai.rag.vector_store import faiss_evidence_store
from app.ai.agents.judge_agent import JudgeAgent
from app.ai.agents.fallacy_detection_agent import FallacyDetectionAgent

class TestBackendHardening(unittest.TestCase):

    def test_deterministic_scoring_formula_known_numbers(self):
        """Part 5: Verify deterministic scoring formula with exact known test numbers (overall = 38.9)."""
        categories = JudgeCategoryScores(
            argument_quality=35.0,
            evidence_usage=32.5,
            logical_consistency=0.0,
            rebuttal_effectiveness=86.0,
            communication_skills=60.0
        )
        perf = PerformanceScoringEngine.calculate(categories)
        self.assertEqual(perf.overall_score, 38.9)

    def test_deterministic_scoring_formula_no_rebuttal(self):
        """Part 4 & 5: Verify normalized scoring formula when rebuttal_effectiveness is None."""
        categories = JudgeCategoryScores(
            argument_quality=35.0,
            evidence_usage=32.5,
            logical_consistency=0.0,
            rebuttal_effectiveness=None,
            communication_skills=60.0
        )
        perf = PerformanceScoringEngine.calculate(categories)
        # weighted_sum = 35*0.3 + 32.5*0.2 + 0*0.2 + 60*0.15 = 26.0
        # total_weight = 0.85
        # 26.0 / 0.85 = 30.5882 -> 30.59
        self.assertEqual(perf.overall_score, 30.59)

    def test_evidence_relevance_filtering(self):
        """Part 2 & 7: Verify unrelated knowledge base documents are filtered out."""
        query = "Cybersecurity AI firewalls network protection"
        results = faiss_evidence_store.search(query, limit=3)
        self.assertEqual(results, [], f"Expected empty evidence for unrelated cybersecurity query, got {results}")

    def test_evidence_strength_consistency_validator(self):
        """Part 3: Verify EvidenceEvaluation validator prevents contradiction between strength and analysis."""
        raw_data = {
            "evidence_items": [],
            "evidence_strength": "Strong",
            "evidence_analysis": "Limited evidence, overgeneralized."
        }
        eval_obj = EvidenceEvaluation.model_validate(raw_data)
        self.assertEqual(eval_obj.evidence_strength, "Weak")

    def test_opening_argument_no_rebuttal_judge(self):
        """Part 4: Verify opening argument (round 1) returns rebuttal_effectiveness=None."""
        judge = JudgeAgent()
        categories = judge.evaluate(
            argument="We should implement carbon taxes.",
            argument_analysis={"evaluation_criteria": {"clarity": 8, "relevance": 8, "persuasiveness": 8}},
            fallacies={"detected_fallacies": []},
            current_round=1,
            memory={"recent_turns": []}
        )
        self.assertIsNone(categories.rebuttal_effectiveness)


def run_live_groq_validations():
    """Live validation suite executing real requests against Groq API."""
    print("\n==================================================", flush=True)
    print("      RUNNING LIVE GROQ HARDENING VALIDATIONS      ", flush=True)
    print("==================================================\n", flush=True)

    fallacy_agent = FallacyDetectionAgent()

    # STEP 2 & STEP 3: Dedicated Straw Man Test
    straw_man_arg = (
        "My opponent says we should introduce reasonable limits on employee monitoring to protect privacy. "
        "Therefore, my opponent wants hackers to have unrestricted access to every company system and does not care about cybersecurity."
    )
    print("--- STEP 3. Dedicated Straw Man Test ---", flush=True)
    res_straw = fallacy_agent.detect_fallacies(straw_man_arg)
    print(f"Straw Man Argument Fallacies Detected Count: {len(res_straw.detected_fallacies)}", flush=True)
    straw_man_found = False
    for f in res_straw.detected_fallacies:
        print(f"   - [{f.severity}] {f.fallacy_type}: '{f.snippet}' -> {f.explanation}", flush=True)
        if f.fallacy_type == "Straw Man":
            straw_man_found = True
    print(f"Straw Man Detected Result: {'SUCCESS' if straw_man_found else 'FAILED'}\n", flush=True)

    # STEP 4: Clean Argument Test
    clean_arg = (
        "Traditional firewalls remain useful for network security, while AI-based "
        "security tools may improve threat detection. Organizations should compare "
        "both approaches using measurable security performance, cost, privacy, and "
        "maintenance requirements before deciding whether to adopt AI-based tools."
    )
    print("--- STEP 4. Testing Clean Argument ---", flush=True)
    res_clean = fallacy_agent.detect_fallacies(clean_arg)
    print(f"Clean Argument Fallacies Detected Count: {len(res_clean.detected_fallacies)} (Expected: 0)", flush=True)
    for f in res_clean.detected_fallacies:
        print(f"   - [{f.severity}] {f.fallacy_type}: '{f.snippet}'", flush=True)

    # STEP 5: Combined 8-Fallacy Argument Test
    combined_arg = (
        "Anyone who disagrees with our cybersecurity plan is completely clueless and unfit to work in IT. "
        "Our opponents claim we should throw away all traditional security tools and rely solely on magic, "
        "which is ridiculous. Either we deploy this expensive AI firewall across every server immediately "
        "or our entire corporation will be destroyed by hackers tomorrow. If we allow one employee to use "
        "an unapproved password manager, the entire global financial system will collapse. Dr. Smith, a world-famous "
        "cardiologist, insists that this AI firewall software is 100% impenetrable. We must buy this firewall "
        "because our official policy requires buying it. Yesterday I saw one software update fail, which proves that "
        "all technology upgrades always fail completely. Besides, why worry about firewall configuration when our company "
        "cafeteria serves terrible coffee?"
    )
    print("\n--- STEP 5. Testing Combined 8-Fallacy Argument ---", flush=True)
    res_comb = fallacy_agent.detect_fallacies(combined_arg)
    print(f"Combined Fallacies Detected Count: {len(res_comb.detected_fallacies)}", flush=True)
    detected_types = []
    for f in res_comb.detected_fallacies:
        print(f"   - [{f.severity}] {f.fallacy_type}: '{f.snippet}' -> {f.explanation}", flush=True)
        detected_types.append(f.fallacy_type)

    taxonomy = [
        "Ad Hominem", "Straw Man", "False Dilemma", "Slippery Slope",
        "Appeal to Authority", "Circular Reasoning", "Hasty Generalization", "Red Herring"
    ]
    print("\nTaxonomy Detection Breakdown:")
    for tax in taxonomy:
        found = tax in detected_types
        print(f"   - {tax}: {'DETECTED' if found else 'MISSED'}")

    # STEP 6: Full POST /api/v1/ai/analyze Live API Test
    print("\n--- STEP 6. Testing Full POST /api/v1/ai/analyze Endpoint ---", flush=True)
    client = TestClient(app)
    payload = {
        "session_id": 99,
        "argument": clean_arg,
        "debate_format": "One-on-One",
        "difficulty": "Intermediate",
        "user_position": "Affirmative",
        "current_round": 1
    }
    response = client.post("/api/v1/ai/analyze", json=payload)
    print(f"HTTP Status: {response.status_code}", flush=True)
    res_json = response.json()
    data = res_json.get("data", {})

    print(f"success: {res_json.get('success')}", flush=True)
    print(f"execution_status: {data.get('execution_status')}", flush=True)
    print(f"errors: {data.get('errors')}", flush=True)
    
    if data.get("counterargument_analysis"):
        sources = data["counterargument_analysis"].get("evidence_sources", [])
        print(f"evidence_sources count: {len(sources)} (Expected: 0)", flush=True)

    if data.get("judge_evaluation"):
        rebuttal_score = data["judge_evaluation"].get("rebuttal_effectiveness")
        print(f"rebuttal_effectiveness: {rebuttal_score} (Expected: None)", flush=True)

    if data.get("performance_score"):
        print(f"final overall_score: {data['performance_score'].get('overall_score')}%", flush=True)


if __name__ == "__main__":
    unittest.main(exit=False)
    run_live_groq_validations()
