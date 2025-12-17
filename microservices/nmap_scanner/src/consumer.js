import amqp from 'amqplib';
import { scanIP } from './scanner.js';
import databaseService from './database_service.js';
import timeService from './time_service.js';
import dotenv from 'dotenv';

dotenv.config();

const QUEUE_NAME = 'nmap_scan_queue';
const RABBITMQ_URL = process.env.RABBITMQ_URL || 'amqp://guest:guest@rabbitmq:5672/';

export async function startConsumer() {
    let retryCount = 0;
    const maxRetries = 10;

    const connect = async () => {
        try {
            console.log(`🐰 Connecting to RabbitMQ at ${RABBITMQ_URL}...`);
            const connection = await amqp.connect(RABBITMQ_URL);
            const channel = await connection.createChannel();

            // Handle connection close
            connection.on('close', () => {
                console.error('❌ RabbitMQ connection closed. Reconnecting...');
                setTimeout(connect, 5000);
            });

            connection.on('error', (err) => {
                console.error('❌ RabbitMQ connection error:', err);
            });

            await channel.assertQueue(QUEUE_NAME, { durable: true });
            console.log(`✅ Connected to RabbitMQ. Waiting for messages in ${QUEUE_NAME}...`);
            retryCount = 0; // Reset retry count on successful connection

            channel.consume(QUEUE_NAME, async (msg) => {
                if (msg !== null) {
                    const content = JSON.parse(msg.content.toString());
                    const { job_id, target } = content;

                    console.log(`📥 Received scan job: ${job_id} for target: ${target}`);

                    // Get distributed timestamp for processing start
                    const processingTimestamp = await timeService.getCurrentTimestamp();

                    // Update status to processing with timestamp
                    await databaseService.updateJobStatus(job_id, 'processing', {
                        processed_at: processingTimestamp
                    });

                    const startTime = Date.now();

                    try {
                        // Perform Scan
                        console.log(`🔍 Starting Nmap scan for ${target}...`);
                        const scanResult = await scanIP(target);

                        const endTime = Date.now();
                        const processingTimeSeconds = Math.floor((endTime - startTime) / 1000);

                        console.log(`✅ Scan completed for ${job_id} in ${processingTimeSeconds} seconds`);
                        console.log(`📊 Scan results:`, JSON.stringify(scanResult, null, 2));

                        // Get distributed timestamp for completion
                        const completedTimestamp = await timeService.getCurrentTimestamp();

                        // Extract port counts from scan results
                        const ports = scanResult.ports || [];
                        const openPorts = ports.filter(p => p.state === 'open');
                        const closedPorts = ports.filter(p => p.state === 'closed');
                        const filteredPorts = ports.filter(p => p.state === 'filtered' || p.state.includes('filtered'));

                        // Update job status to completed with full results
                        await databaseService.updateJobStatus(job_id, 'completed', {
                            completed_at: completedTimestamp,
                            processing_time_seconds: processingTimeSeconds,
                            total_ports_found: ports.length,
                            open_ports_count: openPorts.length,
                            closed_ports_count: closedPorts.length,
                            filtered_ports_count: filteredPorts.length,
                            scan_results: scanResult
                        });

                        // Save individual port results to nmap_scan_results table
                        if (ports.length > 0) {
                            console.log(`💾 Saving ${ports.length} port results to database...`);
                            const scannedTimestamp = await timeService.getCurrentTimestamp();

                            for (const port of ports) {
                                try {
                                    await databaseService.saveScanResult(job_id, {
                                        port_number: port.port,
                                        protocol: port.protocol || 'tcp',
                                        port_state: port.state,
                                        service_name: port.service || null,
                                        service_product: port.product || null,
                                        service_version: port.version || null,
                                        service_extra_info: port.extrainfo || null,
                                        os_match: scanResult.os_match || null,
                                        os_accuracy: scanResult.os_accuracy || null,
                                        script_output: port.scripts || null,
                                        raw_data: port,
                                        scanned_at: scannedTimestamp
                                    });
                                } catch (portError) {
                                    console.error(`❌ Error saving port ${port.port}:`, portError);
                                }
                            }
                            console.log(`✅ Saved ${ports.length} port results to database`);
                        }

                        console.log(`✅ Job ${job_id} completed successfully`);
                        channel.ack(msg);
                    } catch (error) {
                        console.error(`❌ Scan failed for ${job_id}:`, error);

                        // Get distributed timestamp for failure
                        const failedTimestamp = await timeService.getCurrentTimestamp();

                        await databaseService.updateJobStatus(job_id, 'failed', {
                            completed_at: failedTimestamp,
                            error_message: error.message || String(error)
                        });

                        channel.ack(msg);
                    }
                }
            });
        } catch (error) {
            console.error(`❌ RabbitMQ Consumer Error (attempt ${retryCount + 1}/${maxRetries}):`, error.message);
            retryCount++;

            if (retryCount < maxRetries) {
                const delay = Math.min(5000 * retryCount, 30000); // Exponential backoff, max 30s
                console.log(`⏳ Retrying in ${delay / 1000} seconds...`);
                setTimeout(connect, delay);
            } else {
                console.error('❌ Max retries reached. Consumer stopped.');
            }
        }
    };

    await connect();
}
