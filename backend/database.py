import sqlite3

def get_connection():
    conn = sqlite3.connect("inventario.db")
    conn.row_factory = sqlite3.Row
    return conn

def crear_tabla():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            cantidad INTEGER,
            tipo TEXT,
            marca TEXT,
            fecha_ingreso TEXT,
            fecha_caducidad TEXT
        )
    """)

    conn.commit()
    conn.close()

def actualizar_tabla():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Crear nueva tabla
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos_nueva (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT,
                cantidad INTEGER,
                tipo TEXT,
                marca TEXT,
                fecha_ingreso TEXT,
                fecha_caducidad TEXT
            )
        """)

        cursor.execute("""
            INSERT INTO productos_nueva (id, nombre, cantidad, tipo, marca, fecha_ingreso, fecha_caducidad)
            SELECT id, nombre, cantidad, tipo, marca, fecha_ingreso, fecha_caducidad
            FROM productos
        """)

        cursor.execute("DROP TABLE productos")

        cursor.execute("ALTER TABLE productos_nueva RENAME TO productos")

        conn.commit()

    except Exception as e:
        print("Error actualizando tabla:", e)

    finally:
        conn.close()
