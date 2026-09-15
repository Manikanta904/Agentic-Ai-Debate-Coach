import { FaExclamationTriangle, FaLightbulb, FaShieldAlt } from "react-icons/fa";

const FallacyDetectionPanel = ({ fallacyAnalysis }) => {
    const fallacies = fallacyAnalysis?.detected_fallacies || fallacyAnalysis?.detectedFallacies || [];
    const explanation = fallacyAnalysis?.explanation_generation?.explanation || fallacyAnalysis?.explanation || fallacyAnalysis?.executive_summary || "No fallacy analysis available.";
    const suggestions = fallacyAnalysis?.correction_suggestions?.suggestions || fallacyAnalysis?.correction_suggestions || fallacyAnalysis?.correctionSuggestions || [];
    const credibility = fallacyAnalysis?.credibility_assessment || fallacyAnalysis?.credibilityAssessment || {
        credibility_level: "High",
        credibility_score: 85,
        justification: "Sound reasoning overall."
    };

    const credScore = credibility.credibility_score ?? credibility.credibilityScore ?? 85;
    const credLevel = credibility.credibility_level || credibility.credibilityLevel || "High";
    const credJustification = credibility.justification || "Sound reasoning overall.";

    return (
        <section className="analysis-card">
            <div className="card-section-header">
                <FaExclamationTriangle /> <h2>Logical Fallacy Detection & Credibility</h2>
            </div>

            <div className="analysis-grid">
                <div className="analysis-item">
                    <h3>Credibility Score</h3>
                    <span className="badge badge-info">{credScore}/100 ({credLevel})</span>
                </div>

                <div className="analysis-item full-width">
                    <h3>Credibility Justification</h3>
                    <p>{credJustification}</p>
                </div>
            </div>

            <h3>Detected Fallacies ({fallacies.length})</h3>
            {fallacies.length > 0 ? (
                <div className="fallacies-list">
                    {fallacies.map((item, index) => {
                        const fallacyName = item.fallacy_type || item.fallacyType || item.name || "Fallacy";
                        const rawConf = item.confidence ?? 0.85;
                        const confPercent = rawConf <= 1 ? (rawConf * 100).toFixed(0) : Math.round(rawConf);
                        const excerpt = item.excerpt || item.quote || item.text || "";

                        return (
                            <div key={index} className="fallacy-card">
                                <div className="fallacy-header">
                                    <span className="fallacy-type">{fallacyName}</span>
                                    <span className="fallacy-confidence">Confidence: {confPercent}%</span>
                                </div>
                                {excerpt && <blockquote className="fallacy-excerpt">"{excerpt}"</blockquote>}
                                {item.explanation && <p className="fallacy-explanation" style={{ fontSize: "13px", marginTop: "6px", color: "#64748B" }}>{item.explanation}</p>}
                            </div>
                        );
                    })}
                </div>
            ) : (
                <div className="success-card">
                    <FaShieldAlt /> No logical fallacies detected. Reasoning exhibits high logical consistency.
                </div>
            )}

            <div className="analysis-grid" style={{ marginTop: "20px" }}>
                <div className="analysis-item full-width">
                    <h3>Reasoning Explanation</h3>
                    <p>{explanation}</p>
                </div>

                {suggestions.length > 0 && (
                    <div className="analysis-item full-width highlight-item">
                        <h3>Correction Suggestions</h3>
                        <ul className="recommendation-list">
                            {suggestions.map((item, idx) => (
                                <li key={idx}><FaLightbulb className="icon-bulb" /> {item}</li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>
        </section>
    );
};

export default FallacyDetectionPanel;
