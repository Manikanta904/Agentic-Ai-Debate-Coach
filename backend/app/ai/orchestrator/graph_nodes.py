"""LangGraph nodes. Agents never communicate through REST."""
from datetime import datetime, timezone
from time import perf_counter
from sqlalchemy.orm import Session
from app.ai.agents.argument_analysis_agent import ArgumentAnalysisAgent
from app.ai.agents.fallacy_detection_agent import FallacyDetectionAgent
from app.ai.agents.counterargument_agent import CounterargumentAgent
from app.ai.agents.ai_debate_opponent_agent import AIDebateOpponentAgent
from app.ai.agents.judge_agent import JudgeAgent
from app.ai.agents.coaching_agent import CoachingAgent
from app.ai.agents.recommendation_agent import RecommendationAgent
from app.ai.agents.learning_path_agent import LearningPathAgent
from app.ai.memory.conversation_memory import conversation_memory
from app.ai.rag.retriever import evidence_retriever
from app.ai.scoring.scoring_engine import PerformanceScoringEngine
from app.ai.llm.llm import llm
from app.db.database import SessionLocal
from app.models.debate_session import DebateSession
from app.models.user_skill import UserSkill
from app.mongodb.debate_repository import debate_repository

argument_agent, fallacy_agent = ArgumentAnalysisAgent(), FallacyDetectionAgent()
counter_agent, opponent_agent, judge_agent = CounterargumentAgent(), AIDebateOpponentAgent(), JudgeAgent()
coaching_agent, recommendation_agent, learning_path_agent = CoachingAgent(), RecommendationAgent(), LearningPathAgent()

def _dump(value): return value.model_dump() if hasattr(value, "model_dump") else value

def _time_node(state, name, func):
    t0 = perf_counter()
    res = func()
    elapsed = int((perf_counter() - t0) * 1000)
    timings = dict(state.get("node_timings", {}))
    timings[name] = elapsed
    res["node_timings"] = timings
    print(f"| {name:30s} | {elapsed:7d} ms |", flush=True)
    return res

def load_context(state):
    def run():
        context = {"profile": {}, "topic": {}, "previous_skill_snapshot": {}}
        db: Session = SessionLocal()
        try:
            debate = db.query(DebateSession).filter(DebateSession.id == state["session_id"]).first()
            if debate:
                state_user_id = debate.user_id
                context["user_id"] = state_user_id
                context["topic"] = {"id": debate.topic_id, "format": debate.debate_format}
                if debate.user and debate.user.profile:
                    context["profile"] = {"experience_level": debate.user.profile.experience_level, "learning_goals": debate.user.profile.learning_goals, "coaching_preferences": debate.user.profile.coaching_preferences}
                if debate.user and debate.user.skills:
                    skills = debate.user.skills
                    context["previous_skill_snapshot"] = {"communication": float(skills.communication_score or 0), "critical_thinking": float(skills.critical_thinking_score or 0), "argument": float(skills.argument_score or 0)}
        except Exception as exc:
            return {"context": context, "errors": state.get("errors", []) + [f"context: {exc}"]}
        finally: db.close()
        return {"context": context, "user_id": state.get("user_id") or context.get("user_id")}
    return _time_node(state, "load_context", run)

def load_memory(state):
    def run():
        try:
            res = conversation_memory.load(state["session_id"])
            return {"memory": res}
        except Exception as exc:
            return {
                "memory": {"recent_turns": [], "summary": "", "previous_scores": []},
                "errors": state.get("errors", []) + [f"memory: {exc}"],
            }
    return _time_node(state, "load_memory", run)

def argument_analysis(state):
    def run():
        try:
            res = _dump(argument_agent.analyze_argument(state["argument"]))
            return {"argument_analysis": res}
        except Exception as exc:
            print(f"[NODE ERROR argument_analysis]: {exc}", flush=True)
            err_list = list(state.get("errors", []))
            err_list.append(f"argument_analysis: {exc}")
            return {"argument_analysis": None, "errors": err_list}
    return _time_node(state, "argument_analysis", run)

def fallacy_detection(state):
    def run():
        try:
            res = _dump(fallacy_agent.detect_fallacies(argument=state["argument"], argument_analysis=state.get("argument_analysis")))
            return {"logical_fallacy_analysis": res}
        except Exception as exc:
            print(f"[NODE ERROR fallacy_detection]: {exc}", flush=True)
            err_list = list(state.get("errors", []))
            err_list.append(f"fallacy_detection: {exc}")
            return {"logical_fallacy_analysis": None, "errors": err_list}
    return _time_node(state, "fallacy_detection", run)

def counterargument_generation(state):
    def run():
        try:
            t_rag0 = perf_counter()
            evidence = evidence_retriever.retrieve(state["argument"])
            t_rag = int((perf_counter() - t_rag0) * 1000)
            print(f"   [RAG Retrieval Time: {t_rag} ms]", flush=True)

            result = counter_agent.generate(
                argument=state["argument"],
                argument_analysis=state.get("argument_analysis", {}),
                fallacies=state.get("logical_fallacy_analysis", {}),
                evidence=[_dump(item) for item in evidence],
                debate_format=state.get("debate_format", "One-on-One"),
                difficulty=state.get("difficulty", "Intermediate"),
                user_position=state.get("user_position", "Affirmative"),
                topic=state.get("context", {}).get("topic", {})
            )
            if not evidence and hasattr(result, "evidence_sources"):
                result.evidence_sources = []
            return {
                "evidence": [_dump(item) for item in evidence],
                "retrieved_evidence": [_dump(item) for item in evidence],
                "counterargument": _dump(result)
            }
        except Exception as exc:
            print(f"[NODE ERROR counterargument_generation]: {exc}", flush=True)
            err_list = list(state.get("errors", []))
            err_list.append(f"counterargument_generation: {exc}")
            return {"counterargument": None, "errors": err_list}
    return _time_node(state, "counterargument_generation", run)

def ai_debate_opponent(state):
    def run():
        try:
            result = opponent_agent.respond(
                argument=state["argument"],
                counterargument=state.get("counterargument", {}),
                fallacies=state.get("logical_fallacy_analysis", {}),
                debate_format=state.get("debate_format", "One-on-One"),
                difficulty=state.get("difficulty", "Intermediate"),
                user_position=state.get("user_position", "Affirmative"),
                memory=state.get("memory", {}),
                current_round=state.get("current_round", 1)
            )
            return {"ai_debate_opponent": _dump(result)}
        except Exception as exc:
            print(f"[NODE ERROR ai_debate_opponent]: {exc}", flush=True)
            err_list = list(state.get("errors", []))
            err_list.append(f"ai_debate_opponent: {exc}")
            return {"ai_debate_opponent": None, "errors": err_list}
    return _time_node(state, "ai_debate_opponent", run)

def performance_scoring(state):
    def run():
        try:
            categories = judge_agent.evaluate(
                argument=state["argument"],
                argument_analysis=state.get("argument_analysis", {}),
                fallacies=state.get("logical_fallacy_analysis", {}),
                counterargument=state.get("counterargument", {}),
                opponent=state.get("ai_debate_opponent", {}),
                context=state.get("context", {}),
                current_round=state.get("current_round", 1),
                memory=state.get("memory", {})
            )
            perf = PerformanceScoringEngine.calculate(categories)
            return {
                "judge_categories": _dump(categories),
                "judge_evaluation": _dump(categories),
                "performance": _dump(perf)
            }
        except Exception as exc:
            print(f"[NODE ERROR performance_scoring]: {exc}", flush=True)
            err_list = list(state.get("errors", []))
            err_list.append(f"performance_scoring: {exc}")
            return {"judge_evaluation": None, "performance": None, "errors": err_list}
    return _time_node(state, "performance_scoring", run)

def coaching(state):
    def run():
        try:
            result = coaching_agent.coach(
                argument=state["argument"],
                score=state.get("performance", {}),
                rationale=state.get("judge_categories", {}).get("rationale", []),
                fallacies=state.get("logical_fallacy_analysis", {})
            )
            return {"coaching": _dump(result)}
        except Exception as exc:
            print(f"[NODE ERROR coaching]: {exc}", flush=True)
            err_list = list(state.get("errors", []))
            err_list.append(f"coaching: {exc}")
            return {"coaching": None, "errors": err_list}
    return _time_node(state, "coaching", run)

def recommendations(state):
    def run():
        try:
            result = recommendation_agent.recommend(
                score=state.get("performance", {}),
                weaknesses=state.get("coaching", {}).get("weaknesses", []),
                profile=state.get("context", {}).get("profile", {})
            )
            return {"recommendations": _dump(result)}
        except Exception as exc:
            print(f"[NODE ERROR recommendations]: {exc}", flush=True)
            err_list = list(state.get("errors", []))
            err_list.append(f"recommendations: {exc}")
            return {"recommendations": None, "errors": err_list}
    return _time_node(state, "recommendations", run)

def learning_path(state):
    def run():
        try:
            result = learning_path_agent.create(
                profile=state.get("context", {}).get("profile", {}),
                previous_scores=state.get("memory", {}).get("previous_scores", []),
                recommendations=state.get("recommendations", {}),
                user_skills=state.get("context", {}).get("previous_skill_snapshot", {})
            )
            return {"learning_path": _dump(result)}
        except Exception as exc:
            print(f"[NODE ERROR learning_path]: {exc}", flush=True)
            err_list = list(state.get("errors", []))
            err_list.append(f"learning_path: {exc}")
            return {"learning_path": None, "errors": err_list}
    return _time_node(state, "learning_path", run)

def progress_update(state):
    def run():
        db = SessionLocal()
        try:
            user_id = state.get("user_id")
            if user_id:
                skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).first()
                categories = state["performance"]["categories"]
                arg_s = round(categories["argument_quality"], 2)
                reb_eff = categories.get("rebuttal_effectiveness")
                if reb_eff is not None:
                    crit_s = round((categories["logical_consistency"] + float(reb_eff)) / 2.0, 2)
                else:
                    crit_s = round(categories["logical_consistency"], 2)
                comm_s = round(categories["communication_skills"], 2)

                if skills:
                    skills.argument_score = arg_s
                    skills.critical_thinking_score = crit_s
                    skills.communication_score = comm_s
                    skills.total_debates = (skills.total_debates or 0) + 1
                else:
                    skills = UserSkill(
                        user_id=user_id,
                        argument_score=arg_s,
                        critical_thinking_score=crit_s,
                        communication_score=comm_s,
                        presentation_score=0.0,
                        confidence_score=70.0,
                        total_debates=1,
                        total_presentations=0
                    )
                    db.add(skills)

                db.commit()
            return {"progress_updated": True}
        except Exception as exc:
            db.rollback(); return {"progress_updated": False, "errors": state.get("errors", []) + [f"progress_update: {exc}"]}
        finally: db.close()
    return _time_node(state, "progress_update", run)

def persist_results(state):
    def run():
        started = state.get("observability", {}).get("started_at")
        timer = state.get("observability", {}).get("timer", perf_counter())
        now = datetime.now(timezone.utc)
        execution_time = int((perf_counter() - timer) * 1000)
        metadata = {
            "model_used": getattr(llm, "model_name", None) or getattr(llm, "model", "configured-provider"),
            "latency_ms": execution_time,
            "execution_time_ms": execution_time,
            "token_usage": {},
            "errors": state.get("errors", []),
            "started_at": started,
            "completed_at": now.isoformat()
        }
        effective_user_id = state.get("user_id") or state.get("context", {}).get("user_id")
        state_to_save = dict(state)
        state_to_save["user_id"] = effective_user_id
        state_to_save["observability"] = metadata
        try:
            debate_repository.save_workflow_result(state["session_id"], effective_user_id, state_to_save)
            conversation_memory.save(state["session_id"], {"role": "user", "content": state["argument"], "round": state.get("current_round", 1)}, f"Latest claim: {state['argument'][:500]}", state.get("performance", {}).get("overall_score"))
            debate_repository.save_observability({"session_id": state["session_id"], "user_id": effective_user_id, **metadata})
        except Exception as exc:
            metadata["errors"].append(f"persistence: {exc}")
        return {"observability": metadata, **{k: v for k, v in state.items() if k != "observability"}}
    return _time_node(state, "persist_results", run)

