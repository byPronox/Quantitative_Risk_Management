import React, { useState } from "react";
import api from "../services/api";
import "./CicidsPredictor.css";

export default function CicidsPredictor() {
  const [form, setForm] = useState({
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
  });
  const [result, setResult] = useState(null);

  const handleChange = e => {
    setForm({ ...form, [e.target.name]: Number(e.target.value) });
  };

  const handleSubmit = async e => {
    e.preventDefault();
    const res = await api.post("/predict/cicids/", form);
    setResult(res.data.attack_probability);
  };

  return (
    <div className="cicids-container">
      <h2>CICIDS Attack Prediction</h2>
      <form onSubmit={handleSubmit} className="cicids-form">
        {Object.keys(form).map(key => (
          <div key={key} className="cicids-field">
            <label>{key}</label>
            <input
              type="number"
              name={key}
              value={form[key]}
              onChange={handleChange}
            />
          </div>
        ))}
        <button type="submit">Predecir</button>
      </form>
      {result !== null && (
        <div className="cicids-result">
          <strong>Probabilidad de ataque:</strong> {result}
        </div>
      )}
    </div>
  );
}