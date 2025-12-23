import React, { useState, useEffect } from 'react';
import {
    addIpToQueue,
    getAllQueueResults,
    getQueueStatus,
    startConsumer,
    getConsumerStatus
} from '../services/nmap';

export default function NmapPage() {
    const [targetIp, setTargetIp] = useState('');
    const [queueJobs, setQueueJobs] = useState([]);
    const [queueStatus, setQueueStatus] = useState(null);
    const [loading, setLoading] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [selectedJob, setSelectedJob] = useState(null);
    const [consumerRunning, setConsumerRunning] = useState(false);
    const [loadingConsumer, setLoadingConsumer] = useState(false);

    // Educational sections state
    const [expandedSections, setExpandedSections] = useState({
        whatIs: false,
        whatFor: false,
        whyImportant: false,
        riskFormula: false,
        architecture: false
    });

    // Load queue data and consumer status
    useEffect(() => {
        loadQueueData();
        checkConsumerStatusFn();
    }, []);

    const checkConsumerStatusFn = async () => {
        try {
            const status = await getConsumerStatus();
            setConsumerRunning(status.running);
        } catch (e) {
            console.error('Error checking consumer status:', e);
            setConsumerRunning(false);
        }
    };

    const loadQueueData = async () => {
        setLoading(true);
        setError(null);
        try {
            const [jobsData, statusData] = await Promise.all([
                getAllQueueResults(),
                getQueueStatus()
            ]);

            if (jobsData.success) {
                setQueueJobs(jobsData.jobs || []);
            }

            if (statusData.success) {
                setQueueStatus(statusData);
            }
        } catch (err) {
            console.error('Error loading queue data:', err);
            setError('Error al cargar datos de la cola');
        } finally {
            setLoading(false);
        }
    };

    const handleSubmitToQueue = async (e) => {
        e.preventDefault();

        if (!targetIp.trim()) {
            setError('Por favor ingresa una IP o hostname');
            return;
        }

        setSubmitting(true);
        setError(null);
        setSuccess(null);

        try {
            const result = await addIpToQueue(targetIp.trim());

            if (result.success) {
                setSuccess(`✅ IP ${targetIp} agregada a la cola con Job ID: ${result.job_id}`);
                setTargetIp('');
                setTimeout(loadQueueData, 1000);
            } else {
                setError(result.error || 'Error al agregar IP a la cola');
            }
        } catch (err) {
            console.error('Error submitting to queue:', err);
            setError('Error al enviar IP a la cola');
        } finally {
            setSubmitting(false);
        }
    };

    const handleStartConsumer = async () => {
        setLoadingConsumer(true);
        setError(null);
        setSuccess(null);
        try {
            await startConsumer();
            setSuccess('✅ Consumidor iniciado correctamente');
            setTimeout(checkConsumerStatusFn, 1500);
            setTimeout(loadQueueData, 2000);
        } catch (error) {
            console.error('Error starting consumer:', error);
            setError(`Error al iniciar consumidor: ${error.response?.data?.detail || error.message}`);
        } finally {
            setLoadingConsumer(false);
        }
    };

    const toggleSection = (section) => {
        setExpandedSections(prev => ({
            ...prev,
            [section]: !prev[section]
        }));
    };

    const getRiskColor = (score) => {
        if (score >= 75) return 'bg-red-100 text-red-800 border-red-300';
        if (score >= 50) return 'bg-orange-100 text-orange-800 border-orange-300';
        if (score >= 25) return 'bg-yellow-100 text-yellow-800 border-yellow-300';
        return 'bg-green-100 text-green-800 border-green-300';
    };

    const getRiskCategory = (score) => {
        if (score >= 75) return 'Crítico';
        if (score >= 50) return 'Alto';
        if (score >= 25) return 'Medio';
        return 'Bajo';
    };

    const formatTimestamp = (timestamp) => {
        if (!timestamp) return 'N/A';
        const date = new Date(timestamp * 1000);
        return date.toLocaleString('es-ES');
    };

    return (
        <div className="container mx-auto px-4 py-8 max-w-7xl">
            {/* Header */}
            <div className="mb-8 text-center">
                <h1 className="text-4xl font-bold text-gray-900 mb-2">
                    🔍 Nmap Scanner - Análisis de Puertos
                </h1>

            </div>

            {/* Educational Sections - Collapsible */}
            <div className="bg-white border border-gray-200 rounded-lg shadow-sm mb-6">
                <div className="p-6">
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">
                        📚 Información del Sistema
                    </h2>

                    {/* ¿Qué es esto? */}
                    <div className="mb-4 border-b border-gray-200 pb-4">
                        <button
                            onClick={() => toggleSection('whatIs')}
                            className="w-full flex justify-between items-center text-left hover:bg-gray-50 p-3 rounded-lg transition-colors"
                        >
                            <span className="text-lg font-semibold text-blue-900">
                                🔍 ¿Qué es el Escaneo de Puertos con Nmap?
                            </span>
                            <span className="text-2xl text-blue-600">
                                {expandedSections.whatIs ? '▲' : '▼'}
                            </span>
                        </button>
                        {expandedSections.whatIs && (
                            <div className="mt-4 pl-6 text-gray-700 space-y-3">
                                <p>
                                    <strong>Nmap (Network Mapper)</strong> es una herramienta de código abierto para exploración de redes y auditoría de seguridad.
                                    Permite descubrir hosts y servicios en una red informática mediante el envío de paquetes y análisis de las respuestas.
                                </p>
                                <p>
                                    Este sistema utiliza Nmap para realizar escaneos de puertos y detección de vulnerabilidades en objetivos específicos (direcciones IP o nombres de host).
                                </p>
                                <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                                    <p className="font-semibold text-blue-900 mb-2">Comando Nmap utilizado:</p>
                                    <code className="bg-gray-800 text-green-400 px-3 py-2 rounded block">
                                        nmap -sV --script vuln [TARGET] -oX scan_result.xml
                                    </code>
                                    <ul className="mt-3 text-sm space-y-1">
                                        <li><strong>-sV:</strong> Detección de versiones de servicios</li>
                                        <li><strong>--script vuln:</strong> Ejecuta scripts de detección de vulnerabilidades</li>
                                        <li><strong>-oX:</strong> Salida en formato XML para procesamiento</li>
                                    </ul>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* ¿Para qué sirve? */}
                    <div className="mb-4 border-b border-gray-200 pb-4">
                        <button
                            onClick={() => toggleSection('whatFor')}
                            className="w-full flex justify-between items-center text-left hover:bg-gray-50 p-3 rounded-lg transition-colors"
                        >
                            <span className="text-lg font-semibold text-blue-900">
                                🎯 ¿Para qué sirve este sistema?
                            </span>
                            <span className="text-2xl text-blue-600">
                                {expandedSections.whatFor ? '▲' : '▼'}
                            </span>
                        </button>
                        {expandedSections.whatFor && (
                            <div className="mt-4 pl-6 text-gray-700">
                                <ul className="space-y-3">
                                    <li className="flex items-start">
                                        <span className="text-2xl mr-3">🔓</span>
                                        <div>
                                            <strong>Descubrir servicios expuestos:</strong> Identifica qué puertos están abiertos y qué servicios están corriendo en cada puerto.
                                        </div>
                                    </li>
                                    <li className="flex items-start">
                                        <span className="text-2xl mr-3">🛡️</span>
                                        <div>
                                            <strong>Identificar vulnerabilidades conocidas:</strong> Detecta versiones de software con vulnerabilidades documentadas (CVEs).
                                        </div>
                                    </li>
                                    <li className="flex items-start">
                                        <span className="text-2xl mr-3">📊</span>
                                        <div>
                                            <strong>Evaluar la superficie de ataque:</strong> Proporciona una visión completa de los puntos de entrada potenciales a un sistema.
                                        </div>
                                    </li>
                                    <li className="flex items-start">
                                        <span className="text-2xl mr-3">⚠️</span>
                                        <div>
                                            <strong>Cumplimiento normativo:</strong> Ayuda a cumplir con estándares de seguridad como PCI-DSS, ISO 27001, NIST.
                                        </div>
                                    </li>
                                    <li className="flex items-start">
                                        <span className="text-2xl mr-3">🔄</span>
                                        <div>
                                            <strong>Monitoreo continuo:</strong> Permite realizar escaneos periódicos para detectar cambios en la infraestructura.
                                        </div>
                                    </li>
                                </ul>
                            </div>
                        )}
                    </div>

                    {/* ¿Por qué es importante? */}
                    <div className="mb-4 border-b border-gray-200 pb-4">
                        <button
                            onClick={() => toggleSection('whyImportant')}
                            className="w-full flex justify-between items-center text-left hover:bg-gray-50 p-3 rounded-lg transition-colors"
                        >
                            <span className="text-lg font-semibold text-blue-900">
                                ⚡ ¿Por qué es importante la seguridad de puertos?
                            </span>
                            <span className="text-2xl text-blue-600">
                                {expandedSections.whyImportant ? '▲' : '▼'}
                            </span>
                        </button>
                        {expandedSections.whyImportant && (
                            <div className="mt-4 pl-6 text-gray-700 space-y-4">
                                <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                                    <h4 className="font-bold text-red-900 mb-2">🚨 Riesgos de puertos abiertos no gestionados:</h4>
                                    <ul className="space-y-2 text-sm">
                                        <li>• <strong>Acceso no autorizado:</strong> Puertos abiertos pueden ser explotados por atacantes</li>
                                        <li>• <strong>Fuga de datos:</strong> Servicios mal configurados pueden exponer información sensible</li>
                                        <li>• <strong>Ataques DoS/DDoS:</strong> Servicios vulnerables pueden ser utilizados para ataques de denegación de servicio</li>
                                        <li>• <strong>Propagación de malware:</strong> Puertos abiertos facilitan la propagación lateral en la red</li>
                                    </ul>
                                </div>
                                <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                                    <h4 className="font-bold text-green-900 mb-2">✅ Beneficios del escaneo proactivo:</h4>
                                    <ul className="space-y-2 text-sm">
                                        <li>• <strong>Detección temprana:</strong> Identificar vulnerabilidades antes que los atacantes</li>
                                        <li>• <strong>Reducción de superficie de ataque:</strong> Cerrar puertos innecesarios</li>
                                        <li>• <strong>Cumplimiento:</strong> Demostrar debida diligencia en seguridad</li>
                                        <li>• <strong>Priorización:</strong> Enfocar recursos en las vulnerabilidades más críticas</li>
                                    </ul>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Fórmula de Riesgo */}
                    <div className="mb-4 border-b border-gray-200 pb-4">
                        <button
                            onClick={() => toggleSection('riskFormula')}
                            className="w-full flex justify-between items-center text-left hover:bg-gray-50 p-3 rounded-lg transition-colors"
                        >
                            <span className="text-lg font-semibold text-blue-900">
                                📐 Matriz de Riesgos - Fórmula de Cálculo
                            </span>
                            <span className="text-2xl text-blue-600">
                                {expandedSections.riskFormula ? '▲' : '▼'}
                            </span>
                        </button>
                        {expandedSections.riskFormula && (
                            <div className="mt-4 pl-6 text-gray-700 space-y-4">
                                <div className="bg-purple-50 p-6 rounded-lg border border-purple-200">
                                    <h4 className="font-bold text-purple-900 mb-4 text-lg">Fórmula de Cálculo de Riesgo</h4>

                                    <div className="bg-white p-4 rounded border border-purple-300 mb-4">
                                        <code className="text-lg font-mono text-purple-900">
                                            Risk Score = (Severity × 0.4) + (Exposure × 0.3) + (Exploitability × 0.2) + (Impact × 0.1)
                                        </code>
                                    </div>

                                    <div className="space-y-3 text-sm">
                                        <div>
                                            <strong className="text-purple-900">Severity (40%):</strong> Gravedad de la vulnerabilidad según CVSS
                                            <ul className="ml-6 mt-1 space-y-1">
                                                <li>• Critical (10.0): 100 puntos</li>
                                                <li>• High (7.0-9.9): 75 puntos</li>
                                                <li>• Medium (4.0-6.9): 50 puntos</li>
                                                <li>• Low (0.1-3.9): 25 puntos</li>
                                            </ul>
                                        </div>

                                        <div>
                                            <strong className="text-purple-900">Exposure (30%):</strong> Nivel de exposición del servicio
                                            <ul className="ml-6 mt-1 space-y-1">
                                                <li>• Puerto público en Internet: 100 puntos</li>
                                                <li>• Puerto en red DMZ: 75 puntos</li>
                                                <li>• Puerto en red interna: 50 puntos</li>
                                                <li>• Puerto localhost: 25 puntos</li>
                                            </ul>
                                        </div>

                                        <div>
                                            <strong className="text-purple-900">Exploitability (20%):</strong> Facilidad de explotación
                                            <ul className="ml-6 mt-1 space-y-1">
                                                <li>• Exploit público disponible: 100 puntos</li>
                                                <li>• PoC (Proof of Concept) disponible: 75 puntos</li>
                                                <li>• Requiere conocimiento avanzado: 50 puntos</li>
                                                <li>• Difícil de explotar: 25 puntos</li>
                                            </ul>
                                        </div>

                                        <div>
                                            <strong className="text-purple-900">Impact (10%):</strong> Impacto en el negocio
                                            <ul className="ml-6 mt-1 space-y-1">
                                                <li>• Crítico para el negocio: 100 puntos</li>
                                                <li>• Alto impacto operacional: 75 puntos</li>
                                                <li>• Impacto moderado: 50 puntos</li>
                                                <li>• Bajo impacto: 25 puntos</li>
                                            </ul>
                                        </div>
                                    </div>

                                    <div className="mt-4 bg-white p-4 rounded border border-purple-300">
                                        <h5 className="font-bold text-purple-900 mb-2">Categorización del Riesgo:</h5>
                                        <div className="grid grid-cols-2 gap-3 text-sm">
                                            <div className="flex items-center gap-2">
                                                <div className="w-4 h-4 bg-red-500 rounded"></div>
                                                <span><strong>Crítico:</strong> 75-100 puntos</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <div className="w-4 h-4 bg-orange-500 rounded"></div>
                                                <span><strong>Alto:</strong> 50-74 puntos</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <div className="w-4 h-4 bg-yellow-500 rounded"></div>
                                                <span><strong>Medio:</strong> 25-49 puntos</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <div className="w-4 h-4 bg-green-500 rounded"></div>
                                                <span><strong>Bajo:</strong> 0-24 puntos</span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="mt-4 bg-blue-50 p-4 rounded border border-blue-200">
                                        <h5 className="font-bold text-blue-900 mb-2">¿Por qué esta fórmula?</h5>
                                        <p className="text-sm">
                                            Esta fórmula ponderada se basa en el framework NIST 800-30 y metodologías FAIR (Factor Analysis of Information Risk).
                                            Prioriza la <strong>severidad técnica</strong> (40%) porque determina el daño potencial, seguida de la <strong>exposición</strong> (30%)
                                            que indica la probabilidad de ataque. La <strong>explotabilidad</strong> (20%) considera la facilidad de ataque, y el <strong>impacto</strong> (10%)
                                            contextualiza el riesgo al negocio específico.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Arquitectura del Sistema Distribuido */}
                    <div className="mb-4">
                        <button
                            onClick={() => toggleSection('architecture')}
                            className="w-full flex justify-between items-center text-left hover:bg-gray-50 p-3 rounded-lg transition-colors"
                        >
                            <span className="text-lg font-semibold text-blue-900">
                                🏗️ Arquitectura del Sistema Distribuido
                            </span>
                            <span className="text-2xl text-blue-600">
                                {expandedSections.architecture ? '▲' : '▼'}
                            </span>
                        </button>
                        {expandedSections.architecture && (
                            <div className="mt-4 pl-6 text-gray-700 space-y-4">
                                <div className="bg-gray-50 p-6 rounded-lg border border-gray-300">
                                    <pre className="text-sm font-mono overflow-x-auto">
                                        {`┌─────────────────┐
│   Frontend      │  React + Vite
│   (Port 5173)   │  
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│  Kong Cloud     │  API Gateway + Rate Limiting
│  Gateway        │  + Authentication
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│  Backend        │  FastAPI (Python)
│  (Port 8000)    │  Middleware + Validation
└────────┬────────┘
         │ AMQP
         ▼
┌─────────────────┐
│  RabbitMQ       │  CloudAMQP (Message Queue)
│  Cloud          │  Asynchronous Processing
└────────┬────────┘
         │ Consumer
         ▼
┌─────────────────┐
│  Nmap Scanner   │  Node.js + Nmap
│  Service        │  Vulnerability Detection
│  (Port 8004)    │
└────────┬────────┘
         │ PostgreSQL
         ▼
┌─────────────────┐
│  Supabase       │  Distributed Database
│  (PostgreSQL)   │  + Real-time subscriptions
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  WorldTimeAPI   │  Time Synchronization
│  + Docker Time  │  (Fallback mechanism)
└─────────────────┘`}
                                    </pre>
                                </div>

                                <div className="space-y-3">
                                    <h5 className="font-bold text-gray-900">Características del Sistema Distribuido:</h5>
                                    <ul className="space-y-2 text-sm">
                                        <li className="flex items-start">
                                            <span className="text-green-600 mr-2">✓</span>
                                            <div>
                                                <strong>Escalabilidad Horizontal:</strong> Múltiples consumers pueden procesar la cola simultáneamente
                                            </div>
                                        </li>
                                        <li className="flex items-start">
                                            <span className="text-green-600 mr-2">✓</span>
                                            <div>
                                                <strong>Tolerancia a Fallos:</strong> RabbitMQ garantiza entrega de mensajes, fallback de tiempo
                                            </div>
                                        </li>
                                        <li className="flex items-start">
                                            <span className="text-green-600 mr-2">✓</span>
                                            <div>
                                                <strong>Procesamiento Asíncrono:</strong> Escaneos largos no bloquean la interfaz de usuario
                                            </div>
                                        </li>
                                        <li className="flex items-start">
                                            <span className="text-green-600 mr-2">✓</span>
                                            <div>
                                                <strong>Persistencia Distribuida:</strong> Supabase replica datos en múltiples zonas geográficas
                                            </div>
                                        </li>
                                        <li className="flex items-start">
                                            <span className="text-green-600 mr-2">✓</span>
                                            <div>
                                                <strong>API Gateway:</strong> Kong Cloud maneja rate limiting, autenticación y enrutamiento
                                            </div>
                                        </li>
                                        <li className="flex items-start">
                                            <span className="text-green-600 mr-2">✓</span>
                                            <div>
                                                <strong>Sincronización de Tiempo:</strong> WorldTimeAPI con fallback a Docker para timestamps consistentes
                                            </div>
                                        </li>
                                    </ul>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Queue Status Card */}
            {queueStatus && (
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6 mb-6 shadow-sm">
                    <h2 className="text-lg font-semibold mb-4 text-blue-900">📊 Estado de RabbitMQ Cloud</h2>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                        <div className="bg-white p-4 rounded-lg shadow-sm">
                            <p className="text-xs text-gray-600 mb-1">En Cola</p>
                            <p className="text-3xl font-bold text-blue-600">{queueStatus.queue_size || 0}</p>
                            <p className="text-xs text-gray-500 mt-1">Mensajes en RabbitMQ</p>
                        </div>
                        <div className="bg-white p-4 rounded-lg shadow-sm">
                            <p className="text-xs text-gray-600 mb-1">Pendientes</p>
                            <p className="text-3xl font-bold text-yellow-600">{queueStatus.jobs?.pending || 0}</p>
                            <p className="text-xs text-gray-500 mt-1">Sin procesar</p>
                        </div>
                        <div className="bg-white p-4 rounded-lg shadow-sm">
                            <p className="text-xs text-gray-600 mb-1">Procesando</p>
                            <p className="text-3xl font-bold text-blue-600">{queueStatus.jobs?.processing || 0}</p>
                            <p className="text-xs text-gray-500 mt-1">En ejecución</p>
                        </div>
                        <div className="bg-white p-4 rounded-lg shadow-sm">
                            <p className="text-xs text-gray-600 mb-1">Completados</p>
                            <p className="text-3xl font-bold text-green-600">{queueStatus.jobs?.completed || 0}</p>
                            <p className="text-xs text-gray-500 mt-1">Finalizados</p>
                        </div>
                        <div className="bg-white p-4 rounded-lg shadow-sm">
                            <p className="text-xs text-gray-600 mb-1">Fallidos</p>
                            <p className="text-3xl font-bold text-red-600">{queueStatus.jobs?.failed || 0}</p>
                            <p className="text-xs text-gray-500 mt-1">Con errores</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Submit IP Form */}
            <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6 shadow-sm">
                <h2 className="text-lg font-semibold mb-4">📨 Enviar IP a Cola de Escaneo</h2>

                {error && (
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
                        ❌ {error}
                    </div>
                )}

                {success && (
                    <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded mb-4">
                        {success}
                    </div>
                )}

                <form onSubmit={handleSubmitToQueue} className="flex gap-3">
                    <input
                        type="text"
                        value={targetIp}
                        onChange={(e) => setTargetIp(e.target.value)}
                        placeholder="192.168.1.1 o scanme.nmap.org"
                        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        disabled={submitting}
                    />
                    <button
                        type="submit"
                        disabled={submitting || !targetIp.trim()}
                        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed font-medium transition-colors"
                    >
                        {submitting ? '⏳ Enviando...' : '📨 Enviar a Cola'}
                    </button>
                </form>

                <p className="text-sm text-gray-500 mt-3">
                    💡 El escaneo puede tomar hasta 20 minutos dependiendo del objetivo
                </p>
            </div>

            {/* Consumer Control Section */}
            <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6 shadow-sm">
                <h2 className="text-lg font-semibold mb-4">⚙️ Control del Consumidor RabbitMQ</h2>

                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className={`w-4 h-4 rounded-full ${consumerRunning ? 'bg-green-500 animate-pulse' : 'bg-gray-300'}`}></div>
                        <div>
                            <span className="text-sm font-medium block">
                                Estado: <span className={consumerRunning ? 'text-green-600' : 'text-gray-500'}>
                                    {consumerRunning ? '🟢 Activo' : '⚪ Detenido'}
                                </span>
                            </span>
                            <span className="text-xs text-gray-500">
                                {consumerRunning
                                    ? 'Procesando trabajos de RabbitMQ automáticamente'
                                    : 'Presiona el botón para iniciar el procesamiento de la cola'}
                            </span>
                        </div>
                    </div>

                    <button
                        onClick={handleStartConsumer}
                        disabled={loadingConsumer || consumerRunning}
                        className={`px-6 py-2 rounded-lg font-medium transition-colors ${consumerRunning
                            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            : 'bg-green-600 text-white hover:bg-green-700 disabled:bg-gray-300'
                            }`}
                    >
                        {loadingConsumer ? '⏳ Iniciando...' : consumerRunning ? '✅ Consumidor Activo' : '▶️ Iniciar Consumidor'}
                    </button>
                </div>
            </div>

            {/* Jobs List */}
            <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-lg font-semibold">📋 Trabajos en Cola ({queueJobs.length})</h2>
                    <button
                        onClick={loadQueueData}
                        disabled={loading}
                        className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium transition-colors disabled:opacity-50"
                    >
                        {loading ? '🔄 Cargando...' : '🔄 Actualizar'}
                    </button>
                </div>

                {loading && queueJobs.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                        <div className="animate-spin inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mb-2"></div>
                        <p>Cargando trabajos...</p>
                    </div>
                ) : queueJobs.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                        <p className="text-4xl mb-2">📭</p>
                        <p>No hay trabajos en la cola</p>
                        <p className="text-sm mt-1">Envía una IP para comenzar un escaneo</p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {queueJobs.map((job) => (
                            <JobCard
                                key={job.job_id}
                                job={job}
                                formatTimestamp={formatTimestamp}
                                getRiskColor={getRiskColor}
                                getRiskCategory={getRiskCategory}
                            />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

// Job Card Component with detailed results
function JobCard({ job, formatTimestamp, getRiskColor, getRiskCategory }) {
    const [expanded, setExpanded] = useState(false);

    const getStatusBadge = (status) => {
        const badges = {
            pending: { bg: 'bg-yellow-100', text: 'text-yellow-800', border: 'border-yellow-300', icon: '⏳' },
            processing: { bg: 'bg-blue-100', text: 'text-blue-800', border: 'border-blue-300', icon: '🔄' },
            completed: { bg: 'bg-green-100', text: 'text-green-800', border: 'border-green-300', icon: '✅' },
            failed: { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-300', icon: '❌' }
        };
        return badges[status] || badges.pending;
    };

    const badge = getStatusBadge(job.status);

    return (
        <div className="border border-gray-200 rounded-lg p-5 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-bold text-xl text-gray-900">{job.target_ip}</h3>
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${badge.bg} ${badge.text} ${badge.border}`}>
                            {badge.icon} {job.status.toUpperCase()}
                        </span>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm text-gray-600">
                        <div>
                            <span className="font-medium">Job ID:</span>
                            <br />
                            <span className="text-xs font-mono">{job.job_id?.slice(0, 16)}...</span>
                        </div>
                        <div>
                            <span className="font-medium">Creado:</span>
                            <br />
                            {formatTimestamp(job.created_at)}
                        </div>
                        {job.processing_time_seconds && (
                            <div>
                                <span className="font-medium">Duración:</span>
                                <br />
                                {job.processing_time_seconds}s
                            </div>
                        )}
                        {job.total_ports_found > 0 && (
                            <div>
                                <span className="font-medium">Puertos:</span>
                                <br />
                                {job.total_ports_found} encontrados
                            </div>
                        )}
                    </div>

                    {job.error_message && (
                        <div className="mt-3 text-sm text-red-600 bg-red-50 p-3 rounded border border-red-200">
                            ❌ Error: {job.error_message}
                        </div>
                    )}
                </div>

                {job.status === 'completed' && (
                    <button
                        onClick={() => setExpanded(!expanded)}
                        className="ml-4 px-4 py-2 text-sm bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-lg transition-colors font-medium"
                    >
                        {expanded ? '▲ Ocultar Resultados' : '▼ Ver Resultados Detallados'}
                    </button>
                )}
            </div>

            {expanded && job.status === 'completed' && (
                <DetailedResults job={job} getRiskColor={getRiskColor} getRiskCategory={getRiskCategory} />
            )}
        </div>
    );
}

// Detailed Results Component
function DetailedResults({ job, getRiskColor, getRiskCategory }) {
    const results = job.scan_results || {};
    const ports = results.ports || [];

    return (
        <div className="mt-4 pt-4 border-t border-gray-200">
            {/* Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                    <p className="text-xs text-gray-600 mb-1">Total Puertos</p>
                    <p className="text-3xl font-bold text-blue-600">{job.total_ports_found || 0}</p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                    <p className="text-xs text-gray-600 mb-1">Abiertos</p>
                    <p className="text-3xl font-bold text-green-600">{job.open_ports_count || 0}</p>
                </div>
                <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                    <p className="text-xs text-gray-600 mb-1">Cerrados</p>
                    <p className="text-3xl font-bold text-red-600">{job.closed_ports_count || 0}</p>
                </div>
                <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                    <p className="text-xs text-gray-600 mb-1">Filtrados</p>
                    <p className="text-3xl font-bold text-yellow-600">{job.filtered_ports_count || 0}</p>
                </div>
            </div>

            {/* Ports Table */}
            {ports.length > 0 && (
                <div className="mb-6">
                    <h4 className="font-semibold text-lg mb-3 text-gray-900">🔌 Puertos Detectados</h4>
                    <div className="max-h-96 overflow-y-auto border rounded-lg">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50 sticky top-0">
                                <tr>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Puerto</th>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Estado</th>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Servicio</th>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Versión</th>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Producto</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {ports.map((port, idx) => (
                                    <tr key={idx} className="hover:bg-gray-50">
                                        <td className="px-4 py-3 text-sm font-mono font-semibold">{port.port}/{port.protocol || 'tcp'}</td>
                                        <td className="px-4 py-3 text-sm">
                                            <span className={`px-2 py-1 rounded text-xs font-semibold ${port.state === 'open' ? 'bg-green-100 text-green-800' :
                                                port.state === 'closed' ? 'bg-red-100 text-red-800' :
                                                    'bg-yellow-100 text-yellow-800'
                                                }`}>
                                                {port.state}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-sm">{port.service || 'N/A'}</td>
                                        <td className="px-4 py-3 text-sm text-gray-600">{port.version || 'N/A'}</td>
                                        <td className="px-4 py-3 text-sm text-gray-600">{port.product || 'N/A'}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Vulnerabilities Section - Will be populated by backend */}
            {results.vulnerabilities && results.vulnerabilities.length > 0 && (
                <div>
                    <h4 className="font-semibold text-lg mb-3 text-gray-900">
                        🛡️ Vulnerabilidades Detectadas ({results.vulnerabilities.length})
                    </h4>
                    <div className="space-y-4">
                        {results.vulnerabilities.map((vuln, idx) => (
                            <VulnerabilityCard
                                key={idx}
                                vulnerability={vuln}
                                getRiskColor={getRiskColor}
                                getRiskCategory={getRiskCategory}
                            />
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

// Vulnerability Card Component
function VulnerabilityCard({ vulnerability, getRiskColor, getRiskCategory }) {
    const [showRemediation, setShowRemediation] = useState(false);

    return (
        <div className="border border-gray-300 rounded-lg p-5 bg-white shadow-sm">
            <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                        <h5 className="font-bold text-lg text-gray-900">{vulnerability.title || 'Vulnerabilidad Detectada'}</h5>
                        {vulnerability.risk && (
                            <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getRiskColor(vulnerability.risk.score)}`}>
                                {getRiskCategory(vulnerability.risk.score)} - {vulnerability.risk.score}/100
                            </span>
                        )}
                    </div>

                    {vulnerability.cve && (
                        <p className="text-sm text-red-600 font-semibold mb-2">
                            🔴 CVE: {vulnerability.cve}
                        </p>
                    )}

                    <p className="text-sm text-gray-700 mb-3">
                        {vulnerability.description || 'Sin descripción disponible'}
                    </p>

                    {vulnerability.context && (
                        <div className="bg-gray-50 p-3 rounded border border-gray-200 mb-3">
                            <p className="text-xs text-gray-600 mb-1">Contexto:</p>
                            <p className="text-sm">
                                <strong>Puerto:</strong> {vulnerability.context.port} |
                                <strong className="ml-2">Servicio:</strong> {vulnerability.context.product || 'N/A'}
                            </p>
                        </div>
                    )}
                </div>
            </div>

            {/* Treatment Strategy */}
            {vulnerability.treatment && (
                <div className="mb-3 p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <p className="text-sm font-semibold text-blue-900 mb-2">
                        📋 Estrategia de Tratamiento: <span className="uppercase">{vulnerability.treatment.treatment}</span>
                    </p>
                    <p className="text-sm text-gray-700">
                        <strong>Justificación:</strong> {vulnerability.treatment.reason}
                    </p>
                </div>
            )}

            {/* Remediation Recommendations */}
            {vulnerability.treatment?.remediation && (
                <div>
                    <button
                        onClick={() => setShowRemediation(!showRemediation)}
                        className="w-full text-left px-4 py-2 bg-green-50 hover:bg-green-100 rounded-lg border border-green-200 transition-colors"
                    >
                        <span className="font-semibold text-green-900">
                            {showRemediation ? '▲' : '▼'} Recomendaciones de Remediación Personalizadas
                        </span>
                    </button>

                    {showRemediation && (
                        <div className="mt-3 p-4 bg-green-50 rounded-lg border border-green-200">
                            <ul className="space-y-2">
                                {vulnerability.treatment.remediation.map((rec, idx) => (
                                    <li key={idx} className="flex items-start text-sm text-gray-800">
                                        <span className="text-green-600 mr-2 font-bold">{idx + 1}.</span>
                                        <span>{rec}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
