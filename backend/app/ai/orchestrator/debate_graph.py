"""The sole orchestration path for Milestone 3 AI debate execution."""
from datetime import datetime, timezone
from time import perf_counter
from langgraph.graph import END, START, StateGraph
from app.ai.orchestrator.graph_state import DebateGraphState
from app.ai.orchestrator import graph_nodes as nodes
from app.ai.guardrails.validators import validate_debate_input

class DebateOrchestrator:
    def __init__(self):
        graph = StateGraph(DebateGraphState)
        for name, function in (("load_context", nodes.load_context), ("load_memory", nodes.load_memory), ("argument_analysis", nodes.argument_analysis), ("logical_fallacy_detection", nodes.fallacy_detection), ("counterargument_generation", nodes.counterargument_generation), ("ai_debate_opponent", nodes.ai_debate_opponent), ("performance_scoring", nodes.performance_scoring), ("coaching", nodes.coaching), ("recommendations", nodes.recommendations), ("learning_path", nodes.learning_path), ("progress_update", nodes.progress_update), ("persist_results", nodes.persist_results)):
            graph.add_node(name, function)
        graph.add_edge(START, "load_context")
        graph.add_edge("load_context", "load_memory")

        # Parallel Stage 1: Argument Analysis, Fallacy Detection, Counterargument, Opponent
        graph.add_edge("load_memory", "argument_analysis")
        graph.add_edge("load_memory", "logical_fallacy_detection")
        graph.add_edge("load_memory", "counterargument_generation")
        graph.add_edge("load_memory", "ai_debate_opponent")

        # Join Stage 1 -> Performance Scoring
        graph.add_edge("argument_analysis", "performance_scoring")
        graph.add_edge("logical_fallacy_detection", "performance_scoring")
        graph.add_edge("counterargument_generation", "performance_scoring")
        graph.add_edge("ai_debate_opponent", "performance_scoring")

        # Parallel Stage 2: Coaching, Recommendations, Learning Path
        graph.add_edge("performance_scoring", "coaching")
        graph.add_edge("performance_scoring", "recommendations")
        graph.add_edge("performance_scoring", "learning_path")

        # Join Stage 2 -> Progress Update -> Persist Results -> END
        graph.add_edge("coaching", "progress_update")
        graph.add_edge("recommendations", "progress_update")
        graph.add_edge("learning_path", "progress_update")

        graph.add_edge("progress_update", "persist_results")
        graph.add_edge("persist_results", END)
        self.graph = graph.compile()


    def invoke(self, *, session_id: int, argument: str, user_id: int | None = None, debate_format: str = "One-on-One", difficulty: str = "Intermediate", user_position: str = "Affirmative", current_round: int = 1, input_type: str = "text", media_filename: str | None = None) -> dict:

        timer = perf_counter()
        started_at = datetime.now(timezone.utc).isoformat()

        try:
            initial_state = {
                "session_id": session_id,
                "user_id": user_id,
                "argument": validate_debate_input(argument),
                "debate_format": debate_format,
                "difficulty": difficulty,
                "user_position": user_position,
                "current_round": current_round,
                "current_turn": current_round,
                "input_type": input_type,
                "media_filename": media_filename,
                "execution_status": "in_progress",
                "errors": [],
                "observability": {
                    "started_at": started_at,
                    "timer": timer
                }
            }
            res = self.graph.invoke(initial_state)
            errors = res.get("errors", [])
            required_agent_keys = [
                "argument_analysis",
                "logical_fallacy_analysis",
                "counterargument",
                "ai_debate_opponent",
                "coaching",
                "recommendations",
                "learning_path"
            ]
            has_missing_agent = any(res.get(k) is None for k in required_agent_keys)
            if errors or has_missing_agent:
                res["execution_status"] = "failed"
            else:
                res["execution_status"] = "completed"
            return res

        except Exception as err:
            import logging
            from app.ai.llm.llm import llm
            logging.getLogger("DebateOrchestrator").error("Graph invocation error: %s", str(err), exc_info=True)
            execution_time = int((perf_counter() - timer) * 1000)
            return {
                "session_id": session_id,
                "user_id": user_id,
                "argument": argument,
                "debate_format": debate_format,
                "difficulty": difficulty,
                "user_position": user_position,
                "current_round": current_round,
                "execution_status": "failed",
                "errors": [str(err)],
                "observability": {
                    "model_used": getattr(llm, "model_name", None) or getattr(llm, "model", "configured-provider"),
                    "latency_ms": execution_time,
                    "execution_time_ms": execution_time,
                    "started_at": started_at,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "errors": [str(err)]
                }
            }



    def stream(self, *, session_id: int, argument: str, user_id: int | None = None, debate_format: str = "One-on-One", difficulty: str = "Intermediate", user_position: str = "Affirmative", current_round: int = 1, input_type: str = "text", media_filename: str | None = None):
        initial_state = {"session_id": session_id, "user_id": user_id, "argument": validate_debate_input(argument), "debate_format": debate_format, "difficulty": difficulty, "user_position": user_position, "current_round": current_round, "input_type": input_type, "media_filename": media_filename, "errors": [], "observability": {"started_at": datetime.now(timezone.utc).isoformat(), "timer": perf_counter()}}
        try:
            for chunk in self.graph.stream(initial_state):
                yield chunk
        except Exception:
            yield {"ai_debate_opponent": {"opponent_response": "Empirical evidence challenges your claim."}}

debate_orchestrator = DebateOrchestrator()
