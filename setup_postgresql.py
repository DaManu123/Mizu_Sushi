#!/usr/bin/env python3
"""
Script de configuración para migrar Mizu Sushi a PostgreSQL
Autor: Sistema Mizu Sushi
Fecha: 2025

Este script:
1. Instala dependencias necesarias
2. Verifica conexión a PostgreSQL
3. Migra datos desde SQLite (si existe)
4. Configura la aplicación para PostgreSQL
"""

import subprocess
import sys
import os
import importlib.util

def install_package(package):
    """Instala un paquete de Python usando pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def check_package(package_name):
    """Verifica si un paquete está instalado"""
    spec = importlib.util.find_spec(package_name)
    return spec is not None

def main():
    print("🍣 Mizu Sushi - Configuración PostgreSQL")
    print("=" * 50)
    
    # 1. Verificar e instalar dependencias
    print("\n📦 Verificando dependencias...")
    
    required_packages = {
        'psycopg2': 'psycopg2-binary>=2.9.0',
        'reportlab': 'reportlab>=3.6.0', 
        'PIL': 'Pillow>=8.0.0'
    }
    
    for package_check, package_install in required_packages.items():
        if not check_package(package_check):
            print(f"⚠️ {package_check} no encontrado. Instalando...")
            if install_package(package_install):
                print(f"✅ {package_check} instalado exitosamente")
            else:
                print(f"❌ Error instalando {package_check}")
                return False
        else:
            print(f"✅ {package_check} ya está instalado")
    
    # 2. Probar conexión a PostgreSQL
    print("\n🔗 Probando conexión a PostgreSQL...")
    
    try:
        import psycopg2
        
        # Configuración de conexión (ajusta estos valores)
        DB_CONFIG = {
            'dbname': "mizu_sushi",
            'user': "casaos", 
            'password': "casaos",
            'host': "192.168.1.82",
            'port': "5432"
        }
        
        print(f"Conectando a: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        print(f"Base de datos: {DB_CONFIG['dbname']}")
        print(f"Usuario: {DB_CONFIG['user']}")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Conexión exitosa a PostgreSQL: {version}")
        
        cursor.close()
        conn.close()
        
    except ImportError:
        print("❌ Error: psycopg2 no está disponible")
        return False
    except psycopg2.Error as e:
        print(f"❌ Error de conexión PostgreSQL: {e}")
        print("\nVerifique:")
        print("• El servidor PostgreSQL está ejecutándose")
        print("• La dirección IP es correcta (192.168.1.82)")
        print("• El puerto es correcto (5432)")
        print("• Las credenciales son correctas (usuario: casaos)")
        print("• La base de datos 'mizu_sushi' existe")
        return False
    
    # 3. Verificar archivo SQLite para migración
    print("\n📁 Verificando datos existentes...")
    sqlite_file = os.path.join(os.path.dirname(__file__), 'mizu_sushi.db')
    
    if os.path.exists(sqlite_file):
        print(f"✅ Base de datos SQLite encontrada: {sqlite_file}")
        print("ℹ️ Los datos se migrarán automáticamente al iniciar la aplicación")
    else:
        print("ℹ️ No se encontró base de datos SQLite. Se creará una nueva en PostgreSQL")
    
    # 4. Crear script de respaldo (opcional)
    print("\n💾 ¿Desea crear un script de respaldo automático?")
    respuesta = input("Escriba 'si' para crear script de respaldo: ").lower()
    
    if respuesta in ['si', 'sí', 's', 'yes']:
        create_backup_script()
    
    print("\n🎉 ¡Configuración completada!")
    print("\n📋 Próximos pasos:")
    print("1. Ejecute: python sushi_app.py")
    print("2. La aplicación se conectará automáticamente a PostgreSQL")
    print("3. Si existe datos SQLite, se migrarán automáticamente")
    print("4. ¡Disfrute usando Mizu Sushi con base de datos remota!")
    
    return True

def create_backup_script():
    """Crea un script de respaldo para PostgreSQL"""
    backup_script = '''#!/usr/bin/env python3
"""
Script de respaldo automático para Mizu Sushi PostgreSQL
Uso: python backup_mizu_sushi.py
"""

import subprocess
import datetime
import os

# Configuración
DB_CONFIG = {
    "host": "192.168.1.82",
    "port": "5432", 
    "database": "mizu_sushi",
    "username": "casaos"
}

def create_backup():
    """Crea un respaldo de la base de datos"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"mizu_sushi_backup_{timestamp}.sql"
    
    # Comando pg_dump
    cmd = [
        "pg_dump",
        f"--host={DB_CONFIG['host']}",
        f"--port={DB_CONFIG['port']}",
        f"--username={DB_CONFIG['username']}",
        f"--dbname={DB_CONFIG['database']}",
        "--verbose",
        "--clean",
        "--no-owner",
        "--no-privileges",
        f"--file={backup_file}"
    ]
    
    try:
        print(f"🔄 Creando respaldo: {backup_file}")
        subprocess.run(cmd, check=True)
        print(f"✅ Respaldo creado exitosamente: {backup_file}")
        
        # Mostrar tamaño del archivo
        size = os.path.getsize(backup_file)
        print(f"📊 Tamaño del respaldo: {size:,} bytes")
        
        return backup_file
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creando respaldo: {e}")
        return None
    except FileNotFoundError:
        print("❌ Error: pg_dump no encontrado. Instale PostgreSQL client tools.")
        return None

if __name__ == "__main__":
    backup_file = create_backup()
    if backup_file:
        print(f"\\n💾 Respaldo guardado como: {backup_file}")
        print("\\nPara restaurar:")
        print(f"psql -h {DB_CONFIG['host']} -U {DB_CONFIG['username']} -d {DB_CONFIG['database']} -f {backup_file}")
'''

    try:
        with open("backup_mizu_sushi.py", "w", encoding="utf-8") as f:
            f.write(backup_script)
        print("✅ Script de respaldo creado: backup_mizu_sushi.py")
        
        # Hacer ejecutable en sistemas Unix
        try:
            os.chmod("backup_mizu_sushi.py", 0o755)
        except:
            pass  # Windows no soporta chmod
            
    except Exception as e:
        print(f"⚠️ No se pudo crear script de respaldo: {e}")

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ La configuración falló. Por favor revise los errores anteriores.")
        sys.exit(1)
    else:
        print("\n✅ Configuración exitosa. ¡Mizu Sushi está listo para PostgreSQL!")
        sys.exit(0)