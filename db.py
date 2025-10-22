import psycopg2
from psycopg2.extras import RealDictCursor
import psycopg2.pool
import sqlite3
import json
import os
from typing import List, Dict, Any, Optional
import hashlib
import datetime

# Configuración de conexión PostgreSQL
DB_CONFIG = {
    'dbname': "mizu_sushi",
    'user': "casaos", 
    'password': "casaos",
    'host': "192.168.1.82",
    'port': "5432"
}

# Pool de conexiones para mejor rendimiento
connection_pool = None

def init_connection_pool():
    """Inicializa el pool de conexiones PostgreSQL"""
    global connection_pool
    if connection_pool is None:
        try:
            connection_pool = psycopg2.pool.ThreadedConnectionPool(
                1, 20,  # min y max conexiones
                **DB_CONFIG
            )
            print("✅ Pool de conexiones PostgreSQL inicializado exitosamente")
        except Exception as e:
            print(f"❌ Error inicializando pool de conexiones: {e}")
            raise

def get_connection():
    """Obtiene una conexión del pool de PostgreSQL"""
    global connection_pool
    if connection_pool is None:
        init_connection_pool()
    
    try:
        conn = connection_pool.getconn()
        return conn
    except Exception as e:
        print(f"❌ Error obteniendo conexión: {e}")
        raise

def return_connection(conn):
    """Devuelve una conexión al pool"""
    global connection_pool
    if connection_pool and conn:
        connection_pool.putconn(conn)

# Ruta por defecto de la base de datos SQLite (para migración)
DB_FILE = os.path.join(os.path.dirname(__file__), 'mizu_sushi.db')


def init_db(path: Optional[str] = None):
    """Inicializa la base de datos PostgreSQL y crea las tablas necesarias."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        print("🔄 Inicializando base de datos PostgreSQL...")

        # Productos / menú
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(255),
            description TEXT,
            price DECIMAL(10,2),
            stock INTEGER DEFAULT 50,
            categoria VARCHAR(100) DEFAULT 'general',
            activo BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Ofertas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS offers (
            id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(255),
            description TEXT,
            type VARCHAR(50),
            products_aplicables TEXT,
            descuento INTEGER,
            activa BOOLEAN DEFAULT true,
            fecha_inicio DATE,
            fecha_fin DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Carrito temporal
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id SERIAL PRIMARY KEY,
            product_id VARCHAR(50),
            product_name VARCHAR(255),
            quantity INTEGER,
            price DECIMAL(10,2),
            session_id VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Pedidos / ventas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id VARCHAR(50) PRIMARY KEY,
            fecha TIMESTAMP,
            productos TEXT,
            oferta_aplicada VARCHAR(255),
            descuento_aplicado DECIMAL(10,2),
            total_sin_descuento DECIMAL(10,2),
            total_final DECIMAL(10,2),
            metodo_pago VARCHAR(50),
            cajero VARCHAR(255),
            estado VARCHAR(50) DEFAULT 'En preparación',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Usuarios
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            full_name VARCHAR(255),
            role VARCHAR(50) NOT NULL DEFAULT 'cliente',
            email VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            active BOOLEAN DEFAULT true
        )
        ''')

        # Categorías
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            name VARCHAR(100) PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Crear índices para mejor rendimiento
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_active ON products(activo)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_categoria ON products(categoria)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_fecha ON orders(fecha)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_offers_activa ON offers(activa)')

        conn.commit()
        print("✅ Tablas PostgreSQL creadas exitosamente")
        
        # Inicializar categorías por defecto
        init_default_categories()
        
        # Inicializar usuarios por defecto después de crear las tablas
        init_default_users()

        # Intentar migración automática desde SQLite si existe
        if os.path.exists(DB_FILE):
            print("📦 Archivo SQLite encontrado. Iniciando migración automática...")
            sync_local_to_remote()
            
    except psycopg2.Error as e:
        print(f"❌ Error de PostgreSQL: {e}")
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            cursor.close()
            return_connection(conn)

def init_default_categories():
    """Inicializa categorías por defecto"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        defaults = ['Rolls', 'Especiales', 'Vegetarianos', 'Postres', 'Bebidas', 'Entradas', 'Sopas']
        
        for categoria in defaults:
            cursor.execute('INSERT INTO categories (name) VALUES (%s) ON CONFLICT (name) DO NOTHING', (categoria,))
        
        conn.commit()
        print("✅ Categorías por defecto inicializadas")
        
    except Exception as e:
        print(f"❌ Error inicializando categorías: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cursor.close()
            return_connection(conn)


def _get_conn(path: Optional[str] = None):
    """Función legacy para compatibilidad con SQLite (solo para migración)"""
    if path is None:
        path = os.path.join(os.path.dirname(__file__), 'mizu_sushi.db')
    return sqlite3.connect(path)

def load_products() -> List[Dict[str, Any]]:
    """Carga productos desde PostgreSQL"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT id, name, description, price, stock, categoria, activo FROM products WHERE activo = 1 ORDER BY categoria, name')
        rows = cursor.fetchall()
        
        productos = []
        for row in rows:
            productos.append({
                'id': row['id'], 
                'nombre': row['name'], 
                'descripcion': row['description'] or '',
                'precio': float(row['price']) if row['price'] else 0.0,
                'stock': row['stock'] if row['stock'] is not None else 50,
                'categoria': row['categoria'] if row['categoria'] is not None else 'general',
                'activo': bool(row['activo']) if row['activo'] is not None else True
            })
        
        return productos
        
    except psycopg2.Error as e:
        print(f"❌ Error cargando productos: {e}")
        return []
    except Exception as e:
        print(f"❌ Error inesperado cargando productos: {e}")
        return []
    finally:
        if conn:
            cursor.close()
            return_connection(conn)


def save_product(prod: Dict[str, Any]):
    """Guarda producto en PostgreSQL"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO products (id, name, description, price, stock, categoria, activo) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                price = EXCLUDED.price,
                stock = EXCLUDED.stock,
                categoria = EXCLUDED.categoria,
                activo = EXCLUDED.activo
        ''', (
            prod.get('id'), 
            prod.get('nombre'), 
            prod.get('descripcion', ''), 
            float(prod.get('precio', 0)),
            int(prod.get('stock', 50)),
            prod.get('categoria', 'general'),
            int(bool(prod.get('activo', True)))  # Convertir boolean a int
        ))
        
        conn.commit()
        
    except psycopg2.Error as e:
        print(f"❌ Error guardando producto: {e}")
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        print(f"❌ Error inesperado guardando producto: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            cursor.close()
            return_connection(conn)

def delete_product(product_id: str):
    """Elimina producto de PostgreSQL"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM products WHERE id = %s', (product_id,))
        conn.commit()
        
    except psycopg2.Error as e:
        print(f"❌ Error eliminando producto: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            cursor.close()
            return_connection(conn)


def load_offers() -> List[Dict[str, Any]]:
    """Carga ofertas desde PostgreSQL"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT id, name, description, type, products_aplicables, descuento, activa, fecha_inicio, fecha_fin FROM offers ORDER BY activa DESC, name')
        rows = cursor.fetchall()
        
        ofertas = []
        for row in rows:
            try:
                productos = json.loads(row['products_aplicables']) if row['products_aplicables'] else []
            except Exception:
                productos = []
            
            ofertas.append({
                'id': row['id'],
                'nombre': row['name'],
                'descripcion': row['description'] or '',
                'tipo': row['type'] or '',
                'productos_aplicables': productos,
                'descuento': row['descuento'] or 0,
                'activa': bool(row['activa']),
                'fecha_inicio': str(row['fecha_inicio']) if row['fecha_inicio'] else '',
                'fecha_fin': str(row['fecha_fin']) if row['fecha_fin'] else ''
            })
        return ofertas
        
    except psycopg2.Error as e:
        print(f"❌ Error cargando ofertas: {e}")
        return []
    except Exception as e:
        print(f"❌ Error inesperado cargando ofertas: {e}")
        return []
    finally:
        if conn:
            cursor.close()
            return_connection(conn)

def save_offer(oferta: Dict[str, Any]):
    """Guarda oferta en PostgreSQL"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        productos_json = json.dumps(oferta.get('productos_aplicables', []), ensure_ascii=False)
        
        cursor.execute('''
            INSERT INTO offers (id, name, description, type, products_aplicables, descuento, activa, fecha_inicio, fecha_fin) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                type = EXCLUDED.type,
                products_aplicables = EXCLUDED.products_aplicables,
                descuento = EXCLUDED.descuento,
                activa = EXCLUDED.activa,
                fecha_inicio = EXCLUDED.fecha_inicio,
                fecha_fin = EXCLUDED.fecha_fin
        ''', (
            oferta.get('id'), 
            oferta.get('nombre'), 
            oferta.get('descripcion'), 
            oferta.get('tipo'), 
            productos_json,
            int(oferta.get('descuento', 0)), 
            int(bool(oferta.get('activa', True))),  # Convertir boolean a int
            oferta.get('fecha_inicio'), 
            oferta.get('fecha_fin')
        ))
        
        conn.commit()
        
    except psycopg2.Error as e:
        print(f"❌ Error guardando oferta: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            cursor.close()
            return_connection(conn)


def load_categories() -> List[str]:
    """Devuelve la lista de categorías desde PostgreSQL"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Cargar desde la tabla categories
        cursor.execute('SELECT name FROM categories ORDER BY name')
        rows = cursor.fetchall()
        if rows:
            return [row[0] for row in rows if row and row[0]]

        # Fallback: categorías distintas de productos
        cursor.execute("SELECT DISTINCT categoria FROM products WHERE categoria IS NOT NULL ORDER BY categoria")
        rows = cursor.fetchall()
        return [row[0] for row in rows if row and row[0]]
        
    except psycopg2.Error as e:
        print(f"❌ Error cargando categorías: {e}")
        return ['general']
    except Exception as e:
        print(f"❌ Error inesperado cargando categorías: {e}")
        return ['general']
    finally:
        if conn:
            cursor.close()
            return_connection(conn)

def set_product_category(product_id: str, categoria: str):
    """Establece/actualiza la categoría de un producto en PostgreSQL"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE products SET categoria = %s WHERE id = %s', (categoria, product_id))
        conn.commit()
        
    except psycopg2.Error as e:
        print(f"❌ Error actualizando categoría: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cursor.close()
            return_connection(conn)

def add_category(name: str):
    """Agrega una categoría a PostgreSQL"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO categories (name) VALUES (%s) ON CONFLICT (name) DO NOTHING', (name,))
        conn.commit()
        
    except psycopg2.Error as e:
        print(f"❌ Error agregando categoría: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cursor.close()
            return_connection(conn)


def get_product_by_id(product_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene producto por ID desde PostgreSQL"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT id, name, description, price, stock, categoria, activo FROM products WHERE id = %s', (product_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
            
        return {
            'id': row['id'],
            'nombre': row['name'],
            'descripcion': row['description'] or '',
            'precio': float(row['price']) if row['price'] else 0.0,
            'stock': row['stock'] if row['stock'] is not None else 0,
            'categoria': row['categoria'] if row['categoria'] is not None else 'general',
            'activo': bool(row['activo']) if row['activo'] is not None else True
        }
        
    except psycopg2.Error as e:
        print(f"❌ Error obteniendo producto por ID: {e}")
        return None
    finally:
        if conn:
            cursor.close()
            return_connection(conn)

def get_product_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Obtiene producto por nombre desde PostgreSQL"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Búsqueda exacta
        cursor.execute('SELECT id, name, description, price, stock, categoria, activo FROM products WHERE name = %s', (name,))
        row = cursor.fetchone()
        
        if not row:
            # Búsqueda insensible a mayúsculas
            cursor.execute('SELECT id, name, description, price, stock, categoria, activo FROM products WHERE LOWER(name) = LOWER(%s)', (name,))
            row = cursor.fetchone()
            
        if not row:
            return None
            
        return {
            'id': row['id'],
            'nombre': row['name'],
            'descripcion': row['description'] or '',
            'precio': float(row['price']) if row['price'] else 0.0,
            'stock': row['stock'] if row['stock'] is not None else 0,
            'categoria': row['categoria'] if row['categoria'] is not None else 'general',
            'activo': bool(row['activo']) if row['activo'] is not None else True
        }
        
    except psycopg2.Error as e:
        print(f"❌ Error obteniendo producto por nombre: {e}")
        return None
    finally:
        if conn:
            cursor.close()
            return_connection(conn)

def update_product_stock(product_id: str, delta: int) -> int:
    """Ajusta el stock del producto en PostgreSQL. Devuelve el stock resultante."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT stock FROM products WHERE id = %s', (product_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError('Producto no encontrado')
            
        current = row[0] if row[0] is not None else 0
        new_stock = int(current + int(delta))
        if new_stock < 0:
            new_stock = 0
            
        cursor.execute('UPDATE products SET stock = %s WHERE id = %s', (new_stock, product_id))
        conn.commit()
        return new_stock
        
    except psycopg2.Error as e:
        print(f"❌ Error actualizando stock: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            cursor.close()
            return_connection(conn)


def delete_offer(oferta_id: str):
    """Elimina oferta de PostgreSQL"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM offers WHERE id = %s', (oferta_id,))
        conn.commit()
        
    except psycopg2.Error as e:
        print(f"❌ Error eliminando oferta: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            cursor.close()
            return_connection(conn)

def toggle_offer(oferta_id: str, activo: bool):
    """Activa/desactiva oferta en PostgreSQL"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE offers SET activa = %s WHERE id = %s', (int(bool(activo)), oferta_id))
        conn.commit()
        
    except psycopg2.Error as e:
        print(f"❌ Error toggling oferta: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            cursor.close()
            return_connection(conn)


def load_orders() -> List[Dict[str, Any]]:
    """Carga órdenes desde PostgreSQL"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT id, fecha, productos, oferta_aplicada, descuento_aplicado, total_sin_descuento, total_final, metodo_pago, cajero, estado FROM orders ORDER BY fecha DESC')
        rows = cursor.fetchall()
        
        orders = []
        for row in rows:
            try:
                productos = json.loads(row['productos']) if row['productos'] else []
            except Exception:
                productos = []
                
            orders.append({
                'id': row['id'],
                'fecha': str(row['fecha']) if row['fecha'] else '',
                'productos': productos,
                'oferta_aplicada': row['oferta_aplicada'] or '',
                'descuento_aplicado': float(row['descuento_aplicado']) if row['descuento_aplicado'] else 0.0,
                'total_sin_descuento': float(row['total_sin_descuento']) if row['total_sin_descuento'] else 0.0,
                'total_final': float(row['total_final']) if row['total_final'] else 0.0,
                'metodo_pago': row['metodo_pago'] or '',
                'cajero': row['cajero'] or '',
                'estado': row['estado'] or 'En preparación'
            })
        return orders
        
    except psycopg2.Error as e:
        print(f"❌ Error cargando órdenes: {e}")
        return []
    except Exception as e:
        print(f"❌ Error inesperado cargando órdenes: {e}")
        return []
    finally:
        if conn:
            cursor.close()
            return_connection(conn)

def save_order(order: Dict[str, Any]):
    """Guarda orden en PostgreSQL"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        productos_json = json.dumps(order.get('productos', []), ensure_ascii=False)
        
        cursor.execute('''
            INSERT INTO orders (id, fecha, productos, oferta_aplicada, descuento_aplicado, total_sin_descuento, total_final, metodo_pago, cajero, estado) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                fecha = EXCLUDED.fecha,
                productos = EXCLUDED.productos,
                oferta_aplicada = EXCLUDED.oferta_aplicada,
                descuento_aplicado = EXCLUDED.descuento_aplicado,
                total_sin_descuento = EXCLUDED.total_sin_descuento,
                total_final = EXCLUDED.total_final,
                metodo_pago = EXCLUDED.metodo_pago,
                cajero = EXCLUDED.cajero,
                estado = EXCLUDED.estado
        ''', (
            order.get('id'), 
            order.get('fecha'), 
            productos_json, 
            order.get('oferta_aplicada'), 
            float(order.get('descuento_aplicado', 0)),
            float(order.get('total_sin_descuento', 0)), 
            float(order.get('total_final', 0)), 
            order.get('metodo_pago'), 
            order.get('cajero'), 
            order.get('estado', 'En preparación')
        ))
        
        conn.commit()
        
    except psycopg2.Error as e:
        print(f"❌ Error guardando orden: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            cursor.close()
            return_connection(conn)


def add_cart_item(product_id: str, product_name: str, quantity: int, price: float):
    """Agrega item al carrito en PostgreSQL"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Si el item ya existe, incrementar cantidad
        cursor.execute('SELECT id, quantity FROM cart WHERE product_id = %s', (product_id,))
        row = cursor.fetchone()
        
        if row:
            new_q = row[1] + quantity
            cursor.execute('UPDATE cart SET quantity = %s WHERE id = %s', (new_q, row[0]))
        else:
            cursor.execute('INSERT INTO cart (product_id, product_name, quantity, price) VALUES (%s, %s, %s, %s)',
                          (product_id, product_name, int(quantity), float(price)))
        
        conn.commit()
        
    except psycopg2.Error as e:
        print(f"❌ Error agregando al carrito: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            cursor.close()
            return_connection(conn)

def get_cart_items() -> List[Dict[str, Any]]:
    """Obtiene items del carrito desde PostgreSQL"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT id, product_id, product_name, quantity, price FROM cart ORDER BY id')
        rows = cursor.fetchall()
        
        return [{
            'id': row['id'], 
            'product_id': row['product_id'], 
            'product_name': row['product_name'], 
            'quantity': row['quantity'], 
            'price': float(row['price']) if row['price'] else 0.0
        } for row in rows]
        
    except psycopg2.Error as e:
        print(f"❌ Error obteniendo carrito: {e}")
        return []
    finally:
        if conn:
            cursor.close()
            return_connection(conn)

def clear_cart():
    """Limpia el carrito en PostgreSQL"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cart')
        conn.commit()
        
    except psycopg2.Error as e:
        print(f"❌ Error limpiando carrito: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            cursor.close()
            return_connection(conn)

def update_cart_item_quantity(item_id: int, new_quantity: int):
    """Actualiza la cantidad de un item del carrito en PostgreSQL"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE cart SET quantity = %s WHERE id = %s', (int(new_quantity), int(item_id)))
        conn.commit()
        
    except psycopg2.Error as e:
        print(f"❌ Error actualizando cantidad carrito: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            cursor.close()
            return_connection(conn)

def remove_cart_item(item_id: int):
    """Elimina un item específico del carrito en PostgreSQL"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cart WHERE id = %s', (int(item_id),))
        conn.commit()
        
    except psycopg2.Error as e:
        print(f"❌ Error eliminando item del carrito: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            cursor.close()
            return_connection(conn)

def get_cart_total() -> float:
    """Obtiene el total del carrito"""
    items = get_cart_items()
    return sum(item['quantity'] * float(item['price']) for item in items)

def get_cart_item_count() -> int:
    """Obtiene el número total de items en el carrito"""
    items = get_cart_items()
    return sum(item['quantity'] for item in items)


# Funciones para manejo de usuarios
def create_user(username: str, password: str, full_name: str, role: str = 'cliente', email: Optional[str] = None) -> bool:
    """Crea un nuevo usuario en PostgreSQL"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Hash de la contraseña
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Insertar usuario
        cursor.execute('''INSERT INTO users (username, password, full_name, role, email, created_at, active) 
                         VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                      (username, password_hash, full_name, role, email, 
                       datetime.datetime.now(), 1))
        conn.commit()
        return True
        
    except psycopg2.IntegrityError:
        if conn:
            conn.rollback()
        return False  # Usuario ya existe
    except psycopg2.Error as e:
        print(f"❌ Error creando usuario: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            cursor.close()
            return_connection(conn)

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Autentica un usuario en PostgreSQL y devuelve sus datos si es válido"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Hash de la contraseña
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute('''SELECT id, username, full_name, role, email, created_at, last_login 
                         FROM users WHERE username = %s AND password = %s AND active = 1''',
                      (username, password_hash))
        row = cursor.fetchone()
        
        if row:
            # Actualizar último login
            cursor.execute('UPDATE users SET last_login = %s WHERE id = %s',
                          (datetime.datetime.now(), row['id']))
            conn.commit()
            
            user_data = {
                'id': row['id'],
                'username': row['username'],
                'full_name': row['full_name'],
                'role': row['role'],
                'email': row['email'],
                'created_at': str(row['created_at']) if row['created_at'] else '',
                'last_login': str(row['last_login']) if row['last_login'] else ''
            }
            return user_data
        
        return None
        
    except psycopg2.Error as e:
        print(f"❌ Error autenticando usuario: {e}")
        return None
    finally:
        if conn:
            cursor.close()
            return_connection(conn)

def load_users() -> List[Dict[str, Any]]:
    """Carga todos los usuarios desde PostgreSQL"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''SELECT id, username, full_name, role, email, created_at, last_login, active 
                         FROM users ORDER BY created_at DESC''')
        rows = cursor.fetchall()
        
        users = []
        for row in rows:
            users.append({
                'id': row['id'],
                'username': row['username'],
                'full_name': row['full_name'],
                'role': row['role'],
                'email': row['email'],
                'created_at': str(row['created_at']) if row['created_at'] else '',
                'last_login': str(row['last_login']) if row['last_login'] else '',
                'active': bool(row['active'])
            })
        return users
        
    except psycopg2.Error as e:
        print(f"❌ Error cargando usuarios: {e}")
        return []
    finally:
        if conn:
            cursor.close()
            return_connection(conn)

def update_user(user_id: int, full_name: Optional[str] = None, role: Optional[str] = None, email: Optional[str] = None, active: Optional[bool] = None):
    """Actualiza información de un usuario en PostgreSQL"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if full_name is not None:
            updates.append("full_name = %s")
            params.append(full_name)
        
        if role is not None:
            updates.append("role = %s")
            params.append(role)
        
        if email is not None:
            updates.append("email = %s")
            params.append(email)
        
        if active is not None:
            updates.append("active = %s")
            params.append(int(bool(active)))
        
        if updates:
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
            params.append(user_id)
            cursor.execute(query, params)
            conn.commit()
            
    except psycopg2.Error as e:
        print(f"❌ Error actualizando usuario: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            cursor.close()
            return_connection(conn)

def delete_user(user_id: int):
    """Elimina un usuario de PostgreSQL"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
        conn.commit()
        
    except psycopg2.Error as e:
        print(f"❌ Error eliminando usuario: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            cursor.close()
            return_connection(conn)

def change_user_password(user_id: int, new_password: str) -> bool:
    """Cambia la contraseña de un usuario en PostgreSQL"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Hash de la nueva contraseña
        password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        
        cursor.execute('UPDATE users SET password = %s WHERE id = %s', (password_hash, user_id))
        conn.commit()
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Error cambiando contraseña: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            cursor.close()
            return_connection(conn)


def init_default_users():
    """Inicializa usuarios por defecto en PostgreSQL si no existen"""
    try:
        # Verificar si ya hay usuarios
        users = load_users()
        if not users:
            # Crear usuarios por defecto
            default_users = [
                ("admin", "admin123", "Administrador del Sistema", "admin", "admin@mizusushi.com"),
                ("cajero", "cajero123", "Cajero Principal", "cajero", "cajero@mizusushi.com"),
                ("cliente", "cliente123", "Cliente Demo", "cliente", "cliente@mizusushi.com")
            ]
            
            for username, password, full_name, role, email in default_users:
                if create_user(username, password, full_name, role, email):
                    print(f"✅ Usuario por defecto creado: {username}")
                else:
                    print(f"⚠️ Usuario ya existe: {username}")
            
            print("✅ Inicialización de usuarios completada")
            return True
        else:
            print(f"ℹ️ Ya existen {len(users)} usuarios en la base de datos")
            return True
            
    except Exception as e:
        print(f"❌ Error inicializando usuarios por defecto: {e}")
        return False

def sync_local_to_remote():
    """Migra datos desde SQLite local hacia PostgreSQL remoto"""
    if not os.path.exists(DB_FILE):
        print("ℹ️ No se encontró base de datos SQLite local para migrar")
        return True
    
    try:
        print("🔄 Iniciando migración desde SQLite a PostgreSQL...")
        
        # Conectar a SQLite local
        sqlite_conn = sqlite3.connect(DB_FILE)
        sqlite_cursor = sqlite_conn.cursor()
        
        # 1. Migrar productos
        print("📦 Migrando productos...")
        sqlite_cursor.execute('SELECT id, name, description, price, stock, categoria, activo FROM products')
        productos_sqlite = sqlite_cursor.fetchall()
        
        for producto in productos_sqlite:
            prod_dict = {
                'id': producto[0],
                'nombre': producto[1], 
                'descripcion': producto[2] or '',
                'precio': float(producto[3]) if producto[3] else 0.0,
                'stock': producto[4] if producto[4] is not None else 50,
                'categoria': producto[5] if producto[5] else 'general',
                'activo': bool(producto[6]) if producto[6] is not None else True
            }
            try:
                save_product(prod_dict)
            except Exception as e:
                print(f"⚠️ Error migrando producto {producto[0]}: {e}")
        
        print(f"✅ Migrados {len(productos_sqlite)} productos")
        
        # 2. Migrar ofertas
        print("🎯 Migrando ofertas...")
        sqlite_cursor.execute('SELECT id, name, description, type, products_aplicables, descuento, activa, fecha_inicio, fecha_fin FROM offers')
        ofertas_sqlite = sqlite_cursor.fetchall()
        
        for oferta in ofertas_sqlite:
            oferta_dict = {
                'id': oferta[0],
                'nombre': oferta[1],
                'descripcion': oferta[2] or '',
                'tipo': oferta[3] or '',
                'productos_aplicables': json.loads(oferta[4]) if oferta[4] else [],
                'descuento': oferta[5] or 0,
                'activa': bool(oferta[6]),
                'fecha_inicio': oferta[7],
                'fecha_fin': oferta[8]
            }
            try:
                save_offer(oferta_dict)
            except Exception as e:
                print(f"⚠️ Error migrando oferta {oferta[0]}: {e}")
        
        print(f"✅ Migradas {len(ofertas_sqlite)} ofertas")
        
        # 3. Migrar órdenes
        print("📋 Migrando órdenes...")
        sqlite_cursor.execute('SELECT id, fecha, productos, oferta_aplicada, descuento_aplicado, total_sin_descuento, total_final, metodo_pago, cajero, estado FROM orders')
        ordenes_sqlite = sqlite_cursor.fetchall()
        
        for orden in ordenes_sqlite:
            orden_dict = {
                'id': orden[0],
                'fecha': orden[1],
                'productos': json.loads(orden[2]) if orden[2] else [],
                'oferta_aplicada': orden[3] or '',
                'descuento_aplicado': float(orden[4]) if orden[4] else 0.0,
                'total_sin_descuento': float(orden[5]) if orden[5] else 0.0,
                'total_final': float(orden[6]) if orden[6] else 0.0,
                'metodo_pago': orden[7] or '',
                'cajero': orden[8] or '',
                'estado': orden[9] if len(orden) > 9 and orden[9] else 'En preparación'
            }
            try:
                save_order(orden_dict)
            except Exception as e:
                print(f"⚠️ Error migrando orden {orden[0]}: {e}")
        
        print(f"✅ Migradas {len(ordenes_sqlite)} órdenes")
        
        # 4. Migrar usuarios (con precaución para no duplicar)
        print("👥 Migrando usuarios...")
        sqlite_cursor.execute('SELECT username, password, full_name, role, email, created_at, active FROM users')
        usuarios_sqlite = sqlite_cursor.fetchall()
        
        usuarios_migrados = 0
        for usuario in usuarios_sqlite:
            try:
                # Verificar si el usuario ya existe en PostgreSQL
                existing_users = load_users()
                usernames_existentes = [u['username'] for u in existing_users]
                
                if usuario[0] not in usernames_existentes:
                    # Crear directamente en PostgreSQL con hash existente
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute('''INSERT INTO users (username, password, full_name, role, email, created_at, active) 
                                     VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                                  (usuario[0], usuario[1], usuario[2], usuario[3], usuario[4], 
                                   usuario[5] or datetime.datetime.now(), int(bool(usuario[6]))))
                    conn.commit()
                    cursor.close()
                    return_connection(conn)
                    usuarios_migrados += 1
                    
            except Exception as e:
                print(f"⚠️ Error migrando usuario {usuario[0]}: {e}")
        
        print(f"✅ Migrados {usuarios_migrados} usuarios")
        
        # 5. Migrar categorías
        print("🏷️ Migrando categorías...")
        try:
            sqlite_cursor.execute('SELECT name FROM categories')
            categorias_sqlite = sqlite_cursor.fetchall()
            
            for categoria in categorias_sqlite:
                add_category(categoria[0])
                
            print(f"✅ Migradas {len(categorias_sqlite)} categorías")
        except Exception:
            print("ℹ️ No se encontraron categorías para migrar")
        
        sqlite_conn.close()
        
        # Renombrar archivo SQLite como respaldo
        backup_file = DB_FILE + ".backup_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        os.rename(DB_FILE, backup_file)
        print(f"📁 Archivo SQLite respaldado como: {backup_file}")
        
        print("🎉 ¡Migración completada exitosamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        return False
