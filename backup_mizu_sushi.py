#!/usr/bin/env python3
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
        print(f"\n💾 Respaldo guardado como: {backup_file}")
        print("\nPara restaurar:")
        print(f"psql -h {DB_CONFIG['host']} -U {DB_CONFIG['username']} -d {DB_CONFIG['database']} -f {backup_file}")
