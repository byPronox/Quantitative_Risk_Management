# Microservices Management Script for Quantitative Risk Management System
# PowerShell version for Windows

param(
    [Parameter(Position=0)]
    [string]$Command = "help",
    
    [Parameter(Position=1)]
    [string]$Service = "",
    
    [Parameter(Position=2)]
    [string]$Mode = ""
)

# Function to write colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Function to check if Docker is running
function Test-Docker {
    try {
        docker info | Out-Null
        return $true
    }
    catch {
        Write-ColorOutput "Docker is not running. Please start Docker first." "Red"
        exit 1
    }
}

# Function to check if docker-compose is available
function Test-DockerCompose {
    try {
        docker-compose version | Out-Null
        return $true
    }
    catch {
        Write-ColorOutput "docker-compose not found. Please install docker-compose." "Red"
        exit 1
    }
}

# Function to start microservices
function Start-Microservices {
    Write-ColorOutput "Starting microservices..." "Blue"
    docker-compose -f docker-compose.microservices.yml up -d
    Write-ColorOutput "Microservices started successfully!" "Green"
    Write-ColorOutput "Services available at:" "Yellow"
    Write-ColorOutput "  - ML Prediction Service: http://localhost:8001" "Yellow"
    Write-ColorOutput "  - NVD Service: http://localhost:8002" "Yellow"
    Write-ColorOutput "  - RabbitMQ Management: http://localhost:15672" "Yellow"
    Write-ColorOutput "  - Redis: localhost:6379" "Yellow"
}

# Function to start full system
function Start-FullSystem {
    Write-ColorOutput "Starting full system..." "Blue"
    docker-compose up -d
    Write-ColorOutput "Full system started successfully!" "Green"
    Write-ColorOutput "Services available at:" "Yellow"
    Write-ColorOutput "  - Frontend: http://localhost:5173" "Yellow"
    Write-ColorOutput "  - Backend (Legacy): http://localhost:8000" "Yellow"
    Write-ColorOutput "  - ML Prediction Service: http://localhost:8001" "Yellow"
    Write-ColorOutput "  - NVD Service: http://localhost:8002" "Yellow"
    Write-ColorOutput "  - Database: localhost:5432" "Yellow"
    Write-ColorOutput "  - RabbitMQ Management: http://localhost:15672" "Yellow"
    Write-ColorOutput "  - Redis: localhost:6379" "Yellow"
}

# Function to stop services
function Stop-Services {
    param([string]$Type)
    
    Write-ColorOutput "Stopping services..." "Blue"
    if ($Type -eq "microservices") {
        docker-compose -f docker-compose.microservices.yml down
    } else {
        docker-compose down
    }
    Write-ColorOutput "Services stopped!" "Green"
}

# Function to show logs
function Show-Logs {
    param([string]$ServiceName, [string]$Type)
    
    if ($Type -eq "microservices") {
        docker-compose -f docker-compose.microservices.yml logs -f $ServiceName
    } else {
        docker-compose logs -f $ServiceName
    }
}

# Function to show service status
function Show-Status {
    param([string]$Type)
    
    Write-ColorOutput "Service Status:" "Blue"
    if ($Type -eq "microservices") {
        docker-compose -f docker-compose.microservices.yml ps
    } else {
        docker-compose ps
    }
}

# Function to rebuild services
function Rebuild-Services {
    param([string]$Type)
    
    Write-ColorOutput "Rebuilding services..." "Blue"
    if ($Type -eq "microservices") {
        docker-compose -f docker-compose.microservices.yml build --no-cache
    } else {
        docker-compose build --no-cache
    }
    Write-ColorOutput "Services rebuilt!" "Green"
}

# Function to run tests
function Run-Tests {
    Write-ColorOutput "Running tests for microservices..." "Blue"
    
    # Test ML Prediction Service
    Write-ColorOutput "Testing ML Prediction Service..." "Yellow"
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8001/health" -TimeoutSec 10
        Write-ColorOutput "ML Service: OK" "Green"
    }
    catch {
        Write-ColorOutput "ML Service not responding" "Red"
    }
    
    # Test NVD Service  
    Write-ColorOutput "Testing NVD Service..." "Yellow"
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8002/api/v1/health" -TimeoutSec 10
        Write-ColorOutput "NVD Service: OK" "Green"
    }
    catch {
        Write-ColorOutput "NVD Service not responding" "Red"
    }
    
    Write-ColorOutput "Tests completed!" "Green"
}

# Function to show help
function Show-Help {
    Write-ColorOutput "Quantitative Risk Management - Microservices Manager" "Blue"
    Write-Host ""
    Write-ColorOutput "Usage: .\microservices.ps1 <command> [options]" "Yellow"
    Write-Host ""
    Write-ColorOutput "Commands:" "Green"
    Write-Host "  start-micro     Start only microservices (ML, NVD, Queue, Cache)"
    Write-Host "  start-full      Start complete system (includes legacy backend)"
    Write-Host "  stop            Stop all services"
    Write-Host "  stop-micro      Stop microservices only"
    Write-Host "  status          Show service status"
    Write-Host "  status-micro    Show microservices status"
    Write-Host "  logs <service>  Show logs for specific service"
    Write-Host "  rebuild         Rebuild all services"
    Write-Host "  rebuild-micro   Rebuild microservices only"
    Write-Host "  test            Run health checks on microservices"
    Write-Host "  help            Show this help message"
    Write-Host ""
    Write-ColorOutput "Examples:" "Yellow"
    Write-Host "  .\microservices.ps1 start-micro                    # Start microservices"
    Write-Host "  .\microservices.ps1 logs nvd-service               # Show NVD service logs"
    Write-Host "  .\microservices.ps1 status-micro                   # Show microservices status"
    Write-Host ""
}

# Main script logic
switch ($Command.ToLower()) {
    "start-micro" {
        Test-Docker
        Test-DockerCompose
        Start-Microservices
    }
    "start-full" {
        Test-Docker
        Test-DockerCompose
        Start-FullSystem
    }
    "stop" {
        Stop-Services "full"
    }
    "stop-micro" {
        Stop-Services "microservices"
    }
    "status" {
        Show-Status "full"
    }
    "status-micro" {
        Show-Status "microservices"
    }
    "logs" {
        if ([string]::IsNullOrEmpty($Service)) {
            Write-ColorOutput "Please specify a service name" "Red"
            exit 1
        }
        Show-Logs $Service $Mode
    }
    "rebuild" {
        Test-Docker
        Test-DockerCompose
        Rebuild-Services "full"
    }
    "rebuild-micro" {
        Test-Docker
        Test-DockerCompose
        Rebuild-Services "microservices"
    }
    "test" {
        Run-Tests
    }
    default {
        Show-Help
    }
}
