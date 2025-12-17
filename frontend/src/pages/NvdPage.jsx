import React, { useEffect, useState } from "react";
import { addKeywordToQueue, getAllQueueResults, startConsumer, getConsumerStatus } from "../services/nvd";
import { backendApi } from "../services/api";

export default function NvdPage() {
  const [keyword, setKeyword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [queueJobs, setQueueJobs] = useState([]);
  const [loadingJobs, setLoadingJobs] = useState(false);
  const [consumerRunning, setConsumerRunning] = useState(false);
  const [loadingConsumer, setLoadingConsumer] = useState(false);

  // Cargar jobs de RabbitMQ y estado del consumidor
  const loadQueueJobs = async () => {
    setLoadingJobs(true);
    setError("");
    try {
      const results = await getAllQueueResults();
      // El endpoint devuelve {success: true, jobs: [...]} o directamente un array
      if (results && results.success && Array.isArray(results.jobs)) {
        setQueueJobs(results.jobs);
      } else if (Array.isArray(results)) {
        setQueueJobs(results);
      } else {
        setQueueJobs([]);
      }
    } catch (error) {
      console.error("Error loading queue jobs:", error);
      setError("Error al cargar trabajos de la cola");
      setQueueJobs([]);
    } finally {
      setLoadingJobs(false);
    }
  };

  // Verificar estado del consumidor
  const checkConsumerStatus = async () => {
    try {
      const status = await getConsumerStatus();
      setConsumerRunning(status.running);
    } catch (e) {
      console.error("Error checking consumer status:", e);
      setConsumerRunning(false);
    }
  };

  // Enviar keyword a la cola de RabbitMQ
  const handleSubmitToQueue = async (e) => {
    e.preventDefault();
    if (!keyword.trim()) {
      setError("Por favor ingresa una keyword");
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const result = await addKeywordToQueue(keyword.trim());
      setSuccess(`Trabajo enviado a la cola: ${result.job_id || "ID generado"}`);
      setKeyword("");
      // Recargar jobs después de enviar
      setTimeout(loadQueueJobs, 1000);
    } catch (error) {
      console.error("Error adding keyword to queue:", error);
      setError(`Error al enviar a la cola: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Iniciar consumidor
  const handleStartConsumer = async () => {
    setLoadingConsumer(true);
    setError("");
    try {
      await startConsumer();
      setSuccess("Consumidor iniciado correctamente");
      // Esperar un poco y verificar estado
      setTimeout(checkConsumerStatus, 1500);
      // Recargar jobs después de iniciar consumidor
      setTimeout(loadQueueJobs, 2000);
    } catch (error) {
      console.error("Error starting consumer:", error);
      setError(`Error al iniciar consumidor: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoadingConsumer(false);
    }
  };

  // Cargar datos al montar el componente
  useEffect(() => {
    loadQueueJobs();
    checkConsumerStatus();
    // Polling cada 5 segundos para actualizar datos
    const interval = setInterval(() => {
      loadQueueJobs();
      checkConsumerStatus();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{
      padding: "2rem",
      maxWidth: "1200px",
      margin: "0 auto",
      width: "100%"
    }}>
      <div style={{ textAlign: "center", marginBottom: "2rem" }}>
        <h1 style={{
          fontSize: "2.5rem",
          fontWeight: "700",
          color: "#1e40af",
          marginBottom: "0.5rem"
        }}>
          🛡️ Vulnerabilidades NVD
        </h1>
        <p style={{
          fontSize: "1.1rem",
          color: "#64748b"
        }}>
          Analiza vulnerabilidades usando NVD con RabbitMQ
        </p>
      </div>

      {/* Formulario para enviar keyword a la cola */}
      <div style={{
        background: "#ffffff",
        padding: "2rem",
        borderRadius: "1rem",
        boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
        marginBottom: "2rem"
      }}>
        <h2 style={{
          fontSize: "1.5rem",
          color: "#1e40af",
          marginBottom: "1.5rem",
          fontWeight: "600"
        }}>
          📤 Enviar Keyword a Cola RabbitMQ
        </h2>

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

        {success && (
          <div style={{
            background: "#dcfce7",
            color: "#166534",
            padding: "1rem",
            borderRadius: "0.5rem",
            border: "1px solid #bbf7d0",
            marginBottom: "1rem"
          }}>
            <strong>Éxito:</strong> {success}
          </div>
        )}

        <form onSubmit={handleSubmitToQueue} style={{ display: "flex", gap: "1rem", alignItems: "flex-start" }}>
          <div style={{ flex: 1 }}>
            <label style={{
              display: "block",
              marginBottom: "0.5rem",
              color: "#374151",
              fontWeight: "500"
            }}>
              Keyword (ej: apache, mysql, java)
            </label>
            <input
              type="text"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="Ingresa una keyword para buscar vulnerabilidades"
              style={{
                width: "100%",
                padding: "0.75rem",
                borderRadius: "0.5rem",
                border: "1px solid #d1d5db",
                fontSize: "1rem"
              }}
              disabled={loading}
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            style={{
              background: "#2563eb",
              color: "white",
              border: "none",
              padding: "0.75rem 2rem",
              borderRadius: "0.5rem",
              fontWeight: "600",
              cursor: loading ? "not-allowed" : "pointer",
              fontSize: "1rem",
              marginTop: "1.75rem",
              opacity: loading ? 0.6 : 1
            }}
          >
            {loading ? "⏳ Enviando..." : "📨 Enviar a Cola"}
          </button>
        </form>
      </div>

      {/* Botón para iniciar consumidor */}
      <div style={{
        background: "#ffffff",
        padding: "2rem",
        borderRadius: "1rem",
        boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
        marginBottom: "2rem"
      }}>
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center"
        }}>
          <div>
            <h2 style={{
              fontSize: "1.5rem",
              color: "#1e40af",
              marginBottom: "0.5rem",
              fontWeight: "600"
            }}>
              ⚙️ Consumidor de Cola
            </h2>
            <p style={{ color: "#64748b", margin: 0 }}>
              {consumerRunning 
                ? "✅ Consumidor activo - Procesando trabajos de la cola" 
                : "⏸️ Consumidor detenido - Inicia para procesar trabajos"}
            </p>
          </div>
          <button
            onClick={handleStartConsumer}
            disabled={loadingConsumer || consumerRunning}
            style={{
              background: consumerRunning ? "#10b981" : "#2563eb",
              color: "white",
              border: "none",
              padding: "0.75rem 2rem",
              borderRadius: "0.5rem",
              fontWeight: "600",
              cursor: (loadingConsumer || consumerRunning) ? "not-allowed" : "pointer",
              fontSize: "1rem",
              opacity: (loadingConsumer || consumerRunning) ? 0.6 : 1
            }}
          >
            {loadingConsumer 
              ? "⏳ Iniciando..." 
              : consumerRunning 
                ? "✅ Consumidor Activo" 
                : "▶️ Iniciar Consumidor"}
          </button>
        </div>
      </div>

      {/* Lista de trabajos en la cola */}
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
          marginBottom: "1.5rem"
        }}>
          <h2 style={{
            fontSize: "1.5rem",
            color: "#1e40af",
            margin: 0,
            fontWeight: "600"
          }}>
            📋 Trabajos en Cola RabbitMQ ({queueJobs.length})
          </h2>
          <button
            onClick={loadQueueJobs}
            disabled={loadingJobs}
            style={{
              background: "#2563eb",
              color: "white",
              border: "none",
              padding: "0.5rem 1rem",
              borderRadius: "0.5rem",
              fontWeight: "600",
              cursor: loadingJobs ? "not-allowed" : "pointer",
              fontSize: "0.9rem",
              opacity: loadingJobs ? 0.6 : 1
            }}
          >
            {loadingJobs ? "🔄 Cargando..." : "🔄 Actualizar"}
          </button>
        </div>

        {loadingJobs ? (
          <div style={{
            textAlign: "center",
            padding: "3rem",
            color: "#64748b"
          }}>
            <div style={{ fontSize: "2rem", marginBottom: "1rem" }}>⏳</div>
            <p>Cargando trabajos de la cola...</p>
          </div>
        ) : queueJobs.length === 0 ? (
          <div style={{
            textAlign: "center",
            padding: "3rem",
            background: "#f8fafc",
            borderRadius: "0.5rem",
            border: "1px solid #e2e8f0"
          }}>
            <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>📭</div>
            <h3 style={{ color: "#374151", marginBottom: "0.5rem" }}>
              No hay trabajos en la cola
            </h3>
            <p style={{ color: "#64748b" }}>
              Envía una keyword para crear un trabajo en la cola
            </p>
          </div>
        ) : (
          <div style={{ display: "grid", gap: "1rem" }}>
            {queueJobs.map((job, index) => (
              <div
                key={job.job_id || index}
                style={{
                  background: "#f8fafc",
                  border: "1px solid #e2e8f0",
                  borderRadius: "0.75rem",
                  padding: "1.5rem"
                }}
              >
                <div style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "0.5rem"
                }}>
                  <h3 style={{
                    color: "#1e40af",
                    margin: 0,
                    fontSize: "1.1rem",
                    fontWeight: "600"
                  }}>
                    📦 {job.keyword || `Trabajo ${job.job_id?.slice(0, 8)}`}
                  </h3>
                  <span style={{
                    background: job.status === "completed" ? "#dcfce7" : 
                               job.status === "processing" ? "#dbeafe" : "#fef3c7",
                    color: job.status === "completed" ? "#166534" : 
                           job.status === "processing" ? "#1e40af" : "#92400e",
                    padding: "0.25rem 0.75rem",
                    borderRadius: "0.5rem",
                    fontSize: "0.8rem",
                    fontWeight: "600",
                    textTransform: "uppercase"
                  }}>
                    {job.status === "completed" ? "✅ Completado" :
                     job.status === "processing" ? "⚙️ Procesando" :
                     job.status === "pending" ? "⏳ Pendiente" :
                     job.status || "❓ Desconocido"}
                  </span>
                </div>
                <div style={{
                  display: "flex",
                  gap: "1.5rem",
                  fontSize: "0.9rem",
                  color: "#64748b",
                  marginTop: "0.5rem"
                }}>
                  <span><strong>ID:</strong> {job.job_id?.slice(0, 20)}...</span>
                  {job.total_results !== undefined && (
                    <span><strong>Vulnerabilidades:</strong> {job.total_results}</span>
                  )}
                  {job.processed_at && (
                    <span><strong>Procesado:</strong> {new Date(job.processed_at).toLocaleString()}</span>
                  )}
                </div>
                {job.vulnerabilities && job.vulnerabilities.length > 0 && (
                  <div style={{ marginTop: "1rem" }}>
                    <details>
                      <summary style={{
                        cursor: "pointer",
                        color: "#2563eb",
                        fontWeight: "500"
                      }}>
                        Ver {job.vulnerabilities.length} vulnerabilidades encontradas
                      </summary>
                      <div style={{
                        marginTop: "1rem",
                        display: "grid",
                        gap: "0.75rem",
                        maxHeight: "300px",
                        overflowY: "auto"
                      }}>
                        {job.vulnerabilities.slice(0, 10).map((vuln, vulnIndex) => (
                          <div
                            key={vulnIndex}
                            style={{
                              background: "#ffffff",
                              border: "1px solid #d1d5db",
                              borderRadius: "0.5rem",
                              padding: "0.75rem"
                            }}
                          >
                            <strong style={{ color: "#dc2626" }}>
                              {vuln.cve?.id || "CVE Desconocido"}
                            </strong>
                            {vuln.cve?.descriptions?.[0]?.value && (
                              <p style={{
                                margin: "0.5rem 0 0 0",
                                fontSize: "0.85rem",
                                color: "#475569"
                              }}>
                                {vuln.cve.descriptions[0].value.substring(0, 150)}...
                              </p>
                            )}
                          </div>
                        ))}
                        {job.vulnerabilities.length > 10 && (
                          <p style={{ color: "#64748b", fontSize: "0.85rem", textAlign: "center" }}>
                            ... y {job.vulnerabilities.length - 10} más
                          </p>
                        )}
                      </div>
                    </details>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
