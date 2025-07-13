import React, { useEffect, useState } from "react";
import { getAllQueueResults } from "../services/nvd";
import AsyncSoftwareAnalysis from "../components/AsyncSoftwareAnalysis";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend
} from "chart.js";

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend);

function NvdDashboard({ allQueueResults, loading }) {
  // Calculate dashboard metrics
  const totalJobs = allQueueResults.length;
  const completedJobs = allQueueResults.filter(j => j.status === "completed").length;
  const inProgressJobs = allQueueResults.filter(j => j.status === "processing" || j.status === "pending").length;
  const totalVulnerabilities = allQueueResults.reduce((sum, job) => sum + (job.vulnerabilities ? job.vulnerabilities.length : 0), 0);

  // Prepare chart data: vulnerabilities per job
  const chartLabels = allQueueResults.map(j => j.keyword || `Job ${j.job_id}`);
  const chartData = allQueueResults.map(j => (j.vulnerabilities ? j.vulnerabilities.length : 0));
  const barData = {
    labels: chartLabels,
    datasets: [
      {
        label: "Vulnerabilities per Job",
        data: chartData,
        backgroundColor: "#2563eb",
        borderRadius: 8,
        maxBarThickness: 40
      }
    ]
  };
  const barOptions = {
    responsive: true,
    plugins: {
      legend: { display: false },
      tooltip: { enabled: true }
    },
    scales: {
      x: {
        title: { display: true, text: "Job" },
        ticks: { color: "#64748b" }
      },
      y: {
        title: { display: true, text: "Vulnerabilities" },
        beginAtZero: true,
        ticks: { color: "#64748b", precision: 0 }
      }
    }
  };

  return (
    <div style={{ marginTop: "2.5rem" }}>
      <div style={{
        display: "flex",
        gap: "2rem",
        marginBottom: "2rem",
        justifyContent: "center"
      }}>
        <div style={{
          background: "#f1f5f9",
          borderRadius: "1rem",
          padding: "1.5rem 2rem",
          minWidth: "180px",
          textAlign: "center",
          boxShadow: "0 2px 4px rgba(0,0,0,0.04)"
        }}>
          <div style={{ fontSize: "2rem" }}>📦</div>
          <div style={{ fontWeight: 700, fontSize: "1.2rem", color: "#1e40af" }}>{loading ? "..." : totalJobs}</div>
          <div style={{ color: "#64748b", fontSize: "0.95rem" }}>Total Jobs</div>
        </div>
        <div style={{
          background: "#f1f5f9",
          borderRadius: "1rem",
          padding: "1.5rem 2rem",
          minWidth: "180px",
          textAlign: "center",
          boxShadow: "0 2px 4px rgba(0,0,0,0.04)"
        }}>
          <div style={{ fontSize: "2rem" }}>✅</div>
          <div style={{ fontWeight: 700, fontSize: "1.2rem", color: "#16a34a" }}>{loading ? "..." : completedJobs}</div>
          <div style={{ color: "#64748b", fontSize: "0.95rem" }}>Completed</div>
        </div>
        <div style={{
          background: "#f1f5f9",
          borderRadius: "1rem",
          padding: "1.5rem 2rem",
          minWidth: "180px",
          textAlign: "center",
          boxShadow: "0 2px 4px rgba(0,0,0,0.04)"
        }}>
          <div style={{ fontSize: "2rem" }}>⏳</div>
          <div style={{ fontWeight: 700, fontSize: "1.2rem", color: "#f59e42" }}>{loading ? "..." : inProgressJobs}</div>
          <div style={{ color: "#64748b", fontSize: "0.95rem" }}>In Progress</div>
        </div>
        <div style={{
          background: "#f1f5f9",
          borderRadius: "1rem",
          padding: "1.5rem 2rem",
          minWidth: "180px",
          textAlign: "center",
          boxShadow: "0 2px 4px rgba(0,0,0,0.04)"
        }}>
          <div style={{ fontSize: "2rem" }}>🚨</div>
          <div style={{ fontWeight: 700, fontSize: "1.2rem", color: "#dc2626" }}>{loading ? "..." : totalVulnerabilities}</div>
          <div style={{ color: "#64748b", fontSize: "0.95rem" }}>Vulnerabilities Found</div>
        </div>
      </div>
      <div style={{
        background: "#fff",
        borderRadius: "1rem",
        boxShadow: "0 2px 4px rgba(0,0,0,0.04)",
        padding: "2rem",
        maxWidth: "900px",
        margin: "0 auto"
      }}>
        <h3 style={{ color: "#1e40af", fontWeight: 600, marginBottom: "1.5rem" }}>Vulnerabilities per Job</h3>
        {chartLabels.length === 0 ? (
          <div style={{ textAlign: "center", color: "#64748b", padding: "2rem" }}>
            No jobs to display.
          </div>
        ) : (
          <Bar data={barData} options={barOptions} height={260} />
        )}
      </div>
    </div>
  );
}

export default function NvdPage() {
  const [allQueueResults, setAllQueueResults] = useState([]);
  const [loadingAllResults, setLoadingAllResults] = useState(false);
  const [error, setError] = useState("");

  const loadAllQueueResults = async () => {
    setLoadingAllResults(true);
    setError("");
    try {
      const results = await getAllQueueResults();
      setAllQueueResults(results);
    } catch (error) {
      setError("Failed to load queue results");
    } finally {
      setLoadingAllResults(false);
    }
  };

  useEffect(() => {
    loadAllQueueResults();
  }, []);

  return (
    <div className="nvd-page" style={{ 
      padding: "2rem", 
      maxWidth: "1400px", 
      margin: "0 auto", 
      width: "100%",
      minHeight: "100vh"
    }}>
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
      {/* Async Analysis Section */}
      <div style={{ 
        background: "#ffffff",
        padding: "2rem",
        borderRadius: "1rem",
        boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
        marginBottom: "2rem"
      }}>
        <AsyncSoftwareAnalysis />
      </div>
      {/* Found Vulnerabilities Section (always visible) */}
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
            🔍 Found Vulnerabilities from Queue Analysis
          </h2>
          <button
            onClick={loadAllQueueResults}
            disabled={loadingAllResults}
            style={{
              background: "#2563eb",
              color: "white",
              border: "none",
              padding: "0.75rem 1.5rem",
              borderRadius: "0.5rem",
              fontWeight: "600",
              cursor: loadingAllResults ? "not-allowed" : "pointer",
              fontSize: "0.9rem"
            }}
          >
            {loadingAllResults ? "🔄 Loading..." : "🔄 Refresh Results"}
          </button>
        </div>
        {error && (
          <div style={{
            background: "#fee2e2",
            color: "#dc2626",
            padding: "1rem",
            borderRadius: "0.5rem",
            border: "1px solid #fecaca",
            marginBottom: "1rem"
          }}>
            <strong>Error:</strong> {error}
          </div>
        )}
        {loadingAllResults ? (
          <div style={{ 
            textAlign: "center", 
            padding: "3rem",
            background: "#f8fafc",
            borderRadius: "1rem",
            border: "1px solid #e2e8f0"
          }}>
            <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>🔄</div>
            <p style={{ color: "#64748b", fontSize: "1.1rem" }}>
              Loading vulnerability results...
            </p>
          </div>
        ) : allQueueResults.length === 0 ? (
          <div style={{ 
            textAlign: "center", 
            padding: "3rem",
            background: "#f8fafc",
            borderRadius: "1rem",
            border: "1px solid #e2e8f0"
          }}>
            <div style={{ fontSize: "4rem", marginBottom: "1rem" }}>📋</div>
            <h3 style={{ color: "#374151", marginBottom: "0.5rem" }}>
              No Vulnerability Results Found
            </h3>
            <p style={{ color: "#64748b", fontSize: "1rem", maxWidth: "500px", margin: "0 auto" }}>
              Run some software analysis using the Async Analysis section to see vulnerability results here.
            </p>
          </div>
        ) : (
          <div style={{ display: "grid", gap: "2rem" }}>
            {allQueueResults.map((job, index) => (
              <div
                key={job.job_id || index}
                style={{
                  background: "#f8fafc",
                  border: "1px solid #e2e8f0",
                  borderRadius: "1rem",
                  padding: "1.5rem",
                  boxShadow: "0 2px 4px rgba(0,0,0,0.05)"
                }}
              >
                <div style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "1rem"
                }}>
                  <h3 style={{
                    color: "#1e40af",
                    margin: 0,
                    fontSize: "1.25rem",
                    fontWeight: "600"
                  }}>
                    📦 {job.keyword || `Job ${job.job_id}`}
                  </h3>
                  <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
                    <span style={{
                      background: job.status === "completed" ? "#dcfce7" : "#fef3c7",
                      color: job.status === "completed" ? "#166534" : "#92400e",
                      padding: "0.25rem 0.75rem",
                      borderRadius: "0.5rem",
                      fontSize: "0.8rem",
                      fontWeight: "600",
                      textTransform: "uppercase"
                    }}>
                      {job.status || "Unknown"}
                    </span>
                    <span style={{
                      color: "#64748b",
                      fontSize: "0.9rem"
                    }}>
                      ID: {job.job_id}
                    </span>
                  </div>
                </div>
                {job.processed_at && (
                  <p style={{
                    color: "#64748b",
                    fontSize: "0.9rem",
                    margin: "0 0 1rem 0"
                  }}>
                    🕒 Processed: {new Date(job.processed_at).toLocaleString()}
                  </p>
                )}
                {job.vulnerabilities && job.vulnerabilities.length > 0 ? (
                  <div>
                    <h4 style={{
                      color: "#374151",
                      marginBottom: "1rem",
                      fontSize: "1.1rem"
                    }}>
                      🚨 Vulnerabilities Found ({job.total_results || job.vulnerabilities.length})
                    </h4>
                    <div style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(auto-fill, minmax(350px, 1fr))",
                      gap: "1rem",
                      maxHeight: "400px",
                      overflowY: "auto"
                    }}>
                      {job.vulnerabilities.map((vuln, vulnIndex) => (
                        <div
                          key={`${job.job_id}-${vulnIndex}`}
                          style={{
                            background: "#ffffff",
                            border: "1px solid #d1d5db",
                            borderRadius: "0.75rem",
                            padding: "1rem",
                            borderLeft: "4px solid #dc2626"
                          }}
                        >
                          <div style={{
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "flex-start",
                            marginBottom: "0.75rem"
                          }}>
                            <h5 style={{
                              color: "#dc2626",
                              margin: 0,
                              fontSize: "0.95rem",
                              fontWeight: "600",
                              lineHeight: "1.2"
                            }}>
                              {vuln.cve?.id || "Unknown CVE"}
                            </h5>
                          </div>
                          {vuln.cve?.descriptions?.[0]?.value && (
                            <p style={{
                              color: "#475569",
                              fontSize: "0.85rem",
                              lineHeight: "1.4",
                              margin: "0 0 0.75rem 0",
                              display: "-webkit-box",
                              WebkitLineClamp: 3,
                              WebkitBoxOrient: "vertical",
                              overflow: "hidden"
                            }}>
                              {vuln.cve.descriptions[0].value}
                            </p>
                          )}
                          <div style={{
                            display: "grid",
                            gridTemplateColumns: "1fr 1fr",
                            gap: "0.5rem",
                            fontSize: "0.8rem",
                            color: "#64748b"
                          }}>
                            {vuln.cve?.published && (
                              <div>
                                <strong>Published:</strong><br />
                                {new Date(vuln.cve.published).toLocaleDateString()}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div style={{
                    background: "#ffffff",
                    border: "1px solid #d1d5db",
                    borderRadius: "0.75rem",
                    padding: "2rem",
                    textAlign: "center"
                  }}>
                    <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>✅</div>
                    <p style={{ color: "#10b981", fontWeight: "600", margin: 0 }}>
                      No vulnerabilities found for this software
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      {/* NVD Dashboard (moved below) */}
      <NvdDashboard allQueueResults={allQueueResults} loading={loadingAllResults} />
    </div>
  );
}
