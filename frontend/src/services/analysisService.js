import apiClient from "./apiClient";

/**
 * Normalizes raw backend API response from POST /api/v1/ai/analyze into a unified AnalysisResult structure.
 * Provides dual property aliases (camelCase & snake_case) to maintain 100% compatibility with existing UI components.
 */
export const normalizeAnalysisResult = (rawResponse) => {
    if (!rawResponse) return null;

    const payloadData = rawResponse.data ? rawResponse.data : rawResponse;
    const isSuccess = rawResponse.success !== undefined ? Boolean(rawResponse.success) : true;
    const responseMsg = rawResponse.message || "AI analysis complete.";

    const argAnalysis = payloadData.argument_analysis || payloadData.argumentAnalysis || {};
    const fallacyAnalysis = payloadData.logical_fallacy_analysis || payloadData.logicalFallacyAnalysis || {};
    const counterAnalysis = payloadData.counterargument_analysis || payloadData.counterargumentAnalysis || payloadData.counterargument || {};
    const simAnalysis = payloadData.debate_simulation || payloadData.debateSimulation || payloadData.ai_debate_opponent || {};
    const judgeEval = payloadData.judge_evaluation || payloadData.judgeEvaluation || payloadData.judge_categories || {};
    const perfScore = payloadData.performance_score || payloadData.performanceScore || payloadData.performance || {};
    const coachingData = payloadData.coaching || {};
    const recData = payloadData.recommendations || {};
    const pathData = payloadData.learning_path || payloadData.learningPath || {};

        const rawTranscriptVal = payloadData.transcript || rawResponse.transcript;

        const candidates = [
            payloadData.argument,
            payloadData.speech_text,
            rawResponse.argument,
            typeof rawTranscriptVal === "string" ? rawTranscriptVal : rawTranscriptVal?.transcript,
            argAnalysis.transcript,
            argAnalysis.argument_extraction?.original_argument,
            argAnalysis.argument,
        ].filter((c) => typeof c === "string" && c.trim() !== "");

        // Select longest candidate if multiple candidates exist (to avoid choosing short extracted primary claim over full speech)
        const fullSubmittedArgument = candidates.length > 0
            ? candidates.reduce((longest, current) => (current.length > longest.length ? current : longest), "")
            : null;

        let normalizedTranscript = null;
        if (fullSubmittedArgument) {
            normalizedTranscript = { transcript: fullSubmittedArgument };
        }

        const resolvedArgumentText = fullSubmittedArgument;

        const normalizedData = {
            session: payloadData.session || {
                session_id: payloadData.session_id || 1,
                debate_format: payloadData.debate_format || "One-on-One",
                difficulty: payloadData.difficulty || "Intermediate",
                user_position: payloadData.user_position || "Affirmative",
                current_round: payloadData.current_round || 1,
            },
            session_id: payloadData.session_id || payloadData.session?.session_id || 1,
            debate_format: payloadData.debate_format || payloadData.session?.debate_format || "One-on-One",
            argument: resolvedArgumentText,

            // Primary structured sections with dual alias compatibility
            argumentAnalysis: argAnalysis,
            argument_analysis: argAnalysis,

            logicalFallacyAnalysis: fallacyAnalysis,
            logical_fallacy_analysis: fallacyAnalysis,

            counterargumentAnalysis: counterAnalysis,
            counterargument_analysis: counterAnalysis,
            counterargument: counterAnalysis,

            debateSimulation: simAnalysis,
            debate_simulation: simAnalysis,
            ai_debate_opponent: simAnalysis,

            judgeEvaluation: judgeEval,
            judge_evaluation: judgeEval,

            performanceScore: perfScore,
            performance_score: perfScore,
            performance: perfScore,

            coaching: coachingData,
            recommendations: recData,

            learningPath: pathData,
            learning_path: pathData,

            executionStatus: payloadData.execution_status || "completed",
            execution_status: payloadData.execution_status || "completed",
            errors: payloadData.errors || [],
            metadata: payloadData.metadata || null,
            transcript: normalizedTranscript,
            speech_metrics: payloadData.speech_metrics || null,
        };

    return {
        success: isSuccess,
        message: responseMsg,
        data: normalizedData,
    };
};

export const analyzeArgument = async (payload) => {
    const requestPayload = {
        session_id: Number(payload.session_id || payload.sessionId || 1),
        argument: String(payload.argument || payload.speech_text || payload.speechText || "").trim(),
        debate_format: payload.debate_format || payload.debateFormat || "One-on-One",
        difficulty: payload.difficulty || "Intermediate",
        user_position: payload.user_position || payload.userPosition || "Affirmative",
        current_round: Number(payload.current_round || payload.currentRound || 1),
    };

    const response = await apiClient.post("/api/v1/ai/analyze", requestPayload);
    return normalizeAnalysisResult(response.data);
};

export const analyzeDebate = async (sessionId, speechText = "", mediaFile = null, extraFields = {}) => {
    // For text-based argument analysis without binary audio files, route through POST /api/v1/ai/analyze
    if (!mediaFile && speechText && speechText.trim() !== "") {
        return analyzeArgument({
            session_id: sessionId,
            argument: speechText,
            debate_format: extraFields.debate_format || extraFields.debateFormat || "One-on-One",
            difficulty: extraFields.difficulty || "Intermediate",
            user_position: extraFields.user_position || extraFields.userPosition || "Affirmative",
            current_round: extraFields.current_round || extraFields.currentRound || 1,
        });
    }

    const formData = new FormData();
    formData.append("session_id", sessionId);

    if (speechText && speechText.trim() !== "") {
        formData.append("speech_text", speechText);
    }

    if (mediaFile) {
        formData.append("media_file", mediaFile);
    }

    Object.entries(extraFields).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "") {
            formData.append(key, value);
        }
    });

    const response = await apiClient.post("/api/v1/debate/analyze", formData, {
        headers: {
            "Content-Type": "multipart/form-data",
        },
    });

    return normalizeAnalysisResult(response.data);
};

export const streamDebateAnalysis = async (payload) => {
    const response = await apiClient.post("/api/v1/debate/analyze/stream", payload);
    return normalizeAnalysisResult(response.data);
};

export default {
    normalizeAnalysisResult,
    analyzeArgument,
    analyzeDebate,
    streamDebateAnalysis,
};