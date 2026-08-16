"""
Capa de acceso a SQLite. Sin ORM a propósito: el schema es chico y
sqlite3 (stdlib) alcanza — sumar SQLAlchemy aquí sería complejidad
sin beneficio real por ahora.
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.config import DB_PATH

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Crea las tablas si no existen. Idempotente — seguro de llamar
    en cada arranque de la app."""
    with _connect() as conn:
        conn.executescript(SCHEMA_PATH.read_text())


@contextmanager
def get_connection():
    """Uso: `with get_connection() as conn: ...`. Hace commit al salir
    sin error, rollback si hay excepción."""
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
