from app.ai.llm.structured_output import invoke_structured
from app.ai.schemas.milestone3_schema import AIDebateOpponentResponse


class AIDebateOpponentAgent:
    def respond(self, **kwargs) -> AIDebateOpponentResponse:
        user_position = kwargs.get("user_position", "Affirmative")
        argument = kwargs.get("argument", "")
        counterargument = kwargs.get("counterargument", {})
        debate_format = kwargs.get("debate_format", "One-on-One")
        difficulty = kwargs.get("difficulty", "Intermediate")
        memory = kwargs.get("memory", [])

        system_msg = (
            "You are the AI Debate Opponent Agent. "
            f"Act as a formidable, highly disciplined debate opponent opposing the user's position ({user_position}). "
            f"Directly dissect and attack the specific claims, premises, and evidence in the user's argument ({argument}). "
            "Provide a direct counterargument, challenge unbacked claims, and pose a sharp rebuttal question for the next round. "
            "CRITICAL RULES: Keep all text fields concise (under 20 words each). "
            f"Respect the debate format ({debate_format}), difficulty level ({difficulty}), and conversation memory."
        )
        human_msg = (
            f"Learner Argument: {argument}\n"
            f"Key Counterargument Points: {counterargument}\n"
            f"Format: {debate_format}\n"
            f"Difficulty: {difficulty}\n"
            f"Learner Position: {user_position}\n"
            f"Conversation Memory: {memory}"
        )

        messages = [
            ("system", system_msg),
            ("human", human_msg),
        ]
        return invoke_structured(messages, AIDebateOpponentResponse)
