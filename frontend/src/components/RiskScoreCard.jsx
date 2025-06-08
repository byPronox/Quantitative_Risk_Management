import React from "react";

function getRiskLevel(score) {
  if (score < 0.33) return { label: "Low", color: "#22c55e", shadow: "#22c55e30" };
  if (score < 0.66) return { label: "Medium", color: "#eab308", shadow: "#eab30830" };
  return { label: "High", color: "#ef4444", shadow: "#ef444430" };
}

export default function RiskScoreCard({ result }) {
  const { combined_score, cicids_probability, lanl_probability } = result;
  const risk = getRiskLevel(combined_score);

  return (
    <div className="risk-score-card" style={{ borderColor: risk.color, boxShadow: `0 2px 16px ${risk.shadow}` }}>
      <h3>
        Threat Score: <span style={{ color: risk.color }}>{(combined_score * 100).toFixed(2)}%</span>
      </h3>
      <p style={{ fontWeight: 600, color: risk.color, fontSize: '1.08rem', margin: '0.5em 0' }}>
        <strong>Risk Level:</strong> <span>{risk.label}</span>
      </p>
      <div className="risk-details">
        <small>CICIDS Model: <b style={{color:'#2563eb'}}>{(cicids_probability * 100).toFixed(2)}%</b></small>
        <br />
        <small>LANL Model: <b style={{color:'#2563eb'}}>{(lanl_probability * 100).toFixed(2)}%</b></small>
      </div>
    </div>
  );
}