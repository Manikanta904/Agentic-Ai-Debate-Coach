from app.ai.llm.structured_output import invoke_structured
from app.ai.schemas.milestone3_schema import RecommendationResponse


class RecommendationAgent:
    def recommend(self, **kwargs) -> RecommendationResponse:
        score = kwargs.get("score", {})
        weaknesses = kwargs.get("weaknesses", [])
        profile = kwargs.get("profile", {})

        system_msg = (
            "Recommend concrete debate practice appropriate to the learner. "
            "CRITICAL RULES: Keep descriptions concise (under 15 words each). "
            "Limit all lists (debate_topics, exercises, resources, practice_plan) to max 2 concise items each. Return structured output."
        )
        human_msg = (
            f"Score: {score}\n"
            f"Weaknesses: {weaknesses}\n"
            f"Profile: {profile}"
        )

        messages = [
            ("system", system_msg),
            ("human", human_msg),
        ]
        return invoke_structured(messages, RecommendationResponse)
