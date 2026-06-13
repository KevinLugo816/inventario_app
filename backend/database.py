import os
import psycopg2
import psycopg2.extras

def get_connection():
    conn = psycopg2.connect(
        host=os.environ.get("PGHOST"),
        user=os.environ.get("PGUSER"),
        password=os.environ.get("PGPASSWORD"),
        dbname=os.environ.get("PGDATABASE"),
        port=os.environ.get("PGPORT", 5432)
    )
    return conn


def crear_tabla():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            tipo TEXT DEFAULT 'Por definir',
            marca TEXT DEFAULT 'Por definir',
            fecha_ingreso DATE DEFAULT CURRENT_DATE,
            fecha_caducidad TEXT DEFAULT 'Por definir'
        )
    """)

    conn.commit()
    conn.close()


def actualizar_tabla():
    pass
