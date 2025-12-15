import React from "react";

export default function NvdRiskPie({ results }) {
  // Ensure results is an array before proceeding
  if (!results || !Array.isArray(results) || results.length === 0) return null;

  // Flatten all keywords and their risk_percent into a single array for charting
  const chartData = results.map(({ keyword, risk_percent }) => {
    // Find the highest risk level for this keyword
    let maxLevel = "Bajo";
    let maxValue = 0;
    Object.entries(risk_percent).forEach(([level, value]) => {
      if (value > maxValue) {
        maxLevel = level;
        maxValue = value;
      }
    });
    return {
      keyword,
      level: maxLevel,
      value: maxValue,
      risk_percent
    };
  });
  // Pie chart colors for each risk level
  const colors = {
    "Crítico": "#ef4444",
    "Alto": "#eab308",
    "Medio": "#38bdf8",
    "Bajo": "#22c55e",
    "Muy Bajo": "#a3a3a3"
  };

  // Total for pie chart (sum of maxValue for each keyword)
  const total = chartData.reduce((sum, d) => sum + d.value, 0);

  // Pie chart SVG (simple, no external lib)
  let startAngle = 0;
  const pieSlices = chartData.map((d, i) => {
    const angle = (d.value / total) * 360;
    const endAngle = startAngle + angle;
    // Convert angles to radians
    const largeArc = angle > 180 ? 1 : 0;
    const x1 = 100 + 90 * Math.cos((Math.PI * startAngle) / 180);
    const y1 = 100 + 90 * Math.sin((Math.PI * startAngle) / 180);
    const x2 = 100 + 90 * Math.cos((Math.PI * endAngle) / 180);
    const y2 = 100 + 90 * Math.sin((Math.PI * endAngle) / 180);
    const pathData = `M100,100 L${x1},${y1} A90,90 0 ${largeArc},1 ${x2},${y2} Z`;
    const slice = (
      <path
        key={d.keyword}
        d={pathData}
        fill={colors[d.level] || "#888"}
        stroke="#fff"
        strokeWidth={2}
      >
        <title>{`${d.keyword}: ${d.level} (${d.value.toFixed(1)}%)`}</title>
      </path>
    );
    startAngle = endAngle;
    return slice;
  });

  return (
    <div style={{ marginTop: 32, textAlign: "center" }}>      <h3 style={{ color: "#2563eb", marginBottom: 12 }}>Gráfico Circular de Análisis de Riesgos</h3>
      <svg width={220} height={220} viewBox="0 0 200 200">
        {pieSlices}
        <circle cx={100} cy={100} r={60} fill="#fff" />
        <text x={100} y={105} textAnchor="middle" fontSize={18} fontWeight={700} fill="#2563eb">Riesgo</text>
      </svg>
      <div style={{ marginTop: 18, display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 16 }}>
        {chartData.map((d, i) => (
          <div key={d.keyword} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ width: 16, height: 16, borderRadius: 8, background: colors[d.level], display: "inline-block" }} />
            <span style={{ fontWeight: 600 }}>{d.keyword}</span>
            <span style={{ color: colors[d.level], fontWeight: 600 }}>{d.level}</span>
            <span style={{ color: "#64748b", fontSize: 13 }}>({d.value.toFixed(1)}%)</span>
          </div>
        ))}
      </div>
    </div>
  );
}
