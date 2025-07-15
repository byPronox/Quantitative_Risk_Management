import React, { useState } from "react";
import { loginUser } from "../services/user";

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await loginUser(username, password);
      if (onLogin) onLogin(data);
      setLoading(false);
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed");
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "linear-gradient(135deg, #e0e7ff 0%, #f8fafc 100%)"
    }}>
      <form
        onSubmit={handleSubmit}
        style={{
          background: "#fff",
          padding: 36,
          borderRadius: 16,
          boxShadow: "0 4px 24px 0 rgba(0,0,0,0.08)",
          minWidth: 340,
          maxWidth: 380,
          width: "100%"
        }}
      >
        <h2 style={{
          textAlign: "center",
          marginBottom: 28,
          color: "#1e293b",
          fontWeight: 700,
          fontSize: 28
        }}>
          Iniciar sesión
        </h2>
        <div style={{ marginBottom: 18 }}>
          <label style={{ fontWeight: 500, color: "#475569" }}>Usuario</label>
          <input
            type="text"
            value={username}
            onChange={e => setUsername(e.target.value)}
            required
            style={{
              width: "100%",
              padding: "10px 12px",
              marginTop: 6,
              border: "1px solid #cbd5e1",
              borderRadius: 8,
              fontSize: 16,
              outline: "none",
              background: "#f1f5f9"
            }}
            placeholder="Tu usuario"
          />
        </div>
        <div style={{ marginBottom: 18 }}>
          <label style={{ fontWeight: 500, color: "#475569" }}>Contraseña</label>
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            style={{
              width: "100%",
              padding: "10px 12px",
              marginTop: 6,
              border: "1px solid #cbd5e1",
              borderRadius: 8,
              fontSize: 16,
              outline: "none",
              background: "#f1f5f9"
            }}
            placeholder="Tu contraseña"
          />
        </div>
        {error && <div style={{ color: "#ef4444", marginBottom: 16, textAlign: "center" }}>{error}</div>}
        <button
          type="submit"
          disabled={loading}
          style={{
            width: "100%",
            padding: "12px 0",
            background: "linear-gradient(90deg, #6366f1 0%, #3b82f6 100%)",
            color: "#fff",
            fontWeight: 600,
            fontSize: 17,
            border: "none",
            borderRadius: 8,
            cursor: loading ? "not-allowed" : "pointer",
            boxShadow: "0 2px 8px 0 rgba(59,130,246,0.10)",
            transition: "background 0.2s"
          }}
        >
          {loading ? "Entrando..." : "Entrar"}
        </button>
      </form>
    </div>
  );
}
