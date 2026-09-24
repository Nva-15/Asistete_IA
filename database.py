import sqlite3
import pandas as pd
from datetime import date, datetime, timedelta

DB_PATH = "panaderia.db"

def _conn():
    return sqlite3.connect(DB_PATH)

def obtener_stock():
    with _conn() as conn:
        return pd.read_sql_query(
            "SELECT id, nombre AS producto, stock_actual, stock_minimo, precio "
            "FROM productos", conn
        )

def obtener_ventas_dia(fecha=None):
    fecha = fecha or date.today().isoformat()
    with _conn() as conn:
        return pd.read_sql_query("""
            SELECT v.hora, p.nombre AS producto, v.cantidad, v.total
            FROM ventas v
            JOIN productos p ON p.id = v.producto_id
            WHERE v.fecha = ?
            ORDER BY v.hora
        """, conn, params=(fecha,))

def obtener_ventas_semana():
    inicio = (date.today() - timedelta(days=6)).isoformat()
    with _conn() as conn:
        return pd.read_sql_query("""
            SELECT fecha, SUM(total) AS total
            FROM ventas WHERE fecha >= ?
            GROUP BY fecha ORDER BY fecha
        """, conn, params=(inicio,))

def obtener_top_productos(fecha=None, limite=5):
    fecha = fecha or date.today().isoformat()
    with _conn() as conn:
        return pd.read_sql_query("""
            SELECT p.nombre AS producto, SUM(v.cantidad) AS cantidad,
                   SUM(v.total) AS total
            FROM ventas v
            JOIN productos p ON p.id = v.producto_id
            WHERE v.fecha = ?
            GROUP BY p.nombre
            ORDER BY cantidad DESC LIMIT ?
        """, conn, params=(fecha, limite))

def obtener_consumo_promedio(dias=7):
    inicio = (date.today() - timedelta(days=dias)).isoformat()
    with _conn() as conn:
        return pd.read_sql_query("""
            SELECT p.nombre AS producto,
                   ROUND(SUM(v.cantidad) * 1.0 / ?, 2) AS consumo_diario
            FROM ventas v
            JOIN productos p ON p.id = v.producto_id
            WHERE v.fecha >= ?
            GROUP BY p.nombre
        """, conn, params=(dias, inicio))

def registrar_venta(producto_id, cantidad, total, usuario="sistema"):
    ahora = datetime.now()
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO ventas (fecha, hora, producto_id, cantidad, total, usuario)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (ahora.date().isoformat(), ahora.strftime("%H:%M:%S"),
              producto_id, cantidad, total, usuario))
        cur.execute("""
            UPDATE productos SET stock_actual = stock_actual - ?
            WHERE id = ?
        """, (cantidad, producto_id))
        conn.commit()

def guardar_reporte(tipo, contenido):
    with _conn() as conn:
        conn.execute("""
            INSERT INTO reportes_ia (tipo, fecha_generacion, contenido)
            VALUES (?, ?, ?)
        """, (tipo, datetime.now().isoformat(), contenido))
        conn.commit()

def obtener_ultimo_reporte(tipo):
    """Devuelve (contenido, fecha_generacion) del último reporte guardado de ese tipo, o None."""
    with _conn() as conn:
        cur = conn.execute("""
            SELECT contenido, fecha_generacion FROM reportes_ia
            WHERE tipo = ? ORDER BY fecha_generacion DESC LIMIT 1
        """, (tipo,))
        return cur.fetchone()

def guardar_notificacion(tipo, prioridad, mensaje):
    with _conn() as conn:
        conn.execute("""
            INSERT INTO notificaciones (tipo, prioridad, mensaje, fecha)
            VALUES (?, ?, ?, ?)
        """, (tipo, prioridad, mensaje, datetime.now().isoformat()))
        conn.commit()

def marcar_notificacion_leida(notificacion_id):
    with _conn() as conn:
        conn.execute("UPDATE notificaciones SET leida = 1 WHERE id = ?", (notificacion_id,))
        conn.commit()

def limpiar_notificaciones_leidas():
    with _conn() as conn:
        conn.execute("DELETE FROM notificaciones WHERE leida = 1")
        conn.commit()

def obtener_notificaciones_no_leidas():
    with _conn() as conn:
        return pd.read_sql_query("""
            SELECT id, tipo, prioridad, mensaje, fecha
            FROM notificaciones WHERE leida = 0
            ORDER BY fecha DESC
        """, conn)


def obtener_ventas_rango(desde, hasta):
    """Ventas entre dos fechas ISO (inclusive), con el costo de lo vendido."""
    with _conn() as conn:
        return pd.read_sql_query("""
            SELECT v.fecha, v.hora, p.nombre AS producto, v.cantidad, v.total,
                   v.cantidad * p.costo AS costo_total
            FROM ventas v
            JOIN productos p ON p.id = v.producto_id
            WHERE v.fecha BETWEEN ? AND ?
            ORDER BY v.fecha, v.hora
        """, conn, params=(desde, hasta))

def obtener_margen_productos():
    """Precio, costo y margen unitario (soles y %) de cada producto."""
    with _conn() as conn:
        return pd.read_sql_query("""
            SELECT nombre AS producto, precio, costo,
                   ROUND(precio - costo, 2) AS margen_unitario,
                   ROUND((precio - costo) * 100.0 / precio, 1) AS margen_pct
            FROM productos ORDER BY margen_pct DESC
        """, conn)