"""
Logical Fallacy Detection Agent

Purpose:
    Coordinates the complete logical fallacy detection workflow by
    connecting the prompt, language model, and response schema via Groq native strict JSON schema.
"""

from app.ai.llm.structured_output import invoke_structured
from app.ai.prompts.fallacy_detection_prompt import (
    FALLACY_DETECTION_SYSTEM_PROMPT,
)
from app.ai.schemas.fallacy_detection_schema import (
    FallacyDetectionResponse,
)


class FallacyDetectionAgent:
    """
    AI Agent responsible for detecting logical fallacies in debate arguments.
    """

    def detect_fallacies(
        self,
        argument: str,
        argument_analysis: dict | None = None,
    ) -> FallacyDetectionResponse:
        """
        Detect logical fallacies in a user's debate argument.

        Args:
            argument:
                User's debate argument.
            argument_analysis:
                Optional structured argument analysis output from previous node.

        Returns:
            Structured FallacyDetectionResponse.
        """
        input_text = f"Argument:\n{argument}"
        if argument_analysis and isinstance(argument_analysis, dict):
            claim = argument_analysis.get("claim_identification", {}).get("primary_claim", "")
            summary = argument_analysis.get("executive_summary", "")
            if claim or summary:
                input_text += f"\n\nContext: Primary Claim: {claim} | Summary: {summary}"

        messages = [
            ("system", FALLACY_DETECTION_SYSTEM_PROMPT),
            ("human", input_text),
        ]
        return invoke_structured(messages, FallacyDetectionResponse)