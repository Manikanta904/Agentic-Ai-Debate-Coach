from app.ai.llm.structured_output import invoke_structured
from app.ai.schemas.milestone3_schema import LearningPathResponse


class LearningPathAgent:
    def create(self, **kwargs) -> LearningPathResponse:
        profile = kwargs.get("profile", {})
        previous_scores = kwargs.get("previous_scores", [])
        recommendations = kwargs.get("recommendations", {})

        system_msg = (
            "Create a progressive debate learning path. "
            "CRITICAL RULES: Keep descriptions concise (under 15 words each). "
            "Limit all lists (milestones, target_skills) to max 2 concise items each. Return structured output."
        )
        human_msg = (
            f"Profile: {profile}\n"
            f"Previous scores: {previous_scores}\n"
            f"Recommendations: {recommendations}"
        )

        messages = [
            ("system", system_msg),
            ("human", human_msg),
        ]
        return invoke_structured(messages, LearningPathResponse)
