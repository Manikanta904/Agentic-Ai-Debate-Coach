from app.ai.llm.structured_output import invoke_structured
from app.ai.schemas.milestone3_schema import CoachingResponse


class CoachingAgent:
    def coach(self, **kwargs) -> CoachingResponse:
        argument = kwargs.get("argument", "")
        score = kwargs.get("score", {})
        rationale = kwargs.get("rationale", [])
        fallacies = kwargs.get("fallacies", {})

        system_msg = (
            "You are an expert AI debate coach. Provide constructive feedback and clear rewrite suggestions based on the argument and score. "
            "CRITICAL RULES: If detected_fallacies is empty or missing, do NOT claim, invent, or reference logical fallacies in your strengths, weaknesses, or practice advice. "
            "Keep rewrite examples clean plain text without quotes. Keep rewrite suggestions extremely brief (1 short sentence, under 25 words). "
            "Limit all lists (strengths, weaknesses, rewrite_suggestions, practice_advice, next_actions) to at most 2 concise items each. Return structured output."
        )
        human_msg = (
            f"Argument: {argument}\n"
            f"Score: {score}\n"
            f"Judge Rationale: {rationale}\n"
            f"Detected Fallacies: {fallacies}"
        )

        messages = [
            ("system", system_msg),
            ("human", human_msg),
        ]
        return invoke_structured(messages, CoachingResponse)
