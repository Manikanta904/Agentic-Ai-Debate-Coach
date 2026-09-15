"""
AI Analysis API

Purpose:
    Exposes REST endpoints for AI-powered debate analysis.

Responsibilities:
    - Validate incoming requests.
    - Invoke the AI Analysis Service.
    - Return standardized API responses.

Note:
    This module should not contain AI logic.
"""

import asyncio
from fastapi import APIRouter, HTTPException, status

from app.schemas.ai_analysis import (
    ArgumentAnalysisRequest,
    AIAnalysisAPIResponse,
    AIAnalysisData,
)
from app.services.ai_analysis_service import ai_analysis_service
from app.ai.schemas.argument_analysis_schema import ArgumentAnalysisResponse
from app.ai.schemas.fallacy_detection_schema import FallacyDetectionResponse
from app.ai.schemas.milestone3_schema import (
    CounterargumentResponse,
    AIDebateOpponentResponse,
    JudgeCategoryScores,
    PerformanceScore,
    CoachingResponse,
    RecommendationResponse,
    LearningPathResponse,
)

router = APIRouter(
    prefix="/ai",
    tags=["AI Analysis"],
)


@router.post(
    "/analyze",
    response_model=AIAnalysisAPIResponse,
    status_code=status.HTTP_200_OK,
)
async def analyze_argument(
    request: ArgumentAnalysisRequest,
):
    """
    Perform complete AI analysis of a debate argument.

    Executes the full 8-agent AI Debate Coach pipeline:
        1. Argument Analysis
        2. Logical Fallacy Detection
        3. Counterargument Generation
        4. AI Debate Simulation / Opponent
        5. Judge Evaluation
        6. Performance Scoring
        7. Coaching
        8. Recommendation & Learning Path
    """

    try:
        workflow = await asyncio.to_thread(
            ai_analysis_service.analyze_with_workflow,
            session_id=request.session_id, argument=request.argument,
            debate_format=request.debate_format, difficulty=request.difficulty,
            user_position=request.user_position, current_round=request.current_round,
        )

        status_flag = workflow.get("execution_status", "completed")
        if status_flag == "failed":
            return AIAnalysisAPIResponse(
                success=False,
                message="AI analysis failed during execution.",
                data=AIAnalysisData(
                    session={
                        "session_id": request.session_id,
                        "debate_format": request.debate_format,
                        "difficulty": request.difficulty,
                        "user_position": request.user_position,
                        "current_round": request.current_round,
                    },
                    execution_status="failed",
                    errors=workflow.get("errors", ["AI analysis failed."]),
                    metadata=workflow.get("observability"),
                ),
            )

        data = AIAnalysisData(
            session={
                "session_id": request.session_id,
                "debate_format": request.debate_format,
                "difficulty": request.difficulty,
                "user_position": request.user_position,
                "current_round": request.current_round,
            },
            argument=request.argument,
            transcript={"transcript": request.argument},
            argument_analysis=ArgumentAnalysisResponse.model_validate(workflow["argument_analysis"]) if "argument_analysis" in workflow else None,
            logical_fallacy_analysis=FallacyDetectionResponse.model_validate(workflow["logical_fallacy_analysis"]) if "logical_fallacy_analysis" in workflow else None,
            counterargument_analysis=CounterargumentResponse.model_validate(workflow["counterargument"]) if "counterargument" in workflow else None,
            debate_simulation=AIDebateOpponentResponse.model_validate(workflow["ai_debate_opponent"]) if "ai_debate_opponent" in workflow else None,
            judge_evaluation=JudgeCategoryScores.model_validate(workflow.get("judge_categories") or workflow.get("judge_evaluation")) if ("judge_categories" in workflow or "judge_evaluation" in workflow) else None,
            performance_score=PerformanceScore.model_validate(workflow["performance"]) if "performance" in workflow else None,
            coaching=CoachingResponse.model_validate(workflow["coaching"]) if "coaching" in workflow else None,
            recommendations=RecommendationResponse.model_validate(workflow["recommendations"]) if "recommendations" in workflow else None,
            learning_path=LearningPathResponse.model_validate(workflow["learning_path"]) if "learning_path" in workflow else None,
            execution_status=status_flag,
            errors=workflow.get("errors", []),
            metadata=workflow.get("observability"),
        )

        return AIAnalysisAPIResponse(
            success=True,
            message="AI analysis completed successfully across the 8-agent pipeline.",
            data=data,
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI analysis error: {str(exc)}",
        ) from exc
