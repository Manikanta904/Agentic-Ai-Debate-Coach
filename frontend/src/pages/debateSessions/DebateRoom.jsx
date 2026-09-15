import { useEffect, useMemo, useState, useRef } from "react";
import { useNavigate, useParams, useLocation } from "react-router-dom";

import MainLayout from "../../components/layout/MainLayout";
import DebateHeader from "../../components/debateRoom/DebateHeader";
import SpeechEditor from "../../components/debateRoom/SpeechEditor";
import TranscriptPanel from "../../components/debateRoom/TranscriptPanel";
import RoundProgress from "../../components/debateRoom/RoundProgress";
import DebateTimer from "../../components/debateSessions/DebateTimer";
import SessionParticipants from "../../components/debateSessions/SessionParticipants";
import Breadcrumb from "../../components/common/Breadcrumb";
import RecordingPanel from "../../components/debateRoom/RecordingPanel";
import ErrorBoundary from "../../components/common/ErrorBoundary";

import { analyzeDebate } from "../../services/debateAnalysisService";
import { getSessionById, getParticipants, getRounds } from "../../services/debateSessionService";
import { getTopicById } from "../../services/debateTopicService";
import { formatDateTime, toArray } from "../../utils/learnerHelpers";

import { useToast } from "../../context/ToastContext";

import "./DebateRoom.css";

const DebateRoomContent = () => {
    const navigate = useNavigate();
    const { sessionId } = useParams();
    const location = useLocation();
    const { showToast } = useToast();

    const selectedTopic = location.state?.selectedTopic || null;
    const selectedSession = location.state?.selectedSession || null;

    const [session, setSession] = useState(null);
    const [topic, setTopic] = useState(selectedTopic);
    const [participants, setParticipants] = useState([]);
    const [rounds, setRounds] = useState([]);
    const [speech, setSpeech] = useState("");
    const [uploadedAudio, setUploadedAudio] = useState(null);
    const [uploadedVideo, setUploadedVideo] = useState(null);
    const [recordedAudioFile, setRecordedAudioFile] = useState(null);
    const [transcripts, setTranscripts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [analyzing, setAnalyzing] = useState(false);
    const [analysisStageText, setAnalysisStageText] = useState("");
    const [error, setError] = useState("");
    const [notice, setNotice] = useState("");

    const isSubmittingRef = useRef(false);

    useEffect(() => {
        let active = true;

        const loadRoom = async () => {
            try {
                setLoading(true);

                const sessionData = selectedSession || await getSessionById(sessionId);
                const topicData = selectedTopic || (sessionData?.topic_id ? await getTopicById(sessionData.topic_id).catch(() => null) : null);
                const [participantData, roundData] = await Promise.all([
                    getParticipants(sessionId).catch(() => []),
                    getRounds(sessionId).catch(() => []),
                ]);

                if (!active) return;

                setSession(sessionData);
                setTopic(topicData);
                setParticipants(toArray(participantData).map((participant) => ({
                    id: participant.id,
                    name: participant.role_in_session || `User ${participant.user_id}`,
                    position: participant.position,
                    ready: Boolean(participant.joined_at && !participant.left_at),
                })));
                setRounds(toArray(roundData).map((round) => ({
                    id: round.id,
                    name: round.round_name,
                    description: round.status || `Round ${round.round_number}`,
                    duration: `${round.duration_minutes} min`,
                })));
                setError("");
            } catch (loadError) {
                console.error(loadError);
                if (active) {
                    setError("Unable to load debate room right now.");
                }
            } finally {
                if (active) {
                    setLoading(false);
                }
            }
        };

        void loadRoom();

        return () => {
            active = false;
        };
    }, [selectedSession, selectedTopic, sessionId]);

    const sessionModel = useMemo(() => ({
        id: session?.id || sessionId,
        topic_title: topic?.title || `Session #${sessionId}`,
        topic_description: topic?.learning_goal || topic?.description || "",
        debate_format: session?.debate_format || topic?.debate_format || "Oxford Debate",
        position: session?.debate_position || session?.position || "Affirmative",
        status: session?.session_status || session?.status || "Live",
    }), [session, sessionId, topic]);

    const currentRound = useMemo(() => {
        const activeIndex = rounds.findIndex((round) => round.description.toLowerCase().includes("active"));
        return activeIndex >= 0 ? activeIndex : 0;
    }, [rounds]);

    const pushTranscript = (speaker, message) => {
        setTranscripts((current) => [
            ...current,
            {
                id: `${speaker}-${Date.now()}`,
                speaker,
                message,
                time: formatDateTime(new Date()),
            },
        ]);
    };

    const handleSpeechSubmit = async () => {
        if (isSubmittingRef.current || analyzing) return;

        const mediaFile = uploadedAudio || uploadedVideo || recordedAudioFile;
        const currentSpeechText = (speech || "").trim();

        if (!currentSpeechText && !mediaFile) {
            setNotice("Please type your speech or record/upload audio/video.");
            showToast("Please type your speech or record/upload audio/video.", "warning");
            return;
        }

        try {
            isSubmittingRef.current = true;
            setAnalyzing(true);
            setError("");
            setNotice("");

            if (mediaFile) {
                setAnalysisStageText("Uploading binary file to MongoDB GridFS & transcribing speech with Whisper...");
                showToast("Storing binary in GridFS & transcribing speech...", "info");
            } else {
                setAnalysisStageText("Orchestrating Multi-Agent AI Debate Pipeline...");
                showToast("Orchestrating Multi-Agent AI Debate Pipeline...", "info");
            }

            const response = await analyzeDebate(sessionModel.id, currentSpeechText, mediaFile, {
                debate_format: sessionModel.debate_format,
                user_position: sessionModel.position,
                difficulty: location.state?.difficulty || "Intermediate",
                current_round: currentRound + 1,
            });

            // Check if analysis failed on backend
            if (response?.success === false || response?.data?.execution_status === "failed") {
                const rawErr = response?.data?.errors?.[0] || response?.message || "";
                const isRateLimit = /rate limit|429|tpm|tpd|tokens per/i.test(rawErr);
                const userErrMsg = isRateLimit
                    ? "AI analysis is temporarily rate-limited by Groq API. Please try again shortly."
                    : (rawErr || "AI analysis could not be completed. Please try again.");
                
                setError(userErrMsg);
                showToast(userErrMsg, "error");
                return; // Do NOT navigate on failure
            }

            const assignmentId = location.state?.assignmentId;
            if (assignmentId) {
                try {
                    const { updatePracticeTaskStatus } = await import("../../services/coachService");
                    await updatePracticeTaskStatus(assignmentId, "AI_Analyzed", sessionModel.id);
                } catch (taskErr) {
                    console.warn("Could not update practice assignment status:", taskErr);
                }
            }

            const generatedTranscriptText = response?.data?.transcript?.transcript || currentSpeechText || "Submitted recording";

            pushTranscript("Learner", generatedTranscriptText);
            pushTranscript("AI Coach", response?.data?.ai_debate_opponent?.opponent_response || "Multi-agent debate analysis completed.");
            showToast("Multi-agent AI Analysis completed successfully!", "success");

            const analysisPayload = {
                ...response,
                argument: currentSpeechText,
                transcript: { transcript: generatedTranscriptText || currentSpeechText },
                data: response?.data ? {
                    ...response.data,
                    argument: currentSpeechText,
                    transcript: { transcript: generatedTranscriptText || currentSpeechText }
                } : response?.data
            };

            try {
                sessionStorage.setItem("latest_debate_analysis", JSON.stringify(analysisPayload));
            } catch (cacheErr) {
                console.warn("Could not cache latest debate analysis in sessionStorage:", cacheErr);
            }

            navigate("/ai-analysis-report", {
                state: {
                    analysis: analysisPayload,
                    originalSubmittedArgument: currentSpeechText,
                    selectedTopic: topic,
                    selectedSession: sessionModel,
                    assignmentId,
                },
            });
        } catch (submissionError) {
            console.error(submissionError);
            const errStr = String(submissionError?.message || submissionError || "");
            const isRateLimit = /rate limit|429|tpm|tpd|tokens per/i.test(errStr);
            const userErrMsg = isRateLimit
                ? "AI analysis is temporarily rate-limited by Groq API. Please try again shortly."
                : "Analysis failed. Please check backend server and retry.";
            setError(userErrMsg);
            showToast(userErrMsg, "error");
        } finally {
            setAnalyzing(false);
            setAnalysisStageText("");
            isSubmittingRef.current = false;
        }
    };

    const handleClearSpeech = () => {
        setSpeech("");
        showToast("Cleared speech text.", "info");
    };

    const handleSaveDraft = () => {
        setNotice("Draft saved locally.");
        showToast("Draft saved locally.", "success");
    };

    const handleLeaveRoom = () => {
        navigate(-1);
    };

    const handleAudioUpload = (file) => {
        setUploadedAudio(file);
        setUploadedVideo(null);
        setRecordedAudioFile(null);
        showToast(`Audio attached: ${file.name}`, "info");
    };

    const handleVideoUpload = (file) => {
        setUploadedVideo(file);
        setUploadedAudio(null);
        setRecordedAudioFile(null);
        showToast(`Video attached: ${file.name}`, "info");
    };

    const handleRecordingChange = (blob, file) => {
        setRecordedAudioFile(file);
        if (file) {
            setUploadedAudio(null);
            setUploadedVideo(null);
            showToast("Recorded speech ready for analysis!", "success");
        }
    };

    if (loading) {
        return (
            <MainLayout>
                <div className="debate-room-page">
                    <div className="empty-state">Loading debate room...</div>
                </div>
            </MainLayout>
        );
    }

    return (
        <MainLayout>
            <div className="debate-room-page">
                <Breadcrumb
                    items={[
                        { label: "Debate Topics", path: "/topics" },
                        { label: "Debate Sessions", path: "/debate-sessions" },
                        { label: "Session Details", path: `/debate-sessions/${sessionId}` },
                        { label: "Debate Room" },
                    ]}
                />

                {location.state?.assignmentId && (
                    <div style={{ background: "linear-gradient(135deg, #0F172A, #1E293B)", color: "#FFFFFF", padding: "16px 20px", borderRadius: "12px", marginBottom: "20px", borderLeft: "5px solid #3B82F6", boxShadow: "0 4px 12px rgba(0,0,0,0.15)" }}>
                        <div style={{ fontSize: "12px", textTransform: "uppercase", letterSpacing: "1px", color: "#93C5FD", fontWeight: 700 }}>Assigned Debate Practice</div>
                        <h3 style={{ margin: "6px 0 8px", fontSize: "18px", color: "#FFFFFF" }}>Topic: {location.state.topicTitle || topic?.title || "Assigned Practice Topic"}</h3>
                        <div style={{ display: "flex", gap: "20px", fontSize: "13px", flexWrap: "wrap", color: "#CBD5E1" }}>
                            <span><strong>Format:</strong> {location.state.debateFormat || sessionModel?.debate_format || "Oxford Debate"}</span>
                            <span><strong>Difficulty:</strong> {location.state.difficulty || "Intermediate"}</span>
                            <span><strong>Coach:</strong> {location.state.coachName || "Debate Coach"}</span>
                        </div>
                        {location.state.instructions && (
                            <p style={{ margin: "8px 0 0", fontSize: "13px", color: "#94A3B8", fontStyle: "italic" }}>
                                <strong>Instructions:</strong> "{location.state.instructions}"
                            </p>
                        )}
                    </div>
                )}

                <DebateHeader session={sessionModel} onLeave={handleLeaveRoom} />

                {error && (
                    <div style={{
                        background: "linear-gradient(135deg, #451A03, #78350F)",
                        color: "#FEF3C7",
                        padding: "20px 24px",
                        borderRadius: "12px",
                        marginBottom: "20px",
                        borderLeft: "5px solid #F59E0B",
                        boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        flexWrap: "wrap",
                        gap: "16px"
                    }}>
                        <div>
                            <h4 style={{ margin: "0 0 6px", fontSize: "16px", color: "#FDE68A" }}>⚠️ AI Analysis Could Not Be Completed</h4>
                            <p style={{ margin: 0, fontSize: "14px", color: "#FEF3C7" }}>{error}</p>
                        </div>
                        <div style={{ display: "flex", gap: "12px" }}>
                            <button
                                type="button"
                                onClick={handleSpeechSubmit}
                                disabled={analyzing}
                                style={{
                                    background: "#F59E0B",
                                    color: "#78350F",
                                    fontWeight: 700,
                                    border: "none",
                                    padding: "10px 18px",
                                    borderRadius: "8px",
                                    cursor: "pointer",
                                    fontSize: "14px"
                                }}
                            >
                                🔄 Retry Analysis
                            </button>
                            <button
                                type="button"
                                onClick={() => navigate("/topics")}
                                style={{
                                    background: "rgba(255,255,255,0.1)",
                                    color: "#FDE68A",
                                    fontWeight: 600,
                                    border: "1px solid rgba(253,230,138,0.3)",
                                    padding: "10px 18px",
                                    borderRadius: "8px",
                                    cursor: "pointer",
                                    fontSize: "14px"
                                }}
                            >
                                Back to Topics
                            </button>
                        </div>
                    </div>
                )}
                {notice && <div className="success-message">{notice}</div>}

                {analyzing && (
                    <div style={{
                        background: "linear-gradient(135deg, #1E293B, #0F172A)",
                        color: "#FFFFFF",
                        padding: "24px",
                        borderRadius: "12px",
                        marginBottom: "20px",
                        boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
                        display: "flex",
                        alignItems: "center",
                        gap: "16px"
                    }}>
                        <div className="spinner" style={{ fontSize: "28px", color: "#3B82F6" }}>⚡</div>
                        <div>
                            <h3 style={{ margin: "0 0 4px", fontSize: "18px", color: "#F8FAFC" }}>Analyzing Debate with AI Coach...</h3>
                            <p style={{ margin: 0, fontSize: "14px", color: "#94A3B8" }}>{analysisStageText || "Evaluating argument quality, speech metrics, logical consistency, counter-points, and coaching recommendations."}</p>
                        </div>
                    </div>
                )}

                <div className="debate-grid">
                    <div className="debate-main">
                        <SpeechEditor
                            value={speech}
                            speechText={speech}
                            onChange={setSpeech}
                            setSpeechText={setSpeech}
                            onSubmit={handleSpeechSubmit}
                            onClear={handleClearSpeech}
                            onSaveDraft={handleSaveDraft}
                            onAudioUpload={handleAudioUpload}
                            onVideoUpload={handleVideoUpload}
                            uploadedAudio={uploadedAudio}
                            uploadedVideo={uploadedVideo}
                            onClearAudio={() => setUploadedAudio(null)}
                            onClearVideo={() => setUploadedVideo(null)}
                            analyzing={analyzing}
                            disabled={analyzing}
                        />

                        <RecordingPanel
                            onRecordingChange={handleRecordingChange}
                            onAnalyze={handleSpeechSubmit}
                            analyzing={analyzing}
                        />

                        <TranscriptPanel transcripts={transcripts} />
                    </div>

                    <div className="debate-sidebar">
                        <DebateTimer initialMinutes={5} />
                        <RoundProgress rounds={rounds} currentRound={currentRound} />
                        <SessionParticipants participants={participants} />
                    </div>
                </div>
            </div>
        </MainLayout>
    );
};

const DebateRoom = () => (
    <ErrorBoundary>
        <DebateRoomContent />
    </ErrorBoundary>
);

export default DebateRoom;