import React, { useState, useEffect } from 'react';
import { backendApi } from '../services/api';

const ReportsPage = () => {
    const [nvdJobs, setNvdJobs] = useState([]);
    const [vulnerabilities, setVulnerabilities] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('jobs'); // 'jobs' or 'vulnerabilities'

    useEffect(() => {
        loadNvdReports();
    }, []);

    const loadNvdReports = async () => {
        try {
            setLoading(true);
            setError(null);

            // Load jobs from nvd_jobs table
            console.log('Loading jobs from /nvd/database/jobs...');
            const jobsResponse = await backendApi.get('/nvd/database/jobs');
            console.log('Jobs response:', jobsResponse.data);

            if (jobsResponse.data) {
                if (jobsResponse.data.success !== false && jobsResponse.data.jobs) {
                    setNvdJobs(jobsResponse.data.jobs || []);
                    console.log('Jobs loaded:', jobsResponse.data.jobs?.length || 0);
                } else if (Array.isArray(jobsResponse.data)) {
                    // Si la respuesta es directamente un array
                    setNvdJobs(jobsResponse.data);
                    console.log('Jobs loaded (array format):', jobsResponse.data.length);
                } else {
                    console.warn('Unexpected jobs response format:', jobsResponse.data);
                    setNvdJobs([]);
                }
            } else {
                setNvdJobs([]);
            }

            // Load vulnerabilities from nvd_vulnerabilities table
            console.log('Loading vulnerabilities from /nvd/database/vulnerabilities...');
            const vulnsResponse = await backendApi.get('/nvd/database/vulnerabilities', {
                params: { limit: 100 }
            });
            console.log('Vulnerabilities response:', vulnsResponse.data);

            if (vulnsResponse.data) {
                if (vulnsResponse.data.success !== false && vulnsResponse.data.vulnerabilities) {
                    setVulnerabilities(vulnsResponse.data.vulnerabilities || []);
                    console.log('Vulnerabilities loaded:', vulnsResponse.data.vulnerabilities?.length || 0);
                } else if (Array.isArray(vulnsResponse.data)) {
                    // Si la respuesta es directamente un array
                    setVulnerabilities(vulnsResponse.data);
                    console.log('Vulnerabilities loaded (array format):', vulnsResponse.data.length);
                } else {
                    console.warn('Unexpected vulnerabilities response format:', vulnsResponse.data);
                    setVulnerabilities([]);
                }
            } else {
                setVulnerabilities([]);
            }
        } catch (err) {
            console.error('Error loading NVD reports:', err);
            console.error('Error details:', {
                message: err.message,
                response: err.response?.data,
                status: err.response?.status,
                statusText: err.response?.statusText
            });
            setError(`Error al cargar reportes de NVD: ${err.message || 'Error desconocido'}`);
        } finally {
            setLoading(false);
        }
    };

    // Helper function to translate job status
    const translateStatus = (status) => {
        const map = {
            'completed': 'Completado',
            'pending': 'Pendiente',
            'processing': 'Procesando',
            'failed': 'Fallido'
        };
        return map[status] || status;
    };

    // Helper function to translate severity
    const translateSeverity = (severity) => {
        if (!severity) return 'Desconocido';
        const map = {
            'CRITICAL': 'CRÍTICO',
            'HIGH': 'ALTO',
            'MEDIUM': 'MEDIO',
            'LOW': 'BAJO'
        };
        return map[severity.toUpperCase()] || severity;
    };

    if (loading) {
        return (
            <div style={{ padding: '40px', textAlign: 'center' }}>
                <h2>Cargando reportes...</h2>
            </div>
        );
    }

    if (error) {
        return (
            <div style={{ padding: '40px', textAlign: 'center', color: '#dc3545' }}>
                <h2>❌ {error}</h2>
                <button onClick={loadNvdReports} style={{ marginTop: '20px', padding: '10px 20px' }}>
                    Reintentar
                </button>
            </div>
        );
    }

    // Extract unique keywords for filter
    const uniqueKeywords = [...new Set(vulnerabilities.map(v => v.keyword).filter(k => k))].sort();
    const [selectedKeyword, setSelectedKeyword] = useState('ALL');

    // Filter vulnerabilities
    const filteredVulnerabilities = selectedKeyword === 'ALL'
        ? vulnerabilities
        : vulnerabilities.filter(v => v.keyword === selectedKeyword);

    return (
        <div style={{ padding: '20px', maxWidth: '1400px', margin: '0 auto' }}>
            <div style={{ marginBottom: '30px', textAlign: 'center' }}>
                <h1 style={{ color: '#2c3e50', marginBottom: '10px' }}>📊 Reportes de Análisis NVD</h1>
            </div>

            {/* Tab Navigation */}
            <div style={{ marginBottom: '20px', borderBottom: '2px solid #e9ecef', display: 'flex', gap: '10px' }}>
                <button
                    onClick={() => setActiveTab('jobs')}
                    style={{
                        padding: '12px 24px',
                        border: 'none',
                        background: activeTab === 'jobs' ? '#007bff' : '#f8f9fa',
                        color: activeTab === 'jobs' ? 'white' : '#6c757d',
                        borderRadius: '8px 8px 0 0',
                        cursor: 'pointer',
                        fontSize: '1rem',
                        fontWeight: activeTab === 'jobs' ? 'bold' : 'normal',
                        transition: 'all 0.3s ease'
                    }}
                >
                    📋 Trabajos ({nvdJobs.length})
                </button>
                <button
                    onClick={() => setActiveTab('vulnerabilities')}
                    style={{
                        padding: '12px 24px',
                        border: 'none',
                        background: activeTab === 'vulnerabilities' ? '#007bff' : '#f8f9fa',
                        color: activeTab === 'vulnerabilities' ? 'white' : '#6c757d',
                        borderRadius: '8px 8px 0 0',
                        cursor: 'pointer',
                        fontSize: '1rem',
                        fontWeight: activeTab === 'vulnerabilities' ? 'bold' : 'normal',
                        transition: 'all 0.3s ease'
                    }}
                >
                    🛡️ Vulnerabilidades ({vulnerabilities.length})
                </button>
                <div style={{ flex: 1 }}></div>
                <button
                    onClick={loadNvdReports}
                    style={{
                        padding: '10px 20px',
                        backgroundColor: '#28a745',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        marginTop: '5px'
                    }}
                >
                    🔄 Actualizar
                </button>
            </div>

            {/* Jobs Tab Content */}
            {activeTab === 'jobs' && (
                <>
                    {nvdJobs.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: '60px 20px' }}>
                            <h3 style={{ color: '#6c757d' }}>No hay jobs disponibles</h3>
                            <p>Ejecute análisis de NVD para ver jobs aquí</p>
                        </div>
                    ) : (
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '20px' }}>
                            {nvdJobs.map((job) => (
                                <div
                                    key={job.job_id}
                                    style={{
                                        border: '1px solid #ddd',
                                        borderRadius: '8px',
                                        padding: '20px',
                                        backgroundColor: 'white',
                                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                                    }}
                                >
                                    <div style={{ marginBottom: '15px' }}>
                                        <h3 style={{ margin: '0 0 10px 0', color: '#2c3e50' }}>
                                            🔍 {job.keyword}
                                        </h3>
                                        <div style={{ fontSize: '0.85em', color: '#6c757d' }}>
                                            <span>ID: {job.job_id.substring(0, 12)}...</span>
                                        </div>
                                    </div>

                                    <div style={{ marginBottom: '15px' }}>
                                        <div style={{ marginBottom: '8px' }}>
                                            <strong>Estado:</strong>{' '}
                                            <span
                                                style={{
                                                    padding: '4px 8px',
                                                    borderRadius: '4px',
                                                    backgroundColor: job.status === 'completed' ? '#28a745' : '#ffc107',
                                                    color: 'white',
                                                    fontSize: '0.85em'
                                                }}
                                            >
                                                {translateStatus(job.status)}
                                            </span>
                                        </div>
                                        <div style={{ marginBottom: '8px' }}>
                                            <strong>Vulnerabilidades:</strong> {job.total_results || 0}
                                        </div>
                                        <div style={{ marginBottom: '8px' }}>
                                            <strong>Procesado vía:</strong> {job.processed_via || 'N/A'}
                                        </div>
                                        <div style={{ fontSize: '0.85em', color: '#6c757d' }}>
                                            <strong>Fecha:</strong> {new Date(job.created_at).toLocaleString()}
                                        </div>
                                    </div>

                                    {job.vulnerabilities && job.vulnerabilities.length > 0 && (
                                        <div style={{ marginTop: '15px', borderTop: '1px solid #eee', paddingTop: '15px' }}>
                                            <strong style={{ display: 'block', marginBottom: '10px' }}>
                                                Vulnerabilidades detectadas ({job.vulnerabilities.length}):
                                            </strong>
                                            <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                                                <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                                                    {job.vulnerabilities.map((vuln, idx) => (
                                                        <div
                                                            key={idx}
                                                            style={{
                                                                padding: '8px',
                                                                marginBottom: '8px',
                                                                backgroundColor: '#f8f9fa',
                                                                borderRadius: '4px',
                                                                fontSize: '0.85em'
                                                            }}
                                                        >
                                                            <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
                                                                {vuln.cve?.id || 'N/A'}
                                                            </div>
                                                            <div style={{ color: '#6c757d', fontSize: '0.9em' }}>
                                                                {vuln.cve?.descriptions?.[0]?.value || 'Sin descripción'}
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </>
            )}

            {/* Vulnerabilities Tab Content */}
            {activeTab === 'vulnerabilities' && (
                <>
                    <div style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <label htmlFor="keyword-filter" style={{ fontWeight: 'bold', color: '#495057' }}>Filtrar por Keyword:</label>
                        <select
                            id="keyword-filter"
                            value={selectedKeyword}
                            onChange={(e) => setSelectedKeyword(e.target.value)}
                            style={{
                                padding: '8px 12px',
                                borderRadius: '4px',
                                border: '1px solid #ced4da',
                                backgroundColor: 'white',
                                fontSize: '1rem',
                                minWidth: '200px'
                            }}
                        >
                            <option value="ALL">Todas ({vulnerabilities.length})</option>
                            {uniqueKeywords.map(keyword => (
                                <option key={keyword} value={keyword}>
                                    {keyword} ({vulnerabilities.filter(v => v.keyword === keyword).length})
                                </option>
                            ))}
                        </select>
                    </div>

                    {filteredVulnerabilities.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: '60px 20px' }}>
                            <h3 style={{ color: '#6c757d' }}>No hay vulnerabilidades disponibles</h3>
                            <p>
                                {vulnerabilities.length > 0
                                    ? "No hay vulnerabilidades que coincidan con el filtro seleccionado."
                                    : "Ejecute análisis de NVD para ver vulnerabilidades aquí"}
                            </p>
                        </div>
                    ) : (
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))',
                            gap: '20px'
                        }}>
                            {filteredVulnerabilities.map((vuln, idx) => (
                                <div
                                    key={vuln.id || idx}
                                    style={{
                                        border: '1px solid #ddd',
                                        borderRadius: '8px',
                                        padding: '20px',
                                        backgroundColor: 'white',
                                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                                    }}
                                >
                                    <div style={{ marginBottom: '15px' }}>
                                        <h3 style={{ margin: '0 0 10px 0', color: '#2c3e50' }}>
                                            🔒 {vuln.cve_id || 'N/A'}
                                        </h3>
                                        <div style={{ fontSize: '0.85em', color: '#6c757d' }}>
                                            <span>Job ID: {vuln.job_id ? vuln.job_id.substring(0, 12) + '...' : 'N/A'}</span>
                                            {vuln.keyword && (
                                                <span style={{ marginLeft: '10px' }}>• Palabra clave: {vuln.keyword}</span>
                                            )}
                                        </div>
                                    </div>

                                    <div style={{ marginBottom: '15px' }}>
                                        {vuln.cvss_v3_score !== null && vuln.cvss_v3_score !== undefined && (
                                            <div style={{ marginBottom: '8px' }}>
                                                <strong>Puntaje CVSS v3:</strong>{' '}
                                                <span
                                                    style={{
                                                        padding: '4px 8px',
                                                        borderRadius: '4px',
                                                        backgroundColor:
                                                            vuln.cvss_v3_score >= 9 ? '#dc3545' :
                                                                vuln.cvss_v3_score >= 7 ? '#fd7e14' :
                                                                    vuln.cvss_v3_score >= 4 ? '#ffc107' : '#28a745',
                                                        color: 'white',
                                                        fontSize: '0.9em',
                                                        fontWeight: 'bold'
                                                    }}
                                                >
                                                    {vuln.cvss_v3_score}
                                                </span>
                                            </div>
                                        )}
                                        {vuln.cvss_v3_severity && (
                                            <div style={{ marginBottom: '8px' }}>
                                                <strong>Severidad:</strong>{' '}
                                                <span
                                                    style={{
                                                        padding: '4px 8px',
                                                        borderRadius: '4px',
                                                        backgroundColor:
                                                            vuln.cvss_v3_severity === 'CRITICAL' ? '#dc3545' :
                                                                vuln.cvss_v3_severity === 'HIGH' ? '#fd7e14' :
                                                                    vuln.cvss_v3_severity === 'MEDIUM' ? '#ffc107' : '#28a745',
                                                        color: 'white',
                                                        fontSize: '0.85em'
                                                    }}
                                                >
                                                    {translateSeverity(vuln.cvss_v3_severity)}
                                                </span>
                                            </div>
                                        )}
                                        {vuln.vuln_status && (
                                            <div style={{ marginBottom: '8px' }}>
                                                <strong>Estado:</strong> {vuln.vuln_status}
                                            </div>
                                        )}
                                        {vuln.description && (
                                            <div style={{ marginBottom: '8px' }}>
                                                <strong>Descripción:</strong>
                                                <div style={{
                                                    marginTop: '5px',
                                                    fontSize: '0.9em',
                                                    color: '#6c757d',
                                                    maxHeight: '100px',
                                                    overflowY: 'auto'
                                                }}>
                                                    {vuln.description}
                                                </div>
                                            </div>
                                        )}
                                        {vuln.published && (
                                            <div style={{ fontSize: '0.85em', color: '#6c757d' }}>
                                                <strong>Publicado:</strong> {new Date(vuln.published).toLocaleString()}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default ReportsPage;
