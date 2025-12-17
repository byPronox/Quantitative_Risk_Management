import pkg from 'pg';
const { Pool } = pkg;

/**
 * DatabaseService - Supabase (PostgreSQL) connection and operations
 * Handles nmap_jobs and nmap_scan_results tables
 */
class DatabaseService {
    constructor() {
        this.pool = null;
        this.isConnected = false;
    }

    /**
     * Initialize database connection pool
     */
    async connect() {
        if (this.isConnected) {
            return;
        }

        try {
            const DATABASE_URL = process.env.DATABASE_URL;

            if (!DATABASE_URL) {
                throw new Error('DATABASE_URL environment variable is not set');
            }

            this.pool = new Pool({
                connectionString: DATABASE_URL,
                ssl: {
                    rejectUnauthorized: false // Required for Supabase
                },
                max: 20, // Maximum pool size
                idleTimeoutMillis: 30000,
                connectionTimeoutMillis: 2000,
            });

            // Test connection
            const client = await this.pool.connect();
            await client.query('SELECT NOW()');
            client.release();

            this.isConnected = true;
            console.log('[DatabaseService] Connected to Supabase successfully');

        } catch (error) {
            console.error('[DatabaseService] Failed to connect to Supabase:', error.message);
            throw error;
        }
    }

    /**
     * Save or update job in nmap_jobs table
     * @param {Object} job - Job object
     */
    async saveJob(job) {
        await this.connect();

        const query = `
      INSERT INTO nmap_jobs (
        job_id, target_ip, status, scan_type, scan_options,
        total_ports_found, open_ports_count, closed_ports_count, filtered_ports_count,
        created_at, processed_at, completed_at,
        processed_via, processing_time_seconds, error_message, scan_results
      ) VALUES (
        $1, $2, $3, $4, $5,
        $6, $7, $8, $9,
        $10, $11, $12,
        $13, $14, $15, $16
      )
      ON CONFLICT (job_id) DO UPDATE SET
        status = EXCLUDED.status,
        total_ports_found = EXCLUDED.total_ports_found,
        open_ports_count = EXCLUDED.open_ports_count,
        closed_ports_count = EXCLUDED.closed_ports_count,
        filtered_ports_count = EXCLUDED.filtered_ports_count,
        processed_at = EXCLUDED.processed_at,
        completed_at = EXCLUDED.completed_at,
        processed_via = EXCLUDED.processed_via,
        processing_time_seconds = EXCLUDED.processing_time_seconds,
        error_message = EXCLUDED.error_message,
        scan_results = EXCLUDED.scan_results
    `;

        const values = [
            job.job_id,
            job.target_ip,
            job.status || 'pending',
            job.scan_type || 'default',
            JSON.stringify(job.scan_options || {}),
            job.total_ports_found || 0,
            job.open_ports_count || 0,
            job.closed_ports_count || 0,
            job.filtered_ports_count || 0,
            job.created_at,
            job.processed_at || null,
            job.completed_at || null,
            job.processed_via || null,
            job.processing_time_seconds || null,
            job.error_message || null,
            JSON.stringify(job.scan_results || {})
        ];

        try {
            await this.pool.query(query, values);
            console.log(`[DatabaseService] Job ${job.job_id} saved successfully`);
        } catch (error) {
            console.error(`[DatabaseService] Error saving job ${job.job_id}:`, error.message);
            throw error;
        }
    }

    /**
     * Update job status and optional metadata
     * @param {string} jobId - Job ID
     * @param {string} status - New status (pending, processing, completed, failed)
     * @param {Object} updates - Optional fields to update (processed_at, completed_at, etc.)
     */
    async updateJobStatus(jobId, status, updates = {}) {
        await this.connect();

        // First, get the existing job to preserve data
        const existingJob = await this.getJobById(jobId);
        if (!existingJob) {
            throw new Error(`Job ${jobId} not found`);
        }

        // Merge existing job with updates
        const updatedJob = {
            ...existingJob,
            status,
            ...updates
        };

        // Use saveJob to update
        await this.saveJob(updatedJob);
        console.log(`[DatabaseService] Job ${jobId} status updated to ${status}`);
    }

    /**
     * Save a single scan result to nmap_scan_results table
     * @param {string} jobId - Job ID
     * @param {Object} portData - Port data object
     */
    async saveScanResult(jobId, portData) {
        await this.connect();

        const query = `
      INSERT INTO nmap_scan_results (
        job_id, port_number, protocol, port_state,
        service_name, service_product, service_version, service_extra_info,
        os_match, os_accuracy, script_output, raw_data, scanned_at
      ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
      )
    `;

        const values = [
            jobId,
            portData.port_number,
            portData.protocol || 'tcp',
            portData.port_state || 'unknown',
            portData.service_name || null,
            portData.service_product || null,
            portData.service_version || null,
            portData.service_extra_info || null,
            portData.os_match || null,
            portData.os_accuracy || null,
            JSON.stringify(portData.script_output || {}),
            JSON.stringify(portData.raw_data || {}),
            portData.scanned_at || Math.floor(Date.now() / 1000)
        ];

        try {
            await this.pool.query(query, values);
        } catch (error) {
            console.error(`[DatabaseService] Error saving port result:`, error.message);
            throw error;
        }
    }

    /**
     * Save scan results to nmap_scan_results table
     * @param {string} jobId - Job ID
     * @param {Array} ports - Array of port objects
     */
    async saveScanResults(jobId, ports) {
        await this.connect();

        if (!ports || ports.length === 0) {
            console.log(`[DatabaseService] No ports to save for job ${jobId}`);
            return;
        }

        const query = `
      INSERT INTO nmap_scan_results (
        job_id, port_number, protocol, port_state,
        service_name, service_product, service_version, service_extra_info,
        os_match, os_accuracy, script_output, raw_data, scanned_at
      ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
      )
    `;

        const client = await this.pool.connect();

        try {
            await client.query('BEGIN');

            for (const port of ports) {
                const values = [
                    jobId,
                    port.port_number,
                    port.protocol || 'tcp',
                    port.port_state || 'unknown',
                    port.service_name || null,
                    port.service_product || null,
                    port.service_version || null,
                    port.service_extra_info || null,
                    port.os_match || null,
                    port.os_accuracy || null,
                    JSON.stringify(port.script_output || {}),
                    JSON.stringify(port.raw_data || {}),
                    port.scanned_at || Math.floor(Date.now() / 1000)
                ];

                await client.query(query, values);
            }

            await client.query('COMMIT');
            console.log(`[DatabaseService] Saved ${ports.length} port results for job ${jobId}`);

        } catch (error) {
            await client.query('ROLLBACK');
            console.error(`[DatabaseService] Error saving scan results for job ${jobId}:`, error.message);
            throw error;
        } finally {
            client.release();
        }
    }

    /**
     * Get all jobs from nmap_jobs table
     * @returns {Promise<Array>} Array of job objects
     */
    async getAllJobs() {
        await this.connect();

        const query = `
      SELECT 
        id, job_id, target_ip, status, scan_type, scan_options,
        total_ports_found, open_ports_count, closed_ports_count, filtered_ports_count,
        created_at, processed_at, completed_at,
        processed_via, processing_time_seconds, error_message, scan_results
      FROM nmap_jobs
      ORDER BY created_at DESC
      LIMIT 100
    `;

        try {
            const result = await this.pool.query(query);
            console.log(`[DatabaseService] Retrieved ${result.rows.length} jobs`);
            return result.rows;
        } catch (error) {
            console.error('[DatabaseService] Error getting all jobs:', error.message);
            throw error;
        }
    }

    /**
     * Get job by ID
     * @param {string} jobId - Job ID
     * @returns {Promise<Object|null>} Job object or null
     */
    async getJobById(jobId) {
        await this.connect();

        const query = `
      SELECT * FROM nmap_jobs WHERE job_id = $1
    `;

        try {
            const result = await this.pool.query(query, [jobId]);
            return result.rows[0] || null;
        } catch (error) {
            console.error(`[DatabaseService] Error getting job ${jobId}:`, error.message);
            throw error;
        }
    }

    /**
     * Get scan results for a job
     * @param {string} jobId - Job ID
     * @returns {Promise<Array>} Array of port results
     */
    async getScanResults(jobId) {
        await this.connect();

        const query = `
      SELECT * FROM nmap_scan_results
      WHERE job_id = $1
      ORDER BY port_number ASC
    `;

        try {
            const result = await this.pool.query(query, [jobId]);
            console.log(`[DatabaseService] Retrieved ${result.rows.length} port results for job ${jobId}`);
            return result.rows;
        } catch (error) {
            console.error(`[DatabaseService] Error getting scan results for job ${jobId}:`, error.message);
            throw error;
        }
    }

    /**
     * Close database connection
     */
    async close() {
        if (this.pool) {
            await this.pool.end();
            this.isConnected = false;
            console.log('[DatabaseService] Database connection closed');
        }
    }
}

// Export singleton instance
const databaseService = new DatabaseService();
export default databaseService;
