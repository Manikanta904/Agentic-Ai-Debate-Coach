"""
Argument Analysis Agent

Purpose:
    Coordinates the complete argument analysis workflow by connecting
    the prompt, language model, and response schema via Groq native strict JSON schema.
"""

from app.ai.llm.structured_output import invoke_structured
from app.ai.prompts.argument_analysis_prompt import (
    ARGUMENT_ANALYSIS_SYSTEM_PROMPT,
)
from app.ai.schemas.argument_analysis_schema import (
    ArgumentAnalysisResponse,
)


class ArgumentAnalysisAgent:
    """
    AI Agent responsible for performing argument analysis.
    """

    def analyze_argument(
        self,
        argument: str,
    ) -> ArgumentAnalysisResponse:
        """
        Analyze a user's debate argument.

        Args:
            argument:
                User's debate argument.

        Returns:
            Structured ArgumentAnalysisResponse.
        """
        messages = [
            ("system", ARGUMENT_ANALYSIS_SYSTEM_PROMPT),
            ("human", argument),
        ]
        return invoke_structured(messages, ArgumentAnalysisResponse)