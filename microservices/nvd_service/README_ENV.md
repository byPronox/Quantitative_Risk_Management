# NVD Service Configuration

## Environment Setup

This service requires environment variables to be configured. Follow these steps:

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file with your actual configuration:**

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MONGODB_URL` | MongoDB Atlas connection string | `mongodb+srv://user:pass@cluster.mongodb.net/` |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Application environment |
| `SERVICE_NAME` | `nvd-service` | Service name |
| `SERVICE_VERSION` | `1.0.0` | Service version |
| `HOST` | `0.0.0.0` | Host to bind the service |
| `PORT` | `8002` | Port to run the service |
| `NVD_API_KEY` | - | NVD API key (optional) |
| `NVD_BASE_URL` | `https://services.nvd.nist.gov/rest/json/cves/2.0` | NVD API base URL |
| `KONG_PROXY_URL` | - | Kong Gateway proxy URL (optional) |
| `USE_KONG_NVD` | `false` | Whether to use Kong Gateway |
| `MONGODB_DATABASE` | `cveScanner` | MongoDB database name |
| `RABBITMQ_HOST` | `rabbitmq` | RabbitMQ host |
| `RABBITMQ_USER` | `guest` | RabbitMQ username |
| `RABBITMQ_PASSWORD` | `guest` | RabbitMQ password |
| `RABBITMQ_QUEUE` | `nvd_analysis_queue` | RabbitMQ queue name |
| `BACKEND_URL` | `http://backend:8000` | Backend service URL |
| `MAX_RETRIES` | `5` | Maximum retry attempts |
| `RETRY_DELAY` | `2` | Delay between retries (seconds) |
| `REQUEST_TIMEOUT` | `60` | Request timeout (seconds) |
| `MAX_VULNERABILITIES_PER_REQUEST` | `1000` | Max vulnerabilities per request |

## Security Notes

- **Never commit the `.env` file to version control**
- The `.env` file is included in `.gitignore`
- Only commit the `.env.example` file with placeholder values
- Keep sensitive information like database URLs and API keys secure

## Docker Usage

When using Docker, you can:

1. Use the `.env` file (recommended for development)
2. Pass environment variables directly to Docker:
   ```bash
   docker run -e MONGODB_URL="your_connection_string" nvd-service
   ```
3. Use Docker Compose with environment variables defined in `docker-compose.yml`
