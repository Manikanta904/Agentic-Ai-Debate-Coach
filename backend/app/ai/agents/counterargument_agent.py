from app.ai.llm.structured_output import invoke_structured
from app.ai.schemas.milestone3_schema import CounterargumentResponse


class CounterargumentAgent:
    def generate(self, **kwargs) -> CounterargumentResponse:
        argument = kwargs.get("argument", "")
        argument_analysis = kwargs.get("argument_analysis", {})
        fallacies = kwargs.get("fallacies", {})
        evidence = kwargs.get("evidence", [])
        debate_format = kwargs.get("debate_format", "One-on-One")
        difficulty = kwargs.get("difficulty", "Intermediate")
        user_position = kwargs.get("user_position", "Affirmative")
        topic = kwargs.get("topic", {})

        system_msg = (
            "You are a debate counterargument specialist. Evaluate the argument, claims, and fallacies. "
            "CRITICAL RULES: Do NOT invent or fabricate external evidence sources. Set evidence_sources to [] unless relevant retrieved evidence was explicitly provided in the input. "
            "Keep all rebuttals under 15 words each. Limit all lists (challenge_questions, debate_strategies) to max 2 concise items each. Return structured output."
        )
        human_msg = (
            f"Argument: {argument}\n"
            f"Argument Analysis: {argument_analysis}\n"
            f"Detected Fallacies: {fallacies}\n"
            f"Evidence: {evidence}\n"
            f"Format: {debate_format}\n"
            f"Difficulty: {difficulty}\n"
            f"Position: {user_position}\n"
            f"Topic: {topic}"
        )

        messages = [
            ("system", system_msg),
            ("human", human_msg),
        ]
        return invoke_structured(messages, CounterargumentResponse)
