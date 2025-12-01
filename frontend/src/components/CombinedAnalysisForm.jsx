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

const assetDescriptions = {
  "Servidor Web": {
    title: "Análisis de Tráfico Web",
    description: "Evaluación de riesgos para servidores expuestos a internet (HTTP/HTTPS).",
    details: "Los servidores web son la cara visible de la organización y el objetivo principal de ataques como SQL Injection, XSS y DDoS. Este modelo busca patrones de tráfico que indiquen intentos de saturación o manipulación de consultas.",
    icon: "🌐"
  },
  "Servidor de Base de Datos": {
    title: "Seguridad de Datos Críticos",
    description: "Monitoreo de acceso a información sensible y prevención de fugas.",
    details: "Las bases de datos contienen el activo más valioso: la información. Analizamos las conexiones para detectar exfiltración masiva de datos (paquetes inusualmente grandes) o accesos desde usuarios no autorizados (movimiento lateral).",
    icon: "💾"
  },
  "Controlador de Dominio": {
    title: "Integridad de la Red",
    description: "Protección del núcleo de autenticación y control de acceso.",
    details: "Si cae el Controlador de Dominio, cae la red. Buscamos intentos de fuerza bruta, escalada de privilegios y autenticaciones en horarios anómalos que sugieran una cuenta comprometida.",
    icon: "🛡️"
  }
};

export default function CombinedAnalysisForm({ asset }) {
  const [cicids, setCicids] = useState(initialCICIDS);
  const [lanl, setLanl] = useState(initialLANL);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  const assetInfo = assetDescriptions[asset.name] || {
    title: "Análisis de Riesgo General",
    description: "Evaluación de seguridad basada en el comportamiento.",
    details: "Análisis general de anomalías en el tráfico de red y patrones de autenticación.",
    icon: "🔍"
  };

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
      alert("Error al analizar el riesgo. Verifique la conexión con el servidor.");
    }
    setLoading(false);
  };

  return (
    <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">

      {/* Educational Header Section */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 mb-10 transition-all duration-300">
        <div className="max-w-5xl">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4 mb-6">
              <span className="text-5xl">{assetInfo.icon}</span>
              <div>
                <h1 className="text-3xl font-bold text-slate-900">{assetInfo.title}</h1>
                <p className="text-blue-600 font-medium text-lg">{asset.name}</p>
              </div>
            </div>
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="text-sm font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-50 px-4 py-2 rounded-lg transition-colors"
            >
              {showDetails ? "Ocultar Detalles Pedagógicos" : "Ver Explicación Detallada"}
            </button>
          </div>

          <div className="prose prose-slate text-slate-600 max-w-none">
            <p className="text-lg leading-relaxed text-slate-700">
              {assetInfo.details}
            </p>

            {/* Collapsible Pedagogical Content */}
            {showDetails && (
              <div className="mt-8 grid md:grid-cols-2 gap-8 animate-slide-up">
                {/* Column 1: The "Why" */}
                <div className="space-y-6">
                  <div className="bg-indigo-50 p-6 rounded-xl border border-indigo-100">
                    <h3 className="text-indigo-900 font-bold text-lg mb-3 flex items-center gap-2">
                      <span className="text-xl">🧠</span> ¿Por qué Inteligencia Artificial?
                    </h3>
                    <p className="text-sm text-indigo-800 leading-relaxed">
                      Los firewalls tradicionales funcionan como un guardia con una lista de "personas prohibidas" (reglas estáticas). Si un atacante no está en la lista, entra.
                      <br /><br />
                      <strong>Nuestro modelo es diferente:</strong> Funciona como un detective experto que observa el <em>comportamiento</em>. Si alguien entra y empieza a abrir cajones muy rápido (tráfico anómalo) o intenta entrar a zonas restringidas (autenticación inusual), el modelo lo detecta, aunque sea la primera vez que ve a esa persona.
                    </p>
                  </div>

                  <div className="bg-slate-50 p-6 rounded-xl border border-slate-200">
                    <h3 className="text-slate-900 font-bold text-lg mb-3 flex items-center gap-2">
                      <span className="text-xl">📊</span> Entendiendo los Datos (CICIDS)
                    </h3>
                    <ul className="space-y-3 text-sm text-slate-700">
                      <li className="flex gap-3 items-start">
                        <span className="font-bold text-slate-900 min-w-[120px]">Flow Duration:</span>
                        <span>¿Cuánto dura la conversación? Conexiones muy largas pueden indicar robo de datos lento; muy cortas, un escaneo de puertos.</span>
                      </li>
                      <li className="flex gap-3 items-start">
                        <span className="font-bold text-slate-900 min-w-[120px]">Packet Size:</span>
                        <span>El tamaño importa. Paquetes inusualmente grandes pueden contener archivos robados o malware oculto.</span>
                      </li>
                      <li className="flex gap-3 items-start">
                        <span className="font-bold text-slate-900 min-w-[120px]">Flow Bytes/s:</span>
                        <span>La velocidad de transmisión. Un pico repentino es la firma clásica de un ataque de Denegación de Servicio (DDoS).</span>
                      </li>
                    </ul>
                  </div>
                </div>

                {/* Column 2: The "How" & LANL */}
                <div className="space-y-6">
                  <div className="bg-blue-50 p-6 rounded-xl border border-blue-100">
                    <h3 className="text-blue-900 font-bold text-lg mb-3 flex items-center gap-2">
                      <span className="text-xl">🔐</span> Entendiendo la Autenticación (LANL)
                    </h3>
                    <p className="text-sm text-blue-800 mb-4">
                      Analizamos el contexto de "Quién, Dónde y Cuándo" para detectar credenciales robadas.
                    </p>
                    <ul className="space-y-3 text-sm text-blue-800">
                      <li className="flex gap-3 items-start">
                        <span className="font-bold text-blue-900 min-w-[100px]">Tiempo:</span>
                        <span>¿A qué hora se conecta? Un acceso a las 3:00 AM de un empleado de oficina es altamente sospechoso.</span>
                      </li>
                      <li className="flex gap-3 items-start">
                        <span className="font-bold text-blue-900 min-w-[100px]">Usuario/PC:</span>
                        <span>¿Es normal que el usuario de "Marketing" acceda al servidor de "Base de Datos"? Esto ayuda a detectar movimientos laterales dentro de la red.</span>
                      </li>
                    </ul>
                  </div>

                  <div className="bg-emerald-50 p-6 rounded-xl border border-emerald-100">
                    <h3 className="text-emerald-900 font-bold text-lg mb-3 flex items-center gap-2">
                      <span className="text-xl">🎯</span> Objetivo Final
                    </h3>
                    <p className="text-sm text-emerald-800">
                      El objetivo no es solo bloquear ataques, sino <strong>predecir el riesgo</strong>. El sistema le dará una puntuación (0-100%) que representa la probabilidad de que la actividad actual sea maliciosa, permitiéndole actuar <em>antes</em> de que el daño sea irreversible.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {!showDetails && (
              <div className="mt-6 flex gap-4 text-sm text-slate-500 bg-slate-50 p-4 rounded-lg border border-slate-200">
                <span className="flex items-center gap-2">
                  <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                  Haga clic en <strong>"Ver Explicación Detallada"</strong> para aprender cómo la IA detecta amenazas invisibles.
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Form Section */}
        <div className="flex-1">
          <form onSubmit={handleSubmit} autoComplete="off" className="space-y-6">

            {/* CICIDS Card */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden group hover:shadow-md transition-shadow duration-200">
              <div className="bg-slate-50 px-6 py-4 border-b border-slate-200 flex justify-between items-center">
                <div>
                  <h3 className="text-lg font-semibold text-slate-800">Parámetros de Red (CICIDS)</h3>
                  <p className="text-xs text-slate-500">Datos técnicos del flujo de tráfico</p>
                </div>
                <div className="h-8 w-8 rounded-full bg-white border border-slate-200 flex items-center justify-center text-slate-400 group-hover:text-blue-500 group-hover:border-blue-200 transition-colors">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 3v1.5M4.5 8.25H3m18 0h-1.5M4.5 12H3m18 0h-1.5m-15 3.75H3m18 0h-1.5M8.25 19.5V21M12 3v1.5m0 15V21m3.75-18v1.5m0 15V21m-9-1.5h10.5a2.25 2.25 0 002.25-2.25V6.75a2.25 2.25 0 00-2.25-2.25H6.75A2.25 2.25 0 004.5 6.75v10.5a2.25 2.25 0 002.25 2.25zm.75-12h9v9h-9v-9z" />
                  </svg>
                </div>
              </div>

              <div className="p-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
                {Object.keys(cicids).map(key => (
                  <div key={key} className="space-y-1">
                    <label className="block text-xs font-medium text-slate-700 truncate" title={cicidsLabels[key] || key}>
                      {cicidsLabels[key] || key}
                    </label>
                    <input
                      type="number"
                      name={key}
                      value={cicids[key]}
                      onChange={handleCicidsChange}
                      required
                      min={0}
                      step={1}
                      className="block w-full rounded-lg border-slate-200 bg-slate-50 text-slate-900 focus:border-blue-500 focus:ring-blue-500 sm:text-sm py-2 px-3 transition-colors hover:bg-white"
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* LANL Card */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden group hover:shadow-md transition-shadow duration-200">
              <div className="bg-slate-50 px-6 py-4 border-b border-slate-200 flex justify-between items-center">
                <div>
                  <h3 className="text-lg font-semibold text-slate-800">Datos de Autenticación (LANL)</h3>
                  <p className="text-xs text-slate-500">Contexto de usuario y dispositivo</p>
                </div>
                <div className="h-8 w-8 rounded-full bg-white border border-slate-200 flex items-center justify-center text-slate-400 group-hover:text-indigo-500 group-hover:border-indigo-200 transition-colors">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                  </svg>
                </div>
              </div>

              <div className="p-6 grid grid-cols-1 sm:grid-cols-3 gap-5">
                <div className="space-y-1">
                  <label className="block text-xs font-medium text-slate-700">Tiempo (Timestamp)</label>
                  <input
                    type="number"
                    name="time"
                    value={lanl.time}
                    onChange={handleLanlChange}
                    required
                    min={0}
                    step={1}
                    className="block w-full rounded-lg border-slate-200 bg-slate-50 text-slate-900 focus:border-blue-500 focus:ring-blue-500 sm:text-sm py-2 px-3 transition-colors hover:bg-white"
                  />
                </div>
                <div className="space-y-1">
                  <label className="block text-xs font-medium text-slate-700">ID Usuario</label>
                  <input
                    type="text"
                    name="user"
                    value={lanl.user}
                    onChange={handleLanlChange}
                    required
                    placeholder="Ej: U123"
                    maxLength={8}
                    className="block w-full rounded-lg border-slate-200 bg-slate-50 text-slate-900 focus:border-blue-500 focus:ring-blue-500 sm:text-sm py-2 px-3 transition-colors hover:bg-white"
                  />
                </div>
                <div className="space-y-1">
                  <label className="block text-xs font-medium text-slate-700">ID Computadora</label>
                  <input
                    type="text"
                    name="computer"
                    value={lanl.computer}
                    onChange={handleLanlChange}
                    required
                    placeholder="Ej: C456"
                    maxLength={8}
                    className="block w-full rounded-lg border-slate-200 bg-slate-50 text-slate-900 focus:border-blue-500 focus:ring-blue-500 sm:text-sm py-2 px-3 transition-colors hover:bg-white"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <button
                type="submit"
                disabled={loading}
                className="inline-flex items-center justify-center rounded-lg bg-blue-600 px-8 py-3 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {loading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Procesando Análisis...
                  </>
                ) : (
                  <>
                    Ejecutar Análisis de Riesgo
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="ml-2 w-5 h-5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                    </svg>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Result Section (Sticky on desktop) */}
        {result && (
          <div className="lg:w-96">
            <div className="sticky top-24 animate-slide-up">
              <RiskScoreCard result={result} />
            </div>
          </div>
        )}
      </div>
    </section>
  );
}