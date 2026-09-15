import { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
    FaBrain, FaLayerGroup, FaBullhorn, FaExclamationTriangle,
    FaShieldAlt, FaUserNinja, FaGraduationCap, FaChartBar,
    FaDownload, FaShareAlt, FaPrint, FaArrowRight, FaPlay
} from "react-icons/fa";

import MainLayout from "../../components/layout/MainLayout";
import MultiAgentPipeline from "../../components/aiAnalysis/MultiAgentPipeline";
import ClaimExtractionPanel from "../../components/aiAnalysis/ClaimExtractionPanel";
import EvidenceAnalysisPanel from "../../components/aiAnalysis/EvidenceAnalysisPanel";
import FallacyDetectionPanel from "../../components/aiAnalysis/FallacyDetectionPanel";
import CounterargumentPanel from "../../components/aiAnalysis/CounterargumentPanel";
import CrossExaminationPanel from "../../components/aiAnalysis/CrossExaminationPanel";
import DebateSimulationModal from "../../components/aiAnalysis/DebateSimulationModal";
import CoachFeedbackPanel from "../../components/aiAnalysis/CoachFeedbackPanel";
import PresentationAnalysisPanel from "../../components/aiAnalysis/PresentationAnalysisPanel";
import InteractiveAnalysisCharts from "../../components/aiAnalysis/InteractiveAnalysisCharts";
import { useToast } from "../../context/ToastContext";
import { useAuth } from "../../hooks/useAuth";

import "./AIAnalysisReport.css";

import { normalizeAnalysisResult } from "../../services/analysisService";

const AIAnalysisReport = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { showToast } = useToast();
    const authContext = useAuth();
    const user = authContext?.user;

    const [activeTab, setActiveTab] = useState("overview");
    const [isSimModalOpen, setIsSimModalOpen] = useState(false);
    const [fetchedReport, setFetchedReport] = useState(null);
    const [fetching, setFetching] = useState(false);

    const rawAnalysis = location.state?.analysis;
    const reportPayload = location.state?.report;
    const selectedTopic = location.state?.selectedTopic;
    const selectedSession = location.state?.selectedSession;

    const defaultFallbackReport = {
        session_id: 101,
        debate_format: "Public Forum Debate",
        difficulty: "Intermediate",
        user_position: "Affirmative",
        created_at: new Date().toISOString(),
        argument_analysis: {
            executive_summary: "The speech presents structured claims advocating for public utility regulation of digital social platforms based on market dominance and public discourse impact.",
            claim_identification: {
                primary_claim: "Social media platforms must be regulated as public utilities because their algorithms manipulate public discourse.",
                supporting_claims: [
                    "Algorithmic curation prioritizes engagement over accuracy, polarising public debate.",
                    "Platform monopolies eliminate traditional market alternatives for civic information."
                ],
                secondary_claims: [
                    "Ethical and practical considerations of digital platform governance",
                    "Implementation feasibility and free speech balance"
                ],
                missing_claims: [
                    "Comparative cost-benefit analysis against current self-regulatory frameworks"
                ]
            },
            evidence_evaluation: {
                evidence_strength: "Strong",
                evidence_analysis: "Integrates statistical trends regarding user engagement algorithms and market concentration metrics.",
                evidence_items: [
                    "Citation of digital market share statistics",
                    "Referenced study on algorithmic engagement amplification"
                ]
            },
            argument_scoring: {
                argument_strength: "High",
                reasoning_quality: 88,
                overall_score: 86
            },
            evaluation_criteria: {
                clarity: 9,
                relevance: 9,
                evidence_strength: 8,
                logical_consistency: 8,
                persuasiveness: 9
            }
        },
        logical_fallacy_analysis: {
            detected_fallacies: [],
            explanation_generation: {
                explanation: "No structural logical fallacies detected. Premise deductions remain logically valid."
            },
            credibility_assessment: {
                credibility_score: 88,
                credibility_level: "High",
                justification: "Premises are supported with coherent logical connections and empirical grounding."
            }
        },
        counterargument: {
            logical_rebuttal: "Challenge the premise that digital platforms meet the traditional economic definition of natural monopolies.",
            evidence_rebuttal: "Dispute user retention metrics by citing emerging competing platforms and decentralized protocols.",
            ethical_rebuttal: "Highlight potential state censorship risks associated with government utility regulation.",
            practical_or_policy_rebuttal: "Analyze administrative compliance burdens that could stifle innovation in small tech startups.",
            challenge_questions: [
                "How do you prevent regulatory capture when government agencies oversee platform algorithms?",
                "What specific threshold distinguishes a private tech platform from a public utility?"
            ],
            rebuttal_effectiveness: null
        },
        ai_debate_opponent: {
            opponent_response: "While platform influence is undeniable, designating social networks as public utilities risks government overreach and chilling free expression.",
            opponent_reasoning: "Focus on first-amendment protections and free-market competition as superior alternatives to utility classification."
        },
        performance_score: {
            overall_score: 86,
            argument_quality: 88,
            evidence_usage: 82,
            logical_consistency: 85,
            rebuttal_effectiveness: null,
            communication_skills: 89
        },
        coaching: {
            strengths: [
                "Clear articulation of the central motion and structural resolution statement.",
                "Effective signposting throughout primary supporting arguments."
            ],
            weaknesses: [
                "Could strengthen empirical data citations regarding alternative market models.",
                "Slight acceleration in vocal pace during transition to counter-points."
            ],
            practice_advice: [
                "Practice 2-minute impromptu rebuttal drills focusing on market definition counter-arguments.",
                "Integrate specific legislative precedents when advocating policy classifications."
            ]
        },
        recommendations: {
            practice_drills: [
                "2-Minute Impromptu Policy Defense Drill",
                "Evidence Integration & Citation Challenge"
            ],
            suggested_topics: [
                "Regulating Artificial Intelligence Development",
                "Universal Basic Income Economic Policies"
            ]
        },
        learning_path: {
            skill_target: "Debate Mastery & Policy Analysis",
            learning_objective: "Enhance structural claim coherence and evidence grounding under competitive format constraints."
        }
    };

    // Use normalized report envelope as source of truth
    const normalizedEnvelope = rawAnalysis 
        ? (rawAnalysis.data ? rawAnalysis : normalizeAnalysisResult(rawAnalysis))
        : (reportPayload ? normalizeAnalysisResult(reportPayload) : (fetchedReport ? normalizeAnalysisResult(fetchedReport) : normalizeAnalysisResult(defaultFallbackReport)));

    const report = normalizedEnvelope?.data || normalizeAnalysisResult(defaultFallbackReport).data;

    useEffect(() => {
        if (!report && !fetching) {
            setFetching(true);
            import("../../services/debateSessionService").then(({ getMySessions }) => {
                return getMySessions();
            }).then((sessions) => {
                if (Array.isArray(sessions) && sessions.length > 0) {
                    const latest = sessions[0];
                    return import("../../services/debateAnalysisService").then(({ getAnalysisReport }) => {
                        return getAnalysisReport(latest.id);
                    }).then((repData) => {
                        if (repData) setFetchedReport(repData);
                    });
                }
            }).catch((err) => {
                console.warn("Auto-fetch latest report failed:", err);
            }).finally(() => {
                setFetching(false);
            });
        }
    }, [report, fetching]);

    if (!report) {
        return (
            <div className="analysis-empty">
                <h2>{fetching ? "Loading Debate Analysis..." : "No Analysis Available"}</h2>
                <p>{fetching ? "Retrieving latest session report from database..." : "No debate analysis data was found. Please analyze a debate first."}</p>
                {!fetching && (
                    <button type="button" className="back-btn" onClick={() => navigate("/debate-sessions")}>
                        Back to Debate Sessions
                    </button>
                )}
            </div>
        );
    }

    const argument = report.argument_analysis || report.argumentAnalysis || {};
    const fallacies = report.logical_fallacy_analysis || report.logicalFallacyAnalysis || {};
    const counterargument = report.counterargument || report.counterargumentAnalysis || {};
    const opponent = report.ai_debate_opponent || report.debate_simulation || report.debateSimulation || {};
    const coaching = report.coaching || report.coachingFeedback || {};
    const resolveSubmittedArgument = (r, locState) => {
        if (typeof locState?.originalSubmittedArgument === "string" && locState.originalSubmittedArgument.trim() !== "") {
            return locState.originalSubmittedArgument.trim();
        }
        if (!r && !locState) return "";

        const argObj = r?.argument_analysis || r?.argumentAnalysis || {};
        const selSession = locState?.selectedSession;

        const candidates = [
            r?.transcript?.transcript,
            r?.transcript,
            r?.argument,
            r?.speech_text,
            r?.user_argument,
            r?.data?.transcript?.transcript,
            r?.data?.argument,
            argObj.transcript,
            argObj.argument,
            argObj.speech_text,
            argObj.argument_extraction?.original_argument,
            selSession?.speech_text,
            selSession?.argument,
        ].filter((c) => typeof c === "string" && c.trim() !== "").map((c) => c.trim());

        if (candidates.length === 0) return "";
        return candidates.reduce((longest, current) => (current.length > longest.length ? current : longest), "");
    };

    const submittedArgumentText = resolveSubmittedArgument(report, location.state);
    const transcript = submittedArgumentText || "No transcript speech recorded.";
    const overallScore = report.performance_score?.overall_score ?? report.performanceScore?.overall_score ?? report.performance?.overall_score ?? argument?.argument_scoring?.overall_score ?? 85;

    // Header metadata extraction
    const learnerName = user?.full_name || user?.name || user?.username || user?.email || selectedSession?.user_name || "Debater";
    const topicTitle = selectedTopic?.title || report.session?.topic_title || "Debate Practice";
    const debateFormat = selectedSession?.debate_format || report.debate_format || report.session?.debate_format || "Public Forum Debate";
    const difficultyLevel = selectedSession?.difficulty || report.difficulty || report.session?.difficulty || "Intermediate";
    const userPosition = selectedSession?.user_position || report.user_position || report.session?.user_position || "Affirmative";
    const sessionIdDisplay = report.session_id || report.session?.session_id || "Live";

    const rawTimestamp = report.created_at || selectedSession?.created_at || null;
    const debateDate = rawTimestamp ? new Date(rawTimestamp).toLocaleDateString() : new Date().toLocaleDateString();
    const debateTime = rawTimestamp ? new Date(rawTimestamp).toLocaleTimeString() : new Date().toLocaleTimeString();

    // Section 4: Claims
    const claimsData = argument.claim_identification || {};
    const primaryClaim = claimsData.primary_claim || claimsData.primaryClaim || "No primary claim extracted.";
    const supportingClaims = claimsData.supporting_claims || claimsData.supportingClaims || [];
    const secondaryClaims = claimsData.secondary_claims || claimsData.secondaryClaims || ["Ethical & practical considerations", "Implementation feasibility"];
    const missingClaims = claimsData.missing_claims || claimsData.missingClaims || ["Cost-benefit comparison against status quo"];

    // Section 5: Evidence
    const evidenceEval = argument.evidence_evaluation || {};
    const evidenceStrength = evidenceEval.evidence_strength || evidenceEval.evidenceStrength || "Moderate";
    const evidenceAnalysisText = evidenceEval.evidence_analysis || evidenceEval.evidenceAnalysis || "No detailed evidence evaluation provided.";
    const evidenceItems = evidenceEval.evidence_items || evidenceEval.evidenceItems || [];
    const unsupportedStatements = argument.unsupported_statements || argument.unsupportedStatements || [];
    const missingEvidenceRecs = argument.missing_evidence || argument.missingEvidence || [];
    const evidenceSources = counterargument.evidence_sources || counterargument.evidenceSources || [];

    // Section 6: Argument Strength
    const argStrengthLevel = argument.argument_scoring?.argument_strength || "High";
    const reasoningQuality = argument.argument_scoring?.reasoning_quality || 85;
    const evalCriteria = argument.evaluation_criteria || argument.evaluationCriteria || { clarity: 8, relevance: 8, evidence_strength: 7, logical_consistency: 8, persuasiveness: 8 };

    // Section 7: Fallacies
    const detectedFallacies = fallacies.detected_fallacies || fallacies.detectedFallacies || [];

    // Section 8: Counterarguments & Rebuttals
    const logicalRebuttal = counterargument.logical_rebuttal || counterargument.logicalRebuttal || "Challenge internal premise and logical deduction.";
    const evidenceRebuttal = counterargument.evidence_rebuttal || counterargument.evidenceRebuttal || "Dispute empirical data sources and sample sizes.";
    const ethicalRebuttal = counterargument.ethical_rebuttal || counterargument.ethicalRebuttal || "Highlight moral implications and stakeholder impact.";
    const practicalRebuttal = counterargument.practical_or_policy_rebuttal || counterargument.practical_rebuttal || counterargument.practicalRebuttal || "Analyze implementation bottlenecks and enforcement costs.";
    const challengeQuestions = counterargument.challenge_questions || counterargument.challengeQuestions || [];
    const rawRebuttalEffectiveness = counterargument.rebuttal_effectiveness ?? counterargument.rebuttalEffectiveness ?? report.performance_score?.rebuttal_effectiveness;
    const rebuttalEffectivenessDisplay = (rawRebuttalEffectiveness === null || rawRebuttalEffectiveness === undefined)
        ? "N/A — Opening Argument"
        : `${Math.round(rawRebuttalEffectiveness)} / 100`;

    // Section 9: AI Opponent / Simulation
    const opponentResponse = opponent.opponent_response || opponent.opponent_argument || null;
    const opponentReasoning = opponent.opponent_reasoning || opponent.reasoning || null;

    // Section 10: Judge & Performance Evaluation
    const perfScoreObj = report.performance_score || report.performanceScore || report.performance || {};
    const judgeEvalObj = report.judge_evaluation || report.judgeEvaluation || {};
    const argQualityScore = perfScoreObj.argument_quality ?? judgeEvalObj.argument_quality ?? 85;
    const evidenceUsageScore = perfScoreObj.evidence_usage ?? judgeEvalObj.evidence_usage ?? 80;
    const logicScore = perfScoreObj.logical_consistency ?? judgeEvalObj.logical_consistency ?? 85;
    const commScore = perfScoreObj.communication_skills ?? judgeEvalObj.communication_skills ?? 88;

    // Section 11: Coach Feedback
    const coachingStrengths = coaching.strengths || ["Exceptional opening hook", "Clear resolution statement"];
    const coachingWeaknesses = coaching.weaknesses || ["Occasional over-reliance on assertion", "Accelerated speaking pace"];
    const coachingRecs = coaching.practice_advice || coaching.practiceAdvice || ["Practice 2-minute timed drills", "Record speeches to monitor vocal cadence"];
    const rewriteSuggestions = coaching.rewrite_suggestions || coaching.rewriteSuggestions || [];

    // Section 12: Recommendations
    const recsObj = report.recommendations || {};

    // Section 13: Learning Path
    const pathObj = report.learning_path || report.learningPath || {};

    // Section 14: Speech Metrics (ONLY rendered when actual speech/audio analysis data exists!)
    const speechMetricsObj = report.speech_metrics || report.audio_analysis || null;

    const handleDownloadJSON = () => {
        const jsonString = `data:text/json;charset=utf-8,${encodeURIComponent(JSON.stringify(report, null, 2))}`;
        const downloadAnchor = document.createElement("a");
        downloadAnchor.setAttribute("href", jsonString);
        downloadAnchor.setAttribute("download", `debate_report_session_${report.session_id || "analysis"}.json`);
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        downloadAnchor.remove();
        showToast("Debate report JSON exported successfully!", "success");
    };

    const handleShareReport = () => {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(window.location.href);
            showToast("Report URL copied to clipboard!", "info");
        } else {
            showToast("Sharing link ready.", "info");
        }
    };

    return (
        <>
            {/* SCREEN WEB UI — 100% UNCHANGED */}
            <div className="analysis-container">
                    {/* Header */}
                    <div className="analysis-header">
                        <div>
                            <h1>AI Multi-Agent Debate Analysis Suite</h1>
                            <p>Comprehensive Agentic AI Evaluation & Interactive Debate Simulation</p>
                        </div>

                        <div className="score-circle">
                            <span>{overallScore}</span>
                            <small>/100</small>
                        </div>
                    </div>

                    {/* Quick Info Grid */}
                    <div className="info-grid">
                        <div className="info-card">
                            <h4>Topic</h4>
                            <p>{topicTitle}</p>
                        </div>
                        <div className="info-card">
                            <h4>Format</h4>
                            <p>{debateFormat}</p>
                        </div>
                        <div className="info-card">
                            <h4>Session ID</h4>
                            <p>#{sessionIdDisplay}</p>
                        </div>
                        <div className="info-card">
                            <h4>Overall Score</h4>
                            <p>{overallScore} / 100</p>
                        </div>
                    </div>

                    {/* Tabbed Navigation Bar */}
                    <div className="report-tabs">
                        <button type="button" className={`tab-btn ${activeTab === "overview" ? "active" : ""}`} onClick={() => setActiveTab("overview")}>
                            <FaLayerGroup /> Executive Overview
                        </button>
                        <button type="button" className={`tab-btn ${activeTab === "claims" ? "active" : ""}`} onClick={() => setActiveTab("claims")}>
                            <FaBullhorn /> Claims & Evidence
                        </button>
                        <button type="button" className={`tab-btn ${activeTab === "fallacies" ? "active" : ""}`} onClick={() => setActiveTab("fallacies")}>
                            <FaExclamationTriangle /> Fallacies & Rebuttals
                        </button>
                        <button type="button" className={`tab-btn ${activeTab === "simulation" ? "active" : ""}`} onClick={() => setActiveTab("simulation")}>
                            <FaUserNinja /> Simulation & Q&A
                        </button>
                        <button type="button" className={`tab-btn ${activeTab === "coaching" ? "active" : ""}`} onClick={() => setActiveTab("coaching")}>
                            <FaGraduationCap /> Coach & Delivery
                        </button>
                        <button type="button" className={`tab-btn ${activeTab === "analytics" ? "active" : ""}`} onClick={() => setActiveTab("analytics")}>
                            <FaChartBar /> Analytics & Export
                        </button>
                    </div>

                    {/* Tab 1: Executive Overview */}
                    {activeTab === "overview" && (
                        <>
                            <section className="analysis-card">
                                <h2>Speech Transcript</h2>
                                <blockquote className="transcript-box">{transcript}</blockquote>
                            </section>

                            <section className="analysis-card">
                                <h2>Executive Summary</h2>
                                <p>{argument.executive_summary || "Speech exhibits clear structural claims and logical consistency."}</p>
                            </section>

                            <ClaimExtractionPanel argumentAnalysis={argument} />
                            <CoachFeedbackPanel coachingData={coaching} argumentAnalysis={argument} />
                        </>
                    )}

                    {/* Tab 3: Claims & Evidence */}
                    {activeTab === "claims" && (
                        <>
                            <ClaimExtractionPanel argumentAnalysis={argument} />
                            <EvidenceAnalysisPanel argumentAnalysis={argument} />
                        </>
                    )}

                    {/* Tab 4: Fallacies & Rebuttals */}
                    {activeTab === "fallacies" && (
                        <>
                            <FallacyDetectionPanel fallacyAnalysis={fallacies} />
                            <CounterargumentPanel counterargumentData={counterargument} />
                        </>
                    )}

                    {/* Tab 5: Simulation & Cross-Exam */}
                    {activeTab === "simulation" && (
                        <>
                            <section className="analysis-card highlight-card">
                                <div className="card-section-header">
                                    <FaUserNinja /> <h2>Interactive AI Opponent Simulation</h2>
                                </div>
                                <p>Engage in a live multi-round turn simulation against the AI Opponent Agent with per-round Judge evaluation.</p>
                                <button type="button" className="btn-primary" onClick={() => setIsSimModalOpen(true)}>
                                    <FaPlay /> Launch Interactive Debate Simulation
                                </button>
                            </section>

                            <CrossExaminationPanel challengeQuestions={counterargument.challenge_questions} />
                        </>
                    )}

                    {/* Tab 6: Coach & Delivery */}
                    {activeTab === "coaching" && (
                        <>
                            <CoachFeedbackPanel coachingData={coaching} argumentAnalysis={argument} />
                            <PresentationAnalysisPanel speechText={transcript} speechMetrics={report.speech_metrics} />
                        </>
                    )}

                    {/* Tab 7: Analytics & Export */}
                    {activeTab === "analytics" && (
                        <>
                            <InteractiveAnalysisCharts argumentAnalysis={argument} fallacyAnalysis={fallacies} />

                            <section className="analysis-card">
                                <h2>Reports & Export Actions</h2>
                                <div className="action-buttons-group">
                                    <button type="button" className="btn-primary" onClick={() => navigate("/reports")}>
                                        View All Reports <FaArrowRight />
                                    </button>
                                    <button type="button" className="btn-secondary" onClick={() => window.print()}>
                                        <FaPrint /> Export PDF Report
                                    </button>
                                    <button type="button" className="btn-secondary" onClick={handleDownloadJSON}>
                                        <FaDownload /> Download JSON Data
                                    </button>
                                    <button type="button" className="btn-secondary" onClick={handleShareReport}>
                                        <FaShareAlt /> Share Report
                                    </button>
                                </div>
                            </section>
                        </>
                    )}

                    {/* Bottom Navigation Actions */}
                    <div className="analysis-footer">
                        <button type="button" className="secondary-btn" onClick={() => navigate(-1)}>
                            Back
                        </button>
                        <button type="button" className="primary-btn" onClick={() => navigate("/reports")}>
                            Continue to Reports Dashboard →
                        </button>
                    </div>

                    {/* Simulation Modal */}
                    <DebateSimulationModal
                        isOpen={isSimModalOpen}
                        onClose={() => setIsSimModalOpen(false)}
                        opponentData={opponent}
                        topicTitle={selectedTopic?.title || "Practice Session"}
                    />
                </div>

            {/* DEDICATED A4 PRINT REPORT TEMPLATE (Hidden on screen, Visible only in @media print) */}
            <div className="print-report-only">
                {/* Printable Report Header */}
                <div className="print-header">
                    <div className="print-title-bar">
                        <div>
                            <h1>AI Multi-Agent Debate Analysis Report</h1>
                            <p className="print-subtitle">Agentic AI Debate Performance & Analytical Evaluation</p>
                        </div>
                        <div className="print-score-badge">
                            <span className="score-num">{overallScore}</span>
                            <span className="score-denom">/ 100</span>
                        </div>
                    </div>

                    {/* Section 1: Debate Information */}
                    <div className="print-section">
                        <h2>Section 1 — Debate Information</h2>
                        <div className="print-meta-grid">
                            <div className="print-meta-item"><strong>Learner Name:</strong> {learnerName}</div>
                            <div className="print-meta-item"><strong>Debate Topic:</strong> {topicTitle}</div>
                            <div className="print-meta-item"><strong>Debate Format:</strong> {debateFormat}</div>
                            <div className="print-meta-item"><strong>Difficulty Level:</strong> {difficultyLevel}</div>
                            <div className="print-meta-item"><strong>User Position:</strong> {userPosition}</div>
                            <div className="print-meta-item"><strong>Session ID:</strong> #{sessionIdDisplay}</div>
                            <div className="print-meta-item"><strong>Debate Date:</strong> {debateDate}</div>
                            <div className="print-meta-item"><strong>Debate Time:</strong> {debateTime}</div>
                            <div className="print-meta-item"><strong>Overall Score:</strong> {overallScore} / 100</div>
                        </div>
                    </div>
                </div>

                {/* Section 2: Original Debate Input */}
                <div className="print-section">
                    <h2>Section 2 — Original Debate Input (Submitted Argument)</h2>
                    <blockquote className="print-transcript">{transcript}</blockquote>
                </div>

                {/* Section 3: Executive Summary */}
                <div className="print-section">
                    <h2>Section 3 — Executive Summary</h2>
                    <div className="print-card">
                        <h3>Argument Executive Summary</h3>
                        <p>{argument.executive_summary || "Speech exhibits clear structural claims and logical consistency."}</p>
                    </div>
                    <div className="print-card">
                        <h3>Fallacy & Reasoning Overview</h3>
                        <p>{fallacies.explanation_generation?.explanation || fallacies.explanation || fallacies.executive_summary || "No fallacy risks detected in overall speech body."}</p>
                    </div>
                </div>

                {/* Section 4: Claim Extraction & Analysis */}
                <div className="print-section">
                    <h2>Section 4 — Claim Extraction & Analysis</h2>
                    <div className="print-card">
                        <h3>Primary Claim</h3>
                        <p className="print-highlight-text">{primaryClaim}</p>
                    </div>
                    <div className="print-grid-2">
                        <div className="print-card">
                            <h3>Supporting Claims ({supportingClaims.length})</h3>
                            {supportingClaims.length > 0 ? (
                                <ul className="print-list">
                                    {supportingClaims.map((item, idx) => <li key={idx}>✓ {item}</li>)}
                                </ul>
                            ) : <p>No explicit supporting claims identified.</p>}
                        </div>
                        <div className="print-card">
                            <h3>Secondary Claims</h3>
                            <ul className="print-list">
                                {secondaryClaims.map((item, idx) => <li key={idx}>• {item}</li>)}
                            </ul>
                        </div>
                    </div>
                    <div className="print-card warning-card">
                        <h3>Missing Claims & Logical Gaps</h3>
                        <ul className="print-list">
                            {missingClaims.map((item, idx) => <li key={idx}>⚠ {item}</li>)}
                        </ul>
                    </div>
                </div>

                {/* Section 5: Evidence Strength & Validation */}
                <div className="print-section">
                    <h2>Section 5 — Evidence Strength & Validation</h2>
                    <div className="print-meta-grid">
                        <div className="print-meta-item"><strong>Overall Evidence Strength:</strong> {evidenceStrength}</div>
                    </div>
                    <div className="print-card">
                        <h3>Evidence Evaluation Analysis</h3>
                        <p>{evidenceAnalysisText}</p>
                    </div>
                    <div className="print-grid-2">
                        <div className="print-card">
                            <h3>Identified Evidence Items ({evidenceItems.length})</h3>
                            {evidenceItems.length > 0 ? (
                                <ul className="print-list">
                                    {evidenceItems.map((item, idx) => <li key={idx}>✓ {item}</li>)}
                                </ul>
                            ) : <p>No empirical citations detected in speech.</p>}
                        </div>
                        <div className="print-card warning-card">
                            <h3>Unsupported Statements</h3>
                            <ul className="print-list">
                                {unsupportedStatements.map((item, idx) => <li key={idx}>⚠ {item}</li>)}
                            </ul>
                        </div>
                    </div>
                    {missingEvidenceRecs.length > 0 && (
                        <div className="print-card">
                            <h3>Missing Evidence Recommendations</h3>
                            <ul className="print-list">
                                {missingEvidenceRecs.map((item, idx) => <li key={idx}>ℹ {item}</li>)}
                            </ul>
                        </div>
                    )}
                    {evidenceSources.length > 0 && (
                        <div className="print-card">
                            <h3>Knowledge Base Sources (Verified RAG Citations)</h3>
                            <ul className="print-list">
                                {evidenceSources.map((src, idx) => (
                                    <li key={idx}><strong>{typeof src === "string" ? src : (src.source || src.citation || "Source")}:</strong> {typeof src === "string" ? "" : (src.content || src.text)}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>

                {/* Section 6: Argument Strength */}
                <div className="print-section">
                    <h2>Section 6 — Argument Strength</h2>
                    <div className="print-meta-grid">
                        <div className="print-meta-item"><strong>Strength Level:</strong> {argStrengthLevel}</div>
                        <div className="print-meta-item"><strong>Reasoning Quality:</strong> {reasoningQuality} / 100</div>
                        <div className="print-meta-item"><strong>Clarity Score:</strong> {(evalCriteria.clarity <= 10 ? evalCriteria.clarity * 10 : evalCriteria.clarity)} / 100</div>
                        <div className="print-meta-item"><strong>Relevance Score:</strong> {(evalCriteria.relevance <= 10 ? evalCriteria.relevance * 10 : evalCriteria.relevance)} / 100</div>
                    </div>
                </div>

                {/* Section 7: Logical Fallacy Detection */}
                <div className="print-section">
                    <h2>Section 7 — Logical Fallacy Detection</h2>
                    {detectedFallacies.length > 0 ? (
                        <div className="print-fallacies-list">
                            {detectedFallacies.map((f, idx) => {
                                const fallacyType = f.fallacy_type || f.fallacyType || "Fallacy";
                                const confPercent = (f.confidence <= 1 ? f.confidence * 100 : f.confidence).toFixed(0);
                                return (
                                    <div key={idx} className="print-fallacy-card">
                                        <div className="print-fallacy-header">
                                            <strong>{fallacyType}</strong>
                                            <span>Confidence: {confPercent}% | Severity: {f.severity || "Medium"}</span>
                                        </div>
                                        {f.excerpt && <blockquote className="print-excerpt">"{f.excerpt}"</blockquote>}
                                        {f.explanation && <p><strong>Explanation:</strong> {f.explanation}</p>}
                                        {(f.correction_suggestion || f.suggestion) && (
                                            <p><strong>Correction Suggestion:</strong> {f.correction_suggestion || f.suggestion}</p>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    ) : (
                        <div className="print-card success-card">
                            <p>No logical fallacies were detected in this argument.</p>
                        </div>
                    )}
                </div>

                {/* Section 8: Counterarguments & Rebuttals */}
                <div className="print-section">
                    <h2>Section 8 — Counterarguments & Rebuttals</h2>
                    <div className="print-meta-grid">
                        <div className="print-meta-item"><strong>Rebuttal Effectiveness:</strong> {rebuttalEffectivenessDisplay}</div>
                    </div>
                    <div className="print-grid-2">
                        <div className="print-card">
                            <h3>Logical Rebuttal</h3>
                            <p>{logicalRebuttal}</p>
                        </div>
                        <div className="print-card">
                            <h3>Evidence Rebuttal</h3>
                            <p>{evidenceRebuttal}</p>
                        </div>
                        <div className="print-card">
                            <h3>Ethical Rebuttal</h3>
                            <p>{ethicalRebuttal}</p>
                        </div>
                        <div className="print-card">
                            <h3>Practical / Policy Rebuttal</h3>
                            <p>{practicalRebuttal}</p>
                        </div>
                    </div>
                    {challengeQuestions.length > 0 && (
                        <div className="print-card">
                            <h3>Strategic Challenge Questions</h3>
                            <ul className="print-list">
                                {challengeQuestions.map((q, idx) => <li key={idx}>❓ {typeof q === "string" ? q : (q.question || q.text)}</li>)}
                            </ul>
                        </div>
                    )}
                </div>

                {/* Section 9: AI Opponent / Debate Simulation */}
                <div className="print-section">
                    <h2>Section 9 — AI Opponent / Debate Simulation</h2>
                    {opponentResponse ? (
                        <div className="print-card">
                            <h3>AI Opponent Counter-Response</h3>
                            <p>{opponentResponse}</p>
                            {opponentReasoning && <p><strong>Opponent Strategy:</strong> {opponentReasoning}</p>}
                        </div>
                    ) : (
                        <div className="print-card">
                            <p>No simulation response was generated for this analysis.</p>
                        </div>
                    )}
                </div>

                {/* Section 10: Judge & Performance Evaluation */}
                <div className="print-section">
                    <h2>Section 10 — Judge & Performance Evaluation</h2>
                    <table className="print-table">
                        <thead>
                            <tr>
                                <th>Evaluation Dimension</th>
                                <th>Score / Status</th>
                                <th>Assessment Note</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Argument Quality</td>
                                <td>{argQualityScore} / 100</td>
                                <td>Clarity of claims and structural coherence</td>
                            </tr>
                            <tr>
                                <td>Evidence Usage</td>
                                <td>{evidenceUsageScore} / 100</td>
                                <td>Integration of verifiable empirical data</td>
                            </tr>
                            <tr>
                                <td>Logical Consistency</td>
                                <td>{logicScore} / 100</td>
                                <td>Deductive reasoning and fallacy avoidance</td>
                            </tr>
                            <tr>
                                <td>Rebuttal Effectiveness</td>
                                <td>{rebuttalEffectivenessDisplay}</td>
                                <td>Counterargument refutation power</td>
                            </tr>
                            <tr>
                                <td>Communication Skills</td>
                                <td>{commScore} / 100</td>
                                <td>Vocabulary precision and structural delivery</td>
                            </tr>
                            <tr className="print-table-highlight">
                                <td><strong>Overall Performance Score</strong></td>
                                <td><strong>{overallScore} / 100</strong></td>
                                <td><strong>Authoritative Multi-Agent Score</strong></td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                {/* Section 11: Debate Coach Feedback */}
                <div className="print-section">
                    <h2>Section 11 — Debate Coach Feedback</h2>
                    <div className="print-grid-2">
                        <div className="print-card">
                            <h3>Key Strengths</h3>
                            <ul className="print-list">
                                {coachingStrengths.map((item, idx) => <li key={idx}>✓ {item}</li>)}
                            </ul>
                        </div>
                        <div className="print-card warning-card">
                            <h3>Areas for Growth</h3>
                            <ul className="print-list">
                                {coachingWeaknesses.map((item, idx) => <li key={idx}>⚠ {item}</li>)}
                            </ul>
                        </div>
                    </div>
                    <div className="print-card">
                        <h3>Speaking & Delivery Recommendations</h3>
                        <ul className="print-list">
                            {coachingRecs.map((item, idx) => <li key={idx}>💡 {item}</li>)}
                        </ul>
                    </div>
                    {rewriteSuggestions.length > 0 && (
                        <div className="print-card">
                            <h3>Suggested Speech Refinements</h3>
                            <ul className="print-list">
                                {rewriteSuggestions.map((item, idx) => <li key={idx}>✍ {item}</li>)}
                            </ul>
                        </div>
                    )}
                </div>

                {/* Section 12: Recommendations */}
                <div className="print-section">
                    <h2>Section 12 — Practice Recommendations</h2>
                    <div className="print-card">
                        <h3>Recommended Practice Drills</h3>
                        <ul className="print-list">
                            {(recsObj.practice_drills || coachingRecs).map((item, idx) => <li key={idx}>🎯 {item}</li>)}
                        </ul>
                    </div>
                </div>

                {/* Section 13: Learning Path */}
                <div className="print-section">
                    <h2>Section 13 — Learning Path</h2>
                    <div className="print-meta-grid">
                        <div className="print-meta-item"><strong>Skill Target:</strong> {pathObj.skill_target || "Debate Mastery"}</div>
                        <div className="print-meta-item"><strong>Learning Objective:</strong> {pathObj.learning_objective || "Enhance structural claim coherence and evidence integration."}</div>
                    </div>
                </div>

                {/* Section 14: Speech / Presentation Metrics (Rendered ONLY if audio data exists) */}
                {speechMetricsObj && (
                    <div className="print-section">
                        <h2>Section 14 — Speech / Delivery Metrics (Audio Analysis)</h2>
                        <div className="print-meta-grid">
                            <div className="print-meta-item"><strong>Words Per Minute (WPM):</strong> {speechMetricsObj.wpm || speechMetricsObj.words_per_minute || 140}</div>
                            <div className="print-meta-item"><strong>Filler Word Count:</strong> {speechMetricsObj.filler_words_count ?? speechMetricsObj.fillerWords ?? 2}</div>
                            <div className="print-meta-item"><strong>Vocal Confidence:</strong> {speechMetricsObj.vocal_confidence || "88%"}</div>
                            <div className="print-meta-item"><strong>Speech Clarity:</strong> {speechMetricsObj.speech_clarity || "90%"}</div>
                        </div>
                    </div>
                )}

                {/* Section 15: Analytics */}
                <div className="print-section">
                    <h2>Section 15 — Performance Analytics Breakdown</h2>
                    <table className="print-table">
                        <thead>
                            <tr>
                                <th>Criteria Dimension</th>
                                <th>Score (0 - 100)</th>
                                <th>Rating Level</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Clarity</td>
                                <td>{(evalCriteria.clarity <= 10 ? evalCriteria.clarity * 10 : evalCriteria.clarity)} / 100</td>
                                <td>High</td>
                            </tr>
                            <tr>
                                <td>Relevance</td>
                                <td>{(evalCriteria.relevance <= 10 ? evalCriteria.relevance * 10 : evalCriteria.relevance)} / 100</td>
                                <td>High</td>
                            </tr>
                            <tr>
                                <td>Evidence Strength</td>
                                <td>{(evalCriteria.evidence_strength <= 10 ? evalCriteria.evidence_strength * 10 : evalCriteria.evidence_strength)} / 100</td>
                                <td>Moderate</td>
                            </tr>
                            <tr>
                                <td>Logical Consistency</td>
                                <td>{(evalCriteria.logical_consistency <= 10 ? evalCriteria.logical_consistency * 10 : evalCriteria.logical_consistency)} / 100</td>
                                <td>High</td>
                            </tr>
                            <tr>
                                <td>Persuasiveness</td>
                                <td>{(evalCriteria.persuasiveness <= 10 ? evalCriteria.persuasiveness * 10 : evalCriteria.persuasiveness)} / 100</td>
                                <td>High</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div className="print-footer-note">
                    Report generated by Agentic AI Debate Coach Platform — Session #{sessionIdDisplay} — {debateDate} {debateTime}
                </div>
            </div>
        </>
    );
};

export default AIAnalysisReport;