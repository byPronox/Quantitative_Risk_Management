#!/bin/bash

# Microservices Management Script for Quantitative Risk Management System

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    printf "${2}${1}${NC}\n"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_color "Docker is not running. Please start Docker first." $RED
        exit 1
    fi
}

# Function to check if docker-compose is available
check_compose() {
    if ! command -v docker-compose > /dev/null 2>&1; then
        print_color "docker-compose not found. Please install docker-compose." $RED
        exit 1
    fi
}

# Function to start microservices
start_microservices() {
    print_color "Starting microservices..." $BLUE
    docker-compose -f docker-compose.microservices.yml up -d
    print_color "Microservices started successfully!" $GREEN
    print_color "Services available at:" $YELLOW
    print_color "  - ML Prediction Service: http://localhost:8001" $YELLOW
    print_color "  - NVD Service: http://localhost:8002" $YELLOW
    print_color "  - RabbitMQ Management: http://localhost:15672" $YELLOW
    print_color "  - Redis: localhost:6379" $YELLOW
}

# Function to start full system
start_full() {
    print_color "Starting full system..." $BLUE
    docker-compose up -d
    print_color "Full system started successfully!" $GREEN
    print_color "Services available at:" $YELLOW
    print_color "  - Frontend: http://localhost:5173" $YELLOW
    print_color "  - Backend (Legacy): http://localhost:8000" $YELLOW
    print_color "  - ML Prediction Service: http://localhost:8001" $YELLOW
    print_color "  - NVD Service: http://localhost:8002" $YELLOW
    print_color "  - Database: localhost:5432" $YELLOW
    print_color "  - RabbitMQ Management: http://localhost:15672" $YELLOW
    print_color "  - Redis: localhost:6379" $YELLOW
}

# Function to stop services
stop_services() {
    print_color "Stopping services..." $BLUE
    if [ "$1" = "microservices" ]; then
        docker-compose -f docker-compose.microservices.yml down
    else
        docker-compose down
    fi
    print_color "Services stopped!" $GREEN
}

# Function to show logs
show_logs() {
    if [ "$2" = "microservices" ]; then
        docker-compose -f docker-compose.microservices.yml logs -f "$1"
    else
        docker-compose logs -f "$1"
    fi
}

# Function to show service status
show_status() {
    print_color "Service Status:" $BLUE
    if [ "$1" = "microservices" ]; then
        docker-compose -f docker-compose.microservices.yml ps
    else
        docker-compose ps
    fi
}

# Function to rebuild services
rebuild_services() {
    print_color "Rebuilding services..." $BLUE
    if [ "$1" = "microservices" ]; then
        docker-compose -f docker-compose.microservices.yml build --no-cache
    else
        docker-compose build --no-cache
    fi
    print_color "Services rebuilt!" $GREEN
}

# Function to run tests
run_tests() {
    print_color "Running tests for microservices..." $BLUE
    
    # Test ML Prediction Service
    print_color "Testing ML Prediction Service..." $YELLOW
    curl -f http://localhost:8001/health || print_color "ML Service not responding" $RED
    
    # Test NVD Service  
    print_color "Testing NVD Service..." $YELLOW
    curl -f http://localhost:8002/api/v1/health || print_color "NVD Service not responding" $RED
    
    print_color "Tests completed!" $GREEN
}

# Function to show help
show_help() {
    print_color "Quantitative Risk Management - Microservices Manager" $BLUE
    echo ""
    print_color "Usage: $0 <command> [options]" $YELLOW
    echo ""
    print_color "Commands:" $GREEN
    echo "  start-micro     Start only microservices (ML, NVD, Queue, Cache)"
    echo "  start-full      Start complete system (includes legacy backend)"
    echo "  stop            Stop all services"
    echo "  stop-micro      Stop microservices only"
    echo "  status          Show service status"
    echo "  status-micro    Show microservices status"
    echo "  logs <service>  Show logs for specific service"
    echo "  rebuild         Rebuild all services"
    echo "  rebuild-micro   Rebuild microservices only"
    echo "  test            Run health checks on microservices"
    echo "  help            Show this help message"
    echo ""
    print_color "Examples:" $YELLOW
    echo "  $0 start-micro                    # Start microservices"
    echo "  $0 logs nvd-service               # Show NVD service logs"
    echo "  $0 status-micro                   # Show microservices status"
    echo ""
}

# Main script logic
case "${1:-help}" in
    "start-micro")
        check_docker
        check_compose
        start_microservices
        ;;
    "start-full")
        check_docker
        check_compose
        start_full
        ;;
    "stop")
        stop_services "full"
        ;;
    "stop-micro")
        stop_services "microservices"
        ;;
    "status")
        show_status "full"
        ;;
    "status-micro")
        show_status "microservices"
        ;;
    "logs")
        if [ -z "$2" ]; then
            print_color "Please specify a service name" $RED
            exit 1
        fi
        show_logs "$2" "$3"
        ;;
    "rebuild")
        check_docker
        check_compose
        rebuild_services "full"
        ;;
    "rebuild-micro")
        check_docker
        check_compose
        rebuild_services "microservices"
        ;;
    "test")
        run_tests
        ;;
    "help"|*)
        show_help
        ;;
esac
