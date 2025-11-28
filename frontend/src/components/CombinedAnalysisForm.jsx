import React, { useState } from "react";
import api from "../services/api";
import RiskScoreCard from "./RiskScoreCard";

const initialCICIDS = {
  "Flow Duration": 100,
  "Total Fwd Packets": 10000,
  "Total Backward Packets": 1,
  "Total Length of Fwd Packets": 1000000,
  "Total Length of Bwd Packets": 100,
  "Fwd Packet Length Mean": 1500,
  "Bwd Packet Length Mean": 10,
  "Flow Bytes/s": 10000000,
  "Flow Packets/s": 100000,
  "Packet Length Mean": 1400,
  "Packet Length Std": 500,
  "Average Packet Size": 1450,
  "Avg Fwd Segment Size": 1500,
  "Avg Bwd Segment Size": 10,
  "Init_Win_bytes_forward": 64,
  "Init_Win_bytes_backward": 64
};

const cicidsLabels = {
  "Flow Duration": "Duración del Flujo",
  "Total Fwd Packets": "Total Paquetes Enviados",
  "Total Backward Packets": "Total Paquetes Recibidos",
  "Total Length of Fwd Packets": "Longitud Total Paquetes Env.",
  "Total Length of Bwd Packets": "Longitud Total Paquetes Rec.",
  "Fwd Packet Length Mean": "Media Longitud Paquete Env.",
  "Bwd Packet Length Mean": "Media Longitud Paquete Rec.",
  "Flow Bytes/s": "Bytes de Flujo/s",
  "Flow Packets/s": "Paquetes de Flujo/s",
  "Packet Length Mean": "Media Longitud de Paquete",
  "Packet Length Std": "Desv. Est. Longitud Paquete",
  "Average Packet Size": "Tamaño Promedio de Paquete",
  "Avg Fwd Segment Size": "Tam. Prom. Segmento Env.",
  "Avg Bwd Segment Size": "Tam. Prom. Segmento Rec.",
  "Init_Win_bytes_forward": "Bytes Ventana Inicial Env.",
  "Init_Win_bytes_backward": "Bytes Ventana Inicial Rec."
};

const initialLANL = {
  time: 1,
  user: "U1",
  computer: "C1"
};

export default function CombinedAnalysisForm({ asset }) {
  const [cicids, setCicids] = useState(initialCICIDS);
  const [lanl, setLanl] = useState(initialLANL);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleCicidsChange = e => {
    setCicids({ ...cicids, [e.target.name]: Number(e.target.value) });
  };

  const handleLanlChange = e => {
    setLanl({
      ...lanl,
      [e.target.name]: e.target.name === "time" ? Number(e.target.value) : e.target.value
    });
  };

  const handleSubmit = async e => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const res = await api.post("/predict/combined/", {
        cicids,
        lanl
      });
      setResult(res.data);
    } catch (err) {
      alert("Error al analizar el riesgo.");
    }
    setLoading(false);
  };

  return (<section className="analysis-form">
    <h2>Analizar Activo: <span style={{ color: '#23272f', fontWeight: 600 }}>{asset.name}</span></h2>
    <form onSubmit={handleSubmit} autoComplete="off">
      <fieldset>
        <legend>Características CICIDS</legend>
        <div className="form-grid">
          {Object.keys(cicids).map(key => (
            <label key={key}>
              {cicidsLabels[key] || key}
              <input
                type="number"
                name={key}
                value={cicids[key]}
                onChange={handleCicidsChange}
                required
                min={0}
                step={1}
              />
            </label>
          ))}
        </div>        </fieldset>
      <fieldset>
        <legend>Características LANL</legend>
        <div className="form-grid">
          <label>
            Tiempo
            <input
              type="number"
              name="time"
              value={lanl.time}
              onChange={handleLanlChange}
              required
              min={0}
              step={1}
            />
          </label>
          <label>
            Usuario
            <input
              type="text"
              name="user"
              value={lanl.user}
              onChange={handleLanlChange}
              required
              placeholder="U1"
              maxLength={8}
            />
          </label>
          <label>
            Computadora
            <input
              type="text"
              name="computer"
              value={lanl.computer}
              onChange={handleLanlChange}
              required
              placeholder="C1"
              maxLength={8}
            />
          </label>
        </div>
      </fieldset>
      <button type="submit" disabled={loading} aria-busy={loading}>
        {loading ? "Analizando..." : "Analizar Riesgo"}
      </button>
    </form>
    {result && <RiskScoreCard result={result} />}
  </section>
  );
}