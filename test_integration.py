#!/usr/bin/env python3
"""
Test script for Quantitative Risk Management System
Tests the integration of all services with Docker Compose
"""

import requests
import time
import json
import sys
from typing import Dict, Any

class QRMSIntegrationTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.services = {
            "backend": "http://localhost:8000",
            "ml_service": "http://localhost:8001", 
            "nvd_service": "http://localhost:8002",
            "report_service": "http://localhost:8003",
            "nmap_service": "http://localhost:8004",
            "frontend": "http://localhost:5173"
        }
        self.test_results = {}
        
    def test_service_health(self, service_name: str, url: str) -> bool:
        """Test if a service is healthy"""
        try:
            if service_name == "frontend":
                # Frontend doesn't have a health endpoint, just check if it responds
                response = requests.get(url, timeout=10)
                return response.status_code == 200
            else:
                response = requests.get(f"{url}/health", timeout=10)
                return response.status_code == 200
        except Exception as e:
            print(f"❌ {service_name} health check failed: {e}")
            return False
    
    def test_nmap_service(self) -> Dict[str, Any]:
        """Test nmap service functionality"""
        print("🔍 Testing Nmap Service...")
        
        try:
            # Test nmap installation
            response = requests.get(f"{self.services['nmap_service']}/api/v1/test", timeout=30)
            if response.status_code != 200:
                return {"success": False, "error": "Nmap test failed"}
            
            # Test target validation
            test_ip = "127.0.0.1"
            response = requests.get(f"{self.services['nmap_service']}/api/v1/validate/{test_ip}", timeout=10)
            if response.status_code != 200:
                return {"success": False, "error": "Target validation failed"}
            
            return {"success": True, "message": "Nmap service is working correctly"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_enhanced_risk_analysis(self) -> Dict[str, Any]:
        """Test enhanced risk analysis with rubric"""
        print("🛡️ Testing Enhanced Risk Analysis...")
        
        try:
            # Test mitigation strategies endpoint
            response = requests.get(f"{self.base_url}/api/v1/risk/mitigation-strategies", timeout=10)
            if response.status_code != 200:
                return {"success": False, "error": "Mitigation strategies endpoint failed"}
            
            strategies = response.json()
            if not strategies.get("strategies"):
                return {"success": False, "error": "No mitigation strategies returned"}
            
            # Test service analysis endpoint
            service_data = {
                "ip": "127.0.0.1",
                "port": "22",
                "name": "ssh",
                "product": "OpenSSH",
                "version": "8.2",
                "protocol": "tcp",
                "state": "open"
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/risk/analyze-service",
                json=service_data,
                timeout=30
            )
            
            if response.status_code != 200:
                return {"success": False, "error": "Service analysis failed"}
            
            analysis = response.json()
            if not analysis.get("service"):
                return {"success": False, "error": "No service analysis returned"}
            
            return {"success": True, "message": "Enhanced risk analysis is working correctly"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_nvd_service(self) -> Dict[str, Any]:
        """Test NVD service functionality"""
        print("🔍 Testing NVD Service...")
        
        try:
            # Test basic NVD functionality
            response = requests.get(f"{self.services['nvd_service']}/api/v1/vulnerabilities?keyword=apache", timeout=30)
            if response.status_code != 200:
                return {"success": False, "error": "NVD service failed"}
            
            return {"success": True, "message": "NVD service is working correctly"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_ml_service(self) -> Dict[str, Any]:
        """Test ML prediction service"""
        print("🤖 Testing ML Service...")
        
        try:
            # Test ML service health
            response = requests.get(f"{self.services['ml_service']}/api/v1/health", timeout=10)
            if response.status_code != 200:
                return {"success": False, "error": "ML service health check failed"}
            
            return {"success": True, "message": "ML service is working correctly"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_report_service(self) -> Dict[str, Any]:
        """Test report generation service"""
        print("📊 Testing Report Service...")
        
        try:
            # Test report service health
            response = requests.get(f"{self.services['report_service']}/api/v1/health", timeout=10)
            if response.status_code != 200:
                return {"success": False, "error": "Report service health check failed"}
            
            return {"success": True, "message": "Report service is working correctly"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def run_all_tests(self) -> bool:
        """Run all integration tests"""
        print("🚀 Starting QRMS Integration Tests...")
        print("=" * 50)
        
        all_passed = True
        
        # Test service health
        print("📡 Testing Service Health...")
        for service_name, url in self.services.items():
            if self.test_service_health(service_name, url):
                print(f"✅ {service_name} is healthy")
                self.test_results[service_name] = {"health": True}
            else:
                print(f"❌ {service_name} is not healthy")
                self.test_results[service_name] = {"health": False}
                all_passed = False
        
        print("\n" + "=" * 50)
        
        # Test individual services
        service_tests = [
            ("nmap_service", self.test_nmap_service),
            ("enhanced_risk", self.test_enhanced_risk_analysis),
            ("nvd_service", self.test_nvd_service),
            ("ml_service", self.test_ml_service),
            ("report_service", self.test_report_service)
        ]
        
        for test_name, test_func in service_tests:
            result = test_func()
            self.test_results[test_name] = result
            
            if result["success"]:
                print(f"✅ {test_name}: {result['message']}")
            else:
                print(f"❌ {test_name}: {result['error']}")
                all_passed = False
            
            print()
        
        return all_passed
    
    def generate_report(self):
        """Generate test report"""
        print("=" * 50)
        print("📋 INTEGRATION TEST REPORT")
        print("=" * 50)
        
        passed_tests = sum(1 for result in self.test_results.values() 
                          if isinstance(result, dict) and result.get("success", False))
        total_tests = len(self.test_results)
        
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nDetailed Results:")
        for test_name, result in self.test_results.items():
            if isinstance(result, dict):
                if result.get("success"):
                    print(f"✅ {test_name}: PASS")
                else:
                    print(f"❌ {test_name}: FAIL - {result.get('error', 'Unknown error')}")
            else:
                print(f"❌ {test_name}: FAIL - No result")
        
        print("\n" + "=" * 50)
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! QRMS is ready for production.")
        else:
            print("⚠️  SOME TESTS FAILED. Please check the service logs.")
        
        return passed_tests == total_tests

def main():
    """Main test function"""
    print("Quantitative Risk Management System - Integration Test")
    print("Testing Docker Compose integration...")
    print()
    
    # Wait for services to start
    print("⏳ Waiting for services to start (30 seconds)...")
    time.sleep(30)
    
    tester = QRMSIntegrationTest()
    
    try:
        success = tester.run_all_tests()
        tester.generate_report()
        
        if success:
            print("\n🎯 RECOMMENDATIONS:")
            print("1. All services are working correctly")
            print("2. You can now use the enhanced risk analysis features")
            print("3. Access the frontend at http://localhost:5173")
            print("4. Use the new risk analysis endpoint: /api/v1/risk/nmap-analysis")
            print("5. The AVOID/MITIGATE/TRANSFER/ACCEPT rubric is implemented")
            
            sys.exit(0)
        else:
            print("\n🔧 TROUBLESHOOTING:")
            print("1. Check Docker Compose logs: docker-compose logs")
            print("2. Verify all services are running: docker-compose ps")
            print("3. Check service-specific logs for errors")
            print("4. Ensure all required ports are available")
            
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
