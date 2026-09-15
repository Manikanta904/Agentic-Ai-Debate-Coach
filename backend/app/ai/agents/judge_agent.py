from app.ai.schemas.milestone3_schema import JudgeCategoryScores

class JudgeAgent:
    """Deterministic judge: component scores derived directly from validated pipeline data."""
    def evaluate(self, **kwargs) -> JudgeCategoryScores:
        analysis = kwargs.get("argument_analysis", {})
        fallacies = kwargs.get("fallacies", {})
        counterargument = kwargs.get("counterargument", {})
        current_round = kwargs.get("current_round", 1)
        memory = kwargs.get("memory", {})

        recent_turns = memory.get("recent_turns", []) if isinstance(memory, dict) else []
        has_prior_opponent = any(isinstance(t, dict) and t.get("role") in ["assistant", "opponent"] for t in recent_turns)
        is_rebuttal = (current_round > 1) or has_prior_opponent

        criteria = analysis.get("evaluation_criteria", {}) if isinstance(analysis, dict) else {}
        scoring = analysis.get("argument_scoring", {}) if isinstance(analysis, dict) else {}
        detected = fallacies.get("detected_fallacies", []) if isinstance(fallacies, dict) else []
        credibility = fallacies.get("credibility_assessment", {}).get("credibility_score", 70) if isinstance(fallacies, dict) else 70

        # 1. Argument Quality (0-100)
        if "overall_score" in scoring and float(scoring.get("overall_score", 0)) > 0:
            argument_quality = float(scoring["overall_score"])
        else:
            clarity = float(criteria.get("clarity", 7))
            relevance = float(criteria.get("relevance", 7))
            persuasiveness = float(criteria.get("persuasiveness", 7))
            argument_quality = (clarity + relevance + persuasiveness) * 10.0 / 3.0

        # 2. Evidence Usage (0-100)
        ev_eval = analysis.get("evidence_evaluation", {}) if isinstance(analysis, dict) else {}
        ev_strength_str = ev_eval.get("evidence_strength", "Weak")
        ev_items = ev_eval.get("evidence_items", [])
        if ev_strength_str in ["Weak", "Very Weak"] or not ev_items:
            evidence_usage = min(45.0, float(credibility) * 0.5)
        else:
            ev_strength = float(criteria.get("evidence_strength", 5))
            evidence_usage = (ev_strength * 10.0 + float(credibility)) / 2.0

        # 3. Logical Consistency (0-100): Deduct deterministically for detected fallacies
        base_consistency = float(criteria.get("logical_consistency", 8)) * 10.0
        fallacy_penalty = 0.0
        for f in detected:
            sev = f.get("severity", "Medium") if isinstance(f, dict) else getattr(f, "severity", "Medium")
            if sev == "Critical":
                fallacy_penalty += 15.0
            elif sev == "High":
                fallacy_penalty += 10.0
            elif sev == "Medium":
                fallacy_penalty += 7.0
            else:
                fallacy_penalty += 4.0

        if not detected:
            fallacy_penalty = 0.0
        logical_consistency = max(0.0, min(100.0, base_consistency - fallacy_penalty))

        # 4. Rebuttal Effectiveness (0-100 or None)
        if is_rebuttal:
            challenge_qs = counterargument.get("challenge_questions", []) if isinstance(counterargument, dict) else []
            evidence_sources = counterargument.get("evidence_sources", []) if isinstance(counterargument, dict) else []
            rebuttal_effectiveness: float | None = min(100.0, max(40.0, 50.0 + min(len(challenge_qs) * 8, 24) + min(len(evidence_sources) * 10, 26)))
        else:
            rebuttal_effectiveness = None

        # 5. Communication Skills (0-100)
        c_clarity = float(criteria.get("clarity", 7))
        c_rel = float(criteria.get("relevance", 7))
        c_pers = float(criteria.get("persuasiveness", 7))
        communication_skills = (c_clarity + c_rel + c_pers) * 10.0 / 3.0

        rationale = [
            f"Argument quality scored at {round(argument_quality, 1)}/100 based on structural claim strength.",
            f"Evidence usage scored at {round(evidence_usage, 1)}/100 incorporating credibility and evidence quality.",
            f"Logical consistency scored at {round(logical_consistency, 1)}/100 with {len(detected)} detected fallacies ({round(fallacy_penalty, 1)} penalty points).",
        ]
        if is_rebuttal and rebuttal_effectiveness is not None:
            rationale.append(f"Rebuttal effectiveness scored at {round(rebuttal_effectiveness, 1)}/100 addressing opponent claims.")
        else:
            rationale.append("Rebuttal effectiveness: N/A (Opening argument submitted without prior opponent turn).")

        return JudgeCategoryScores(
            argument_quality=round(max(0.0, min(100.0, argument_quality)), 2),
            evidence_usage=round(max(0.0, min(100.0, evidence_usage)), 2),
            logical_consistency=round(max(0.0, min(100.0, logical_consistency)), 2),
            rebuttal_effectiveness=round(max(0.0, min(100.0, rebuttal_effectiveness)), 2) if rebuttal_effectiveness is not None else None,
            communication_skills=round(max(0.0, min(100.0, communication_skills)), 2),
            rationale=rationale,
        )

