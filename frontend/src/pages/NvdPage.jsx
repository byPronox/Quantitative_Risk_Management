import React, { useEffect, useState } from "react";
import { fetchNvdVulnerabilities, analyzeNvdRisk, addKeywordToQueue, createObservation, fetchObservations, updateRiskStatus, deleteObservation } from "../services/nvd";
import NvdRiskPie from "../components/NvdRiskPie";
import AssetRiskMatrix from "../components/AssetRiskMatrix";
import { saveAs } from "file-saver";
import jsPDF from "jspdf";

export default function NvdPage() {
  const [keyword, setKeyword] = useState("");
  const [vulnerabilities, setVulnerabilities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [riskResults, setRiskResults] = useState(null);
  const [addedKeywords, setAddedKeywords] = useState([]);
  const [allSearchedVulnerabilities, setAllSearchedVulnerabilities] = useState([]);
  const [analysisHistory, setAnalysisHistory] = useState(() => {
    const saved = localStorage.getItem('analysisHistory');
    return saved ? JSON.parse(saved) : [];
  });
  const [riskThresholds, setRiskThresholds] = useState({
    critical: 80,
    high: 60,
    medium: 40,
    low: 20,
    "very low": 10
  });
  const [activeTab, setActiveTab] = useState("search"); // "search", "analysis", "history"
  const [observations, setObservations] = useState([]);
  const [observationText, setObservationText] = useState("");
  const [obsLoading, setObsLoading] = useState(false);
  const [selectedRiskId, setSelectedRiskId] = useState(null);

  // Opciones de estado
  const riskStatusOptions = ["Pending", "Mitigated", "In Review", "Accepted"];

  const handleSearch = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchNvdVulnerabilities(keyword);
      const newVulns = data.vulnerabilities || [];
      setVulnerabilities(newVulns);
      // Accumulate all vulnerabilities for the report
      setAllSearchedVulnerabilities(prevVulns => {
        const existingIds = new Set(prevVulns.map(v => v.cve.id));
        const filteredNewVulns = newVulns.filter(v => !existingIds.has(v.cve.id));
        return [...prevVulns, ...filteredNewVulns];
      });
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
  useEffect(() => {
    localStorage.setItem('analysisHistory', JSON.stringify(analysisHistory));
  }, [analysisHistory]);

  useEffect(() => {
    if (riskResults && riskResults.length > 0) {
      setSelectedRiskId(Number(riskResults[0].id));
    }
  }, [riskResults]);

  useEffect(() => {
    if (selectedRiskId) {
      fetchObservations(selectedRiskId).then(setObservations);
    }
  }, [selectedRiskId]);

  const handleObservationSubmit = async (e) => {
    e.preventDefault();
    if (!observationText.trim() || !selectedRiskId) return;
    setObsLoading(true);
    const newObs = {
      risk_id: selectedRiskId,
      content: observationText,
      author: "user", // O puedes pedir el nombre
      timestamp: new Date().toISOString()
    };
    try {
      await createObservation(newObs);
      setObservationText("");
      const updated = await fetchObservations(selectedRiskId);
      setObservations(updated);
    } finally {
      setObsLoading(false);
    }
  };

  const handleDeleteObservation = async (observationId) => {
    try {
      await deleteObservation(observationId);
      // Refrescar la lista de observaciones
      const updated = await fetchObservations(selectedRiskId);
      setObservations(updated);
    } catch (error) {
      setError("Error deleting observation");
      console.error("Delete observation error:", error);
    }
  };

  // Función para exportar a CSV
  const exportAnalysisToCSV = async () => {
    let csv = '';
    // 1. General summary
    csv += 'Risk Analysis Full Report\n';
    csv += `Date:,${new Date().toLocaleString()}\n`;
    csv += `Analyzed Keywords:,${(riskResults || []).map(r=>r.keyword).join(', ')}\n\n`;

    // 2. Current Analysis Results
    csv += 'Current Risk Analysis Results\n';
    csv += 'Keyword,Risk Status,Critical %,High %,Medium %,Low %,Very Low %,Observations\n';
    if (riskResults && riskResults.length > 0) {
      for (const risk of riskResults) {
        let obsList = [];
        try {
          obsList = await fetchObservations(risk.id || 1);
        } catch {}
        const obsText = obsList.map(o => `${o.author || "Anon"} (${new Date(o.timestamp).toLocaleString()}): ${o.content.replace(/\n/g, " ")}`).join(" | ");
        csv += `"${risk.keyword}","${risk.status || 'Pending'}","${risk.risk_percent?.Critical?.toFixed(1) || 0}","${risk.risk_percent?.High?.toFixed(1) || 0}","${risk.risk_percent?.Medium?.toFixed(1) || 0}","${risk.risk_percent?.Low?.toFixed(1) || 0}","${risk.risk_percent?.['Very Low']?.toFixed(1) || 0}","${obsText}"\n`;
      }
    } else {
      csv += 'No current analysis results.\n';
    }
    csv += '\n';

    // 3. Vulnerability Search Results (Grouped by Keyword)
    csv += 'Vulnerability Search Results by Keyword\n';
    if (riskResults && riskResults.length > 0) {
      for (const risk of riskResults) {
        const keyword = risk.keyword;
        const vulnsForKeyword = (allSearchedVulnerabilities || []).filter(vuln => {
          // Simple match: check if keyword is in description or id (case-insensitive)
          const desc = vuln.cve.descriptions[0]?.value?.toLowerCase() || '';
          return desc.includes(keyword.toLowerCase()) || vuln.cve.id.toLowerCase().includes(keyword.toLowerCase());
        });
        csv += `Keyword:,${keyword}\n`;
        csv += `Vulnerabilities Found:,${vulnsForKeyword.length}\n`;
        csv += 'CVE ID,Description,Published Date\n';
        if (vulnsForKeyword.length > 0) {
          for (const vuln of vulnsForKeyword) {
            const desc = vuln.cve.descriptions[0]?.value?.replace(/\n/g, ' ') || '';
            const pub = vuln.cve.published ? new Date(vuln.cve.published).toLocaleDateString() : '';
            csv += `"${vuln.cve.id}","${desc}","${pub}"\n`;
          }
        } else {
          csv += 'No vulnerabilities found for this keyword.\n';
        }
        csv += '\n';
        // Add general recommendation (always show)
        const highestSeverity = getHighestSeverityForKeyword(keyword, allSearchedVulnerabilities);
        const rec = getRecommendationBySeverity(highestSeverity);
        csv += `General Recommendation:,${rec}\n\n`;
      }
    } else {
      csv += 'No keywords analyzed, so no grouped vulnerabilities.\n';
    }
    csv += '\n';

    // 4. Analysis History
    csv += 'Analysis History\n';
    if (analysisHistory && analysisHistory.length > 0) {
      for (const analysis of analysisHistory) {
        csv += `Analysis #${analysis.id},Date:,${new Date(analysis.timestamp).toLocaleString()}\n`;
        csv += `Keywords:,${analysis.keywords.join(', ')}\n`;
        csv += 'Keyword,Critical %,High %,Medium %,Low %,Very Low %\n';
        for (const result of analysis.results) {
          csv += `"${result.keyword}","${result.risk_percent?.Critical?.toFixed(1) || 0}","${result.risk_percent?.High?.toFixed(1) || 0}","${result.risk_percent?.Medium?.toFixed(1) || 0}","${result.risk_percent?.Low?.toFixed(1) || 0}","${result.risk_percent?.['Very Low']?.toFixed(1) || 0}"\n`;
        }
        csv += '\n';
      }
    } else {
      csv += 'No analysis history available.\n';
    }
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    saveAs(blob, `risk_analysis_full_${new Date().toISOString().slice(0,10)}.csv`);
  };

  // Función para exportar a PDF
  const exportAnalysisToPDF = async () => {
    const doc = new jsPDF();
    let y = 10;
    doc.setFontSize(16);
    doc.text("Risk Analysis Full Report", 10, y);
    y += 8;
    doc.setFontSize(10);
    doc.text(`Date: ${new Date().toLocaleString()}`, 10, y);
    y += 8;
    doc.text(`Analyzed Keywords: ${(riskResults || []).map(r=>r.keyword).join(', ')}`, 10, y);
    y += 8;

    // 1. Current Analysis Results
    doc.setFontSize(13);
    doc.text("Current Risk Analysis Results", 10, y);
    y += 7;
    doc.setFontSize(10);
    if (riskResults && riskResults.length > 0) {
      for (const risk of riskResults) {
        doc.setFontSize(11);
        doc.text(`Keyword: ${risk.keyword} | Status: ${risk.status || 'Pending'}`, 10, y);
        y += 5;
        doc.setFontSize(10);
        doc.text(`Critical: ${risk.risk_percent?.Critical?.toFixed(1) || 0}%  High: ${risk.risk_percent?.High?.toFixed(1) || 0}%  Medium: ${risk.risk_percent?.Medium?.toFixed(1) || 0}%  Low: ${risk.risk_percent?.Low?.toFixed(1) || 0}%  Very Low: ${risk.risk_percent?.['Very Low']?.toFixed(1) || 0}%`, 10, y);
        y += 5;
        // Observations
        let obsList = [];
        try {
          obsList = await fetchObservations(risk.id || 1);
        } catch {}
        if (obsList.length > 0) {
          doc.setFontSize(10);
          doc.text("Observations:", 10, y);
          y += 5;
          obsList.forEach(obs => {
            const obsText = `${obs.author || "Anon"} (${new Date(obs.timestamp).toLocaleString()}): ${obs.content}`;
            const lines = doc.splitTextToSize(obsText, 180);
            lines.forEach(line => {
              doc.text(line, 12, y);
              y += 5;
            });
          });
        } else {
          doc.text("No observations.", 10, y);
          y += 5;
        }
        y += 2;
        if (y > 270) { doc.addPage(); y = 10; }
      }
    } else {
      doc.text("No current analysis results.", 10, y);
      y += 5;
    }
    y += 5;

    // 2. Vulnerability Search Results (Grouped by Keyword)
    doc.setFontSize(13);
    doc.text("Vulnerability Search Results by Keyword", 10, y);
    y += 7;
    doc.setFontSize(10);
    if (riskResults && riskResults.length > 0) {
      for (const risk of riskResults) {
        const keyword = risk.keyword;
        const vulnsForKeyword = (allSearchedVulnerabilities || []).filter(vuln => {
          const desc = vuln.cve.descriptions[0]?.value?.toLowerCase() || '';
          return desc.includes(keyword.toLowerCase()) || vuln.cve.id.toLowerCase().includes(keyword.toLowerCase());
        });
        doc.setFontSize(11);
        doc.text(`Keyword: ${keyword} | Vulnerabilities Found: ${vulnsForKeyword.length}`, 10, y);
        y += 5;
        doc.setFontSize(10);
        if (vulnsForKeyword.length > 0) {
          for (const vuln of vulnsForKeyword) {
            doc.text(`CVE: ${vuln.cve.id}`, 12, y);
            y += 5;
            if (vuln.cve.descriptions[0]?.value) {
              const descLines = doc.splitTextToSize(vuln.cve.descriptions[0].value, 170);
              descLines.forEach(line => {
                doc.text(line, 16, y);
                y += 5;
              });
            }
            if (vuln.cve.published) {
              doc.text(`Published: ${new Date(vuln.cve.published).toLocaleDateString()}`, 16, y);
              y += 5;
            }
            y += 2;
            if (y > 270) { doc.addPage(); y = 10; }
            // Add general recommendation (always show)
            const highestSeverity = getHighestSeverityForKeyword(keyword, allSearchedVulnerabilities);
            const rec = getRecommendationBySeverity(highestSeverity);
            doc.setFontSize(10);
            doc.text(`General Recommendation: ${rec}`, 12, y);
            y += 6;
            if (y > 270) { doc.addPage(); y = 10; }
          }
        } else {
          doc.text("No vulnerabilities found for this keyword.", 12, y);
          y += 5;
        }
        y += 2;
        if (y > 270) { doc.addPage(); y = 10; }
      }
    } else {
      doc.text("No keywords analyzed, so no grouped vulnerabilities.", 10, y);
      y += 5;
    }
    y += 5;

    // 3. Analysis History
    doc.setFontSize(13);
    doc.text("Analysis History", 10, y);
    y += 7;
    doc.setFontSize(10);
    if (analysisHistory && analysisHistory.length > 0) {
      for (const analysis of analysisHistory) {
        doc.setFontSize(11);
        doc.text(`Analysis #${analysis.id} | Date: ${new Date(analysis.timestamp).toLocaleString()}`, 10, y);
        y += 5;
        doc.setFontSize(10);
        doc.text(`Keywords: ${analysis.keywords.join(', ')}`, 10, y);
        y += 5;
        for (const result of analysis.results) {
          doc.text(`  - ${result.keyword}: Critical: ${result.risk_percent?.Critical?.toFixed(1) || 0}%, High: ${result.risk_percent?.High?.toFixed(1) || 0}%, Medium: ${result.risk_percent?.Medium?.toFixed(1) || 0}%, Low: ${result.risk_percent?.Low?.toFixed(1) || 0}%, Very Low: ${result.risk_percent?.['Very Low']?.toFixed(1) || 0}%`, 10, y);
          y += 5;
          if (y > 270) { doc.addPage(); y = 10; }
        }
        y += 2;
        if (y > 270) { doc.addPage(); y = 10; }
      }
    } else {
      doc.text("No analysis history available.", 10, y);
      y += 5;
    }

    // 4. General Recommendations by Keyword
    doc.setFontSize(13);
    doc.text("General Recommendations by Keyword", 10, y);
    y += 7;
    doc.setFontSize(10);
    if (riskResults && riskResults.length > 0) {
      for (const risk of riskResults) {
        const highestSeverity = getHighestSeverityForKeyword(risk.keyword, allSearchedVulnerabilities);
        const rec = getRecommendationBySeverity(highestSeverity);
        doc.text(`${risk.keyword}: ${rec}`, 12, y);
        y += 6;
        if (y > 270) { doc.addPage(); y = 10; }
      }
    } else {
      doc.text("No keywords analyzed.", 10, y);
      y += 5;
    }

    doc.save(`risk_analysis_full_${new Date().toISOString().slice(0,10)}.pdf`);
  };

  // Helper: get highest severity for a keyword
  function getHighestSeverityForKeyword(keyword, vulnerabilities) {
    // Map severities to a score for comparison
    const severityOrder = { 'critical': 4, 'high': 3, 'medium': 2, 'low': 1, 'very low': 0 };
    let max = -1;
    let found = null;
    (vulnerabilities || []).forEach(vuln => {
      const desc = vuln.cve.descriptions[0]?.value?.toLowerCase() || '';
      if (desc.includes(keyword.toLowerCase()) || vuln.cve.id.toLowerCase().includes(keyword.toLowerCase())) {
        // Try to get severity from vuln (NVD format: vuln.cve.metrics.cvssMetricV31[0].cvssData.baseSeverity)
        let sev = null;
        if (vuln.cve.metrics?.cvssMetricV31?.[0]?.cvssData?.baseSeverity) {
          sev = vuln.cve.metrics.cvssMetricV31[0].cvssData.baseSeverity.toLowerCase();
        } else if (vuln.cve.metrics?.cvssMetricV2?.[0]?.baseSeverity) {
          sev = vuln.cve.metrics.cvssMetricV2[0].baseSeverity.toLowerCase();
        }
        if (sev && severityOrder[sev] !== undefined && severityOrder[sev] > max) {
          max = severityOrder[sev];
          found = sev;
        }
      }
    });
    // Fallback: if no severity found, return null
    return found;
  }

  // Helper: get recommendation by severity
  function getRecommendationBySeverity(severity) {
    switch (severity) {
      case 'critical':
        return 'Immediate action required: Update to the latest version and apply all available security patches.';
      case 'high':
        return 'High risk detected: Review vendor advisories and apply recommended mitigations.';
      case 'medium':
        return 'Medium risk: Monitor for updates and consider applying mitigations.';
      case 'low':
        return 'Low risk: Keep systems updated and follow best security practices.';
      case 'very low':
        return 'Very low risk: Maintain regular security hygiene.';
      default:
        return 'No specific recommendation available. Follow general security best practices.';
    }
  }

  // Función para actualizar el estado de un riesgo
  const handleStatusChange = async (riskId, newStatus) => {
    await updateRiskStatus(riskId, JSON.stringify(newStatus));
    // Refrescar los resultados de riesgo si es necesario
    setRiskResults(riskResults =>
      riskResults.map(r => r.id === riskId ? { ...r, status: newStatus } : r)
    );
  };

  return (
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
      )}      {activeTab === "analysis" && (
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

          {/* Formulario de observaciones */}
          <div style={{
            background: "#f8fafc",
            border: "1px solid #e2e8f0",
            borderRadius: "0.75rem",
            padding: "1.5rem",
            marginTop: "2rem"
          }}>
            <h3 style={{ color: "#1e40af", marginBottom: "1rem" }}>📝 Observations & Recommendations</h3>
            {riskResults && riskResults.length > 0 && (
              <div style={{ marginBottom: "1rem" }}>
                <label style={{ fontWeight: 600, color: "#374151", marginRight: 8 }}>Select Risk:</label>
                <select
                  value={selectedRiskId || ""}
                  onChange={e => setSelectedRiskId(Number(e.target.value))}
                  style={{ padding: "0.5rem", borderRadius: "0.5rem", border: "1px solid #e2e8f0", fontSize: "1rem" }}
                >
                  {riskResults.map(risk => (
                    <option key={risk.id} value={risk.id}>
                      {risk.keyword || `Risk ${risk.id}`}
                    </option>
                  ))}
                </select>
              </div>
            )}
            <form onSubmit={handleObservationSubmit} style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
              <textarea
                value={observationText}
                onChange={e => setObservationText(e.target.value)}
                placeholder="Add your observation or recommendation..."
                rows={2}
                style={{ flex: 1, borderRadius: "0.5rem", border: "1px solid #e2e8f0", padding: "0.75rem", fontSize: "1rem" }}
              />
              <button type="submit" disabled={obsLoading || !observationText.trim()} style={{
                background: "#2563eb",
                color: "#fff",
                border: "none",
                borderRadius: "0.5rem",
                padding: "0.75rem 1.5rem",
                fontWeight: "600",
                cursor: obsLoading ? "not-allowed" : "pointer"
              }}>
                {obsLoading ? "Saving..." : "Add"}
              </button>
            </form>
            <div style={{ maxHeight: 200, overflowY: "auto" }}>
              {observations.length === 0 ? (
                <p style={{ color: "#64748b" }}>No observations yet.</p>
              ) : (
                <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                  {observations.map(obs => (
                    <li key={obs.id} style={{
                      background: "#fff",
                      border: "1px solid #e2e8f0",
                      borderRadius: "0.5rem",
                      padding: "0.75rem",
                      marginBottom: "0.5rem",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center"
                    }}>
                      <div>
                        <div style={{ fontSize: "0.95rem", color: "#374151" }}>{obs.content}</div>
                        <div style={{ fontSize: "0.8rem", color: "#64748b", marginTop: 4 }}>
                          {obs.author ? <b>{obs.author}</b> : "Anon"} | {new Date(obs.timestamp).toLocaleString()}
                        </div>
                      </div>
                      <button 
                        onClick={() => handleDeleteObservation(obs.id)}
                        style={{
                          background: "transparent",
                          border: "none",
                          color: "#ef4444",
                          cursor: "pointer",
                          fontSize: "1.2rem",
                          padding: "0.25rem"
                        }}
                        title="Delete observation"
                      >
                        &times;
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            {riskResults && riskResults.length > 0 && (
              <button
                onClick={exportAnalysisToCSV}
                style={{
                  marginBottom: 16,
                  background: "#059669",
                  color: "#fff",
                  border: "none",
                  borderRadius: "0.5rem",
                  padding: "0.75rem 1.5rem",
                  fontWeight: "600",
                  cursor: "pointer",
                  float: "right"
                }}
              >
                ⬇️ Export Analysis to CSV
              </button>
            )}
            {riskResults && riskResults.length > 0 && (
              <button
                onClick={exportAnalysisToPDF}
                style={{
                  marginBottom: 16,
                  marginLeft: 8,
                  background: "#2563eb",
                  color: "#fff",
                  border: "none",
                  borderRadius: "0.5rem",
                  padding: "0.75rem 1.5rem",
                  fontWeight: "600",
                  cursor: "pointer",
                  float: "right"
                }}
              >
                ⬇️ Export Analysis to PDF
              </button>
            )}
          </div>

          {/* En la sección de análisis, debajo del gráfico o matriz de riesgos, mostrar la lista de riesgos con su estado y selector */}
          <div style={{ marginTop: 32, marginBottom: 32 }}>
            {riskResults && riskResults.length > 0 && (
              <>
                <h3 style={{ color: "#1e40af", marginBottom: 12 }}>🛡️ Risk Status Tracking</h3>
                <table style={{ width: "100%", background: "#fff", borderRadius: 8, border: "1px solid #e2e8f0", boxShadow: "0 2px 8px #0001", fontSize: 15 }}>
                  <thead>
                    <tr style={{ background: "#f8fafc" }}>
                      <th style={{ padding: 8, textAlign: "left" }}>Keyword</th>
                      <th style={{ padding: 8, textAlign: "left" }}>Current Status</th>
                      <th style={{ padding: 8, textAlign: "left" }}>Change Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {riskResults.map(risk => (
                      <tr key={risk.id}>
                        <td style={{ padding: 8 }}>{risk.keyword}</td>
                        <td style={{ padding: 8 }}>{risk.status || "Pending"}</td>
                        <td style={{ padding: 8 }}>
                          <select
                            value={risk.status || "Pending"}
                            onChange={e => handleStatusChange(risk.id, e.target.value)}
                            style={{ padding: "0.5rem", borderRadius: 6, border: "1px solid #e2e8f0" }}
                          >
                            {riskStatusOptions.map(opt => (
                              <option key={opt} value={opt}>{opt}</option>
                            ))}
                          </select>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}
            {/* General Recommendations by Keyword (always show) */}
            <div style={{ marginTop: 32, background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, padding: 24 }}>
              <h4 style={{ color: '#1e40af', marginBottom: 12 }}>General Recommendations by Keyword</h4>
              <ul style={{ listStyle: 'disc', paddingLeft: 24 }}>
                {(riskResults || []).map(risk => {
                  const highestSeverity = getHighestSeverityForKeyword(risk.keyword, allSearchedVulnerabilities);
                  const rec = getRecommendationBySeverity(highestSeverity);
                  return (
                    <li key={risk.keyword} style={{ marginBottom: 8 }}>
                      <b>{risk.keyword}:</b> {rec}
                    </li>
                  );
                })}
              </ul>
            </div>
          </div>
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
