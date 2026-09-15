"""Typed state shared only inside the LangGraph debate workflow."""
from typing import Any, TypedDict

class DebateGraphState(TypedDict, total=False):
    session_id: int
    user_id: int | None
    argument: str
    debate_topic: Any
    debate_format: str
    difficulty: str
    user_position: str
    current_round: int
    current_turn: int
    input_type: str
    media_filename: str | None
    user_context: dict[str, Any]
    recent_memory: dict[str, Any]
    running_summary: str
    context: dict[str, Any]
    memory: dict[str, Any]
    argument_analysis: Any
    logical_fallacy_analysis: Any
    retrieved_evidence: list[Any]
    evidence: list[Any]
    counterargument: Any
    ai_debate_opponent: Any
    judge_evaluation: Any
    judge_categories: Any
    performance: Any
    coaching: Any
    recommendations: Any
    learning_path: Any
    progress_updated: bool
    execution_status: str
    observability: dict[str, Any]
    errors: list[str]

