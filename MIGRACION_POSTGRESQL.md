# 🍣 Mizu Sushi - Migración a PostgreSQL

## 📋 Resumen de Cambios

La aplicación **Mizu Sushi** ha sido completamente migrada de **SQLite local** a **PostgreSQL remoto** para mejorar el rendimiento, escalabilidad y permitir acceso concurrente desde múltiples dispositivos.

---

## 🔧 Configuración PostgreSQL

### Servidor de Base de Datos
```
Host: 192.168.1.82
Puerto: 5432
Base de Datos: mizu_sushi
Usuario: casaos
Contraseña: casaos
```

### Modificar Configuración
Para cambiar la configuración de conexión, edita el archivo `db.py`:

```python
DB_CONFIG = {
    'dbname': "mizu_sushi",      # Nombre de la base de datos
    'user': "casaos",            # Usuario PostgreSQL
    'password': "casaos",        # Contraseña
    'host': "192.168.1.82",      # IP del servidor
    'port': "5432"               # Puerto PostgreSQL
}
```

---

## 🚀 Instalación y Configuración

### Paso 1: Instalar Dependencias
```bash
# Instalar dependencias automáticamente
pip install -r requirements.txt

# O manualmente:
pip install psycopg2-binary reportlab Pillow
```

### Paso 2: Ejecutar Configuración Automática
```bash
python setup_postgresql.py
```

Este script:
- ✅ Verifica e instala dependencias
- 🔗 Prueba la conexión a PostgreSQL
- 📦 Migra datos de SQLite (si existe)
- 💾 Crea script de respaldo (opcional)

### Paso 3: Ejecutar Aplicación
```bash
python sushi_app.py
```

---

## 🔄 Migración Automática

### ¿Qué se Migra?
La migración automática transfiere:

- **🍣 Productos** - Toda la información del menú
- **🎯 Ofertas** - Promociones y descuentos
- **📋 Órdenes** - Historial de ventas completo
- **👥 Usuarios** - Cuentas de admin, cajeros y clientes
- **🏷️ Categorías** - Clasificaciones de productos
- **🛒 Carrito** - Items pendientes (si los hay)

### Proceso de Migración
1. **Detección**: Al iniciar, busca `mizu_sushi.db`
2. **Conexión**: Se conecta a PostgreSQL
3. **Creación**: Crea tablas si no existen
4. **Transferencia**: Copia todos los datos
5. **Respaldo**: Renombra SQLite como `.backup_YYYYMMDD_HHMMSS`
6. **Verificación**: Confirma transferencia exitosa

### Mensaje de Migración
```
🔄 Iniciando migración desde SQLite a PostgreSQL...
📦 Migrando productos... ✅ Migrados 25 productos
🎯 Migrando ofertas... ✅ Migradas 3 ofertas  
📋 Migrando órdenes... ✅ Migradas 150 órdenes
👥 Migrando usuarios... ✅ Migrados 3 usuarios
🏷️ Migrando categorías... ✅ Migradas 7 categorías
📁 Archivo SQLite respaldado como: mizu_sushi.db.backup_20251022_143021
🎉 ¡Migración completada exitosamente!
```

---

## 🛡️ Características de Seguridad

### Pool de Conexiones
- **Mínimo**: 1 conexión activa
- **Máximo**: 20 conexiones simultáneas
- **Beneficios**: Mejor rendimiento y uso eficiente de recursos

### Manejo de Errores
- **Reintentos**: 3 intentos de conexión automática
- **Rollback**: Reversión automática en caso de error
- **Logging**: Registro detallado de errores para depuración

### Transacciones Atómicas
Todas las operaciones usan transacciones:
```python
conn.begin()
try:
    # Operaciones de base de datos
    conn.commit()  # Solo si todo es exitoso
except:
    conn.rollback()  # Revertir en caso de error
```

---

## 🔧 Funciones Principales Migradas

### Productos
```python
# Cargar productos activos
productos = db.load_products()

# Guardar/actualizar producto  
db.save_product(producto_dict)

# Eliminar producto
db.delete_product(product_id)

# Actualizar stock
nuevo_stock = db.update_product_stock(product_id, delta)
```

### Carrito de Compras
```python
# Agregar al carrito
db.add_cart_item(product_id, name, quantity, price)

# Obtener items
items = db.get_cart_items()

# Limpiar carrito
db.clear_cart()

# Total del carrito
total = db.get_cart_total()
```

### Órdenes/Ventas
```python
# Guardar nueva orden
db.save_order(order_dict)

# Cargar historial
ordenes = db.load_orders()
```

### Usuarios
```python
# Autenticación
usuario = db.authenticate_user(username, password)

# Crear usuario
success = db.create_user(username, password, name, role)

# Cargar todos los usuarios
usuarios = db.load_users()
```

---

## 📊 Diferencias vs SQLite

| Característica | SQLite (Antes) | PostgreSQL (Ahora) |
|---|---|---|
| **Ubicación** | Archivo local | Servidor remoto |
| **Concurrencia** | Limitada | Múltiples usuarios |
| **Respaldos** | Manual | Automático con pg_dump |
| **Escalabilidad** | Básica | Empresarial |
| **Tipos de Datos** | Básicos | Avanzados (JSON, Arrays) |
| **Índices** | Básicos | Avanzados y optimizados |
| **Transacciones** | ACID básico | ACID completo |

---

## 🐛 Solución de Problemas

### Error de Conexión
```
❌ Error: No se pudo conectar a PostgreSQL
```
**Soluciones:**
1. Verificar que PostgreSQL esté ejecutándose
2. Comprobar IP: `ping 192.168.1.82`
3. Verificar puerto: `telnet 192.168.1.82 5432`
4. Revisar credenciales de usuario
5. Confirmar que la base de datos existe

### Error de Dependencias
```
❌ Import "psycopg2" could not be resolved
```
**Solución:**
```bash
pip install psycopg2-binary
# o si falla:
pip install psycopg2
```

### Error de Migración
```
❌ Error durante la migración: ...
```
**Soluciones:**
1. Verificar permisos de escritura en directorio
2. Asegurar que SQLite no esté en uso por otra aplicación
3. Revisar integridad del archivo `mizu_sushi.db`

### Pérdida de Conexión
La aplicación maneja automáticamente:
- **Reconexión automática**
- **Pool de conexiones resiliente**  
- **Mensajes informativos al usuario**

---

## 💾 Respaldos

### Automático con pg_dump
```bash
# Crear respaldo
python backup_mizu_sushi.py

# Resultado: mizu_sushi_backup_20251022_143021.sql
```

### Manual
```bash
pg_dump -h 192.168.1.82 -U casaos -d mizu_sushi > respaldo.sql
```

### Restaurar
```bash
psql -h 192.168.1.82 -U casaos -d mizu_sushi -f respaldo.sql
```

---

## 🔮 Características Nuevas

### Índices de Rendimiento
- Productos por categoría y estado activo
- Órdenes por fecha
- Usuarios por username
- Ofertas por estado activo

### Sesiones de Carrito
- Soporte para múltiples sesiones simultáneas
- Identificación por `session_id`

### Timestamps Automáticos
- `created_at` en todas las tablas
- Seguimiento temporal preciso

### Validación de Datos
- Tipos de datos estrictos
- Restricciones de integridad
- Validación automática

---

## 📞 Soporte

Para problemas técnicos:

1. **Revisar logs** en la consola de la aplicación
2. **Verificar configuración** en `db.py`
3. **Ejecutar diagnóstico** con `setup_postgresql.py`
4. **Crear issue** con detalles del error

---

## 🎉 ¡Éxito!

Si ves este mensaje al iniciar la aplicación:
```
✅ Pool de conexiones PostgreSQL inicializado exitosamente
✅ Tablas PostgreSQL creadas exitosamente  
✅ Conexión exitosa a PostgreSQL
```

**¡La migración fue exitosa! 🎊**

Tu aplicación Mizu Sushi ahora funciona completamente con PostgreSQL remoto, ofreciendo mejor rendimiento, escalabilidad y confiabilidad.