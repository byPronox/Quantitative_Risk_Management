-- ⚠️ ADVERTENCIA: Este script eliminará TODOS los datos existentes en estas tablas.

-- 1. Eliminar tablas existentes (orden inverso para respetar claves foráneas)
DROP TABLE IF EXISTS nvd_vulnerabilities;
DROP TABLE IF EXISTS nvd_jobs;

-- 2. Crear tabla principal de trabajos (nvd_jobs)
-- Nota: NO incluimos la columna 'vulnerabilities' porque es redundante.
CREATE TABLE nvd_jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(255) UNIQUE NOT NULL,
    keyword VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    total_results INTEGER DEFAULT 0,
    processed_at TIMESTAMP WITH TIME ZONE,
    processed_via VARCHAR(100) DEFAULT 'nvd_microservice',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Crear tabla de vulnerabilidades (nvd_vulnerabilities)
-- Esta tabla almacena cada vulnerabilidad individualmente, vinculada al trabajo.
CREATE TABLE nvd_vulnerabilities (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(255) REFERENCES nvd_jobs(job_id) ON DELETE CASCADE,
    cve_id VARCHAR(50) NOT NULL,
    source_identifier VARCHAR(255),
    published TIMESTAMP WITH TIME ZONE,
    last_modified TIMESTAMP WITH TIME ZONE,
    vuln_status VARCHAR(100),
    description TEXT,
    cvss_v3_score DECIMAL(3,1),
    cvss_v3_severity VARCHAR(20),
    cvss_v2_score DECIMAL(3,1),
    raw_data JSONB, -- Guardamos el JSON original completo por seguridad
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(job_id, cve_id) -- Evita duplicados de la misma CVE en el mismo trabajo
);

-- 4. Crear índices para velocidad (Performance Tuning)
CREATE INDEX idx_nvd_jobs_keyword ON nvd_jobs(keyword);
CREATE INDEX idx_nvd_jobs_processed_at ON nvd_jobs(processed_at DESC);
CREATE INDEX idx_nvd_vulns_cve_id ON nvd_vulnerabilities(cve_id);
CREATE INDEX idx_nvd_vulns_severity ON nvd_vulnerabilities(cvss_v3_severity);
CREATE INDEX idx_nvd_vulns_job_id ON nvd_vulnerabilities(job_id);

-- Confirmación
SELECT 'Tablas recreadas exitosamente con arquitectura normalizada' as status;
