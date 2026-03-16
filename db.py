from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor

from config import get_settings


@contextmanager
def get_connection():
    settings = get_settings()
    conn = psycopg2.connect(settings.dsn)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_schema() -> None:
    """Crea las tablas necesarias si no existen."""
    ddl = """
    CREATE TABLE IF NOT EXISTS trainers (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS members (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS classes (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        trainer_id INTEGER NOT NULL REFERENCES trainers(id) ON DELETE RESTRICT,
        day_of_week INTEGER NOT NULL,
        start_time TIME NOT NULL,
        end_time TIME NOT NULL,
        capacity INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS enrollments (
        class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
        member_id INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
        PRIMARY KEY (class_id, member_id)
    );

    CREATE TABLE IF NOT EXISTS attendance (
        class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
        member_id INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
        attended_at TIMESTAMP NOT NULL DEFAULT NOW(),
        PRIMARY KEY (class_id, member_id, attended_at)
    );
    """

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(ddl)

