-- ============================================
-- NMAP SCANNER - SUPABASE DATABASE SCHEMA
-- ============================================
-- Este script crea las tablas necesarias para el sistema de análisis
-- asíncrono de escaneo de puertos con Nmap, siguiendo la misma
-- arquitectura que NVD vulnerabilities.
--
-- ORDEN DE EJECUCIÓN:
-- 1. Tablas
-- 2. Índices
-- 3. Vistas
-- 4. Funciones
-- ============================================

-- ============================================
-- PASO 1: CREAR TABLAS
-- ============================================

-- TABLA: nmap_jobs
-- Almacena los trabajos de escaneo Nmap (equivalente a nvd_jobs)
-- Estados: pending, processing, completed, failed

CREATE TABLE IF NOT EXISTS nmap_jobs (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Job Identification
    job_id VARCHAR(255) UNIQUE NOT NULL,
    target_ip VARCHAR(255) NOT NULL,  -- IP o hostname a escanear
    
    -- Job Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    -- Valores posibles: 'pending', 'processing', 'completed', 'failed'
    
    -- Scan Configuration (opcional, para futuras extensiones)
    scan_type VARCHAR(50) DEFAULT 'default',  -- 'default', 'quick', 'full', 'custom'
    scan_options JSONB,  -- Opciones adicionales de nmap (ej: {"-sV": true, "-O": true})
    
    -- Results Summary
    total_ports_found INTEGER DEFAULT 0,
    open_ports_count INTEGER DEFAULT 0,
    closed_ports_count INTEGER DEFAULT 0,
    filtered_ports_count INTEGER DEFAULT 0,
    
    -- Timestamps (usando distributed time service - WorldTimeAPI con fallback a Docker)
    -- Almacenados como NUMERIC (Unix timestamp) para precisión y consistencia distribuida
    created_at NUMERIC DEFAULT EXTRACT(EPOCH FROM NOW()),  -- Timestamp de creación (desde TimeService)
    processed_at NUMERIC,  -- Timestamp cuando inicia procesamiento (desde TimeService)
    completed_at NUMERIC,  -- Timestamp cuando completa (desde TimeService)
    
    -- Processing Metadata
    processed_via VARCHAR(50),  -- 'queue_consumer', 'direct_api'
    processing_time_seconds INTEGER,  -- Duración del escaneo en segundos
    
    -- Error Handling
    error_message TEXT,  -- Mensaje de error si status = 'failed'
    
    -- Raw Results (almacenamiento completo del output de nmap)
    scan_results JSONB,  -- Resultados completos del escaneo en formato JSON
    
    -- Constraints
    CONSTRAINT nmap_jobs_status_check CHECK (status IN ('pending', 'processing', 'completed', 'failed'))
);

-- TABLA: nmap_scan_results
-- Almacena los detalles de cada puerto encontrado (equivalente a nvd_vulnerabilities)
-- Permite consultas granulares por puerto, servicio, etc.

CREATE TABLE IF NOT EXISTS nmap_scan_results (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Foreign Key to nmap_jobs
    job_id VARCHAR(255) NOT NULL,
    
    -- Port Information
    port_number INTEGER NOT NULL,
    protocol VARCHAR(10) NOT NULL,  -- 'tcp', 'udp', 'sctp'
    port_state VARCHAR(20) NOT NULL,  -- 'open', 'closed', 'filtered', 'unfiltered', 'open|filtered', 'closed|filtered'
    
    -- Service Detection
    service_name VARCHAR(255),  -- Nombre del servicio (ej: 'http', 'ssh', 'mysql')
    service_product VARCHAR(255),  -- Producto detectado (ej: 'Apache httpd', 'OpenSSH')
    service_version VARCHAR(255),  -- Versión del servicio (ej: '2.4.41', '8.2p1')
    service_extra_info TEXT,  -- Información adicional del servicio
    
    -- OS Detection (si aplica)
    os_match VARCHAR(255),  -- Sistema operativo detectado
    os_accuracy INTEGER,  -- Precisión de la detección (0-100)
    
    -- Script Results (NSE - Nmap Scripting Engine)
    script_output JSONB,  -- Resultados de scripts NSE ejecutados
    
    -- Raw Data
    raw_data JSONB,  -- Datos completos del puerto en formato JSON
    
    -- Timestamps (usando distributed time service)
    scanned_at NUMERIC DEFAULT EXTRACT(EPOCH FROM NOW()),  -- Timestamp del escaneo
    
    -- Foreign Key Constraint
    CONSTRAINT fk_nmap_job
        FOREIGN KEY (job_id)
        REFERENCES nmap_jobs(job_id)
        ON DELETE CASCADE,
    
    -- Constraints
    CONSTRAINT nmap_scan_results_port_check CHECK (port_number BETWEEN 1 AND 65535),
    CONSTRAINT nmap_scan_results_protocol_check CHECK (protocol IN ('tcp', 'udp', 'sctp'))
);


-- ============================================
-- PASO 2: CREAR ÍNDICES
-- ============================================

-- Índices para nmap_jobs
CREATE INDEX IF NOT EXISTS idx_nmap_jobs_job_id ON nmap_jobs(job_id);
CREATE INDEX IF NOT EXISTS idx_nmap_jobs_target_ip ON nmap_jobs(target_ip);
CREATE INDEX IF NOT EXISTS idx_nmap_jobs_status ON nmap_jobs(status);
CREATE INDEX IF NOT EXISTS idx_nmap_jobs_created_at ON nmap_jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_nmap_jobs_scan_results ON nmap_jobs USING GIN (scan_results);

-- Índices para nmap_scan_results
CREATE INDEX IF NOT EXISTS idx_nmap_scan_results_job_id ON nmap_scan_results(job_id);
CREATE INDEX IF NOT EXISTS idx_nmap_scan_results_port_number ON nmap_scan_results(port_number);
CREATE INDEX IF NOT EXISTS idx_nmap_scan_results_port_state ON nmap_scan_results(port_state);
CREATE INDEX IF NOT EXISTS idx_nmap_scan_results_service_name ON nmap_scan_results(service_name);
CREATE INDEX IF NOT EXISTS idx_nmap_scan_results_script_output ON nmap_scan_results USING GIN (script_output);
CREATE INDEX IF NOT EXISTS idx_nmap_scan_results_job_port ON nmap_scan_results(job_id, port_number);


-- ============================================
-- PASO 3: COMENTARIOS DE DOCUMENTACIÓN
-- ============================================

COMMENT ON TABLE nmap_jobs IS 'Trabajos de escaneo Nmap con procesamiento asíncrono vía RabbitMQ';
COMMENT ON COLUMN nmap_jobs.job_id IS 'Identificador único del trabajo (timestamp-counter)';
COMMENT ON COLUMN nmap_jobs.target_ip IS 'IP o hostname objetivo del escaneo';
COMMENT ON COLUMN nmap_jobs.status IS 'Estado del trabajo: pending, processing, completed, failed';
COMMENT ON COLUMN nmap_jobs.scan_results IS 'Resultados completos del escaneo en formato JSON';
COMMENT ON COLUMN nmap_jobs.processing_time_seconds IS 'Duración del escaneo (puede ser hasta 20 minutos = 1200 segundos)';

COMMENT ON TABLE nmap_scan_results IS 'Detalles de cada puerto encontrado en los escaneos Nmap';
COMMENT ON COLUMN nmap_scan_results.job_id IS 'Referencia al trabajo de escaneo padre';
COMMENT ON COLUMN nmap_scan_results.port_number IS 'Número de puerto (1-65535)';
COMMENT ON COLUMN nmap_scan_results.port_state IS 'Estado del puerto: open, closed, filtered, etc.';
COMMENT ON COLUMN nmap_scan_results.service_name IS 'Nombre del servicio detectado (ej: http, ssh)';
COMMENT ON COLUMN nmap_scan_results.script_output IS 'Resultados de scripts NSE en formato JSON';


-- ============================================
-- PASO 4: CREAR VISTAS
-- ============================================

-- Vista: Resumen de trabajos con conteo de puertos
CREATE OR REPLACE VIEW nmap_jobs_summary AS
SELECT 
    j.id,
    j.job_id,
    j.target_ip,
    j.status,
    j.total_ports_found,
    j.open_ports_count,
    j.created_at,
    j.processed_at,
    j.processing_time_seconds,
    COUNT(r.id) AS detailed_results_count,
    COUNT(CASE WHEN r.port_state = 'open' THEN 1 END) AS open_ports_detailed
FROM nmap_jobs j
LEFT JOIN nmap_scan_results r ON j.job_id = r.job_id
GROUP BY j.id, j.job_id, j.target_ip, j.status, j.total_ports_found, 
         j.open_ports_count, j.created_at, j.processed_at, j.processing_time_seconds
ORDER BY j.created_at DESC;

COMMENT ON VIEW nmap_jobs_summary IS 'Resumen de trabajos Nmap con conteo de resultados detallados';


-- Vista: Puertos abiertos por servicio
CREATE OR REPLACE VIEW nmap_open_ports_by_service AS
SELECT 
    service_name,
    COUNT(*) AS total_occurrences,
    COUNT(DISTINCT job_id) AS unique_scans,
    ARRAY_AGG(DISTINCT port_number ORDER BY port_number) AS common_ports
FROM nmap_scan_results
WHERE port_state = 'open' AND service_name IS NOT NULL
GROUP BY service_name
ORDER BY total_occurrences DESC;

COMMENT ON VIEW nmap_open_ports_by_service IS 'Estadísticas de servicios encontrados en puertos abiertos';


-- ============================================
-- PASO 5: CREAR FUNCIONES
-- ============================================

-- Función: Obtener puertos abiertos de un job
CREATE OR REPLACE FUNCTION get_open_ports(p_job_id VARCHAR)
RETURNS TABLE (
    port_number INTEGER,
    protocol VARCHAR,
    service_name VARCHAR,
    service_version VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.port_number,
        r.protocol,
        r.service_name,
        r.service_version
    FROM nmap_scan_results r
    WHERE r.job_id = p_job_id
      AND r.port_state = 'open'
    ORDER BY r.port_number;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_open_ports IS 'Retorna todos los puertos abiertos de un trabajo específico';


-- Función: Limpiar trabajos antiguos (más de 30 días)
CREATE OR REPLACE FUNCTION cleanup_old_nmap_jobs(days_old INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM nmap_jobs
    WHERE TO_TIMESTAMP(created_at) < NOW() - (days_old || ' days')::INTERVAL
      AND status IN ('completed', 'failed');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_nmap_jobs IS 'Elimina trabajos completados/fallidos más antiguos que N días';


-- ============================================
-- VERIFICACIÓN FINAL
-- ============================================

-- Verificar que las tablas se crearon correctamente
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) AS column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
  AND table_name IN ('nmap_jobs', 'nmap_scan_results')
ORDER BY table_name;

-- Verificar índices
SELECT 
    tablename,
    indexname
FROM pg_indexes
WHERE tablename IN ('nmap_jobs', 'nmap_scan_results')
ORDER BY tablename, indexname;

-- Verificar vistas
SELECT 
    table_name AS view_name
FROM information_schema.views
WHERE table_schema = 'public'
  AND table_name LIKE 'nmap%'
ORDER BY table_name;

