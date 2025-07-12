import React, { useEffect, useState } from "react";
import { fetchNvdVulnerabilities, analyzeNvdRisk, addKeywordToQueue } from "../services/nvd";
import NvdRiskPie from "../components/NvdRiskPie";
import AssetRiskMatrix from "../components/AssetRiskMatrix";
import AsyncSoftwareAnalysis from "../components/AsyncSoftwareAnalysis";

export default function NvdPage() {
  const [keyword, setKeyword] = useState("");
  const [vulnerabilities, setVulnerabilities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [riskResults, setRiskResults] = useState(null);
  const [addedKeywords, setAddedKeywords] = useState([]);
  const [analysisHistory, setAnalysisHistory] = useState([]);
  const [queueStatus, setQueueStatus] = useState(null);
  const [queueLoading, setQueueLoading] = useState(false);  const [riskThresholds, setRiskThresholds] = useState({
    critical: 80,
    high: 60,
    medium: 40,
    low: 20,
    "very low": 10
  });
  const [activeTab, setActiveTab] = useState("search"); // "search", "analysis", "history"

  const handleSearch = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchNvdVulnerabilities(keyword);
      setVulnerabilities(data.vulnerabilities || []);
    } catch (error) {
      setError("Error fetching NVD data");
    } finally {
      setLoading(false);
    }
  };
  const handleAdd = async () => {
    if (!keyword.trim()) {
      setError("Please enter a keyword before adding to queue");
      return;
    }
    
    setLoading(true);
    setError("");
    try {
      const result = await addKeywordToQueue(keyword);
      setAddedKeywords((prev) => [...new Set([...prev, keyword])]);
      // Optionally show success message
      console.log("Added to queue:", result.message);
    } catch (error) {
      setError("Error adding keyword to analysis queue");
      console.error("Add to queue error:", error);
    } finally {
      setLoading(false);
    }
  };
  const handleAnalyze = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await analyzeNvdRisk();
      setRiskResults(data.results || []);
      // Agregar al historial
      const newAnalysis = {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        keywords: [...addedKeywords],
        results: data.results || [],
        totalVulnerabilities: (data.results || []).reduce((sum, r) => 
          sum + Object.values(r.risk_percent || {}).reduce((s, v) => s + v, 0), 0
        )
      };
      setAnalysisHistory(prev => [newAnalysis, ...prev.slice(0, 9)]); // Keep last 10
      setAddedKeywords([]); // Limpia la lista después de analizar
    } catch (error) {
      setError("Error analyzing risk");
    } finally {
      setLoading(false);
    }
  };

  const fetchQueueStatus = async () => {
    setQueueLoading(true);
    try {
      // Use Kong proxy URL for backend API
      const kongUrl = import.meta.env.VITE_API_URL || 'https://kong-b27b67aff4usnspl9.kongcloud.dev';
      const response = await fetch(`${kongUrl}/nvd/queue/status`);
      if (!response.ok) throw new Error('Failed to fetch queue status');
      const data = await response.json();
      setQueueStatus(data);
    } catch (error) {
      console.error('Error fetching queue status:', error);
      setError('Failed to fetch queue status');
    } finally {
      setQueueLoading(false);
    }
  };

  const clearQueue = async () => {
    setQueueLoading(true);
    try {
      // Use Kong proxy URL for backend API
      const kongUrl = import.meta.env.VITE_API_URL || 'https://kong-b27b67aff4usnspl9.kongcloud.dev';
      const response = await fetch(`${kongUrl}/nvd/queue/clear`, {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Failed to clear queue');
      await fetchQueueStatus(); // Refresh status
      alert('Queue cleared successfully');
    } catch (error) {
      console.error('Error clearing queue:', error);
      setError('Failed to clear queue');
    } finally {
      setQueueLoading(false);
    }
  };
  useEffect(() => {
    // Removed automatic search on load since keyword starts empty
    // eslint-disable-next-line
  }, []);

  useEffect(() => {
    // Auto-load queue status when switching to queue tab
    if (activeTab === "queue") {
      fetchQueueStatus();
    }
  }, [activeTab]);return (
    <div className="nvd-page" style={{ 
      padding: "2rem", 
      maxWidth: "1400px", 
      margin: "0 auto", 
      width: "100%",
      minHeight: "100vh"
    }}>
      {/* Page Header */}
      <div style={{ textAlign: "center", marginBottom: "2rem" }}>
        <h1 style={{ 
          fontSize: "2.5rem", 
          fontWeight: "700", 
          color: "#1e40af", 
          marginBottom: "0.5rem" 
        }}>
          🛡️ NVD Vulnerability Management System
        </h1>
        <p style={{ 
          fontSize: "1.1rem", 
          color: "#64748b", 
          maxWidth: "600px", 
          margin: "0 auto" 
        }}>
          Comprehensive vulnerability assessment and risk analysis platform
        </p>
      </div>

      {/* Navigation Tabs */}
      <div style={{ 
        display: "flex", 
        justifyContent: "center",
        marginBottom: "2rem", 
        borderBottom: "2px solid #e2e8f0",
        gap: "1rem"
      }}>
        {[
          { key: "search", label: "🔍 Vulnerability Search", icon: "🔍" },
          { key: "queue", label: "📋 Queue Management", icon: "📋" },
          { key: "analysis", label: "📊 Risk Analysis Dashboard", icon: "📊" },
          { key: "history", label: "📈 Analysis History", icon: "📈" }
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              padding: "0.75rem 1.5rem",
              border: "none",
              background: activeTab === tab.key ? "#2563eb" : "transparent",
              color: activeTab === tab.key ? "white" : "#64748b",
              fontWeight: activeTab === tab.key ? "600" : "normal",
              borderRadius: "0.5rem 0.5rem 0 0",
              cursor: "pointer",
              transition: "all 0.2s",
              fontSize: "0.95rem"
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>      {/* Tab Content */}
      {activeTab === "search" && (
        <div style={{ 
          display: "grid", 
          gridTemplateColumns: "1fr 1fr", 
          gap: "3rem", 
          alignItems: "flex-start", 
          minHeight: "500px",
          background: "#ffffff",
          padding: "2rem",
          borderRadius: "1rem",
          boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)"
        }}>
          <div style={{ width: "100%" }}>
            <h2 style={{ 
              fontSize: "1.75rem", 
              color: "#1e40af", 
              marginBottom: "1.5rem",
              fontWeight: "600"
            }}>
              🔍 Search NVD Vulnerabilities
            </h2>            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSearch();
              }}
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "1rem",
                marginBottom: "1.5rem",
              }}
            >
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <input
                  type="text"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                  placeholder="Enter technology keyword (e.g. apache, mysql, nodejs)"
                  style={{ 
                    flex: "1",
                    padding: "0.75rem",
                    border: "2px solid #e2e8f0",
                    borderRadius: "0.5rem",
                    fontSize: "1rem",
                    outline: "none",
                    transition: "border-color 0.2s"
                  }}
                />
                <button
                  type="submit"
                  disabled={loading}
                  style={{ 
                    padding: "0.75rem 1.5rem",
                    background: "#2563eb",
                    color: "white",
                    border: "none",
                    borderRadius: "0.5rem",
                    fontWeight: "600",
                    cursor: "pointer",
                    fontSize: "1rem"
                  }}
                >
                  {loading ? "Searching..." : "Search"}
                </button>
              </div>
              <button
                type="button"
                onClick={handleAdd}
                disabled={loading || vulnerabilities.length === 0}
                style={{
                  alignSelf: "flex-start",
                  background: "#22c55e",
                  color: "#fff",
                  fontWeight: "600",
                  borderRadius: "0.5rem",
                  border: "none",
                  padding: "0.75rem 1.5rem",
                  cursor: "pointer",
                  fontSize: "1rem"
                }}
              >
                ➕ Add to Analysis Queue
              </button>
            </form>
            {error && (
              <p style={{ color: "#ef4444", fontWeight: 600 }}>{error}</p>
            )}            {loading ? (
              <div style={{ 
                textAlign: "center", 
                padding: "2rem",
                color: "#64748b"
              }}>
                <p style={{ fontSize: "1.1rem" }}>🔄 Loading vulnerabilities...</p>
              </div>
            ) : (
              <div style={{
                maxHeight: "400px",
                overflowY: "auto",
                border: "1px solid #e2e8f0",
                borderRadius: "0.5rem",
                padding: "1rem"
              }}>
                {vulnerabilities.length === 0 ? (
                  <div style={{ 
                    textAlign: "center", 
                    padding: "2rem",
                    color: "#64748b"
                  }}>
                    <p style={{ fontSize: "1.1rem" }}>🔍 No vulnerabilities found for this keyword</p>
                  </div>
                ) : (
                  <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                    {vulnerabilities.map((vuln, idx) => (
                      <li key={idx} style={{
                        padding: "1rem",
                        marginBottom: "0.75rem",
                        background: "#f8fafc",
                        borderRadius: "0.5rem",
                        border: "1px solid #e2e8f0"
                      }}>
                        <strong style={{ 
                          color: "#dc2626", 
                          fontSize: "1.1rem" 
                        }}>
                          {vuln.cve.id}
                        </strong>
                        {vuln.cve.descriptions[0]?.value && (
                          <p style={{
                            marginTop: "0.5rem",
                            color: "#475569",
                            fontSize: "0.9rem",
                            lineHeight: "1.4"
                          }}>
                            {vuln.cve.descriptions[0]?.value}
                          </p>
                        )}
                        {vuln.cve.published && (
                          <p style={{
                            marginTop: "0.5rem",
                            fontSize: "0.8rem",
                            color: "#64748b",
                            margin: 0
                          }}>
                            📅 Published: {new Date(vuln.cve.published).toLocaleDateString()}
                          </p>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}            <div style={{
              marginTop: "1.5rem",
              padding: "1rem",
              background: "#f1f5f9",
              borderRadius: "0.5rem",
              border: "1px solid #e2e8f0"
            }}>
              <button
                type="button"
                onClick={handleAnalyze}
                disabled={loading || addedKeywords.length === 0}
                style={{
                  background: addedKeywords.length > 0 ? "#2563eb" : "#94a3b8",
                  color: "#fff",
                  fontWeight: "600",
                  borderRadius: "0.5rem",
                  border: "none",
                  padding: "1rem 2rem",
                  cursor: addedKeywords.length > 0 ? "pointer" : "not-allowed",
                  fontSize: "1.1rem",
                  width: "100%",
                  marginBottom: "1rem"
                }}
              >
                🔍 Analyze Risk ({addedKeywords.length} keywords)
              </button>
              {addedKeywords.length > 0 && (
                <div style={{ 
                  color: "#475569", 
                  fontSize: "0.9rem",
                  lineHeight: "1.4"
                }}>
                  <strong>Added keywords:</strong><br />
                  {addedKeywords.map((kw, idx) => (
                    <span key={idx} style={{
                      display: "inline-block",
                      background: "#e2e8f0",
                      padding: "0.25rem 0.5rem",
                      borderRadius: "0.25rem",
                      margin: "0.25rem 0.25rem 0 0",
                      fontSize: "0.8rem"
                    }}>
                      {kw}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
          <div style={{ 
            display: "flex", 
            flexDirection: "column",
            alignItems: "center", 
            justifyContent: "center",
            width: "100%",
            minHeight: "400px",
            background: "#f8fafc",
            borderRadius: "0.5rem",
            border: "1px solid #e2e8f0"
          }}>
            {riskResults ? (
              <NvdRiskPie results={riskResults} />
            ) : (
              <div style={{ 
                textAlign: "center", 
                color: "#64748b",
                padding: "2rem"
              }}>
                <div style={{ fontSize: "4rem", marginBottom: "1rem" }}>📊</div>
                <h3 style={{ marginBottom: "0.5rem", color: "#374151" }}>Risk Analysis Chart</h3>
                <p>Add keywords and run analysis to see risk distribution</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Queue Management Tab */}
      {activeTab === "queue" && (
        <div style={{ 
          background: "#ffffff",
          padding: "2rem",
          borderRadius: "1rem",
          boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)"
        }}>
          <div style={{ 
            display: "flex", 
            justifyContent: "space-between", 
            alignItems: "center", 
            marginBottom: "2rem" 
          }}>
            <h2 style={{ 
              fontSize: "1.75rem", 
              color: "#1e40af", 
              margin: 0,
              fontWeight: "600"
            }}>
              📋 Queue Management System
            </h2>
            <div style={{ display: "flex", gap: "1rem" }}>
              <button
                onClick={fetchQueueStatus}
                disabled={queueLoading}
                style={{
                  background: "#2563eb",
                  color: "white",
                  border: "none",
                  padding: "0.75rem 1.5rem",
                  borderRadius: "0.5rem",
                  fontWeight: "600",
                  cursor: queueLoading ? "not-allowed" : "pointer",
                  fontSize: "0.9rem"
                }}
              >
                {queueLoading ? "🔄 Refreshing..." : "🔄 Refresh Status"}
              </button>
              <button
                onClick={clearQueue}
                disabled={queueLoading}
                style={{
                  background: "#dc2626",
                  color: "white",
                  border: "none",
                  padding: "0.75rem 1.5rem",
                  borderRadius: "0.5rem",
                  fontWeight: "600",
                  cursor: queueLoading ? "not-allowed" : "pointer",
                  fontSize: "0.9rem"
                }}
              >
                🗑️ Clear Queue
              </button>
            </div>
          </div>

          {/* Queue Status Cards */}
          <div style={{ 
            display: "grid", 
            gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", 
            gap: "1.5rem",
            marginBottom: "2rem"
          }}>
            <div style={{
              background: "linear-gradient(135deg, #3b82f6, #1d4ed8)",
              color: "white",
              padding: "1.5rem",
              borderRadius: "1rem",
              textAlign: "center"
            }}>
              <h3 style={{ margin: "0 0 0.5rem 0", fontSize: "1rem" }}>Queue Size</h3>
              <p style={{ margin: 0, fontSize: "2.5rem", fontWeight: "700" }}>
                {queueStatus?.queue_size ?? "—"}
              </p>
            </div>
            
            <div style={{
              background: "linear-gradient(135deg, #10b981, #047857)",
              color: "white",
              padding: "1.5rem",
              borderRadius: "1rem",
              textAlign: "center"
            }}>
              <h3 style={{ margin: "0 0 0.5rem 0", fontSize: "1rem" }}>Total Vulnerabilities</h3>
              <p style={{ margin: 0, fontSize: "2.5rem", fontWeight: "700" }}>
                {queueStatus?.total_vulnerabilities ?? "—"}
              </p>
            </div>
            
            <div style={{
              background: "linear-gradient(135deg, #8b5cf6, #7c3aed)",
              color: "white",
              padding: "1.5rem",
              borderRadius: "1rem",
              textAlign: "center"
            }}>
              <h3 style={{ margin: "0 0 0.5rem 0", fontSize: "1rem" }}>Active Keywords</h3>
              <p style={{ margin: 0, fontSize: "2.5rem", fontWeight: "700" }}>
                {queueStatus?.keywords?.length ?? "—"}
              </p>
            </div>
          </div>

          {/* Queue Details */}
          {queueStatus && (
            <div style={{
              background: "#f8fafc",
              padding: "1.5rem",
              borderRadius: "1rem",
              border: "1px solid #e2e8f0"
            }}>
              <h3 style={{ 
                color: "#374151", 
                marginBottom: "1rem", 
                fontSize: "1.25rem" 
              }}>
                📊 Queue Details
              </h3>
              
              {queueStatus.keywords && queueStatus.keywords.length > 0 ? (
                <div>
                  <h4 style={{ color: "#475569", marginBottom: "0.75rem" }}>
                    Keywords in Queue:
                  </h4>
                  <div style={{ 
                    display: "flex", 
                    flexWrap: "wrap", 
                    gap: "0.5rem",
                    marginBottom: "1rem"
                  }}>
                    {queueStatus.keywords.map((keyword, index) => (
                      <span
                        key={index}
                        style={{
                          background: "#e2e8f0",
                          color: "#374151",
                          padding: "0.5rem 1rem",
                          borderRadius: "0.5rem",
                          fontSize: "0.9rem",
                          fontWeight: "500"
                        }}
                      >
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>
              ) : (
                <div style={{ 
                  textAlign: "center", 
                  color: "#64748b", 
                  padding: "2rem",
                  background: "#fff",
                  borderRadius: "0.75rem",
                  border: "1px solid #d1d5db"
                }}>
                  <p style={{ fontSize: "1.1rem", margin: 0 }}>
                    📭 Queue is empty
                  </p>
                  <p style={{ fontSize: "0.9rem", marginTop: "0.5rem", margin: 0 }}>
                    Add keywords from the search tab to populate the queue
                  </p>
                </div>
              )}

              {queueStatus.error && (
                <div style={{
                  background: "#fee2e2",
                  color: "#dc2626",
                  padding: "1rem",
                  borderRadius: "0.5rem",
                  border: "1px solid #fecaca",
                  marginTop: "1rem"
                }}>
                  <strong>Error:</strong> {queueStatus.error}
                </div>
              )}
            </div>
          )}

          {/* Load queue status on tab switch */}
          {!queueStatus && !queueLoading && (
            <div style={{ 
              textAlign: "center", 
              padding: "3rem",
              background: "#f8fafc",
              borderRadius: "1rem",
              border: "1px solid #e2e8f0"
            }}>
              <p style={{ color: "#64748b", marginBottom: "1rem" }}>
                Click "Refresh Status" to load queue information
              </p>
              <button
                onClick={fetchQueueStatus}
                style={{
                  background: "#2563eb",
                  color: "white",
                  border: "none",
                  padding: "0.75rem 2rem",
                  borderRadius: "0.5rem",
                  fontWeight: "600",
                  cursor: "pointer",
                  fontSize: "1rem"
                }}
              >
                🔄 Load Queue Status
              </button>
            </div>
          )}
        </div>
      )}

      {activeTab === "analysis" && (
        <div style={{ 
          display: "flex", 
          flexDirection: "column", 
          gap: "2rem",
          background: "#ffffff",
          padding: "2rem",
          borderRadius: "1rem",
          boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)"
        }}>
          {/* Top Row - Configuration and Current Metrics */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem", alignItems: "start" }}>
            {/* Risk Analysis Configuration */}
            <div style={{ 
              background: "#f8fafc", 
              padding: "1.5rem", 
              borderRadius: "0.75rem",
              border: "1px solid #e2e8f0"
            }}>
              <h3 style={{ color: "#1e40af", marginBottom: "1rem", fontSize: "1.2rem" }}>
                🎯 Risk Assessment Configuration
              </h3>
              <div style={{ marginBottom: "1rem" }}>
                <h4 style={{ color: "#374151", marginBottom: "0.5rem" }}>Risk Thresholds (%)</h4>
                {Object.entries(riskThresholds).map(([level, value]) => (
                  <div key={level} style={{ display: "flex", alignItems: "center", marginBottom: "0.5rem" }}>
                    <label style={{ width: "80px", textTransform: "capitalize", fontSize: "0.9rem" }}>
                      {level}:
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={value}
                      onChange={(e) => setRiskThresholds(prev => ({
                        ...prev,
                        [level]: parseInt(e.target.value)
                      }))}
                      style={{ flex: 1, margin: "0 0.5rem" }}
                    />
                    <span style={{ width: "40px", fontSize: "0.9rem", color: "#64748b" }}>
                      {value}%
                    </span>
                  </div>
                ))}
              </div>
              
              <div style={{ 
                background: "#fff", 
                padding: "1rem", 
                borderRadius: "0.5rem",
                border: "1px solid #d1d5db",
                marginTop: "1rem"
              }}>
                <h4 style={{ color: "#374151", marginBottom: "0.75rem" }}>📋 Queue Status</h4>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ color: "#64748b" }}>Keywords in queue:</span>
                  <span style={{ 
                    background: addedKeywords.length > 0 ? "#22c55e" : "#94a3b8", 
                    color: "white", 
                    padding: "0.25rem 0.75rem", 
                    borderRadius: "1rem",
                    fontSize: "0.8rem",
                    fontWeight: "600"
                  }}>
                    {addedKeywords.length}
                  </span>
                </div>
                {addedKeywords.length > 0 && (
                  <div style={{ marginTop: "0.5rem", fontSize: "0.85rem", color: "#475569" }}>
                    {addedKeywords.join(", ")}
                  </div>
                )}
              </div>
            </div>

            {/* Current Risk Pie Chart */}
            <div style={{ 
              background: "#f8fafc", 
              padding: "1.5rem", 
              borderRadius: "0.75rem",
              border: "1px solid #e2e8f0",
              display: "flex",
              flexDirection: "column",
              alignItems: "center"
            }}>
              <h3 style={{ color: "#1e40af", marginBottom: "1rem", fontSize: "1.2rem" }}>
                📊 Risk Distribution
              </h3>
              {riskResults ? (
                <NvdRiskPie results={riskResults} />
              ) : (
                <div style={{ 
                  textAlign: "center", 
                  color: "#94a3b8", 
                  padding: "2rem",
                  background: "#fff",
                  borderRadius: "0.5rem",
                  border: "1px solid #d1d5db",
                  width: "100%"
                }}>
                  <p>No risk analysis available</p>
                  <p style={{ fontSize: "0.9rem", marginTop: "0.5rem" }}>
                    Add keywords and run analysis to see distribution
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Bottom Row - Enterprise Asset Risk Matrix */}
          {riskResults && (
            <AssetRiskMatrix 
              riskResults={riskResults} 
              riskThresholds={riskThresholds}
            />
          )}
        </div>
      )}      {activeTab === "history" && (
        <div style={{ 
          background: "#ffffff",
          padding: "2rem",
          borderRadius: "1rem",
          boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)"
        }}>
          <h3 style={{ 
            color: "#1e40af", 
            marginBottom: "1.5rem", 
            fontSize: "1.75rem",
            textAlign: "center"
          }}>
            📈 Analysis History Dashboard
          </h3>
          {analysisHistory.length === 0 ? (
            <div style={{ 
              textAlign: "center", 
              color: "#94a3b8", 
              padding: "3rem",
              background: "#f8fafc",
              borderRadius: "0.75rem",
              border: "1px solid #e2e8f0"
            }}>
              <p style={{ fontSize: "1.1rem" }}>No analysis history available</p>
              <p style={{ fontSize: "0.9rem", marginTop: "0.5rem" }}>
                Run some risk analyses to see historical data
              </p>
            </div>
          ) : (
            <div style={{ display: "grid", gap: "1rem" }}>
              {analysisHistory.map((analysis) => (
                <div key={analysis.id} style={{
                  background: "#fff",
                  padding: "1.5rem",
                  borderRadius: "0.75rem",
                  border: "1px solid #d1d5db",
                  boxShadow: "0 1px 3px rgba(0,0,0,0.1)"
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                    <h4 style={{ color: "#374151", margin: 0 }}>
                      Analysis #{analysis.id}
                    </h4>
                    <span style={{ color: "#64748b", fontSize: "0.9rem" }}>
                      {new Date(analysis.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <div style={{ marginBottom: "1rem" }}>
                    <strong style={{ color: "#475569" }}>Keywords analyzed: </strong>
                    <span style={{ color: "#1e40af" }}>{analysis.keywords.join(", ")}</span>
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem" }}>
                    {analysis.results.map((result, idx) => (
                      <div key={idx} style={{
                        background: "#f8fafc",
                        padding: "1rem",
                        borderRadius: "0.5rem",
                        border: "1px solid #e2e8f0"
                      }}>
                        <h5 style={{ color: "#374151", marginBottom: "0.5rem" }}>{result.keyword}</h5>
                        <div style={{ fontSize: "0.85rem" }}>
                          {Object.entries(result.risk_percent || {}).map(([level, percent]) => (
                            <div key={level} style={{ display: "flex", justifyContent: "space-between" }}>
                              <span>{level}:</span>
                              <span style={{ fontWeight: "600" }}>{percent.toFixed(1)}%</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
