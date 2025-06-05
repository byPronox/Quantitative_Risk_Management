import React from "react";

function getRiskLevel(score) {
  if (score < 0.33) return { label: "Low", color: "#22c55e" };
  if (score < 0.66) return { label: "Medium", color: "#eab308" };
  return { label: "High", color: "#ef4444" };
}

export default function RiskScoreCard({ result }) {
  const { combined_score, cicids_probability, lanl_probability } = result;
  const risk = getRiskLevel(combined_score);

  return (
    <div className="risk-score-card" style={{ borderColor: risk.color }}>
      <h3>
        Threat Score: <span style={{ color: risk.color }}>{(combined_score * 100).toFixed(2)}%</span>
      </h3>
      <p>
        <strong>Risk Level:</strong>{" "}
        <span style={{ color: risk.color }}>{risk.label}</span>
      </p>
      <div className="risk-details">
        <small>CICIDS Model: {(cicids_probability * 100).toFixed(2)}%</small>
        <br />
        <small>LANL Model: {(lanl_probability * 100).toFixed(2)}%</small>
      </div>
    </div>
  );
}