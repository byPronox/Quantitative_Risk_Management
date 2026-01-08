import axios from 'axios';

/**
 * TimeService - Distributed time synchronization
 * Uses WorldTimeAPI with fallback to Docker container time
 */
class TimeService {
    /**
     * Get current timestamp from distributed time source
     * @returns {Promise<number>} Unix timestamp (seconds since epoch)
     */
    static async getCurrentTimestamp() {
        try {
            // Attempt 1: WorldTimeAPI (configurable via .env)
            const worldTimeUrl = process.env.WORLDTIME_API_URL || 'http://worldtimeapi.org/api/timezone/Etc/UTC';
            const response = await axios.get(worldTimeUrl, {
                timeout: 2000 // 2 second timeout
            });

            const timestamp = response.data.unixtime;
            console.log(`✅ [TimeService] Using WorldTimeAPI (${worldTimeUrl}): ${timestamp}`);
            return timestamp;

        } catch (error) {
            // Attempt 2: Docker container time (fallback)
            console.warn(`⚠️ [TimeService] WorldTimeAPI failed: ${error.message}`);
            const timestamp = Math.floor(Date.now() / 1000);
            console.log(`🐳 [TimeService] Using local Docker time: ${timestamp}`);
            return timestamp;
        }
    }

    /**
     * Get current timestamp with millisecond precision
     * @returns {Promise<number>} Unix timestamp with milliseconds
     */
    static async getCurrentTimestampMs() {
        const timestamp = await this.getCurrentTimestamp();
        return timestamp + (Date.now() % 1000) / 1000;
    }

    /**
     * Convert Unix timestamp to ISO string
     * @param {number} timestamp - Unix timestamp
     * @returns {string} ISO 8601 formatted date string
     */
    static toISOString(timestamp) {
        return new Date(timestamp * 1000).toISOString();
    }
}

export default TimeService;
