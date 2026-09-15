import {
    RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
    PieChart, Pie, Cell,
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
    LineChart, Line, CartesianGrid, Legend
} from "recharts";
import { FaChartBar, FaChartLine, FaChartPie, FaCheckCircle, FaInfoCircle } from "react-icons/fa";
import { adaptDashboardAnalytics } from "../../utils/dashboardAnalyticsAdapter";
import "./InteractiveAnalysisCharts.css";

const COLORS = ["#2563eb", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"];

const InteractiveAnalysisCharts = ({
    argumentAnalysis,
    fallacyAnalysis,
    counterargument,
    latestReport = null,
    reportsList = [],
    userSkill = null
}) => {
    // Determine active report payload
    const effectiveReport = latestReport || (argumentAnalysis ? { argument_analysis: argumentAnalysis, logical_fallacy_analysis: fallacyAnalysis, counterargument } : null);

    const { radarData, barData, pieData, lineData } = adaptDashboardAnalytics(
        effectiveReport,
        reportsList,
        userSkill
    );

    return (
        <section className="analysis-card">
            <div className="card-section-header">
                <FaChartBar /> <h2>Interactive Performance Analytics & Charts</h2>
            </div>
            <p className="card-description">Interactive visualizations of score breakdowns, evidence distribution, fallacy confidence, and historical improvement timeline.</p>

            <div className="analysis-grid">
                {/* Score Breakdown Radar Chart */}
                <div className="analysis-item">
                    <h3><FaChartPie /> Score Breakdown (Radar)</h3>
                    <div style={{ width: "100%", height: 260 }}>
                        <ResponsiveContainer>
                            <RadarChart data={radarData}>
                                <PolarGrid />
                                <PolarAngleAxis dataKey="subject" />
                                <PolarRadiusAxis angle={30} domain={[0, 100]} />
                                <Radar name="Score" dataKey="score" stroke="#2563eb" fill="#3b82f6" fillOpacity={0.6} />
                            </RadarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Evidence Distribution Pie Chart */}
                <div className="analysis-item">
                    <h3><FaChartPie /> Evidence Distribution</h3>
                    <div style={{ width: "100%", height: 260 }}>
                        {pieData.length > 0 ? (
                            <ResponsiveContainer>
                                <PieChart>
                                    <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                                        {pieData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip />
                                </PieChart>
                            </ResponsiveContainer>
                        ) : (
                            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", color: "#64748b", gap: "8px" }}>
                                <FaInfoCircle style={{ fontSize: "24px", color: "#3b82f6" }} />
                                <span>No evidence distribution metrics for this session.</span>
                            </div>
                        )}
                    </div>
                </div>

                {/* Fallacy Confidence Bar Chart */}
                <div className="analysis-item">
                    <h3><FaChartBar /> Fallacy Distribution & Confidence</h3>
                    <div style={{ width: "100%", height: 260 }}>
                        {barData.length > 0 ? (
                            <ResponsiveContainer>
                                <BarChart data={barData}>
                                    <XAxis dataKey="name" />
                                    <YAxis domain={[0, 100]} />
                                    <Tooltip />
                                    <Bar dataKey="confidence" fill="#ef4444" radius={[6, 6, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        ) : (
                            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", color: "#166534", background: "#f0fdf4", borderRadius: "8px", border: "1px dashed #bbf7d0", gap: "8px" }}>
                                <FaCheckCircle style={{ fontSize: "28px", color: "#22c55e" }} />
                                <strong style={{ fontSize: "14px" }}>No Fallacies Detected!</strong>
                                <span style={{ fontSize: "12px", color: "#15803d" }}>Premise deductions are logically sound.</span>
                            </div>
                        )}
                    </div>
                </div>

                {/* Historical Score Timeline Line Chart */}
                <div className="analysis-item">
                    <h3><FaChartLine /> Historical Score Improvement Timeline</h3>
                    <div style={{ width: "100%", height: 260 }}>
                        {lineData.length > 0 ? (
                            <ResponsiveContainer>
                                <LineChart data={lineData}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="session" />
                                    <YAxis domain={[50, 100]} />
                                    <Tooltip />
                                    <Legend />
                                    <Line type="monotone" dataKey="score" stroke="#10b981" strokeWidth={3} activeDot={{ r: 8 }} />
                                </LineChart>
                            </ResponsiveContainer>
                        ) : (
                            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", color: "#64748b", gap: "8px" }}>
                                <FaChartLine style={{ fontSize: "24px", color: "#10b981" }} />
                                <span>Complete debate sessions to track performance timeline.</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </section>
    );
};

export default InteractiveAnalysisCharts;
