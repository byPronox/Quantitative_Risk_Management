# Nmap Scanner Service

A microservice for vulnerability scanning using nmap, designed to integrate with the Quantitative Risk Management System (QRMS).

## Features

- **Exact nmap command implementation**: `nmap -sV --script vuln [IP] -oX scan_result.xml`
- **XML processing**: Parses nmap XML output using xml2js
- **Structured data extraction**: IP, OS, ports, services, and vulnerabilities
- **Input validation**: IP address and hostname validation
- **Error handling**: Comprehensive error handling with detailed logging
- **Rate limiting**: Prevents abuse with configurable limits
- **Security**: Helmet.js security headers and CORS protection

## API Endpoints

### POST /api/v1/scan
Main scanning endpoint that executes nmap scan.

**Request Body:**
```json
{
  "ip": "192.168.1.1"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "ip": "192.168.1.1",
    "os": "Microsoft Windows",
    "status": "up",
    "services": [
      {
        "port": "135",
        "protocol": "tcp",
        "state": "open",
        "name": "msrpc",
        "product": "Microsoft Windows RPC",
        "version": "",
        "method": "probed",
        "conf": "10",
        "extrainfo": ""
      }
    ],
    "vulnerabilities": [],
    "timestamp": "2025-01-02T21:23:14.694Z",
    "scanDuration": "unknown"
  },
  "scanDuration": "15000ms",
  "timestamp": "2025-01-02T21:23:14.694Z"
}
```

### GET /api/v1/test
Test nmap installation and get version information.

### GET /api/v1/scripts
Get available vulnerability scripts.

### GET /api/v1/validate/:target
Validate IP address or hostname format.

### GET /api/v1/status
Get service status and configuration.

### GET /api/v1/health
Health check endpoint.

## Installation

### Docker (Recommended)
```bash
docker build -t nmap-scanner-service .
docker run -p 8004:8004 nmap-scanner-service
```

### Local Development
```bash
# Install nmap
# Ubuntu/Debian:
sudo apt-get install nmap nmap-scripts

# macOS:
brew install nmap

# Windows:
# Download from https://nmap.org/download.html

# Install Node.js dependencies
npm install

# Start service
npm start
```

## Configuration

### Environment Variables
- `PORT`: Server port (default: 8004)
- `HOST`: Server host (default: 0.0.0.0)
- `NODE_ENV`: Environment (development/production)
- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins

### Rate Limiting
- 10 requests per 15 minutes per IP
- Configurable via express-rate-limit

### Scan Timeout
- 5 minutes maximum per scan
- Configurable in scanner.js

## Test Cases

The service has been tested with:
- `127.0.0.1` (localhost)
- `192.168.1.1` (private network)
- `8.8.8.8` (public DNS)
- `scanme.nmap.org` (nmap test host)

## Error Handling

The service handles various error scenarios:
- Invalid IP format
- Nmap execution failures
- XML parsing errors
- File system errors
- Timeout errors
- Permission errors

## Security Considerations

- Non-root user in Docker container
- Rate limiting to prevent abuse
- Input validation
- Security headers with Helmet.js
- CORS protection
- Temporary file cleanup

## Logging

Comprehensive logging includes:
- Request/response logging
- Nmap command execution
- XML processing steps
- Error details
- Performance metrics

## Integration

This service integrates with the QRMS ecosystem:
- Docker Compose orchestration
- API Gateway routing
- MongoDB for result storage
- RabbitMQ for async processing

## License

MIT License
