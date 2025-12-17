import amqp from 'amqplib';
import databaseService from './database_service.js';
import TimeService from './time_service.js';

/**
 * QueueService - RabbitMQ queue management
 * Handles job creation, publishing, and queue status
 */
class QueueService {
    constructor() {
        this.connection = null;
        this.channel = null;
        this.queueName = 'nmap_scan_queue'; // Hardcoded to prevent env var conflicts
        this.rabbitmqUrl = process.env.RABBITMQ_URL || 'amqp://guest:guest@rabbitmq:5672/';
        this.jobCounter = 0;
    }

    /**
     * Connect to RabbitMQ
     */
    async connect() {
        if (this.channel) {
            return; // Already connected
        }

        try {
            console.log(`[QueueService] Connecting to RabbitMQ at ${this.rabbitmqUrl}...`);
            this.connection = await amqp.connect(this.rabbitmqUrl);
            this.channel = await this.connection.createChannel();

            // Declare queue as durable (simple declaration to match existing queue)
            await this.channel.assertQueue(this.queueName, {
                durable: true
            });

            console.log(`[QueueService] Connected to RabbitMQ successfully`);
            console.log(`[QueueService] Queue: ${this.queueName}`);

            // Handle connection close
            this.connection.on('close', () => {
                console.warn('[QueueService] RabbitMQ connection closed');
                this.channel = null;
                this.connection = null;
            });

            this.connection.on('error', (err) => {
                console.error('[QueueService] RabbitMQ connection error:', err.message);
            });

        } catch (error) {
            console.error('[QueueService] Failed to connect to RabbitMQ:', error.message);
            throw error;
        }
    }

    /**
     * Generate unique job ID
     * @returns {string} Job ID in format: timestamp-counter
     */
    async generateJobId() {
        const timestamp = await TimeService.getCurrentTimestampMs();
        this.jobCounter++;
        return `${Math.floor(timestamp * 1000)}-${this.jobCounter}`;
    }

    /**
     * Add scan job to queue
     * @param {string} targetIp - IP or hostname to scan
     * @param {Object} options - Scan options
     * @returns {Promise<Object>} Job info
     */
    async addJob(targetIp, options = {}) {
        await this.connect();

        try {
            // Generate job ID and timestamps
            const jobId = await this.generateJobId();
            const createdAt = await TimeService.getCurrentTimestamp();

            // Create job object
            const job = {
                job_id: jobId,
                target_ip: targetIp,
                status: 'pending',
                scan_type: options.scan_type || 'default',
                scan_options: options,
                created_at: createdAt,
                total_ports_found: 0,
                open_ports_count: 0,
                closed_ports_count: 0,
                filtered_ports_count: 0
            };

            // Save to database
            await databaseService.saveJob(job);
            console.log(`[QueueService] Job ${jobId} saved to database`);

            // Publish to RabbitMQ
            const message = {
                job_id: jobId,
                target: targetIp,
                options: options,
                created_at: createdAt
            };

            const sent = this.channel.sendToQueue(
                this.queueName,
                Buffer.from(JSON.stringify(message)),
                {
                    persistent: true, // Message survives broker restart
                    timestamp: Date.now()
                }
            );

            if (sent) {
                console.log(`[QueueService] Job ${jobId} published to queue`);
                return {
                    success: true,
                    job_id: jobId,
                    target_ip: targetIp,
                    status: 'queued',
                    message: 'Job added to queue successfully'
                };
            } else {
                throw new Error('Failed to publish message to queue');
            }

        } catch (error) {
            console.error('[QueueService] Error adding job to queue:', error.message);
            throw error;
        }
    }

    /**
     * Get queue status
     * @returns {Promise<Object>} Queue status
     */
    async getQueueStatus() {
        await this.connect();

        try {
            const queueInfo = await this.channel.checkQueue(this.queueName);

            // Get job counts from database
            const jobs = await databaseService.getAllJobs();
            const pending = jobs.filter(j => j.status === 'pending').length;
            const processing = jobs.filter(j => j.status === 'processing').length;
            const completed = jobs.filter(j => j.status === 'completed').length;
            const failed = jobs.filter(j => j.status === 'failed').length;

            return {
                success: true,
                queue_name: this.queueName,
                queue_size: queueInfo.messageCount,
                consumer_count: queueInfo.consumerCount,
                status: 'healthy',
                jobs: {
                    pending,
                    processing,
                    completed,
                    failed,
                    total: jobs.length
                }
            };

        } catch (error) {
            console.error('[QueueService] Error getting queue status:', error.message);
            return {
                success: false,
                error: error.message,
                status: 'unhealthy'
            };
        }
    }

    /**
     * Get all job results from database
     * @returns {Promise<Object>} All jobs
     */
    async getAllJobResults() {
        try {
            const jobs = await databaseService.getAllJobs();

            return {
                success: true,
                total: jobs.length,
                jobs: jobs.map(job => ({
                    id: job.id,
                    job_id: job.job_id,
                    target_ip: job.target_ip,
                    status: job.status,
                    scan_type: job.scan_type,
                    total_ports_found: job.total_ports_found,
                    open_ports_count: job.open_ports_count,
                    closed_ports_count: job.closed_ports_count,
                    filtered_ports_count: job.filtered_ports_count,
                    created_at: job.created_at,
                    processed_at: job.processed_at,
                    completed_at: job.completed_at,
                    processed_via: job.processed_via,
                    processing_time_seconds: job.processing_time_seconds,
                    error_message: job.error_message,
                    scan_results: job.scan_results
                }))
            };

        } catch (error) {
            console.error('[QueueService] Error getting all job results:', error.message);
            return {
                success: false,
                jobs: [],
                error: error.message
            };
        }
    }

    /**
     * Get job result by ID
     * @param {string} jobId - Job ID
     * @returns {Promise<Object>} Job result
     */
    async getJobResult(jobId) {
        try {
            const job = await databaseService.getJobById(jobId);

            if (!job) {
                return {
                    success: false,
                    error: 'Job not found'
                };
            }

            // Get detailed port results
            const ports = await databaseService.getScanResults(jobId);

            return {
                success: true,
                job: {
                    ...job,
                    ports: ports
                }
            };

        } catch (error) {
            console.error(`[QueueService] Error getting job result for ${jobId}:`, error.message);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Close RabbitMQ connection
     */
    async close() {
        if (this.channel) {
            await this.channel.close();
            this.channel = null;
        }
        if (this.connection) {
            await this.connection.close();
            this.connection = null;
        }
        console.log('[QueueService] RabbitMQ connection closed');
    }
}

// Export singleton instance
const queueService = new QueueService();
export default queueService;
