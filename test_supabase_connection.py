#!/usr/bin/env python3
"""
Script de prueba de conexión a Supabase
Verifica que la conexión con Transaction Pooler funcione correctamente
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError, DatabaseError

def print_separator():
    print("=" * 80)

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def print_info(message):
    print(f"ℹ️  {message}")

def test_supabase_connection():
    """Prueba la conexión a Supabase usando Transaction Pooler"""
    
    print_separator()
    print("🔍 PRUEBA DE CONEXIÓN A SUPABASE")
    print_separator()
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Obtener DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print_error("DATABASE_URL no está configurado en .env")
        return False
    
    print_info(f"DATABASE_URL encontrado")
    
    # Parsear la URL para mostrar información (sin mostrar password)
    if "postgresql://" in database_url:
        parts = database_url.replace("postgresql://", "").split("@")
        if len(parts) > 1:
            user = parts[0].split(":")[0]
            host_info = parts[1]
            print_info(f"Usuario: {user}")
            print_info(f"Host: {host_info.split('/')[0]}")
    
    print("\n" + "=" * 80)
    print("📡 PASO 1: Intentando conectar al Transaction Pooler...")
    print_separator()
    
    try:
        # Crear engine de SQLAlchemy
        engine = create_engine(
            database_url,
            pool_pre_ping=True,  # Verifica conexiones antes de usarlas
            echo=True  # Muestra las queries SQL
        )
        
        # Intentar conectar
        with engine.connect() as connection:
            print_success("¡Conexión establecida exitosamente!")
            
            print("\n" + "=" * 80)
            print("🔍 PASO 2: Verificando información de la base de datos...")
            print_separator()
            
            # Obtener versión de PostgreSQL
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print_info(f"Versión PostgreSQL:\n{version}")
            
            # Obtener nombre de la base de datos actual
            result = connection.execute(text("SELECT current_database();"))
            db_name = result.fetchone()[0]
            print_success(f"Base de datos actual: {db_name}")
            
            # Obtener usuario actual
            result = connection.execute(text("SELECT current_user;"))
            current_user = result.fetchone()[0]
            print_success(f"Usuario actual: {current_user}")
            
            print("\n" + "=" * 80)
            print("📋 PASO 3: Listando tablas existentes...")
            print_separator()
            
            # Listar tablas
            inspector = inspect(engine)
            schemas = inspector.get_schema_names()
            
            print_info(f"Schemas disponibles: {', '.join(schemas)}")
            
            tables = inspector.get_table_names(schema='public')
            if tables:
                print_success(f"Tablas encontradas en schema 'public': {len(tables)}")
                for table in tables:
                    print(f"  - {table}")
            else:
                print_info("No hay tablas en el schema 'public' aún")
            
            print("\n" + "=" * 80)
            print("🧪 PASO 4: Probando creación de tabla de prueba...")
            print_separator()
            
            # Crear tabla de prueba
            try:
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS test_connection (
                        id SERIAL PRIMARY KEY,
                        mensaje TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                """))
                connection.commit()
                print_success("Tabla 'test_connection' creada exitosamente")
                
                # Insertar registro de prueba
                connection.execute(text("""
                    INSERT INTO test_connection (mensaje) 
                    VALUES ('Conexión exitosa desde Python + SQLAlchemy');
                """))
                connection.commit()
                print_success("Registro insertado exitosamente")
                
                # Leer registro
                result = connection.execute(text("""
                    SELECT id, mensaje, created_at 
                    FROM test_connection 
                    ORDER BY id DESC 
                    LIMIT 1;
                """))
                row = result.fetchone()
                print_success(f"Registro leído: ID={row[0]}, Mensaje='{row[1]}', Fecha={row[2]}")
                
                # Limpiar tabla de prueba
                connection.execute(text("DROP TABLE IF EXISTS test_connection;"))
                connection.commit()
                print_success("Tabla de prueba eliminada")
                
            except Exception as e:
                print_error(f"Error en prueba de tabla: {str(e)}")
                return False
            
            print("\n" + "=" * 80)
            print("✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
            print_separator()
            print_info("Tu proyecto está correctamente conectado a Supabase!")
            print_info("Usando: Transaction Pooler (puerto 6543)")
            print_separator()
            
            return True
            
    except OperationalError as e:
        print_error(f"Error de conexión: {str(e)}")
        print_info("\nPosibles causas:")
        print("  1. Credenciales incorrectas")
        print("  2. Firewall bloqueando puerto 6543")
        print("  3. URL de conexión mal formada")
        print("  4. Supabase project pausado/inactivo")
        return False
        
    except DatabaseError as e:
        print_error(f"Error de base de datos: {str(e)}")
        return False
        
    except Exception as e:
        print_error(f"Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_environment_variables():
    """Verifica que todas las variables de entorno necesarias estén configuradas"""
    print_separator()
    print("🔍 VERIFICANDO VARIABLES DE ENTORNO")
    print_separator()
    
    required_vars = [
        "DATABASE_URL",
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_ROLE_KEY"
    ]
    
    load_dotenv()
    
    all_present = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mostrar solo los primeros caracteres para no exponer credenciales
            display_value = value[:30] + "..." if len(value) > 30 else value
            print_success(f"{var}: {display_value}")
        else:
            print_error(f"{var}: NO CONFIGURADO")
            all_present = False
    
    print_separator()
    return all_present

if __name__ == "__main__":
    print("\n" * 2)
    print("🚀 INICIANDO PRUEBAS DE SUPABASE")
    print("=" * 80)
    
    # Verificar variables de entorno
    env_ok = check_environment_variables()
    
    if not env_ok:
        print_error("⚠️  Hay variables de entorno faltantes. Por favor configúralas en .env")
        sys.exit(1)
    
    # Probar conexión
    success = test_supabase_connection()
    
    if success:
        print("\n" + "=" * 80)
        print("🎉 ¡TODO FUNCIONA CORRECTAMENTE!")
        print("=" * 80)
        sys.exit(0)
    else:
        print("\n" + "=" * 80)
        print("❌ PRUEBAS FALLIDAS - Revisa los errores arriba")
        print("=" * 80)
        sys.exit(1)
