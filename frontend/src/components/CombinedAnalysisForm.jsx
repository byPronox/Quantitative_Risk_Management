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
      alert("Error analyzing risk.");
    }
    setLoading(false);
  };

  return (
    <section className="analysis-form">
      <h2>Analyze Asset: <span style={{color:'#23272f', fontWeight:600}}>{asset.name}</span></h2>
      <form onSubmit={handleSubmit} autoComplete="off">
        <fieldset>
          <legend>CICIDS Features</legend>
          <div className="form-grid">
            {Object.keys(cicids).map(key => (
              <label key={key}>
                {key}
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
          </div>
        </fieldset>
        <fieldset>
          <legend>LANL Features</legend>
          <div className="form-grid">
            <label>
              time
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
              user
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
              computer
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
          {loading ? "Analyzing..." : "Analyze Risk"}
        </button>
      </form>
      {result && <RiskScoreCard result={result} />}
    </section>
  );
}