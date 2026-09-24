"""
Inicialización automática del entorno para Streamlit Cloud.

Auto-suficiente: no depende de seed_data.py ni init_db.py.
Crea tablas, inserta productos y genera ventas si la BD está vacía.

Evita el IndexError cuando la tabla de productos está vacía.
"""
import os
import sqlite3
import random
import streamlit as st
from datetime import date, timedelta

DB_PATH = "panaderia.db"


# ============================================================
# PRODUCTOS POR DEFECTO (por si la tabla está vacía)
# ============================================================
PRODUCTOS_DEFAULT = [
    ("Pan francés",        0.50, 0.25, 120, 40),
    ("Pan integral",       0.75, 0.40,  25, 20),
    ("Torta de chocolate", 3.50, 1.80,   4, 10),
    ("Empanada",           1.50, 0.80,  18, 15),
    ("Alfajor",            2.00, 1.00,  35, 20),
    ("Pan de yema",        0.80, 0.45,  60, 25),
    ("Croissant",          2.50, 1.20,   8, 15),
    ("Bizcocho",           1.20, 0.60,  45, 20),
    ("Pan de molde",       4.00, 2.00,  12, 10),
    ("Galleta surtida",    1.00, 0.50,  80, 30),
]

HORARIOS = [
    "07:15", "07:45", "08:30", "09:00", "09:45",
    "11:00", "11:30", "12:30", "13:00", "13:45",
    "15:00", "15:30", "16:30", "17:00", "17:45",
    "18:00", "18:30", "19:00"
]


# ============================================================
# HELPERS
# ============================================================
def _conn():
    return sqlite3.connect(DB_PATH)


def _existe_bd():
    return os.path.exists(DB_PATH)


def _contar(tabla):
    """Cuenta filas de una tabla, devuelve 0 si no existe."""
    try:
        with _conn() as conn:
            return conn.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
    except Exception:
        return 0


# ============================================================
# CREAR ESQUEMA Y PRODUCTOS
# ============================================================
def _crear_tablas():
    """Crea todas las tablas si no existen."""
    with _conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                precio REAL NOT NULL,
                costo REAL NOT NULL DEFAULT 0,
                stock_actual INTEGER NOT NULL DEFAULT 0,
                stock_minimo INTEGER NOT NULL DEFAULT 10
            );

            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                hora TEXT NOT NULL,
                producto_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL,
                total REAL NOT NULL,
                usuario TEXT
            );

            CREATE TABLE IF NOT EXISTS movimientos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                producto_id INTEGER NOT NULL,
                tipo TEXT NOT NULL,
                cantidad INTEGER NOT NULL,
                motivo TEXT
            );

            CREATE TABLE IF NOT EXISTS reportes_ia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                fecha_generacion TEXT NOT NULL,
                contenido TEXT NOT NULL,
                leido INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS notificaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                prioridad TEXT NOT NULL,
                mensaje TEXT NOT NULL,
                fecha TEXT NOT NULL,
                leida INTEGER DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha);
            CREATE INDEX IF NOT EXISTS idx_ventas_producto ON ventas(producto_id);
        """)
        conn.commit()


def _insertar_productos_default():
    """Inserta los 10 productos base si la tabla está vacía."""
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM productos")
        n = cur.fetchone()[0]

        if n > 0:
            print(f"[init] Ya hay {n} productos")
            return n

        cur.executemany("""
            INSERT OR IGNORE INTO productos
                (nombre, precio, costo, stock_actual, stock_minimo)
            VALUES (?, ?, ?, ?, ?)
        """, PRODUCTOS_DEFAULT)
        conn.commit()

        cur.execute("SELECT COUNT(*) FROM productos")
        n = cur.fetchone()[0]
        print(f"[init] {n} productos insertados")
        return n


# ============================================================
# GENERAR VENTAS HISTÓRICAS
# ============================================================
def _generar_ventas_historicas(dias=30):
    """Genera ventas para los últimos N días (incluyendo hoy)."""
    with _conn() as conn:
        cur = conn.cursor()

        cur.execute("SELECT id, nombre, precio, stock_actual FROM productos")
        prods = [
            {"id": r[0], "nombre": r[1], "precio": r[2], "stock": r[3]}
            for r in cur.fetchall()
        ]

        if not prods:
            print("[init] No hay productos, no se generan ventas")
            return 0

        hoy = date.today()
        total = 0

        for i in range(dias - 1, -1, -1):
            fecha = hoy - timedelta(days=i)

            # Menos ventas si es hoy (día no terminado)
            if i == 0:
                num_ventas = random.randint(8, 18)
            else:
                num_ventas = random.randint(15, 30)

            for _ in range(num_ventas):
                # Elegir producto con stock
                disponibles = [p for p in prods if p["stock"] > 0]
                if not disponibles:
                    break

                prod = random.choice(disponibles)

                # Cantidad según producto
                if prod["nombre"] == "Pan francés":
                    cant = random.randint(3, 12)
                elif prod["nombre"] in ("Alfajor", "Bizcocho", "Galleta surtida"):
                    cant = random.randint(1, 5)
                else:
                    cant = random.randint(1, 6)

                cant = min(cant, prod["stock"])
                if cant <= 0:
                    continue

                total_venta = round(cant * prod["precio"], 2)
                hora = random.choice(HORARIOS)

                cur.execute("""
                    INSERT INTO ventas (fecha, hora, producto_id, cantidad, total, usuario)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (fecha.isoformat(), hora, prod["id"], cant, total_venta, "seed"))

                cur.execute("""
                    UPDATE productos SET stock_actual = stock_actual - ?
                    WHERE id = ?
                """, (cant, prod["id"]))

                prod["stock"] -= cant
                total += 1

        conn.commit()

    print(f"[init] {total} ventas generadas en {dias} días")
    return total


# ============================================================
# INYECTAR VENTAS DE HOY
# ============================================================
def _inyectar_ventas_hoy(min_ventas=15):
    """Inyecta ventas para hoy si no existen suficientes."""
    hoy = date.today().isoformat()

    with _conn() as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        cur = conn.cursor()

        # ¿Cuántas ventas hay hoy?
        cur.execute("SELECT COUNT(*) FROM ventas WHERE fecha = ?", (hoy,))
        existentes = cur.fetchone()[0]

        if existentes >= min_ventas:
            print(f"[init] Ya hay {existentes} ventas hoy")
            return 0

        faltan = min_ventas - existentes
        print(f"[init] Inyectando {faltan} ventas para hoy...")

        # GUARD 1: verificar que hay productos
        cur.execute("SELECT COUNT(*) FROM productos")
        if cur.fetchone()[0] == 0:
            print("[init] No hay productos. No se puede inyectar.")
            return 0

        # Traer productos con stock
        cur.execute("""
            SELECT id, nombre, precio, stock_actual
            FROM productos WHERE stock_actual > 0
        """)
        productos = [list(r) for r in cur.fetchall()]

        # Si no hay stock, reponer TODOS
        if not productos:
            print("[init] Sin stock. Reponiendo todos los productos...")
            cur.execute("UPDATE productos SET stock_actual = stock_minimo + 100")
            conn.commit()

            cur.execute("""
                SELECT id, nombre, precio, stock_actual
                FROM productos WHERE stock_actual > 0
            """)
            productos = [list(r) for r in cur.fetchall()]

        # GUARD 2: si aún está vacío, salir sin error
        if not productos:
            print("[init] No hay productos con stock. Abortando inyección.")
            return 0

        inyectadas = 0
        intentos = 0
        max_intentos = faltan * 5

        while inyectadas < faltan and intentos < max_intentos:
            intentos += 1

            if not productos:
                break

            prod = random.choice(productos)
            prod_id, nombre, precio, stock = prod

            if stock <= 0:
                productos = [p for p in productos if p[0] != prod_id]
                continue

            # Cantidad según producto
            if nombre == "Pan francés":
                cant = random.randint(3, 12)
            elif nombre in ("Alfajor", "Bizcocho", "Galleta surtida"):
                cant = random.randint(1, 5)
            else:
                cant = random.randint(1, 6)

            cant = min(cant, stock)
            if cant <= 0:
                continue

            total = round(cant * precio, 2)
            hora = random.choice(HORARIOS)

            cur.execute("""
                INSERT INTO ventas (fecha, hora, producto_id, cantidad, total, usuario)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (hoy, hora, prod_id, cant, total, "auto"))

            cur.execute("""
                UPDATE productos SET stock_actual = stock_actual - ?
                WHERE id = ?
            """, (cant, prod_id))

            prod[3] -= cant
            if prod[3] <= 0:
                productos = [p for p in productos if p[0] != prod_id]

            inyectadas += 1

        conn.commit()
        print(f"[init] {inyectadas} ventas inyectadas")
        return inyectadas


# ============================================================
# INICIALIZACIÓN PRINCIPAL
# ============================================================
@st.cache_resource(show_spinner="🚀 Inicializando sistema...")
def inicializar_entorno():
    """
    Flujo:
      1. Crear tablas si no existen.
      2. Insertar productos si la tabla está vacía.
      3. Generar ventas históricas si no hay.
      4. Inyectar ventas de hoy si no hay.
    """
    print("=" * 60)
    print("[init] Iniciando verificación del entorno...")
    print("=" * 60)

    # 1. Crear tablas
    _crear_tablas()

    # 2. Productos
    n_prod = _contar("productos")
    if n_prod == 0:
        print("[init] No hay productos. Insertando...")
        _insertar_productos_default()
    else:
        print(f"[init] BD ya tiene {n_prod} productos")

    # 3. Ventas históricas
    n_ventas = _contar("ventas")
    if n_ventas < 50:
        print(f"[init] Solo {n_ventas} ventas. Generando 30 días...")
        _generar_ventas_historicas(dias=30)
    else:
        print(f"[init] BD ya tiene {n_ventas} ventas")

    # 4. Ventas de hoy
    hoy = date.today().isoformat()
    with _conn() as conn:
        cur = conn.execute(
            "SELECT COUNT(*) FROM ventas WHERE fecha = ?", (hoy,)
        )
        n_hoy = cur.fetchone()[0]

    if n_hoy < 15:
        _inyectar_ventas_hoy(min_ventas=15)
    else:
        print(f"[init] Ya hay {n_hoy} ventas hoy")

    print("=" * 60)
    print("[init] Entorno listo")
    print("=" * 60)
    return True