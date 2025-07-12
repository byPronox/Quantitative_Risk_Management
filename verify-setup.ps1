# Quantitative Risk Management System - Verification Script
# This script verifies that the microservices architecture is properly set up

param(
    [Parameter(Mandatory=$false)]
    [switch]$Verbose = $false
)

function Write-Status {
    param(
        [string]$Message,
        [string]$Status = "INFO",
        [string]$Color = "White"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Status] $Message" -ForegroundColor $Color
}

function Test-FileExists {
    param([string]$Path, [string]$Description)
    
    if (Test-Path $Path) {
        Write-Status "✓ $Description exists" "OK" "Green"
        return $true
    } else {
        Write-Status "✗ $Description missing: $Path" "ERROR" "Red"
        return $false
    }
}

function Test-DirectoryStructure {
    Write-Status "Checking microservices directory structure..." "INFO" "Blue"
    
    $requiredPaths = @(
        @{ Path = "microservices\ml_prediction_service\app\main.py"; Desc = "ML Prediction Service main.py" },
        @{ Path = "microservices\ml_prediction_service\Dockerfile"; Desc = "ML Prediction Service Dockerfile" },
        @{ Path = "microservices\ml_prediction_service\requirements.txt"; Desc = "ML Prediction Service requirements.txt" },
        @{ Path = "microservices\ml_prediction_service\app\models\rf_cicids2017_model.pkl"; Desc = "CICIDS2017 Model" },
        @{ Path = "microservices\ml_prediction_service\app\models\isolation_forest_model.pkl"; Desc = "Isolation Forest Model" },
        @{ Path = "microservices\nvd_service\app\main.py"; Desc = "NVD Service main.py" },
        @{ Path = "microservices\nvd_service\Dockerfile"; Desc = "NVD Service Dockerfile" },
        @{ Path = "microservices\nvd_service\requirements.txt"; Desc = "NVD Service requirements.txt" },
        @{ Path = "backend\app\main.py"; Desc = "API Gateway main.py" },
        @{ Path = "backend\app\middleware\kong_middleware.py"; Desc = "Kong Middleware" },
        @{ Path = "docker-compose.microservices.yml"; Desc = "Microservices Docker Compose" },
        @{ Path = "docker-compose.yml"; Desc = "Full System Docker Compose" },
        @{ Path = "microservices.ps1"; Desc = "PowerShell Management Script" },
        @{ Path = "microservices.sh"; Desc = "Bash Management Script" }
    )
    
    $allExists = $true
    foreach ($item in $requiredPaths) {
        if (-not (Test-FileExists $item.Path $item.Desc)) {
            $allExists = $false
        }
    }
    
    return $allExists
}

function Test-ConfigurationFiles {
    Write-Status "Checking configuration files..." "INFO" "Blue"
    
    $configFiles = @(".env.example", ".env.development")
    $allValid = $true
    
    foreach ($file in $configFiles) {
        if (Test-Path $file) {
            $content = Get-Content $file -Raw
            
            # Check for required environment variables
            $requiredVars = @(
                "NVD_API_KEY",
                "KONG_PROXY_URL", 
                "RABBITMQ_HOST",
                "ML_SERVICE_URL",
                "NVD_SERVICE_URL"
            )
            
            foreach ($var in $requiredVars) {
                if ($content -match $var) {
                    if ($Verbose) {
                        Write-Status "✓ $var found in $file" "OK" "Green"
                    }
                } else {
                    Write-Status "✗ $var missing in $file" "WARNING" "Yellow"
                    $allValid = $false
                }
            }
        }
    }
    
    return $allValid
}

function Test-DockerComposeValid {
    Write-Status "Validating Docker Compose files..." "INFO" "Blue"
    
    try {
        # Test microservices compose
        $output = docker-compose -f docker-compose.microservices.yml config 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Status "✓ docker-compose.microservices.yml is valid" "OK" "Green"
        } else {
            Write-Status "✗ docker-compose.microservices.yml has errors: $output" "ERROR" "Red"
            return $false
        }
        
        # Test full system compose
        $output = docker-compose -f docker-compose.yml config 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Status "✓ docker-compose.yml is valid" "OK" "Green"
        } else {
            Write-Status "✗ docker-compose.yml has errors: $output" "ERROR" "Red"
            return $false
        }
        
        return $true
        
    } catch {
        Write-Status "✗ Docker Compose validation failed: $($_.Exception.Message)" "ERROR" "Red"
        return $false
    }
}

function Show-Summary {
    param([bool]$AllPassed)
    
    Write-Status "" 
    Write-Status "=== VERIFICATION SUMMARY ===" "INFO" "Cyan"
    
    if ($AllPassed) {
        Write-Status "🎉 All checks passed! Your microservices architecture is ready!" "SUCCESS" "Green"
        Write-Status ""
        Write-Status "Next steps:" "INFO" "Yellow"
        Write-Status "1. Run: .\microservices.ps1 start-micro" "INFO" "White"
        Write-Status "2. Test: .\microservices.ps1 test" "INFO" "White"
        Write-Status "3. View logs: .\microservices.ps1 logs <service-name>" "INFO" "White"
    } else {
        Write-Status "❌ Some checks failed. Please review the errors above." "ERROR" "Red"
        Write-Status "Fix the issues and run this script again." "INFO" "Yellow"
    }
    
    Write-Status ""
}

# Main execution
Write-Status "Starting Quantitative Risk Management System verification..." "INFO" "Cyan"
Write-Status ""

$checks = @(
    @{ Name = "Directory Structure"; Test = { Test-DirectoryStructure } },
    @{ Name = "Configuration Files"; Test = { Test-ConfigurationFiles } },
    @{ Name = "Docker Compose Files"; Test = { Test-DockerComposeValid } }
)

$allPassed = $true

foreach ($check in $checks) {
    Write-Status "Running check: $($check.Name)" "INFO" "Blue"
    $result = & $check.Test
    
    if ($result) {
        Write-Status "✓ $($check.Name) check passed" "OK" "Green"
    } else {
        Write-Status "✗ $($check.Name) check failed" "ERROR" "Red"
        $allPassed = $false
    }
    Write-Status ""
}

Show-Summary $allPassed

if ($allPassed) {
    exit 0
} else {
    exit 1
}
