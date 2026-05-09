import { useState, useEffect } from "react";
import axios from "axios";
import {
  Activity, AlertTriangle, CheckCircle, XCircle,
  TrendingUp, DollarSign, FileText, Shield,
  ChevronDown, ChevronUp, Upload, RefreshCw
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell
} from "recharts";

const API = "https://claimsight.onrender.com";

const getRiskColor = (score) => {
  if (score >= 80) return "text-red-500";
  if (score >= 60) return "text-orange-500";
  if (score >= 40) return "text-yellow-500";
  return "text-green-500";
};

const getRiskBg = (score) => {
  if (score >= 80) return "bg-red-500";
  if (score >= 60) return "bg-orange-500";
  if (score >= 40) return "bg-yellow-500";
  return "bg-green-500";
};

const getRiskBadge = (level) => {
  const styles = {
    CRITICAL: "bg-red-100 text-red-800 border border-red-200",
    HIGH: "bg-orange-100 text-orange-800 border border-orange-200",
    MEDIUM: "bg-yellow-100 text-yellow-800 border border-yellow-200",
    LOW: "bg-green-100 text-green-800 border border-green-200",
  };
  return styles[level] || styles.LOW;
};

function StatCard({ icon: Icon, label, value, sub, color }) {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-medium text-gray-500">{label}</span>
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon size={18} className="text-white" />
        </div>
      </div>
      <div className="text-3xl font-bold text-gray-900">{value}</div>
      {sub && <div className="text-sm text-gray-500 mt-1">{sub}</div>}
    </div>
  );
}

function ClaimCard({ claim, onOutcome, onAppeal }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div
        className="p-5 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex flex-col">
              <span className="font-semibold text-gray-900">
                {claim.claim_id}
              </span>
              <span className="text-sm text-gray-500">
                {claim.analyzed_at
                  ? new Date(claim.analyzed_at).toLocaleString()
                  : ""}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex flex-col items-end">
              <div className="flex items-center gap-2">
                <div className="w-24 bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${getRiskBg(claim.risk_score)}`}
                    style={{ width: `${claim.risk_score}%` }}
                  />
                </div>
                <span className={`font-bold ${getRiskColor(claim.risk_score)}`}>
                  {claim.risk_score}
                </span>
              </div>
              <span
                className={`text-xs px-2 py-0.5 rounded-full mt-1 font-medium ${getRiskBadge(claim.risk_level)}`}
              >
                {claim.risk_level}
              </span>
            </div>

            {claim.actual_outcome ? (
              <span
                className={`text-xs px-3 py-1 rounded-full font-medium ${claim.actual_outcome === "APPROVED"
                  ? "bg-green-100 text-green-800"
                  : "bg-red-100 text-red-800"
                  }`}
              >
                {claim.actual_outcome}
              </span>
            ) : (
              <span className="text-xs px-3 py-1 rounded-full bg-gray-100 text-gray-600">
                Pending
              </span>
            )}

            {expanded ? (
              <ChevronUp size={16} className="text-gray-400" />
            ) : (
              <ChevronDown size={16} className="text-gray-400" />
            )}
          </div>
        </div>

        <p className="text-sm text-gray-600 mt-3 bg-gray-50 rounded-lg p-3">
          💡 {claim.recommended_action}
        </p>
      </div>

      {expanded && (
        <div className="px-5 pb-5 border-t border-gray-100 pt-4">
          <div className="flex gap-3 mt-2 flex-wrap">
            {!claim.actual_outcome && (
              <>
                <button
                  onClick={() => onOutcome(claim.claim_id, "APPROVED")}
                  className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-lg text-sm hover:bg-green-600 transition-colors"
                >
                  <CheckCircle size={14} />
                  Mark Approved
                </button>
                <button
                  onClick={() => onOutcome(claim.claim_id, "DENIED")}
                  className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-lg text-sm hover:bg-red-600 transition-colors"
                >
                  <XCircle size={14} />
                  Mark Denied
                </button>
              </>
            )}
            <button
              onClick={() => onAppeal(claim.claim_id)}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700 transition-colors"
            >
              <FileText size={14} />
              Generate Appeal
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function AppealModal({ appeal, onClose }) {
  const copyToClipboard = () => {
    navigator.clipboard.writeText(appeal.letter);
    alert("Appeal letter copied to clipboard!");
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl w-full max-w-2xl shadow-2xl max-h-screen overflow-y-auto">
        <div className="p-6 border-b border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-gray-900">
                Appeal Letter Generated
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                Claim {appeal.claim_id}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${appeal.urgency_level === "URGENT"
                  ? "bg-red-100 text-red-800"
                  : appeal.urgency_level === "EXPEDITED"
                    ? "bg-orange-100 text-orange-800"
                    : "bg-blue-100 text-blue-800"
                }`}>
                {appeal.urgency_level}
              </span>
              <span className="px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                {appeal.estimated_success_rate}% Success Rate
              </span>
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">
              Key Arguments
            </h3>
            <ul className="space-y-1">
              {appeal.key_arguments?.map((arg, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                  <CheckCircle size={14} className="text-green-500 mt-0.5 flex-shrink-0" />
                  {arg}
                </li>
              ))}
            </ul>
          </div>

          <div className="mb-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">
              Supporting Regulations
            </h3>
            <div className="flex flex-wrap gap-2">
              {appeal.supporting_codes?.map((code, i) => (
                <span key={i} className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded">
                  {code}
                </span>
              ))}
            </div>
          </div>

          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">
              Appeal Letter
            </h3>
            <div className="bg-gray-50 rounded-xl p-4 text-sm text-gray-700 whitespace-pre-line font-mono leading-relaxed max-h-64 overflow-y-auto">
              {appeal.letter}
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={copyToClipboard}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
            >
              Copy Letter
            </button>
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 text-sm"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function UploadModal({ onClose, onSuccess }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await axios.post(`${API}/claims/analyze`, formData);
      setResult(res.data);
      onSuccess();
    } catch (e) {
      alert("Error analyzing claim: " + e.message);
    }
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl p-8 w-full max-w-md shadow-2xl">
        <h2 className="text-xl font-bold text-gray-900 mb-2">
          Analyze EDI Claim
        </h2>
        <p className="text-sm text-gray-500 mb-6">
          Upload an EDI 837 file for AI-powered denial risk analysis
        </p>

        {!result ? (
          <>
            <div
              className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center cursor-pointer hover:border-blue-400 transition-colors"
              onClick={() => document.getElementById("fileInput").click()}
            >
              <Upload size={32} className="mx-auto text-gray-400 mb-3" />
              <p className="text-sm text-gray-600">
                {file ? file.name : "Click to upload EDI 837 file"}
              </p>
              <input
                id="fileInput"
                type="file"
                className="hidden"
                accept=".edi,.txt,.837"
                onChange={(e) => setFile(e.target.files[0])}
              />
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={onClose}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleAnalyze}
                disabled={!file || loading}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? "Analyzing..." : "Analyze Claim"}
              </button>
            </div>
          </>
        ) : (
          <div>
            <div
              className={`text-center p-6 rounded-xl mb-4 ${result.analysis.risk_score >= 70
                ? "bg-red-50"
                : "bg-green-50"
                }`}
            >
              <div
                className={`text-5xl font-bold mb-2 ${getRiskColor(
                  result.analysis.risk_score
                )}`}
              >
                {result.analysis.risk_score}
              </div>
              <div className="text-gray-600">Risk Score</div>
              <div
                className={`inline-block mt-2 px-3 py-1 rounded-full text-sm font-medium ${getRiskBadge(
                  result.analysis.risk_level
                )}`}
              >
                {result.analysis.risk_level}
              </div>
            </div>

            <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded-lg mb-4">
              {result.analysis.plain_english}
            </p>

            <div className="bg-blue-50 p-3 rounded-lg mb-4">
              <p className="text-sm font-medium text-blue-800">
                💡 {result.analysis.recommended_action}
              </p>
            </div>

            {result.analysis.counterfactuals?.length > 0 && (
              <div className="bg-green-50 p-3 rounded-lg mb-4">
                <p className="text-xs font-semibold text-green-800 mb-1">
                  If you fix this:
                </p>
                <p className="text-sm text-green-700">
                  {result.analysis.counterfactuals[0].change} → Risk drops to{" "}
                  <strong>
                    {result.analysis.counterfactuals[0].new_risk_score}
                  </strong>
                </p>
              </div>
            )}

            <button
              onClick={onClose}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Done
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default function App() {
  const [analytics, setAnalytics] = useState(null);
  const [claims, setClaims] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [appealData, setAppealData] = useState(null);
  const [appealLoading, setAppealLoading] = useState(false);

  const fetchData = async () => {
    try {
      const [analyticsRes, claimsRes, auditRes] = await Promise.all([
        axios.get(`${API}/analytics/summary`),
        axios.get(`${API}/claims/history`),
        axios.get(`${API}/audit/logs`),
      ]);
      setAnalytics(analyticsRes.data.analytics);
      setClaims(claimsRes.data.claims);
      setAuditLogs(auditRes.data.logs);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleOutcome = async (claimId, outcome) => {
    try {
      await axios.post(
        `${API}/claims/${claimId}/outcome?outcome=${outcome}`
      );
      fetchData();
    } catch (e) {
      alert("Error recording outcome");
    }
  };

  const handleAppeal = async (claimId) => {
    setAppealLoading(true);
    try {
      const res = await axios.get(`${API}/claims/${claimId}/appeal/sample`);
      setAppealData(res.data.appeal);
    } catch (e) {
      alert("Error generating appeal: " + e.message);
    }
    setAppealLoading(false);
  };

  const handleSampleAnalysis = async () => {
    setLoading(true);
    await axios.get(`${API}/claims/analyze-sample`);
    await fetchData();
  };

  const riskDistribution = claims.reduce((acc, c) => {
    const level = c.risk_level || "UNKNOWN";
    acc[level] = (acc[level] || 0) + 1;
    return acc;
  }, {});

  const pieData = Object.entries(riskDistribution).map(([name, value]) => ({
    name,
    value,
  }));

  const PIE_COLORS = {
    CRITICAL: "#ef4444",
    HIGH: "#f97316",
    MEDIUM: "#eab308",
    LOW: "#22c55e",
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Activity size={48} className="mx-auto text-blue-600 animate-pulse mb-4" />
          <p className="text-gray-600">Loading ClaimSight...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <Activity size={18} className="text-white" />
            </div>
            <div>
              <h1 className="font-bold text-gray-900">ClaimSight</h1>
              <p className="text-xs text-gray-500">
                Datadog for Healthcare AI Agents
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchData}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
            >
              <RefreshCw size={16} />
            </button>
            <button
              onClick={handleSampleAnalysis}
              className="px-4 py-2 text-sm border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              Run Sample
            </button>
            <button
              onClick={() => setShowUpload(true)}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
            >
              <Upload size={14} />
              Analyze Claim
            </button>
          </div>
        </div>
      </header>

      {/* Nav */}
      <nav className="bg-white border-b border-gray-200 px-6">
        <div className="max-w-7xl mx-auto flex gap-6">
          {["dashboard", "claims", "audit"].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-3 text-sm font-medium border-b-2 transition-colors capitalize ${activeTab === tab
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
                }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Dashboard Tab */}
        {activeTab === "dashboard" && analytics && (
          <div>
            {/* Stats */}
            <div className="grid grid-cols-4 gap-6 mb-8">
              <StatCard
                icon={FileText}
                label="Total Claims"
                value={analytics.total_claims_analyzed}
                sub="Analyzed by AI"
                color="bg-blue-500"
              />
              <StatCard
                icon={AlertTriangle}
                label="High Risk Claims"
                value={analytics.high_risk_claims}
                sub={`${analytics.high_risk_percentage}% of total`}
                color="bg-red-500"
              />
              <StatCard
                icon={DollarSign}
                label="Revenue Protected"
                value={`$${analytics.estimated_revenue_protected.toLocaleString()}`}
                sub="Estimated savings"
                color="bg-green-500"
              />
              <StatCard
                icon={TrendingUp}
                label="AI Accuracy"
                value={
                  analytics.prediction_accuracy
                    ? `${analytics.prediction_accuracy}%`
                    : "--"
                }
                sub={`${analytics.claims_with_outcomes} outcomes recorded`}
                color="bg-purple-500"
              />
            </div>

            {/* Charts */}
            <div className="grid grid-cols-2 gap-6 mb-8">
              <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-semibold text-gray-900 mb-4">
                  Risk Distribution
                </h3>
                {pieData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={90}
                        dataKey="value"
                        label={({ name, value }) => `${name}: ${value}`}
                      >
                        {pieData.map((entry) => (
                          <Cell
                            key={entry.name}
                            fill={PIE_COLORS[entry.name] || "#94a3b8"}
                          />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-48 flex items-center justify-center text-gray-400">
                    No data yet
                  </div>
                )}
              </div>

              <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-semibold text-gray-900 mb-4">
                  Recent Risk Scores
                </h3>
                {claims.length > 0 ? (
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={claims.slice(0, 10)}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis
                        dataKey="claim_id"
                        tick={{ fontSize: 10 }}
                        tickFormatter={(v) => v.slice(-6)}
                      />
                      <YAxis domain={[0, 100]} />
                      <Tooltip />
                      <Bar dataKey="risk_score" fill="#3b82f6" radius={4} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-48 flex items-center justify-center text-gray-400">
                    No data yet
                  </div>
                )}
              </div>
            </div>

            {/* Recent Claims */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
              <h3 className="font-semibold text-gray-900 mb-4">
                Recent Claims
              </h3>
              {claims.length > 0 ? (
                <div className="space-y-3">
                  {claims.slice(0, 5).map((claim) => (
                    <ClaimCard
                      key={claim.claim_id}
                      claim={claim}
                      onOutcome={handleOutcome}
                      onAppeal={handleAppeal}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-400">
                  <FileText size={48} className="mx-auto mb-3 opacity-50" />
                  <p>No claims analyzed yet</p>
                  <button
                    onClick={handleSampleAnalysis}
                    className="mt-3 text-blue-600 text-sm hover:underline"
                  >
                    Run a sample analysis
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Claims Tab */}
        {activeTab === "claims" && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-gray-900">
                All Claims ({claims.length})
              </h2>
            </div>
            <div className="space-y-3">
              {claims.map((claim) => (
                <ClaimCard
                  key={claim.claim_id}
                  claim={claim}
                  onOutcome={handleOutcome}
                  onAppeal={handleAppeal}
                />
              ))}
            </div>
          </div>
        )}

        {/* Audit Tab */}
        {activeTab === "audit" && (
          <div>
            <div className="flex items-center gap-3 mb-6">
              <Shield size={20} className="text-gray-600" />
              <h2 className="text-xl font-bold text-gray-900">
                HIPAA Audit Trail
              </h2>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Action
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Claim ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Details
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Timestamp
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {auditLogs.map((log, i) => (
                    <tr key={i} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded font-medium">
                          {log.action}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {log.claim_id || "-"}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {JSON.stringify(log.details)}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {appealLoading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-8 text-center">
            <Activity size={32} className="mx-auto text-purple-600 animate-pulse mb-3" />
            <p className="text-gray-700 font-medium">Generating Appeal Letter...</p>
            <p className="text-gray-500 text-sm mt-1">AI is drafting your appeal</p>
          </div>
        </div>
      )}

      {appealData && (
        <AppealModal
          appeal={appealData}
          onClose={() => setAppealData(null)}
        />
      )}

      {showUpload && (
        <UploadModal
          onClose={() => setShowUpload(false)}
          onSuccess={() => {
            setShowUpload(false);
            fetchData();
          }}
        />
      )}
    </div>
  );
}