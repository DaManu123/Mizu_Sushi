import sqlite3
import json
import os
from typing import List, Dict, Any, Optional
import hashlib

# Ruta por defecto de la base de datos
DB_FILE = os.path.join(os.path.dirname(__file__), 'mizu_sushi.db')


def init_db(path: Optional[str] = None):
    """Inicializa la base de datos SQLite y crea las tablas necesarias."""
    if path is None:
        path = os.path.join(os.path.dirname(__file__), 'mizu_sushi.db')
    conn = sqlite3.connect(path)
    c = conn.cursor()

    # Productos / menú
    c.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id TEXT PRIMARY KEY,
        name TEXT,
        description TEXT,
        price REAL,
        stock INTEGER DEFAULT 50,
        categoria TEXT DEFAULT 'general',
        activo INTEGER DEFAULT 1
    )
    ''')

    # Ofertas
    c.execute('''
    CREATE TABLE IF NOT EXISTS offers (
        id TEXT PRIMARY KEY,
        name TEXT,
        description TEXT,
        type TEXT,
        products_aplicables TEXT,
        descuento INTEGER,
        activa INTEGER,
        fecha_inicio TEXT,
        fecha_fin TEXT
    )
    ''')

    # Carrito temporal
    c.execute('''
    CREATE TABLE IF NOT EXISTS cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id TEXT,
        product_name TEXT,
        quantity INTEGER,
        price REAL
    )
    ''')

    # Pedidos / ventas
    c.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id TEXT PRIMARY KEY,
        fecha TEXT,
        productos TEXT,
        oferta_aplicada TEXT,
        descuento_aplicado REAL,
        total_sin_descuento REAL,
        total_final REAL,
        metodo_pago TEXT,
        cajero TEXT,
        estado TEXT DEFAULT 'En preparación'
    )
    ''')

    # Usuarios
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        full_name TEXT,
        role TEXT NOT NULL DEFAULT 'cliente',
        email TEXT,
        created_at TEXT,
        last_login TEXT,
        active INTEGER DEFAULT 1
    )
    ''')

    conn.commit()
    conn.close()
    
    # Inicializar usuarios por defecto después de crear las tablas
    init_default_users()
    
    # Asegurar migración: si la tabla orders ya existía sin la columna 'estado', agregarla
    try:
        conn = sqlite3.connect(path)
        c = conn.cursor()
        c.execute("PRAGMA table_info(orders)")
        cols = [r[1] for r in c.fetchall()]
        if 'estado' not in cols:
            c.execute("ALTER TABLE orders ADD COLUMN estado TEXT DEFAULT 'En preparación'")
            conn.commit()
        conn.close()
    except Exception:
        # No bloquear la inicialización si la migración falla
        pass

    # Asegurar migración: si la tabla products existe sin la columna 'categoria', agregarla
    try:
        conn = sqlite3.connect(path)
        c = conn.cursor()
        c.execute("PRAGMA table_info(products)")
        cols = [r[1] for r in c.fetchall()]
        if 'categoria' not in cols:
            # Agregar columna categoria con valor por defecto 'general'
            c.execute("ALTER TABLE products ADD COLUMN categoria TEXT DEFAULT 'general'")
            conn.commit()
        conn.close()
    except Exception:
        # No bloquear la inicialización si la migración falla
        pass

    # Asegurar existencia de tabla de categorías y sembrar valores por defecto
    try:
        conn = sqlite3.connect(path)
        c = conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            name TEXT PRIMARY KEY
        )
        ''')
        # Semillas por defecto
        defaults = [('Rolls',), ('Especiales',), ('Vegetarianos',), ('Postres',), ('Bebidas',)]
        c.executemany('INSERT OR IGNORE INTO categories (name) VALUES (?)', defaults)
        conn.commit()
        conn.close()
    except Exception:
        pass


def _get_conn(path: Optional[str] = None):
    if path is None:
        path = os.path.join(os.path.dirname(__file__), 'mizu_sushi.db')
    return sqlite3.connect(path)


def load_products() -> List[Dict[str, Any]]:
    conn = _get_conn()
    c = conn.cursor()
    c.execute('SELECT id, name, description, price, stock, categoria, activo FROM products')
    rows = c.fetchall()
    conn.close()
    productos = []
    for r in rows:
        productos.append({
            'id': r[0], 
            'nombre': r[1], 
            'descripcion': r[2], 
            'precio': r[3],
            'stock': r[4] if r[4] is not None else 50,
            'categoria': r[5] if r[5] is not None else 'general',
            'activo': bool(r[6]) if r[6] is not None else True
        })
    return productos


def save_product(prod: Dict[str, Any]):
    conn = _get_conn()
    c = conn.cursor()
    c.execute('REPLACE INTO products (id, name, description, price, stock, categoria, activo) VALUES (?, ?, ?, ?, ?, ?, ?)',
              (prod.get('id'), 
               prod.get('nombre'), 
               prod.get('descripcion', ''), 
               float(prod.get('precio', 0)),
               int(prod.get('stock', 50)),
               prod.get('categoria', 'general'),
               int(bool(prod.get('activo', True)))))
    conn.commit()
    conn.close()


def delete_product(product_id: str):
    conn = _get_conn()
    c = conn.cursor()
    c.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()


def load_offers() -> List[Dict[str, Any]]:
    conn = _get_conn()
    c = conn.cursor()
    c.execute('SELECT id, name, description, type, products_aplicables, descuento, activa, fecha_inicio, fecha_fin FROM offers')
    rows = c.fetchall()
    conn.close()
    ofertas = []
    for r in rows:
        try:
            productos = json.loads(r[4]) if r[4] else []
        except Exception:
            productos = []
        ofertas.append({
            'id': r[0],
            'nombre': r[1],
            'descripcion': r[2],
            'tipo': r[3],
            'productos_aplicables': productos,
            'descuento': r[5],
            'activa': bool(r[6]),
            'fecha_inicio': r[7],
            'fecha_fin': r[8]
        })
    return ofertas


def save_offer(oferta: Dict[str, Any]):
    conn = _get_conn()
    c = conn.cursor()
    productos_json = json.dumps(oferta.get('productos_aplicables', []), ensure_ascii=False)
    c.execute('REPLACE INTO offers (id, name, description, type, products_aplicables, descuento, activa, fecha_inicio, fecha_fin) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
              (oferta.get('id'), oferta.get('nombre'), oferta.get('descripcion'), oferta.get('tipo'), productos_json,
               int(oferta.get('descuento', 0)), int(bool(oferta.get('activa', True))), oferta.get('fecha_inicio'), oferta.get('fecha_fin')))
    conn.commit()
    conn.close()


def load_categories() -> List[str]:
    """Devuelve la lista de categorías únicas de productos."""
    conn = _get_conn()
    c = conn.cursor()
    try:
        # Intentar cargar desde la tabla categories si existe
        try:
            c.execute('SELECT name FROM categories ORDER BY name COLLATE NOCASE')
            rows = c.fetchall()
            if rows:
                return [r[0] for r in rows if r and r[0]]
        except Exception:
            # Si no existe la tabla categories, fallback a distinct en products
            pass

        c.execute("SELECT DISTINCT categoria FROM products WHERE categoria IS NOT NULL")
        rows = c.fetchall()
        return [r[0] for r in rows if r and r[0]]
    except Exception:
        return []
    finally:
        conn.close()


def set_product_category(product_id: str, categoria: str):
    """Establece/actualiza la categoría de un producto dado."""
    conn = _get_conn()
    c = conn.cursor()
    try:
        c.execute('UPDATE products SET categoria = ? WHERE id = ?', (categoria, product_id))
        conn.commit()
    finally:
        conn.close()


def add_category(name: str):
    """Agrega una categoría a la tabla categories (ignora si ya existe)."""
    conn = _get_conn()
    c = conn.cursor()
    try:
        c.execute('INSERT OR IGNORE INTO categories (name) VALUES (?)', (name,))
        conn.commit()
    finally:
        conn.close()


def get_product_by_id(product_id: str) -> Optional[Dict[str, Any]]:
    conn = _get_conn()
    c = conn.cursor()
    try:
        c.execute('SELECT id, name, description, price, stock, categoria, activo FROM products WHERE id = ?', (product_id,))
        r = c.fetchone()
        if not r:
            return None
        return {
            'id': r[0],
            'nombre': r[1],
            'descripcion': r[2],
            'precio': r[3],
            'stock': r[4] if r[4] is not None else 0,
            'categoria': r[5] if r[5] is not None else 'general',
            'activo': bool(r[6]) if r[6] is not None else True
        }
    finally:
        conn.close()


def get_product_by_name(name: str) -> Optional[Dict[str, Any]]:
    conn = _get_conn()
    c = conn.cursor()
    try:
        c.execute('SELECT id, name, description, price, stock, categoria, activo FROM products WHERE name = ?', (name,))
        r = c.fetchone()
        if not r:
            # Try case-insensitive match
            c.execute('SELECT id, name, description, price, stock, categoria, activo FROM products WHERE LOWER(name) = LOWER(?)', (name,))
            r = c.fetchone()
            if not r:
                return None
        return {
            'id': r[0],
            'nombre': r[1],
            'descripcion': r[2],
            'precio': r[3],
            'stock': r[4] if r[4] is not None else 0,
            'categoria': r[5] if r[5] is not None else 'general',
            'activo': bool(r[6]) if r[6] is not None else True
        }
    finally:
        conn.close()


def update_product_stock(product_id: str, delta: int) -> int:
    """Ajusta el stock del producto por delta (positivo o negativo). Devuelve el stock resultante."""
    conn = _get_conn()
    c = conn.cursor()
    try:
        c.execute('SELECT stock FROM products WHERE id = ?', (product_id,))
        r = c.fetchone()
        if not r:
            raise ValueError('Producto no encontrado')
        current = r[0] if r[0] is not None else 0
        new_stock = int(current + int(delta))
        if new_stock < 0:
            new_stock = 0
        c.execute('UPDATE products SET stock = ? WHERE id = ?', (new_stock, product_id))
        conn.commit()
        return new_stock
    finally:
        conn.close()


def delete_offer(oferta_id: str):
    conn = _get_conn()
    c = conn.cursor()
    c.execute('DELETE FROM offers WHERE id = ?', (oferta_id,))
    conn.commit()
    conn.close()


def toggle_offer(oferta_id: str, activo: bool):
    conn = _get_conn()
    c = conn.cursor()
    c.execute('UPDATE offers SET activa = ? WHERE id = ?', (int(bool(activo)), oferta_id))
    conn.commit()
    conn.close()


def load_orders() -> List[Dict[str, Any]]:
    conn = _get_conn()
    c = conn.cursor()
    c.execute('SELECT id, fecha, productos, oferta_aplicada, descuento_aplicado, total_sin_descuento, total_final, metodo_pago, cajero, estado FROM orders')
    rows = c.fetchall()
    conn.close()
    orders = []
    for r in rows:
        try:
            productos = json.loads(r[2])
        except Exception:
            productos = []
        orders.append({
            'id': r[0],
            'fecha': r[1],
            'productos': productos,
            'oferta_aplicada': r[3],
            'descuento_aplicado': r[4],
            'total_sin_descuento': r[5],
            'total_final': r[6],
            'metodo_pago': r[7],
            'cajero': r[8],
            'estado': r[9] if len(r) > 9 else 'En preparación'
        })
    return orders


def save_order(order: Dict[str, Any]):
    conn = _get_conn()
    c = conn.cursor()
    productos_json = json.dumps(order.get('productos', []), ensure_ascii=False)
    c.execute('REPLACE INTO orders (id, fecha, productos, oferta_aplicada, descuento_aplicado, total_sin_descuento, total_final, metodo_pago, cajero, estado) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
              (order.get('id'), order.get('fecha'), productos_json, order.get('oferta_aplicada'), float(order.get('descuento_aplicado', 0)),
               float(order.get('total_sin_descuento', 0)), float(order.get('total_final', 0)), order.get('metodo_pago'), order.get('cajero'), order.get('estado', 'En preparación')))
    conn.commit()
    conn.close()


def add_cart_item(product_id: str, product_name: str, quantity: int, price: float):
    conn = _get_conn()
    c = conn.cursor()
    # Si el item ya existe, incrementar cantidad
    c.execute('SELECT id, quantity FROM cart WHERE product_id = ?', (product_id,))
    row = c.fetchone()
    if row:
        new_q = row[1] + quantity
        c.execute('UPDATE cart SET quantity = ? WHERE id = ?', (new_q, row[0]))
    else:
        c.execute('INSERT INTO cart (product_id, product_name, quantity, price) VALUES (?, ?, ?, ?)',
                  (product_id, product_name, int(quantity), float(price)))
    conn.commit()
    conn.close()


def get_cart_items() -> List[Dict[str, Any]]:
    conn = _get_conn()
    c = conn.cursor()
    c.execute('SELECT id, product_id, product_name, quantity, price FROM cart')
    rows = c.fetchall()
    conn.close()
    return [{'id': r[0], 'product_id': r[1], 'product_name': r[2], 'quantity': r[3], 'price': r[4]} for r in rows]


def clear_cart():
    conn = _get_conn()
    c = conn.cursor()
    c.execute('DELETE FROM cart')
    conn.commit()
    conn.close()


def update_cart_item_quantity(item_id: int, new_quantity: int):
    """Actualiza la cantidad de un item específico en el carrito"""
    conn = _get_conn()
    c = conn.cursor()
    c.execute('UPDATE cart SET quantity = ? WHERE id = ?', (int(new_quantity), int(item_id)))
    conn.commit()
    conn.close()


def remove_cart_item(item_id: int):
    """Elimina un item específico del carrito"""
    conn = _get_conn()
    c = conn.cursor()
    c.execute('DELETE FROM cart WHERE id = ?', (int(item_id),))
    conn.commit()
    conn.close()


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
    """Crea un nuevo usuario en la base de datos"""
    import hashlib
    import datetime
    
    conn = _get_conn()
    c = conn.cursor()
    try:
        # Hash de la contraseña
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Insertar usuario
        c.execute('''INSERT INTO users (username, password, full_name, role, email, created_at, active) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (username, password_hash, full_name, role, email, 
                   datetime.datetime.now().isoformat(), 1))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Usuario ya existe
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Autentica un usuario y devuelve sus datos si es válido"""
    import hashlib
    import datetime
    
    conn = _get_conn()
    c = conn.cursor()
    
    # Hash de la contraseña
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    c.execute('''SELECT id, username, full_name, role, email, created_at, last_login 
                 FROM users WHERE username = ? AND password = ? AND active = 1''',
              (username, password_hash))
    row = c.fetchone()
    
    if row:
        # Actualizar último login
        c.execute('UPDATE users SET last_login = ? WHERE id = ?',
                  (datetime.datetime.now().isoformat(), row[0]))
        conn.commit()
        
        user_data = {
            'id': row[0],
            'username': row[1],
            'full_name': row[2],
            'role': row[3],
            'email': row[4],
            'created_at': row[5],
            'last_login': row[6]
        }
        conn.close()
        return user_data
    
    conn.close()
    return None


def load_users() -> List[Dict[str, Any]]:
    """Carga todos los usuarios de la base de datos"""
    conn = _get_conn()
    c = conn.cursor()
    c.execute('''SELECT id, username, full_name, role, email, created_at, last_login, active 
                 FROM users ORDER BY created_at DESC''')
    rows = c.fetchall()
    conn.close()
    
    users = []
    for row in rows:
        users.append({
            'id': row[0],
            'username': row[1],
            'full_name': row[2],
            'role': row[3],
            'email': row[4],
            'created_at': row[5],
            'last_login': row[6],
            'active': bool(row[7])
        })
    return users


def update_user(user_id: int, full_name: Optional[str] = None, role: Optional[str] = None, email: Optional[str] = None, active: Optional[bool] = None):
    """Actualiza información de un usuario"""
    conn = _get_conn()
    c = conn.cursor()
    
    updates = []
    params = []
    
    if full_name is not None:
        updates.append("full_name = ?")
        params.append(full_name)
    
    if role is not None:
        updates.append("role = ?")
        params.append(role)
    
    if email is not None:
        updates.append("email = ?")
        params.append(email)
    
    if active is not None:
        updates.append("active = ?")
        params.append(int(active))
    
    if updates:
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        params.append(user_id)
        c.execute(query, params)
        conn.commit()
    
    conn.close()


def delete_user(user_id: int):
    """Elimina un usuario de la base de datos"""
    conn = _get_conn()
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()


def change_user_password(user_id: int, new_password: str) -> bool:
    """Cambia la contraseña de un usuario"""
    import hashlib
    
    try:
        conn = _get_conn()
        c = conn.cursor()
        
        # Hash de la nueva contraseña
        password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        
        c.execute('UPDATE users SET password = ? WHERE id = ?', (password_hash, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def init_default_users():
    """Inicializar usuarios por defecto si no existen"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Verificar si ya hay usuarios
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    
    if count == 0:
        # Crear usuarios por defecto
        default_users = [
            ("admin", "123456", "Administrador del Sistema", "admin", "admin@mizusushi.com"),
            ("cajero1", "123456", "Cajero Principal", "cajero", "cajero@mizusushi.com"),
            ("cliente1", "123456", "Cliente Demo", "cliente", "cliente@mizusushi.com")
        ]
        
        for username, password, full_name, role, email in default_users:
            create_user(username, password, full_name, role, email)
        
        print("Usuarios por defecto creados exitosamente")
    
    conn.close()

# Función de inicialización principal actualizada
    """Inicializa usuarios por defecto si no existen"""
    try:
        # Verificar si ya hay usuarios
        users = load_users()
        if not users:
            # Crear usuarios por defecto
            create_user("admin", "admin123", "Administrador", "admin", "admin@mizusushi.com")
            create_user("cajero", "cajero123", "Cajero Principal", "cajero", "cajero@mizusushi.com")
            create_user("cliente", "cliente123", "Cliente Demo", "cliente", "cliente@mizusushi.com")
            return True
    except Exception:
        pass
    return False
