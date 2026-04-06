import sqlite3
from datetime import datetime

DB_NAME = "grademaster.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS SesionRevision (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_prueba TEXT NOT NULL,
            fecha_creacion TEXT NOT NULL
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ConfiguracionRubrica (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sesion_id INTEGER NOT NULL,
            enunciado TEXT,
            hoja_objetivo TEXT NOT NULL DEFAULT 'Hoja1',
            celda_objetivo TEXT NOT NULL,
            formula_esperada TEXT,
            valor_esperado TEXT,
            puntos_formula REAL NOT NULL,
            puntos_valor REAL NOT NULL,
            FOREIGN KEY (sesion_id) REFERENCES SesionRevision(id)
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ResultadosEstudiantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sesion_id INTEGER NOT NULL,
            nombre_estudiante TEXT NOT NULL,
            puntaje_total REAL,
            detalle_json TEXT,
            FOREIGN KEY (sesion_id) REFERENCES SesionRevision(id)
        );
        """)

        # Migración: agregar hoja_objetivo si la tabla ya existía sin esa columna
        cursor.execute("PRAGMA table_info(ConfiguracionRubrica)")
        columnas = [row[1] for row in cursor.fetchall()]
        if "hoja_objetivo" not in columnas:
            cursor.execute(
                "ALTER TABLE ConfiguracionRubrica ADD COLUMN hoja_objetivo TEXT NOT NULL DEFAULT 'Hoja1'"
            )
        if "grupo_id" not in columnas:
            cursor.execute(
                "ALTER TABLE ConfiguracionRubrica ADD COLUMN grupo_id INTEGER NOT NULL DEFAULT 0"
            )

        conn.commit()

def crear_sesion(nombre_prueba: str) -> int:
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO SesionRevision (nombre_prueba, fecha_creacion) VALUES (?, ?)",
            (nombre_prueba, fecha)
        )
        conn.commit()
        return cursor.lastrowid

def guardar_rubrica(sesion_id: int, items: list[dict]):
    with get_connection() as conn:
        cursor = conn.cursor()
        for item in items:
            cursor.execute("""
            INSERT INTO ConfiguracionRubrica
            (sesion_id, enunciado, hoja_objetivo, celda_objetivo, formula_esperada, valor_esperado, puntos_formula, puntos_valor, grupo_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sesion_id,
                item.get("enunciado"),
                item.get("hoja_objetivo", "Hoja1"),
                item.get("celda_objetivo"),
                item.get("formula_esperada"),
                item.get("valor_esperado"),
                item.get("puntos_formula"),
                item.get("puntos_valor"),
                item.get("grupo_id", 0)
            ))
        conn.commit()

def obtener_rubrica(sesion_id: int) -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ConfiguracionRubrica WHERE sesion_id = ?", (sesion_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def guardar_resultado(sesion_id: int, nombre_estudiante: str, puntaje_total: float, detalle_json: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO ResultadosEstudiantes (sesion_id, nombre_estudiante, puntaje_total, detalle_json)
        VALUES (?, ?, ?, ?)
        """, (sesion_id, nombre_estudiante, puntaje_total, detalle_json))
        conn.commit()

def obtener_resultados(sesion_id: int) -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ResultadosEstudiantes WHERE sesion_id = ?", (sesion_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
