import amqp from 'amqplib';
import pg from 'pg';
import { scanIP } from './scanner.js';
import dotenv from 'dotenv';

dotenv.config();

const QUEUE_NAME = 'nmap_scan_queue';
const RABBITMQ_URL = process.env.RABBITMQ_URL || 'amqp://guest:guest@rabbitmq:5672/';
const DATABASE_URL = process.env.DATABASE_URL;

// Database connection pool
const pool = new pg.Pool({
    connectionString: DATABASE_URL,
});

async function updateJobStatus(jobId, status, result = null, error = null) {
    const client = await pool.connect();
    try {
        const now = new Date().toISOString();
        let query = 'UPDATE nmap_jobs SET status = $1';
        const values = [status];
        let paramIndex = 2;

        if (result) {
            query += `, result = $${paramIndex}`;
            values.push(result);
            paramIndex++;
        }
        if (error) {
            query += `, error = $${paramIndex}`;
            values.push(error);
            paramIndex++;
        }
        if (status === 'completed' || status === 'failed') {
            query += `, completed_at = $${paramIndex}`;
            values.push(now);
            paramIndex++;
        }

        query += ` WHERE job_id = $${paramIndex}`;
        values.push(jobId);

        await client.query(query, values);
        console.log(`Job ${jobId} updated to ${status}`);
    } catch (err) {
        console.error(`Failed to update job ${jobId}:`, err);
    } finally {
        client.release();
    }
}

export async function startConsumer() {
    try {
        console.log('Connecting to RabbitMQ...');
        const connection = await amqp.connect(RABBITMQ_URL);
        const channel = await connection.createChannel();

        await channel.assertQueue(QUEUE_NAME, { durable: true });
        console.log(`Waiting for messages in ${QUEUE_NAME}...`);

        channel.consume(QUEUE_NAME, async (msg) => {
            if (msg !== null) {
                const content = JSON.parse(msg.content.toString());
                const { job_id, target } = content;

                console.log(`Received scan job: ${job_id} for target: ${target}`);

                // Update status to processing
                await updateJobStatus(job_id, 'processing');

                try {
                    // Perform Scan
                    console.log(`Starting scan for ${target}...`);
                    const scanResult = await scanIP(target);

                    // Update status to completed
                    await updateJobStatus(job_id, 'completed', scanResult);
                    console.log(`Scan completed for ${job_id}`);

                    channel.ack(msg);
                } catch (error) {
                    console.error(`Scan failed for ${job_id}:`, error);
                    await updateJobStatus(job_id, 'failed', null, error.message || String(error));
                    // We ack even if failed to avoid infinite loop, or we could nack/dead-letter
                    channel.ack(msg);
                }
            }
        });
    } catch (error) {
        console.error('RabbitMQ Consumer Error:', error);
        // Retry logic could go here
        setTimeout(startConsumer, 5000);
    }
}
