import React, { useEffect, useState } from "react";
import { addKeywordToQueue, getAllQueueResults, startConsumer, getConsumerStatus, getQueueStatus } from "../services/nvd";
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
  const [queueStatus, setQueueStatus] = useState(null);
  const [isInfoExpanded, setIsInfoExpanded] = useState(false);

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

  // Obtener estado de la cola (métricas)
  const fetchQueueStatus = async () => {
    try {
      const status = await getQueueStatus();
      setQueueStatus(status);
    } catch (error) {
      console.error("Error fetching queue status:", error);
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
      // Recargar jobs y status después de enviar
      setTimeout(() => {
        loadQueueJobs();
        fetchQueueStatus();
      }, 1000);
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
      setTimeout(() => {
        checkConsumerStatus();
        fetchQueueStatus();
      }, 1500);
      // Recargar jobs después de iniciar consumidor
      setTimeout(loadQueueJobs, 2000);
    } catch (error) {
      console.error("Error starting consumer:", error);
      setError(`Error al iniciar consumidor: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoadingConsumer(false);
    }
  };

  // Cargar datos al montar el componente (solo una vez)
  useEffect(() => {
    loadQueueJobs();
    checkConsumerStatus();
    fetchQueueStatus();

    // Intervalo para actualizar estado de la cola cada 5 segundos
    const intervalId = setInterval(fetchQueueStatus, 5000);
    return () => clearInterval(intervalId);
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

      {/* Sección Educativa: Contexto y PORQUE */}
      <div style={{
        background: "#f0f9ff",
        border: "1px solid #bae6fd",
        borderRadius: "1rem",
        padding: "2rem",
        marginBottom: "2rem",
        transition: "all 0.3s ease"
      }}>
        <div
          onClick={() => setIsInfoExpanded(!isInfoExpanded)}
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            cursor: "pointer",
            userSelect: "none"
          }}
        >
          <h2 style={{ color: "#0369a1", fontSize: "1.5rem", fontWeight: "600", margin: 0 }}>
            📚 Información y Contexto del Análisis
          </h2>
          <span style={{
            fontSize: "1.5rem",
            transform: isInfoExpanded ? "rotate(180deg)" : "rotate(0deg)",
            transition: "transform 0.3s",
            color: "#0369a1"
          }}>
            ▼
          </span>
        </div>

        {isInfoExpanded && (
          <div style={{ marginTop: "2rem", display: "grid", gridTemplateColumns: "1fr", gap: "2rem" }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "2rem" }}>
              <div>
                <h3 style={{ color: "#0c4a6e", fontWeight: "600", marginBottom: "0.5rem", fontSize: "1.2rem" }}>
                  🏛️ ¿Qué es NVD?
                </h3>
                <p style={{ color: "#334155", fontSize: "0.95rem", lineHeight: "1.6" }}>
                  La <strong>National Vulnerability Database (NVD)</strong> es el repositorio oficial del gobierno de EE. UU. de datos de gestión de vulnerabilidades.
                  Su propósito es <strong>automatizar</strong> la gestión de vulnerabilidades, el cumplimiento de seguridad y la medición.
                  La NVD analiza cada CVE publicado en la lista CVE y lo enriquece con:
                </p>
                <ul style={{ listStyleType: "disc", paddingLeft: "1.5rem", marginTop: "0.5rem", color: "#334155" }}>
                  <li>Puntuaciones de impacto (CVSS).</li>
                  <li>Nombres de productos afectados (CPE).</li>
                  <li>Tipos de debilidad (CWE).</li>
                </ul>
              </div>

              <div>
                <h3 style={{ color: "#0c4a6e", fontWeight: "600", marginBottom: "0.5rem", fontSize: "1.2rem" }}>
                  🏷️ ¿Qué es un CVE?
                </h3>
                <p style={{ color: "#334155", fontSize: "0.95rem", lineHeight: "1.6" }}>
                  <strong>Common Vulnerabilities and Exposures (CVE)</strong> es una lista de registros de fallos de seguridad informática divulgados públicamente.
                  Cada CVE tiene un identificador único con el formato <code>CVE-AAAA-NNNNN</code>:
                </p>
                <ul style={{ listStyleType: "disc", paddingLeft: "1.5rem", marginTop: "0.5rem", color: "#334155" }}>
                  <li><strong>AAAA:</strong> El año en que se asignó el ID (no necesariamente cuando se descubrió).</li>
                  <li><strong>NNNNN:</strong> Un número secuencial único.</li>
                </ul>
                <p style={{ color: "#334155", fontSize: "0.95rem", lineHeight: "1.6", marginTop: "0.5rem" }}>
                  El objetivo del CVE es asegurar que todos hablemos del mismo problema con el mismo nombre.
                </p>
              </div>
            </div>

            <div style={{ background: "white", padding: "1.5rem", borderRadius: "0.75rem", border: "1px solid #e2e8f0" }}>
              <h3 style={{ color: "#0c4a6e", fontWeight: "600", marginBottom: "1rem", fontSize: "1.2rem" }}>
                📊 ¿Qué es CVSS y cómo se calcula? (0-10)
              </h3>
              <p style={{ color: "#334155", fontSize: "0.95rem", lineHeight: "1.6", marginBottom: "1rem" }}>
                El <strong>Common Vulnerability Scoring System (CVSS)</strong> es un estándar abierto para evaluar la gravedad de una vulnerabilidad.
                No mide el riesgo (que depende del contexto), sino la <strong>severidad técnica</strong>.
              </p>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "1.5rem", marginBottom: "1.5rem" }}>
                <div>
                  <h4 style={{ color: "#0369a1", fontWeight: "600", marginBottom: "0.5rem" }}>Escala de Severidad</h4>
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                      <span style={{ width: "12px", height: "12px", borderRadius: "50%", background: "#dc2626" }}></span>
                      <span style={{ fontWeight: "600", color: "#dc2626" }}>9.0 - 10.0: CRÍTICO</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                      <span style={{ width: "12px", height: "12px", borderRadius: "50%", background: "#ea580c" }}></span>
                      <span style={{ fontWeight: "600", color: "#ea580c" }}>7.0 - 8.9: ALTO</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                      <span style={{ width: "12px", height: "12px", borderRadius: "50%", background: "#ca8a04" }}></span>
                      <span style={{ fontWeight: "600", color: "#ca8a04" }}>4.0 - 6.9: MEDIO</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                      <span style={{ width: "12px", height: "12px", borderRadius: "50%", background: "#16a34a" }}></span>
                      <span style={{ fontWeight: "600", color: "#16a34a" }}>0.1 - 3.9: BAJO</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 style={{ color: "#0369a1", fontWeight: "600", marginBottom: "0.5rem" }}>Métricas Base (El "Cómo")</h4>
                  <ul style={{ listStyleType: "none", padding: 0, color: "#334155", fontSize: "0.9rem" }}>
                    <li style={{ marginBottom: "0.5rem" }}>
                      🗡️ <strong>Vector de Ataque (AV):</strong> ¿Se puede explotar remotamente (Red) o requiere acceso físico?
                    </li>
                    <li style={{ marginBottom: "0.5rem" }}>
                      🧩 <strong>Complejidad (AC):</strong> ¿Es fácil de explotar o requiere condiciones especiales?
                    </li>
                    <li style={{ marginBottom: "0.5rem" }}>
                      🔑 <strong>Privilegios (PR):</strong> ¿El atacante necesita ser admin o puede ser cualquiera?
                    </li>
                    <li style={{ marginBottom: "0.5rem" }}>
                      👤 <strong>Interacción (UI):</strong> ¿Requiere que un usuario haga clic en algo?
                    </li>
                  </ul>
                </div>
              </div>

              <div style={{ background: "#f8fafc", padding: "1rem", borderRadius: "0.5rem" }}>
                <h4 style={{ color: "#0369a1", fontWeight: "600", marginBottom: "0.5rem" }}>Impacto CIA (Confidencialidad, Integridad, Disponibilidad)</h4>
                <p style={{ color: "#334155", fontSize: "0.9rem" }}>
                  La puntuación sube drásticamente si la vulnerabilidad permite:
                  <br />
                  👁️ <strong>Leer datos</strong> (Pérdida de Confidencialidad total).
                  <br />
                  ✏️ <strong>Modificar datos</strong> (Pérdida de Integridad total).
                  <br />
                  🛑 <strong>Tumbar el servicio</strong> (Pérdida de Disponibilidad total).
                </p>
              </div>
            </div>

            <div>
              <h3 style={{ color: "#0c4a6e", fontWeight: "600", marginBottom: "0.5rem", fontSize: "1.2rem" }}>
                🎯 ¿POR QUÉ realizamos este análisis?
              </h3>
              <p style={{ color: "#334155", fontSize: "0.95rem", lineHeight: "1.6" }}>
                Identificar vulnerabilidades conocidas en el software que utilizamos es el primer paso para la <strong>prevención de ataques</strong>.
                Al cruzar nuestro inventario de software (keywords) con la base de datos NVD, podemos detectar riesgos latentes antes de que sean explotados.
                <br /><br />
                Este proceso proactivo nos permite:
              </p>
              <ul style={{ listStyleType: "disc", paddingLeft: "1.5rem", marginTop: "0.5rem", color: "#334155" }}>
                <li><strong>Parchear</strong> sistemas antes de un incidente.</li>
                <li><strong>Mitigar</strong> riesgos si no hay parche disponible.</li>
                <li><strong>Cumplir</strong> con normativas de seguridad (ISO 27001, PCI-DSS).</li>
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* Estado de RabbitMQ Cloud */}
      {queueStatus && (
        <div style={{
          background: "linear-gradient(to right, #eff6ff, #e0e7ff)",
          border: "1px solid #bfdbfe",
          borderRadius: "0.5rem",
          padding: "1.5rem",
          marginBottom: "1.5rem",
          boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
        }}>
          <h2 style={{ fontSize: "1.125rem", fontWeight: "600", marginBottom: "1rem", color: "#1e3a8a" }}>
            📊 Estado de RabbitMQ Cloud
          </h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "1rem" }}>
            {/* En Cola */}
            <div style={{ background: "white", padding: "1rem", borderRadius: "0.5rem", boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)" }}>
              <p style={{ fontSize: "0.75rem", color: "#4b5563", marginBottom: "0.25rem" }}>En Cola</p>
              <p style={{ fontSize: "1.875rem", fontWeight: "700", color: "#2563eb" }}>{queueStatus.queue_size || 0}</p>
              <p style={{ fontSize: "0.75rem", color: "#6b7280", marginTop: "0.25rem" }}>Mensajes en RabbitMQ</p>
            </div>
            {/* Pendientes */}
            <div style={{ background: "white", padding: "1rem", borderRadius: "0.5rem", boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)" }}>
              <p style={{ fontSize: "0.75rem", color: "#4b5563", marginBottom: "0.25rem" }}>Pendientes</p>
              <p style={{ fontSize: "1.875rem", fontWeight: "700", color: "#ca8a04" }}>{queueStatus.jobs?.pending || 0}</p>
              <p style={{ fontSize: "0.75rem", color: "#6b7280", marginTop: "0.25rem" }}>Sin procesar</p>
            </div>
            {/* Procesando */}
            <div style={{ background: "white", padding: "1rem", borderRadius: "0.5rem", boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)" }}>
              <p style={{ fontSize: "0.75rem", color: "#4b5563", marginBottom: "0.25rem" }}>Procesando</p>
              <p style={{ fontSize: "1.875rem", fontWeight: "700", color: "#2563eb" }}>{queueStatus.jobs?.processing || 0}</p>
              <p style={{ fontSize: "0.75rem", color: "#6b7280", marginTop: "0.25rem" }}>En ejecución</p>
            </div>
            {/* Completados */}
            <div style={{ background: "white", padding: "1rem", borderRadius: "0.5rem", boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)" }}>
              <p style={{ fontSize: "0.75rem", color: "#4b5563", marginBottom: "0.25rem" }}>Completados</p>
              <p style={{ fontSize: "1.875rem", fontWeight: "700", color: "#16a34a" }}>{queueStatus.jobs?.completed || 0}</p>
              <p style={{ fontSize: "0.75rem", color: "#6b7280", marginTop: "0.25rem" }}>Finalizados</p>
            </div>
            {/* Fallidos */}
            <div style={{ background: "white", padding: "1rem", borderRadius: "0.5rem", boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)" }}>
              <p style={{ fontSize: "0.75rem", color: "#4b5563", marginBottom: "0.25rem" }}>Fallidos</p>
              <p style={{ fontSize: "1.875rem", fontWeight: "700", color: "#dc2626" }}>{queueStatus.jobs?.failed || 0}</p>
              <p style={{ fontSize: "0.75rem", color: "#6b7280", marginTop: "0.25rem" }}>Con errores</p>
            </div>
          </div>
        </div>
      )}

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
          📤 Enviar Vulnerabilidad a Cola RabbitMQ
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
              Vulnerabilidad (ej: apache, mysql, java)
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
