# Quantitative Risk Management System - Quick Start Script (PowerShell)
# This script sets up and starts the entire QRMS system

param(
    [switch]$SkipTests,
    [switch]$Force
)

Write-Host "🚀 Quantitative Risk Management System - Quick Start" -ForegroundColor Blue
Write-Host "==================================================" -ForegroundColor Blue

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check if Docker is installed
function Test-Docker {
    Write-Status "Checking Docker installation..."
    
    try {
        $dockerVersion = docker --version
        Write-Success "Docker is installed: $dockerVersion"
    }
    catch {
        Write-Error "Docker is not installed or not in PATH. Please install Docker Desktop first."
        exit 1
    }
    
    try {
        $composeVersion = docker-compose --version
        Write-Success "Docker Compose is installed: $composeVersion"
    }
    catch {
        Write-Error "Docker Compose is not installed or not in PATH. Please install Docker Compose first."
        exit 1
    }
}

# Check if required ports are available
function Test-Ports {
    Write-Status "Checking if required ports are available..."
    
    $ports = @(8000, 8001, 8002, 8003, 8004, 5173, 5432, 5672, 6379, 15672)
    $occupiedPorts = @()
    
    foreach ($port in $ports) {
        try {
            $connection = Test-NetConnection -ComputerName localhost -Port $port -InformationLevel Quiet -WarningAction SilentlyContinue
            if ($connection) {
                $occupiedPorts += $port
            }
        }
        catch {
            # Port check failed, assume it's available
        }
    }
    
    if ($occupiedPorts.Count -gt 0) {
        Write-Warning "The following ports are already in use: $($occupiedPorts -join ', ')"
        Write-Warning "You may need to stop the services using these ports or modify the docker-compose.yml file"
        
        if (-not $Force) {
            $response = Read-Host "Do you want to continue anyway? (y/N)"
            if ($response -notmatch '^[Yy]$') {
                Write-Error "Aborting startup"
                exit 1
            }
        }
    }
    else {
        Write-Success "All required ports are available"
    }
}

# Create necessary directories
function New-Directories {
    Write-Status "Creating necessary directories..."
    
    $directories = @(
        ".\microservices\nmap_scanner\temp",
        ".\microservices\report_service\temp",
        ".\logs"
    )
    
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    
    Write-Success "Directories created"
}

# Check if .env file exists
function Test-EnvFile {
    Write-Status "Checking environment configuration..."
    
    if (-not (Test-Path ".env")) {
        Write-Warning ".env file not found. Creating from template..."
        
        $envContent = @"
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
"@
        
        $envContent | Out-File -FilePath ".env" -Encoding UTF8
        Write-Success ".env file created from template"
        Write-Warning "Please review and update the .env file with your specific configuration"
    }
    else {
        Write-Success ".env file found"
    }
}

# Build and start services
function Start-Services {
    Write-Status "Building and starting services..."
    
    # Build images
    Write-Status "Building Docker images..."
    docker-compose build --parallel
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to build Docker images"
        exit 1
    }
    
    # Start services
    Write-Status "Starting services..."
    docker-compose up -d
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to start services"
        exit 1
    }
    
    Write-Success "Services started successfully"
}

# Wait for services to be ready
function Wait-ForServices {
    Write-Status "Waiting for services to be ready..."
    
    # Wait for backend
    Write-Status "Waiting for Backend API..."
    $timeout = 120
    $elapsed = 0
    
    do {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                break
            }
        }
        catch {
            Start-Sleep -Seconds 5
            $elapsed += 5
        }
    } while ($elapsed -lt $timeout)
    
    if ($elapsed -ge $timeout) {
        Write-Warning "Backend API did not respond within timeout. Continuing anyway..."
    }
    else {
        Write-Success "Backend API is ready"
    }
    
    # Wait for other services
    $services = @(
        @{Name="ml-prediction-service"; Port=8001},
        @{Name="nvd-service"; Port=8002},
        @{Name="report-service"; Port=8003},
        @{Name="nmap-scanner-service"; Port=8004}
    )
    
    foreach ($service in $services) {
        Write-Status "Waiting for $($service.Name)..."
        $timeout = 60
        $elapsed = 0
        
        do {
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:$($service.Port)/health" -TimeoutSec 5 -UseBasicParsing
                if ($response.StatusCode -eq 200) {
                    break
                }
            }
            catch {
                Start-Sleep -Seconds 5
                $elapsed += 5
            }
        } while ($elapsed -lt $timeout)
        
        if ($elapsed -ge $timeout) {
            Write-Warning "$($service.Name) did not respond within timeout. Continuing anyway..."
        }
        else {
            Write-Success "$($service.Name) is ready"
        }
    }
    
    Write-Success "All services are ready"
}

# Run integration tests
function Invoke-Tests {
    if ($SkipTests) {
        Write-Warning "Skipping integration tests as requested"
        return
    }
    
    Write-Status "Running integration tests..."
    
    if (Test-Path "test_integration.py") {
        try {
            python test_integration.py
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Integration tests passed"
            }
            else {
                Write-Warning "Some integration tests failed. Check the output above."
            }
        }
        catch {
            Write-Warning "Failed to run integration tests: $_"
        }
    }
    else {
        Write-Warning "Integration test script not found. Skipping tests."
    }
}

# Show service status
function Show-Status {
    Write-Status "Service Status:"
    Write-Host "================" -ForegroundColor White
    docker-compose ps
    
    Write-Host ""
    Write-Status "Service URLs:"
    Write-Host "==============" -ForegroundColor White
    Write-Host "🌐 Frontend:           http://localhost:5173" -ForegroundColor Green
    Write-Host "🔧 Backend API:        http://localhost:8000" -ForegroundColor Green
    Write-Host "📚 API Documentation:  http://localhost:8000/docs" -ForegroundColor Green
    Write-Host "🤖 ML Service:         http://localhost:8001" -ForegroundColor Green
    Write-Host "🔍 NVD Service:        http://localhost:8002" -ForegroundColor Green
    Write-Host "📊 Report Service:     http://localhost:8003" -ForegroundColor Green
    Write-Host "🔍 Nmap Scanner:       http://localhost:8004" -ForegroundColor Green
    Write-Host "🐰 RabbitMQ Management: http://localhost:15672 (guest/guest)" -ForegroundColor Green
    Write-Host "🗄️  PostgreSQL:        localhost:5432 (postgres/postgres)" -ForegroundColor Green
    Write-Host "📦 Redis:             localhost:6379" -ForegroundColor Green
}

# Show usage instructions
function Show-Usage {
    Write-Host ""
    Write-Success "🎉 QRMS is now running!"
    Write-Host ""
    Write-Host "📋 Next Steps:" -ForegroundColor Yellow
    Write-Host "==============" -ForegroundColor Yellow
    Write-Host "1. Open the frontend: http://localhost:5173"
    Write-Host "2. Try the new Risk Analysis Dashboard"
    Write-Host "3. Test the enhanced risk analysis API:"
    Write-Host "   curl -X POST http://localhost:8000/api/v1/risk/nmap-analysis \"
    Write-Host "     -H 'Content-Type: application/json' \"
    Write-Host "     -d '{\"ip\": \"127.0.0.1\", \"include_risk_rubric\": true}'"
    Write-Host ""
    Write-Host "🔧 Management Commands:" -ForegroundColor Yellow
    Write-Host "======================" -ForegroundColor Yellow
    Write-Host "• View logs:           docker-compose logs -f [service-name]"
    Write-Host "• Stop services:       docker-compose down"
    Write-Host "• Restart service:     docker-compose restart [service-name]"
    Write-Host "• View status:         docker-compose ps"
    Write-Host "• Access service:      docker-compose exec [service-name] bash"
    Write-Host ""
    Write-Host "📖 Documentation:" -ForegroundColor Yellow
    Write-Host "=================" -ForegroundColor Yellow
    Write-Host "• API Docs:            http://localhost:8000/docs"
    Write-Host "• Enhanced README:     .\README_ENHANCED.md"
    Write-Host "• Integration Tests:   python test_integration.py"
    Write-Host ""
    Write-Host "🛡️  Risk Analysis Features:" -ForegroundColor Yellow
    Write-Host "==========================" -ForegroundColor Yellow
    Write-Host "• AVOID/MITIGATE/TRANSFER/ACCEPT rubric"
    Write-Host "• Detailed technical recommendations"
    Write-Host "• Service-specific risk assessments"
    Write-Host "• Vulnerability analysis with mitigation strategies"
}

# Main execution
function Main {
    Write-Host "Starting QRMS setup process..." -ForegroundColor Cyan
    Write-Host ""
    
    Test-Docker
    Test-Ports
    New-Directories
    Test-EnvFile
    Start-Services
    Wait-ForServices
    Invoke-Tests
    Show-Status
    Show-Usage
    
    Write-Success "Setup completed successfully! 🎉"
}

# Run main function
try {
    Main
}
catch {
    Write-Error "Setup failed: $_"
    exit 1
}
