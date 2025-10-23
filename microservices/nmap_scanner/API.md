# Nmap Scanner Service API Documentation

## Overview

The Nmap Scanner Service provides vulnerability scanning capabilities using the exact nmap command: `nmap -sV --script vuln [IP] -oX scan_result.xml`

## Base URL

- **Development**: `http://localhost:8004`
- **Production**: `http://nmap-scanner-service:8004`

## Authentication

No authentication required for this service.

## Rate Limiting

- **Limit**: 10 requests per 15 minutes per IP
- **Headers**: Rate limit information included in response headers

## Endpoints

### POST /api/v1/scan

Execute a vulnerability scan on a target IP or hostname.

**Request Body:**
```json
{
  "ip": "192.168.1.1"
}
```

**Response (Success):**
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

**Response (Error):**
```json
{
  "success": false,
  "error": "Nmap execution failed",
  "details": "Permission denied",
  "target": "192.168.1.1",
  "scanDuration": "5000ms",
  "timestamp": "2025-01-02T21:23:14.694Z"
}
```

**Status Codes:**
- `200`: Scan completed successfully
- `400`: Invalid request (missing IP, invalid format)
- `408`: Scan timeout (exceeded 5 minutes)
- `429`: Rate limit exceeded
- `500`: Internal server error

### GET /api/v1/test

Test nmap installation and get version information.

**Response:**
```json
{
  "success": true,
  "data": {
    "installed": true,
    "version": "Nmap version 7.94 ( https://nmap.org )",
    "message": "Nmap is properly installed"
  },
  "timestamp": "2025-01-02T21:23:14.694Z"
}
```

### GET /api/v1/scripts

Get available vulnerability scripts.

**Response:**
```json
{
  "success": true,
  "data": {
    "scripts": "Scripts available for vuln category...",
    "message": "Vulnerability scripts available"
  },
  "timestamp": "2025-01-02T21:23:14.694Z"
}
```

### GET /api/v1/validate/:target

Validate IP address or hostname format.

**Parameters:**
- `target` (string): IP address or hostname to validate

**Response:**
```json
{
  "target": "192.168.1.1",
  "isValidIP": true,
  "isValidHostname": false,
  "isValid": true,
  "timestamp": "2025-01-02T21:23:14.694Z"
}
```

### GET /api/v1/status

Get service status and configuration.

**Response:**
```json
{
  "service": "Nmap Scanner Service",
  "version": "1.0.0",
  "status": "running",
  "endpoints": {
    "scan": "POST /scan",
    "test": "GET /test",
    "scripts": "GET /scripts",
    "validate": "GET /validate/:target",
    "status": "GET /status",
    "health": "GET /health"
  },
  "configuration": {
    "scanTimeout": "5 minutes",
    "rateLimit": "10 requests per 15 minutes",
    "supportedTargets": ["IP addresses", "hostnames"],
    "nmapCommand": "nmap -sV --script vuln [TARGET] -oX scan_result.xml"
  },
  "timestamp": "2025-01-02T21:23:14.694Z"
}
```

### GET /api/v1/health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "Nmap Scanner Service",
  "version": "1.0.0",
  "nmap": {
    "installed": true,
    "version": "Nmap version 7.94"
  },
  "timestamp": "2025-01-02T21:23:14.694Z"
}
```

## Error Handling

### Common Error Types

1. **Nmap execution failed**
   - Nmap command failed to execute
   - Permission denied
   - Target unreachable

2. **XML processing failed**
   - XML file not created
   - XML parsing error
   - Invalid XML structure

3. **Invalid target format**
   - Invalid IP address format
   - Invalid hostname format

4. **Service unavailable**
   - Cannot connect to nmap service
   - Service not running

### Error Response Format

```json
{
  "success": false,
  "error": "Error type",
  "details": "Detailed error message",
  "target": "192.168.1.1",
  "scanDuration": "5000ms",
  "timestamp": "2025-01-02T21:23:14.694Z"
}
```

## Usage Examples

### cURL Examples

**Scan a target:**
```bash
curl -X POST http://localhost:8004/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{"ip": "192.168.1.1"}'
```

**Test nmap installation:**
```bash
curl http://localhost:8004/api/v1/test
```

**Validate target:**
```bash
curl http://localhost:8004/api/v1/validate/192.168.1.1
```

**Get service status:**
```bash
curl http://localhost:8004/api/v1/status
```

### JavaScript Examples

**Scan a target:**
```javascript
const response = await fetch('http://localhost:8004/api/v1/scan', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ ip: '192.168.1.1' })
});

const result = await response.json();
console.log(result);
```

**Test nmap installation:**
```javascript
const response = await fetch('http://localhost:8004/api/v1/test');
const result = await response.json();
console.log(result.data.version);
```

## Test Cases

The service has been tested with:
- `127.0.0.1` (localhost)
- `192.168.1.1` (private network)
- `8.8.8.8` (public DNS)
- `scanme.nmap.org` (nmap test host)

## Security Considerations

- Rate limiting prevents abuse
- Input validation prevents injection attacks
- Non-root user in Docker container
- Temporary files are cleaned up after processing
- Privileged mode required for network scanning

## Performance

- **Scan timeout**: 5 minutes maximum
- **Rate limit**: 10 requests per 15 minutes
- **Memory usage**: ~50MB per scan
- **Disk usage**: Temporary XML files (~1MB each)

## Troubleshooting

### Common Issues

1. **"nmap not found"**
   - Ensure nmap is installed
   - Check PATH environment variable
   - Verify nmap-scripts package is installed

2. **"Permission denied"**
   - Run with appropriate permissions
   - Check Docker privileged mode
   - Verify network access

3. **"XML processing failed"**
   - Check disk space
   - Verify file permissions
   - Check XML file integrity

4. **"Scan timeout"**
   - Target may be unreachable
   - Network connectivity issues
   - Firewall blocking scans

### Debug Mode

Enable debug logging by setting environment variable:
```bash
NODE_ENV=development
```

## Integration with QRMS

This service integrates with the Quantitative Risk Management System:

- **API Gateway**: Routes requests through backend
- **MongoDB**: Stores scan results
- **RabbitMQ**: Async processing
- **Frontend**: Web interface for scanning

### Backend Integration

The service is integrated via the backend controller:
- `POST /api/v1/nmap/scan`
- `GET /api/v1/nmap/test`
- `GET /api/v1/nmap/validate/:target`
- `GET /api/v1/nmap/status`
- `GET /api/v1/nmap/health`
