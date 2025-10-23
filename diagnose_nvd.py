#!/usr/bin/env python3
"""
NVD System Diagnostic Script
This script helps diagnose issues with the NVD vulnerability system
"""
import asyncio
import httpx
import json
import os
from datetime import datetime

# Configuration
KONG_URL = "https://kong-b27b67aff4usnsp19.kongcloud.dev"
NVD_SERVICE_URL = "http://nvd-service:8002"
BACKEND_URL = "http://backend:8000"

async def test_kong_connection():
    """Test Kong Gateway connection"""
    print("🔍 Testing Kong Gateway connection...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{KONG_URL}/nvd/cves/2.0", params={"resultsPerPage": 1})
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Kong Gateway: OK - Found {data.get('totalResults', 0)} vulnerabilities")
                return True
            else:
                print(f"❌ Kong Gateway: HTTP {response.status_code} - {response.text}")
                return False
    except Exception as e:
        print(f"❌ Kong Gateway: Connection failed - {e}")
        return False

async def test_nvd_service():
    """Test NVD microservice"""
    print("🔍 Testing NVD microservice...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{NVD_SERVICE_URL}/api/v1/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ NVD Service: OK - {data.get('status', 'unknown')}")
                return True
            else:
                print(f"❌ NVD Service: HTTP {response.status_code} - {response.text}")
                return False
    except Exception as e:
        print(f"❌ NVD Service: Connection failed - {e}")
        return False

async def test_backend_nvd():
    """Test backend NVD endpoints"""
    print("🔍 Testing Backend NVD endpoints...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test vulnerabilities endpoint
            response = await client.get(f"{BACKEND_URL}/nvd/vulnerabilities", params={"keyword": "apache"})
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Backend NVD: OK - Found {data.get('totalResults', 0)} vulnerabilities")
                return True
            else:
                print(f"❌ Backend NVD: HTTP {response.status_code} - {response.text}")
                return False
    except Exception as e:
        print(f"❌ Backend NVD: Connection failed - {e}")
        return False

async def test_queue_status():
    """Test queue status"""
    print("🔍 Testing Queue status...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{NVD_SERVICE_URL}/api/v1/queue/status")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Queue Status: OK - Pending: {data.get('pending', 0)}, Completed: {data.get('completed', 0)}")
                return True
            else:
                print(f"❌ Queue Status: HTTP {response.status_code} - {response.text}")
                return False
    except Exception as e:
        print(f"❌ Queue Status: Connection failed - {e}")
        return False

async def test_consumer_status():
    """Test consumer status"""
    print("🔍 Testing Consumer status...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{NVD_SERVICE_URL}/api/v1/queue/status")
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                print(f"✅ Consumer Status: {status}")
                return True
            else:
                print(f"❌ Consumer Status: HTTP {response.status_code} - {response.text}")
                return False
    except Exception as e:
        print(f"❌ Consumer Status: Connection failed - {e}")
        return False

async def test_vulnerability_search():
    """Test vulnerability search with a known software"""
    print("🔍 Testing vulnerability search...")
    test_keywords = ["apache", "mysql", "nginx"]
    
    for keyword in test_keywords:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(f"{KONG_URL}/nvd/cves/2.0", params={
                    "keywordSearch": keyword,
                    "resultsPerPage": 5
                })
                if response.status_code == 200:
                    data = response.json()
                    total = data.get('totalResults', 0)
                    print(f"✅ Search '{keyword}': Found {total} vulnerabilities")
                    if total > 0:
                        return True
                else:
                    print(f"❌ Search '{keyword}': HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Search '{keyword}': {e}")
    
    return False

async def main():
    """Run all diagnostic tests"""
    print("🚀 NVD System Diagnostic Tool")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    tests = [
        ("Kong Gateway", test_kong_connection),
        ("NVD Service", test_nvd_service),
        ("Backend NVD", test_backend_nvd),
        ("Queue Status", test_queue_status),
        ("Consumer Status", test_consumer_status),
        ("Vulnerability Search", test_vulnerability_search),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name}: Exception - {e}")
            results[test_name] = False
        print()
    
    # Summary
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All systems are working correctly!")
    else:
        print("⚠️  Some systems need attention. Check the failed tests above.")
        
        # Recommendations
        print("\n🔧 RECOMMENDATIONS:")
        if not results.get("Kong Gateway", False):
            print("- Check Kong Gateway URL configuration")
            print("- Verify Kong Gateway is running and accessible")
        if not results.get("NVD Service", False):
            print("- Check NVD microservice is running")
            print("- Verify NVD service configuration")
        if not results.get("Vulnerability Search", False):
            print("- Check NVD API key configuration")
            print("- Verify Kong Gateway routing to NVD API")
        if not results.get("Queue Status", False):
            print("- Check RabbitMQ connection")
            print("- Verify queue configuration")

if __name__ == "__main__":
    asyncio.run(main())
