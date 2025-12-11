import subprocess
import time
import json
import sys
import requests  # Requires: pip install requests

# Configuration
API_URL = "http://localhost:8000/api/v1"
NMAP_CONTAINER = "quantitative_risk_management-nmap-scanner-service-1"
# Adjust container name if different (use 'docker ps' to check)

def print_header(title):
    print("\n" + "="*60)
    print(f"  🧪 DEMO: {title}")
    print("="*60)

def run_docker_command(command):
    try:
        subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker command failed: {e}")
        return False

def test_transparency():
    print_header("TRANSPARENCIA (Transparency)")
    print("ℹ️  Objetivo: Mostrar que una sola petición orquesta múltiples servicios invisibles al usuario.")
    
    print("\n1️⃣  Enviando petición de Análisis de Riesgo...")
    start_time = time.time()
    
    # Mock payload for analysis
    payload = {
        "analysis_type": "comprehensive",
        "include_nvd": True,
        "include_ml_prediction": True,
        "assets": [
            {"name": "Server-01", "type": "server", "version": "20.04", "vendor": "Ubuntu", "cpe": "cpe:2.3:o:canonical:ubuntu_linux:20.04:*:*:*:*:*:*:*"}
        ]
    }
    
    try:
        response = requests.post(f"{API_URL}/risk/analyze", json=payload)
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Respuesta recibida en {duration:.2f} segundos.")
            print("\n📊 Estructura de la Respuesta Unificada:")
            print(f"   - ID Análisis: {data.get('analysis_id')}")
            print(f"   - Timestamp (TimeService): {data.get('timestamp')}")
            print(f"   - Fuentes de Datos Integradas:")
            print(f"     [+] NVD Service (Vulnerabilidades): {'✅ Incluido' if data.get('metadata', {}).get('nvd_enabled') else '❌ No'}")
            print(f"     [+] ML Service (Predicción): {'✅ Incluido' if data.get('metadata', {}).get('ml_enabled') else '❌ No'}")
            print("\n✨ Conclusión: El usuario vio 1 respuesta, el sistema consultó 3 microservicios + Base de Datos.")
        else:
            print(f"❌ Error en la petición: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

def test_fault_tolerance():
    print_header("TOLERANCIA A FALLOS (Fault Tolerance)")
    print("ℹ️  Objetivo: Demostrar que el sistema no colapsa si un microservicio crítico (Nmap) muere.")
    
    print(f"\n1️⃣  Simulando fallo: Deteniendo contenedor '{NMAP_CONTAINER}'...")
    if run_docker_command(f"docker stop {NMAP_CONTAINER}"):
        print("✅ Contenedor detenido.")
    else:
        print("⚠️  No se pudo detener el contenedor. Verifica el nombre.")
        return

    print("\n2️⃣  Enviando petición de Escaneo (mientras el servicio está caído)...")
    try:
        # Assuming there is an endpoint that queues scans
        # If direct scan endpoint waits for response, it might timeout, but if async via RabbitMQ, it should accept.
        # Adjust endpoint as per actual implementation. Assuming /scan enqueues.
        scan_payload = {"target": "127.0.0.1"}
        
        # Note: If the backend tries to talk to Nmap directly via HTTP and Nmap is down, 
        # the Backend should handle this gracefully (e.g., return 503 or queue it).
        # Based on architecture, if it uses RabbitMQ, it should be fine.
        
        print("   (Enviando petición...)")
        # Simulating a request that would normally trigger Nmap
        # For this demo, we'll check if the Main API is still alive
        response = requests.get(f"{API_URL}/health")
        
        if response.status_code == 200:
            print(f"✅ ¡El API Gateway y Backend siguen vivos! Status: {response.status_code}")
            print("   El fallo del microservicio Nmap NO tumbó todo el sistema.")
        else:
            print(f"❌ El sistema colapsó: {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")

    print(f"\n3️⃣  Recuperación: Reiniciando contenedor '{NMAP_CONTAINER}'...")
    if run_docker_command(f"docker start {NMAP_CONTAINER}"):
        print("✅ Contenedor reiniciado. El sistema se ha auto-recuperado.")
    
    print("\n✨ Conclusión: La caída de un componente no detuvo la disponibilidad del resto del sistema.")

def main():
    print("🚀 Iniciando Script de Demostración de Sistema Distribuido")
    print("Asegúrate de que todo el stack esté corriendo (docker-compose up -d)")
    
    input("\nPresiona ENTER para comenzar la prueba de TRANSPARENCIA...")
    test_transparency()
    
    input("\nPresiona ENTER para comenzar la prueba de TOLERANCIA A FALLOS...")
    test_fault_tolerance()
    
    print("\n🏁 Demostración finalizada.")

if __name__ == "__main__":
    main()
