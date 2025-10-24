#!/usr/bin/env python3
"""
Test rápido de conectividad para verificar configuraciones básicas
"""

import os
import requests
import json

def test_kong_gateway():
    """Test rápido de Kong Gateway"""
    print("🔍 Probando Kong Gateway...")
    try:
        # Cargar variables del .env
        with open('.env', 'r') as f:
            for line in f:
                if 'KONG_PROXY_URL=' in line:
                    kong_url = line.split('=')[1].strip()
                    break
        
        print(f"URL Kong: {kong_url}")
        
        # Test básico
        response = requests.get(f"{kong_url}/", timeout=10)
        print(f"Status Kong: {response.status_code}")
        
        if response.status_code in [200, 404]:  # 404 es normal si no hay endpoint raíz
            print("✅ Kong Gateway responde")
            return True
        else:
            print(f"⚠️ Kong responde con status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error con Kong: {e}")
        return False

def test_nvd_api():
    """Test rápido de NVD API"""
    print("\n🔍 Probando NVD API...")
    try:
        # Cargar variables
        nvd_key = None
        kong_url = None
        
        with open('.env', 'r') as f:
            for line in f:
                if 'NVD_API_KEY=' in line:
                    nvd_key = line.split('=')[1].strip()
                elif 'KONG_PROXY_URL=' in line:
                    kong_url = line.split('=')[1].strip()
        
        if not nvd_key or not kong_url:
            print("❌ Variables NVD_API_KEY o KONG_PROXY_URL no encontradas")
            return False
        
        print(f"NVD Key: {nvd_key[:10]}...")
        print(f"Kong URL: {kong_url}")
        
        # Test NVD
        headers = {'apiKey': nvd_key}
        test_url = f"{kong_url}/nvd/v2/cves"
        
        response = requests.get(test_url, headers=headers, timeout=15)
        print(f"Status NVD: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ NVD API funciona - {data.get('totalResults', 0)} CVEs disponibles")
            return True
        elif response.status_code == 403:
            print("⚠️ API Key inválida o expirada")
            return False
        else:
            print(f"⚠️ NVD responde con status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error con NVD: {e}")
        return False

def test_docker_services():
    """Test rápido de servicios Docker"""
    print("\n🔍 Verificando servicios Docker...")
    
    services = [
        ("Backend", "http://localhost:8000/health"),
        ("ML Service", "http://localhost:8001/health"),
        ("NVD Service", "http://localhost:8002/health"),
        ("Report Service", "http://localhost:8003/health"),
        ("Nmap Service", "http://localhost:8004/health"),
        ("Frontend", "http://localhost:5173")
    ]
    
    results = []
    for name, url in services:
        try:
            response = requests.get(url, timeout=3)
            status = "✅" if response.status_code == 200 else "⚠️"
            print(f"{status} {name}: {response.status_code}")
            results.append(True if response.status_code == 200 else False)
        except:
            print(f"❌ {name}: No accesible")
            results.append(False)
    
    return any(results)

def main():
    print("🚀 TEST RÁPIDO DE CONFIGURACIÓN")
    print("="*50)
    
    # Test Kong
    kong_ok = test_kong_gateway()
    
    # Test NVD
    nvd_ok = test_nvd_api()
    
    # Test Docker services
    docker_ok = test_docker_services()
    
    print("\n" + "="*50)
    print("📊 RESUMEN:")
    print(f"Kong Gateway: {'✅' if kong_ok else '❌'}")
    print(f"NVD API: {'✅' if nvd_ok else '❌'}")
    print(f"Servicios Docker: {'✅' if docker_ok else '❌'}")
    
    if kong_ok and nvd_ok and docker_ok:
        print("\n🎉 ¡Todo funciona correctamente!")
    else:
        print("\n⚠️ Algunos servicios tienen problemas")

if __name__ == "__main__":
    main()
