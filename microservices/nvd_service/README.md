# NVD Vulnerability Microservice

A dedicated microservice for handling National Vulnerability Database (NVD) operations and risk analysis.

## Features
- NVD API integration
- Vulnerability search and retrieval
- Risk analysis and categorization
- Enterprise metrics calculation
- Queue-based vulnerability processing

## Endpoints
- `GET /nvd` - Search vulnerabilities by keyword
- `POST /nvd/add_to_queue` - Add vulnerability to analysis queue
- `POST /nvd/analyze_risk` - Analyze risks from queue
- `POST /nvd/enterprise_metrics` - Get enterprise risk metrics
- `GET /nvd/queue_status` - Get queue status
- `POST /nvd/clear_queue` - Clear analysis queue
- `GET /health` - Health check

## Architecture
- **Services**: NVD API integration and risk analysis
- **Queue**: RabbitMQ integration for async processing  
- **Analytics**: Enterprise risk calculation and categorization
- **API**: FastAPI endpoints
