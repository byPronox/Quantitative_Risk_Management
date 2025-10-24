#!/usr/bin/env python3
"""
Health Check Script for Quantitative Risk Management System
Verifica la conectividad y funcionamiento de todos los servicios configurados
"""

import os
import sys
import requests
import psycopg2
import pika
import json
from datetime import datetime
from urllib.parse import urlparse
import time

class HealthChecker:
    def __init__(self):
        self.results = []
        self.load_env_vars()
        
    def load_env_vars(self):
        """Carga las variables de entorno desde .env"""
        try:
            with open('.env', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
        except FileNotFoundError:
            print("❌ Archivo .env no encontrado")
            sys.exit(1)
    
    def log_result(self, service, status, message, details=None):
        """Registra el resultado de una verificación"""
        result = {
            'service': service,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        self.results.append(result)
        
        # Emoji para el status
        emoji = "✅" if status == "OK" else "❌" if status == "ERROR" else "⚠️"
        print(f"{emoji} {service}: {message}")
        if details:
            print(f"   Detalles: {details}")
    
    def check_kong_gateway(self):
        """Verifica conectividad con Kong Gateway"""
        try:
            kong_url = os.getenv('KONG_PROXY_URL')
            if not kong_url:
                self.log_result("Kong Gateway", "ERROR", "KONG_PROXY_URL no configurado")
                return
            
            # Test básico de conectividad
            response = requests.get(f"{kong_url}/health", timeout=10)
            if response.status_code == 200:
                self.log_result("Kong Gateway", "OK", f"Conectividad exitosa - Status: {response.status_code}")
            else:
                self.log_result("Kong Gateway", "WARNING", f"Respuesta inesperada - Status: {response.status_code}")
                
        except requests.exceptions.Timeout:
            self.log_result("Kong Gateway", "ERROR", "Timeout - Kong Gateway no responde")
        except requests.exceptions.ConnectionError:
            self.log_result("Kong Gateway", "ERROR", "Error de conexión - Kong Gateway no accesible")
        except Exception as e:
            self.log_result("Kong Gateway", "ERROR", f"Error inesperado: {str(e)}")
    
    def check_postgresql(self):
        """Verifica conexión a PostgreSQL"""
        try:
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                self.log_result("PostgreSQL", "ERROR", "DATABASE_URL no configurado")
                return
            
            # Parsear URL de conexión
            parsed = urlparse(db_url)
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port,
                database=parsed.path[1:],
                user=parsed.username,
                password=parsed.password
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            self.log_result("PostgreSQL", "OK", f"Conexión exitosa - {version}")
            
        except psycopg2.OperationalError as e:
            self.log_result("PostgreSQL", "ERROR", f"Error de conexión: {str(e)}")
        except Exception as e:
            self.log_result("PostgreSQL", "ERROR", f"Error inesperado: {str(e)}")
    
    def check_rabbitmq(self):
        """Verifica conexión a RabbitMQ"""
        try:
            rabbitmq_url = os.getenv('RABBITMQ_URL')
            if not rabbitmq_url:
                self.log_result("RabbitMQ", "ERROR", "RABBITMQ_URL no configurado")
                return
            
            # Parsear URL de RabbitMQ
            parsed = urlparse(rabbitmq_url)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=parsed.hostname,
                    port=parsed.port,
                    virtual_host=parsed.path[1:] if parsed.path else '/',
                    credentials=pika.PlainCredentials(parsed.username, parsed.password)
                )
            )
            
            channel = connection.channel()
            channel.queue_declare(queue=os.getenv('RABBITMQ_QUEUE', 'nvd_analysis_queue'), passive=True)
            
            connection.close()
            
            self.log_result("RabbitMQ", "OK", "Conexión y cola verificadas exitosamente")
            
        except pika.exceptions.AMQPConnectionError as e:
            self.log_result("RabbitMQ", "ERROR", f"Error de conexión AMQP: {str(e)}")
        except Exception as e:
            self.log_result("RabbitMQ", "ERROR", f"Error inesperado: {str(e)}")
    
    def check_nvd_api(self):
        """Verifica API de NVD a través de Kong"""
        try:
            nvd_api_key = os.getenv('NVD_API_KEY')
            kong_url = os.getenv('KONG_PROXY_URL')
            
            if not nvd_api_key or not kong_url:
                self.log_result("NVD API", "ERROR", "NVD_API_KEY o KONG_PROXY_URL no configurados")
                return
            
            # Test con endpoint de NVD a través de Kong
            headers = {
                'apiKey': nvd_api_key,
                'Content-Type': 'application/json'
            }
            
            # Endpoint de prueba para NVD
            test_url = f"{kong_url}/nvd/v2/cves"
            response = requests.get(test_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                total_results = data.get('totalResults', 0)
                self.log_result("NVD API", "OK", f"API funcionando - {total_results} CVEs disponibles")
            elif response.status_code == 403:
                self.log_result("NVD API", "WARNING", "API Key inválida o expirada")
            else:
                self.log_result("NVD API", "WARNING", f"Respuesta inesperada - Status: {response.status_code}")
                
        except requests.exceptions.Timeout:
            self.log_result("NVD API", "ERROR", "Timeout - NVD API no responde")
        except requests.exceptions.ConnectionError:
            self.log_result("NVD API", "ERROR", "Error de conexión - NVD API no accesible")
        except Exception as e:
            self.log_result("NVD API", "ERROR", f"Error inesperado: {str(e)}")
    
    def check_microservices(self):
        """Verifica que los microservicios estén funcionando"""
        services = [
            ("ML Prediction Service", "http://localhost:8001/health"),
            ("NVD Service", "http://localhost:8002/health"),
            ("Report Service", "http://localhost:8003/health"),
            ("Nmap Scanner Service", "http://localhost:8004/health")
        ]
        
        for service_name, url in services:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    self.log_result(service_name, "OK", f"Servicio funcionando - Status: {response.status_code}")
                else:
                    self.log_result(service_name, "WARNING", f"Respuesta inesperada - Status: {response.status_code}")
            except requests.exceptions.ConnectionError:
                self.log_result(service_name, "ERROR", "Servicio no accesible - ¿Está ejecutándose?")
            except Exception as e:
                self.log_result(service_name, "ERROR", f"Error: {str(e)}")
    
    def check_frontend(self):
        """Verifica que el frontend esté accesible"""
        try:
            frontend_url = "http://localhost:5173"
            response = requests.get(frontend_url, timeout=5)
            if response.status_code == 200:
                self.log_result("Frontend", "OK", "Frontend accesible")
            else:
                self.log_result("Frontend", "WARNING", f"Respuesta inesperada - Status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.log_result("Frontend", "ERROR", "Frontend no accesible - ¿Está ejecutándose?")
        except Exception as e:
            self.log_result("Frontend", "ERROR", f"Error: {str(e)}")
    
    def generate_report(self):
        """Genera un reporte de salud del sistema"""
        print("\n" + "="*60)
        print("📊 REPORTE DE SALUD DEL SISTEMA")
        print("="*60)
        
        total_checks = len(self.results)
        ok_checks = len([r for r in self.results if r['status'] == 'OK'])
        warning_checks = len([r for r in self.results if r['status'] == 'WARNING'])
        error_checks = len([r for r in self.results if r['status'] == 'ERROR'])
        
        print(f"Total de verificaciones: {total_checks}")
        print(f"✅ Exitosas: {ok_checks}")
        print(f"⚠️  Advertencias: {warning_checks}")
        print(f"❌ Errores: {error_checks}")
        
        if error_checks > 0:
            print("\n🚨 SERVICIOS CON ERRORES:")
            for result in self.results:
                if result['status'] == 'ERROR':
                    print(f"   - {result['service']}: {result['message']}")
        
        if warning_checks > 0:
            print("\n⚠️  SERVICIOS CON ADVERTENCIAS:")
            for result in self.results:
                if result['status'] == 'WARNING':
                    print(f"   - {result['service']}: {result['message']}")
        
        # Guardar reporte en archivo
        report_file = f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Reporte detallado guardado en: {report_file}")
        
        return error_checks == 0
    
    def run_all_checks(self):
        """Ejecuta todas las verificaciones"""
        print("🔍 INICIANDO VERIFICACIÓN DE SALUD DEL SISTEMA")
        print("="*60)
        
        # Verificaciones de conectividad externa
        self.check_kong_gateway()
        self.check_nvd_api()
        
        # Verificaciones de servicios locales
        self.check_postgresql()
        self.check_rabbitmq()
        self.check_microservices()
        self.check_frontend()
        
        # Generar reporte
        return self.generate_report()

def main():
    """Función principal"""
    print("🏥 Health Checker - Quantitative Risk Management System")
    print("Verificando configuración y conectividad...")
    print()
    
    checker = HealthChecker()
    success = checker.run_all_checks()
    
    if success:
        print("\n🎉 ¡Todos los servicios están funcionando correctamente!")
        sys.exit(0)
    else:
        print("\n💥 Algunos servicios tienen problemas. Revisa el reporte anterior.")
        sys.exit(1)

if __name__ == "__main__":
    main()
