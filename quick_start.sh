#!/bin/bash

# Quantitative Risk Management System - Quick Start Script
# This script sets up and starts the entire QRMS system

set -e

echo "🚀 Quantitative Risk Management System - Quick Start"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    print_status "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Check if required ports are available
check_ports() {
    print_status "Checking if required ports are available..."
    
    ports=(8000 8001 8002 8003 8004 5173 5432 5672 6379 15672)
    occupied_ports=()
    
    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            occupied_ports+=($port)
        fi
    done
    
    if [ ${#occupied_ports[@]} -ne 0 ]; then
        print_warning "The following ports are already in use: ${occupied_ports[*]}"
        print_warning "You may need to stop the services using these ports or modify the docker-compose.yml file"
        read -p "Do you want to continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_error "Aborting startup"
            exit 1
        fi
    else
        print_success "All required ports are available"
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p ./microservices/nmap_scanner/temp
    mkdir -p ./microservices/report_service/temp
    mkdir -p ./logs
    
    print_success "Directories created"
}

# Check if .env file exists
check_env_file() {
    print_status "Checking environment configuration..."
    
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from template..."
        
        cat > .env << EOF
# Production Environment Configuration
# Use Kong Gateway for all API calls

# Frontend Configuration -- Kong Gateway
VITE_API_URL=https://kong-b27b67aff4usnsp19.kongcloud.dev

# Backend Configuration
DATABASE_URL=postgresql://postgres:postgres@db:5432/postgres

# NVD API Configuration (Kong Gateway)
NVD_API_KEY=dc2624cc-b2a6-462b-b859-d7cf0ad1cf66
USE_KONG_NVD=true

# Kong Configuration
KONG_PROXY_URL=https://kong-b27b67aff4usnsp19.kongcloud.dev
KONG_ADMIN_API=https://us.api.konghq.com/v2/control-planes/9d98c0ba-3ac1-44fd-b497-59743e18a80a
KONG_CONTROL_PLANE_ID=9d98c0ba-3ac1-44fd-b497-59743e18a80a

# RabbitMQ Configuration
RABBITMQ_HOST=rabbitmq
RABBITMQ_QUEUE=nvd_analysis_queue
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/

# Additional Service URLs for Docker Compose
ML_SERVICE_URL=http://ml-prediction-service:8001
NVD_SERVICE_URL=http://nvd-service:8002
REPORT_SERVICE_URL=http://report-service:8003
NMAP_SERVICE_URL=http://nmap-scanner-service:8004

# MongoDB Configuration
MONGODB_URL=mongodb+srv://ADMIN:ADMIN@cluster0.7ixig65.mongodb.net/
MONGODB_DATABASE=cveScanner

# Security Configuration
JWT_SECRET_KEY=your-secret-key-change-in-production
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://kong-b27b67aff4usnsp19.kongcloud.dev

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# Environment
ENVIRONMENT=production
EOF
        
        print_success ".env file created from template"
        print_warning "Please review and update the .env file with your specific configuration"
    else
        print_success ".env file found"
    fi
}

# Build and start services
start_services() {
    print_status "Building and starting services..."
    
    # Build images
    print_status "Building Docker images..."
    docker-compose build --parallel
    
    # Start services
    print_status "Starting services..."
    docker-compose up -d
    
    print_success "Services started successfully"
}

# Wait for services to be ready
wait_for_services() {
    print_status "Waiting for services to be ready..."
    
    # Wait for database
    print_status "Waiting for PostgreSQL..."
    timeout 60 bash -c 'until docker-compose exec -T db pg_isready -U postgres; do sleep 2; done'
    
    # Wait for RabbitMQ
    print_status "Waiting for RabbitMQ..."
    timeout 60 bash -c 'until docker-compose exec -T rabbitmq rabbitmq-diagnostics ping; do sleep 2; done'
    
    # Wait for backend
    print_status "Waiting for Backend API..."
    timeout 120 bash -c 'until curl -f http://localhost:8000/health >/dev/null 2>&1; do sleep 5; done'
    
    # Wait for other services
    services=("ml-prediction-service:8001" "nvd-service:8002" "report-service:8003" "nmap-scanner-service:8004")
    
    for service in "${services[@]}"; do
        service_name=$(echo $service | cut -d: -f1)
        service_port=$(echo $service | cut -d: -f2)
        print_status "Waiting for $service_name..."
        timeout 60 bash -c "until curl -f http://localhost:$service_port/health >/dev/null 2>&1; do sleep 5; done"
    done
    
    print_success "All services are ready"
}

# Run integration tests
run_tests() {
    print_status "Running integration tests..."
    
    if [ -f test_integration.py ]; then
        python3 test_integration.py
        if [ $? -eq 0 ]; then
            print_success "Integration tests passed"
        else
            print_warning "Some integration tests failed. Check the output above."
        fi
    else
        print_warning "Integration test script not found. Skipping tests."
    fi
}

# Show service status
show_status() {
    print_status "Service Status:"
    echo "================"
    docker-compose ps
    
    echo ""
    print_status "Service URLs:"
    echo "=============="
    echo "🌐 Frontend:           http://localhost:5173"
    echo "🔧 Backend API:        http://localhost:8000"
    echo "📚 API Documentation:  http://localhost:8000/docs"
    echo "🤖 ML Service:         http://localhost:8001"
    echo "🔍 NVD Service:        http://localhost:8002"
    echo "📊 Report Service:     http://localhost:8003"
    echo "🔍 Nmap Scanner:       http://localhost:8004"
    echo "🐰 RabbitMQ Management: http://localhost:15672 (guest/guest)"
    echo "🗄️  PostgreSQL:        localhost:5432 (postgres/postgres)"
    echo "📦 Redis:             localhost:6379"
}

# Show usage instructions
show_usage() {
    echo ""
    print_success "🎉 QRMS is now running!"
    echo ""
    echo "📋 Next Steps:"
    echo "=============="
    echo "1. Open the frontend: http://localhost:5173"
    echo "2. Try the new Risk Analysis Dashboard"
    echo "3. Test the enhanced risk analysis API:"
    echo "   curl -X POST http://localhost:8000/api/v1/risk/nmap-analysis \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{\"ip\": \"127.0.0.1\", \"include_risk_rubric\": true}'"
    echo ""
    echo "🔧 Management Commands:"
    echo "======================"
    echo "• View logs:           docker-compose logs -f [service-name]"
    echo "• Stop services:       docker-compose down"
    echo "• Restart service:     docker-compose restart [service-name]"
    echo "• View status:         docker-compose ps"
    echo "• Access service:      docker-compose exec [service-name] bash"
    echo ""
    echo "📖 Documentation:"
    echo "================="
    echo "• API Docs:            http://localhost:8000/docs"
    echo "• Enhanced README:     ./README_ENHANCED.md"
    echo "• Integration Tests:   python3 test_integration.py"
    echo ""
    echo "🛡️  Risk Analysis Features:"
    echo "=========================="
    echo "• AVOID/MITIGATE/TRANSFER/ACCEPT rubric"
    echo "• Detailed technical recommendations"
    echo "• Service-specific risk assessments"
    echo "• Vulnerability analysis with mitigation strategies"
}

# Main execution
main() {
    echo "Starting QRMS setup process..."
    echo ""
    
    check_docker
    check_ports
    create_directories
    check_env_file
    start_services
    wait_for_services
    run_tests
    show_status
    show_usage
    
    print_success "Setup completed successfully! 🎉"
}

# Handle script interruption
trap 'print_error "Setup interrupted by user"; exit 1' INT

# Run main function
main "$@"
