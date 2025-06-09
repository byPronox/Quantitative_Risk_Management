// filepath: c:\Users\USER-PC\Desktop\Quantitative_Risk_Management\frontend\src\components\AssetRiskMatrix.jsx
import React from "react";

export default function AssetRiskMatrix({ riskResults, riskThresholds }) {
  if (!riskResults || riskResults.length === 0) return null;

  // Calculate overall risk score for enterprise asset management
  const calculateOverallRisk = (results) => {
    const totalScores = { critical: 0, high: 0, medium: 0, low: 0, veryLow: 0 };
    let totalAssets = results.length;

    results.forEach(result => {
      Object.entries(result.risk_percent || {}).forEach(([level, percent]) => {
        const levelKey = level.toLowerCase().replace(/\s+/g, '');
        if (totalScores.hasOwnProperty(levelKey)) {
          totalScores[levelKey] += percent;
        }
      });
    });

    // Calculate weighted risk score (Critical=5, High=4, Medium=3, Low=2, Very Low=1)
    const weights = { critical: 5, high: 4, medium: 3, low: 2, verylow: 1 };
    let weightedScore = 0;
    let maxPossibleScore = 0;

    Object.entries(totalScores).forEach(([level, score]) => {
      const weight = weights[level] || 1;
      weightedScore += (score / totalAssets) * weight;
      maxPossibleScore += 100 * weight;
    });

    return (weightedScore / maxPossibleScore) * 100;
  };

  const overallRiskScore = calculateOverallRisk(riskResults);
  
  const getRiskLevel = (score) => {
    if (score >= riskThresholds.critical) return { level: "Critical", color: "#dc2626", bg: "#fef2f2" };
    if (score >= riskThresholds.high) return { level: "High", color: "#d97706", bg: "#fffbeb" };
    if (score >= riskThresholds.medium) return { level: "Medium", color: "#0891b2", bg: "#f0f9ff" };
    if (score >= riskThresholds.low) return { level: "Low", color: "#059669", bg: "#f0fdf4" };
    return { level: "Very Low", color: "#6b7280", bg: "#f9fafb" };
  };

  const currentRisk = getRiskLevel(overallRiskScore);

  // Asset categorization based on keywords
  const categorizeAssets = (results) => {
    const categories = {
      "Web Applications": ["react", "vue", "angular", "javascript", "nodejs", "express"],
      "Infrastructure": ["apache", "nginx", "docker", "kubernetes", "linux", "windows"],
      "Databases": ["mysql", "postgresql", "mongodb", "redis", "oracle"],
      "Development Tools": ["git", "jenkins", "python", "java", "php"],
      "Security Tools": ["openssl", "ssh", "ssl", "tls", "crypto"]
    };

    const assetTypes = {};
    results.forEach(result => {
      let categorized = false;
      Object.entries(categories).forEach(([category, keywords]) => {
        if (keywords.some(keyword => result.keyword.toLowerCase().includes(keyword))) {
          if (!assetTypes[category]) assetTypes[category] = [];
          assetTypes[category].push(result);
          categorized = true;
        }
      });
      if (!categorized) {
        if (!assetTypes["Other"]) assetTypes["Other"] = [];
        assetTypes["Other"].push(result);
      }
    });

    return assetTypes;
  };

  const assetCategories = categorizeAssets(riskResults);

  return (
    <div style={{ 
      background: "#fff", 
      padding: "1.5rem", 
      borderRadius: "0.75rem",
      border: "1px solid #e5e7eb",
      boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)"
    }}>
      <h3 style={{ 
        color: "#1f2937", 
        marginBottom: "1.5rem", 
        fontSize: "1.25rem",
        display: "flex",
        alignItems: "center",
        gap: "0.5rem"
      }}>
        🏢 Enterprise Asset Risk Matrix
      </h3>

      {/* Overall Risk Score */}
      <div style={{
        background: currentRisk.bg,
        border: `2px solid ${currentRisk.color}`,
        borderRadius: "0.75rem",
        padding: "1.25rem",
        marginBottom: "1.5rem"
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h4 style={{ color: currentRisk.color, margin: 0, fontSize: "1.1rem" }}>
              Overall Asset Risk Score
            </h4>
            <p style={{ color: "#6b7280", margin: "0.25rem 0 0 0", fontSize: "0.9rem" }}>
              Aggregated risk across all monitored assets
            </p>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ 
              fontSize: "2rem", 
              fontWeight: "bold", 
              color: currentRisk.color,
              lineHeight: 1
            }}>
              {overallRiskScore.toFixed(1)}%
            </div>
            <div style={{ 
              fontSize: "0.9rem", 
              fontWeight: "600", 
              color: currentRisk.color 
            }}>
              {currentRisk.level} Risk
            </div>
          </div>
        </div>
      </div>

      {/* Asset Categories */}
      <div style={{ marginBottom: "1.5rem" }}>
        <h4 style={{ color: "#374151", marginBottom: "1rem", fontSize: "1rem" }}>
          📊 Assets by Category
        </h4>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "1rem" }}>
          {Object.entries(assetCategories).map(([category, assets]) => {
            const categoryRisk = calculateOverallRisk(assets);
            const categoryRiskInfo = getRiskLevel(categoryRisk);
            
            return (
              <div key={category} style={{
                background: "#f8fafc",
                border: "1px solid #e2e8f0",
                borderRadius: "0.5rem",
                padding: "1rem"
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                  <h5 style={{ color: "#374151", margin: 0, fontSize: "0.95rem" }}>
                    {category}
                  </h5>
                  <span style={{
                    background: categoryRiskInfo.color,
                    color: "white",
                    padding: "0.25rem 0.5rem",
                    borderRadius: "0.25rem",
                    fontSize: "0.75rem",
                    fontWeight: "600"
                  }}>
                    {categoryRisk.toFixed(1)}%
                  </span>
                </div>
                <div style={{ fontSize: "0.85rem", color: "#6b7280" }}>
                  <div>Assets: {assets.length}</div>
                  <div>Risk Level: {categoryRiskInfo.level}</div>
                </div>
                <div style={{ marginTop: "0.5rem" }}>
                  {assets.slice(0, 3).map((asset, idx) => (
                    <span key={idx} style={{
                      display: "inline-block",
                      background: "#e5e7eb",
                      color: "#374151",
                      padding: "0.125rem 0.375rem",
                      borderRadius: "0.25rem",
                      fontSize: "0.75rem",
                      marginRight: "0.25rem",
                      marginBottom: "0.25rem"
                    }}>
                      {asset.keyword}
                    </span>
                  ))}
                  {assets.length > 3 && (
                    <span style={{ fontSize: "0.75rem", color: "#9ca3af" }}>
                      +{assets.length - 3} more
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Risk Distribution Chart */}
      <div>
        <h4 style={{ color: "#374151", marginBottom: "1rem", fontSize: "1rem" }}>
          📈 Risk Distribution Across Assets
        </h4>
        {riskResults.map((result, idx) => {
          const maxRisk = Math.max(...Object.values(result.risk_percent || {}));
          const maxLevel = Object.entries(result.risk_percent || {}).find(([, value]) => value === maxRisk)?.[0] || "Unknown";
          const riskInfo = getRiskLevel(maxRisk);
          
          return (
            <div key={idx} style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "0.75rem",
              marginBottom: "0.5rem",
              background: "#f8fafc",
              borderRadius: "0.5rem",
              border: "1px solid #e2e8f0"
            }}>
              <div style={{ flex: 1 }}>
                <span style={{ fontWeight: "600", color: "#374151" }}>
                  {result.keyword}
                </span>
                <div style={{ fontSize: "0.85rem", color: "#6b7280", marginTop: "0.25rem" }}>
                  Primary Risk: {maxLevel} ({maxRisk.toFixed(1)}%)
                </div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <div style={{
                  width: "80px",
                  height: "8px",
                  background: "#e5e7eb",
                  borderRadius: "4px",
                  overflow: "hidden"
                }}>
                  <div style={{
                    width: `${maxRisk}%`,
                    height: "100%",
                    background: riskInfo.color,
                    transition: "width 0.3s ease"
                  }} />
                </div>
                <span style={{
                  background: riskInfo.color,
                  color: "white",
                  padding: "0.25rem 0.5rem",
                  borderRadius: "0.25rem",
                  fontSize: "0.75rem",
                  fontWeight: "600",
                  minWidth: "60px",
                  textAlign: "center"
                }}>
                  {riskInfo.level}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
