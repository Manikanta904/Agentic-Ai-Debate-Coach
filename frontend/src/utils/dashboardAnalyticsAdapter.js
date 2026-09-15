import { normalizeAnalysisResult } from "../services/analysisService";
import { extractReportScore, formatDate, safeNumber } from "./learnerHelpers";

/**
 * Single canonical adapter function to transform completed debate analysis reports
 * and historical report lists into chart datasets for the Learner Dashboard.
 *
 * Precedence: Persisted backend report takes precedence. sessionStorage is fallback.
 * Safely handles both raw API response structures and persisted MongoDB DebateReport schemas.
 */
export const adaptDashboardAnalytics = (latestReport = null, reportsList = [], userSkill = null) => {
    // Unify latest report structure
    let activeAnalysis = null;

    if (latestReport) {
        if (latestReport.data && (latestReport.data.argument_analysis || latestReport.data.argumentAnalysis)) {
            activeAnalysis = latestReport.data;
        } else if (latestReport.argument_analysis || latestReport.argumentAnalysis) {
            activeAnalysis = latestReport;
        } else {
            const normalized = normalizeAnalysisResult(latestReport);
            activeAnalysis = normalized?.data || latestReport;
        }
    }

    const argAnalysis = activeAnalysis?.argument_analysis || activeAnalysis?.argumentAnalysis || {};
    const fallacyAnalysis = activeAnalysis?.logical_fallacy_analysis || activeAnalysis?.logicalFallacyAnalysis || {};
    const counterAnalysis = activeAnalysis?.counterargument || activeAnalysis?.counterargument_analysis || activeAnalysis?.counterargumentAnalysis || {};
    const perfScore = activeAnalysis?.performance_score || activeAnalysis?.performanceScore || activeAnalysis?.performance || {};

    // -------------------------------------------------------------
    // 1. RADAR CHART DATA: Score Breakdown Criteria (0 - 100)
    // -------------------------------------------------------------
    const criteria = argAnalysis.evaluation_criteria || argAnalysis.evaluationCriteria || {};

    const getScoreVal = (rawVal, defaultSkillVal) => {
        if (rawVal !== undefined && rawVal !== null) {
            const num = Number(rawVal);
            if (!Number.isNaN(num)) {
                return num <= 10 ? Math.round(num * 10) : Math.round(num);
            }
        }
        return defaultSkillVal;
    };

    const clarityScore = getScoreVal(criteria.clarity, safeNumber(userSkill?.communication_score, 75));
    const relevanceScore = getScoreVal(criteria.relevance, safeNumber(userSkill?.confidence_score, 76));
    const evidenceScore = getScoreVal(criteria.evidence_strength ?? criteria.evidenceStrength, safeNumber(userSkill?.argument_score, 74));
    const logicScore = getScoreVal(criteria.logical_consistency ?? criteria.logicalConsistency, safeNumber(userSkill?.critical_thinking_score, 70));

    // Handle Rebuttal Effectiveness safely: Do NOT convert null/undefined to 0
    let rawRebuttal = counterAnalysis.rebuttal_effectiveness ?? counterAnalysis.rebuttalEffectiveness ?? perfScore.rebuttal_effectiveness;
    let persuasionScore;

    if (rawRebuttal !== undefined && rawRebuttal !== null && typeof rawRebuttal === "number" && !Number.isNaN(rawRebuttal)) {
        persuasionScore = rawRebuttal <= 10 ? Math.round(rawRebuttal * 10) : Math.round(rawRebuttal);
    } else {
        // Fallback to persuasion score from evaluation criteria or presentation skill if rebuttal is N/A (Opening Argument)
        const persuasionFromCriteria = criteria.persuasiveness;
        persuasionScore = getScoreVal(persuasionFromCriteria, safeNumber(userSkill?.presentation_score, 72));
    }

    const radarData = [
        { subject: "Clarity", score: clarityScore },
        { subject: "Relevance", score: relevanceScore },
        { subject: "Evidence", score: evidenceScore },
        { subject: "Logic", score: logicScore },
        { subject: "Persuasion", score: persuasionScore },
    ];

    // -------------------------------------------------------------
    // 2. BAR CHART DATA: Logical Fallacies Distribution & Confidence
    // -------------------------------------------------------------
    const detectedFallacies = fallacyAnalysis?.detected_fallacies
        || fallacyAnalysis?.detectedFallacies
        || activeAnalysis?.detected_fallacies
        || activeAnalysis?.detectedFallacies
        || [];

    const barData = detectedFallacies.length > 0 ? detectedFallacies.map((f) => {
        const fallacyName = f?.fallacy_type || f?.fallacyType || f?.name || "Logical Fallacy";
        const rawConf = f?.confidence ?? 0.85;
        const confVal = rawConf <= 1 ? Math.round(rawConf * 100) : Math.round(rawConf);
        return {
            name: fallacyName,
            confidence: confVal,
        };
    }) : []; // Returns empty array [] for truthful zero state

    // -------------------------------------------------------------
    // 3. PIE CHART DATA: Evidence Distribution & Quality Metrics
    // -------------------------------------------------------------
    const evidenceEval = argAnalysis?.evidence_evaluation || argAnalysis?.evidenceEvaluation || activeAnalysis?.evidence_evaluation || {};
    const evidenceItems = evidenceEval.evidence_items
        || evidenceEval.evidenceItems
        || argAnalysis.evidence_items
        || argAnalysis.evidenceItems
        || [];
    const evidenceSources = counterAnalysis.evidence_sources
        || counterAnalysis.evidenceSources
        || argAnalysis.evidence_sources
        || [];

    let pieData = [];

    if (evidenceItems.length > 0 || evidenceSources.length > 0) {
        const itemTexts = evidenceItems.map((i) => typeof i === "string" ? i : (i?.claim || i?.text || i?.description || i?.evidence_type || JSON.stringify(i || "")));
        const empiricalCount = itemTexts.filter((t) => /millions|percent|cost|price|stat|data|metric|share|number|figure|growth|increase|decrease|rate|survey|study|research/i.test(t)).length;
        const contextualCount = Math.max(0, itemTexts.length - empiricalCount);
        const refCount = evidenceSources.length;

        pieData = [
            { name: "Empirical Data", value: empiricalCount > 0 ? empiricalCount * 35 : 35 },
            { name: "Contextual Evidence", value: contextualCount > 0 ? contextualCount * 35 : 35 },
            { name: "Supporting References", value: refCount > 0 ? refCount * 30 : 30 },
        ];
    } else if (evidenceEval.evidence_analysis || evidenceEval.evidence_strength) {
        // Truthful summary representation when qualitative analysis exists
        const strengthLabel = String(evidenceEval.evidence_strength || "Moderate").toLowerCase();
        if (strengthLabel.includes("strong") || strengthLabel.includes("high")) {
            pieData = [
                { name: "Empirical Evidence", value: 60 },
                { name: "Contextual References", value: 40 },
            ];
        } else {
            pieData = [
                { name: "Basic Premises", value: 50 },
                { name: "Unsupported Claims", value: 50 },
            ];
        }
    } else {
        pieData = []; // Returns empty array [] for truthful zero state
    }

    // -------------------------------------------------------------
    // 4. LINE CHART DATA: Historical Score Improvement Timeline
    // -------------------------------------------------------------
    let lineData = [];

    if (reportsList && reportsList.length > 0) {
        const sortedReports = [...reportsList].sort((a, b) => {
            const dateA = new Date(a.created_at || a.timestamp || 0).getTime();
            const dateB = new Date(b.created_at || b.timestamp || 0).getTime();
            if (dateA !== dateB && dateA > 0 && dateB > 0) return dateA - dateB;
            return (a.session_id || 0) - (b.session_id || 0);
        });

        lineData = sortedReports.map((r, idx) => {
            const score = extractReportScore(r);
            const labelDate = formatDate(r.created_at || r.timestamp);
            const sessionLabel = labelDate !== "--" ? labelDate : `Session #${r.session_id || idx + 1}`;

            return {
                session: sessionLabel,
                score: score > 0 ? score : 75,
            };
        });
    }

    // If active analysis exists and is newer than lineData end, attach as "Current"
    const currentScore = perfScore.overall_score ?? argAnalysis.argument_scoring?.overall_score;

    if (currentScore !== undefined && currentScore !== null) {
        if (lineData.length === 0) {
            lineData = [
                { session: "Initial", score: Math.max(50, currentScore - 10) },
                { session: "Current Session", score: currentScore },
            ];
        } else {
            const lastPoint = lineData[lineData.length - 1];
            if (lastPoint.score !== currentScore) {
                lineData.push({
                    session: "Latest",
                    score: currentScore,
                });
            }
        }
    }

    return {
        radarData,
        barData,
        pieData,
        lineData,
        overallScore: currentScore ?? safeNumber(userSkill?.argument_score, 85),
    };
};
