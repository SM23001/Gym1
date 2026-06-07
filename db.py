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
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        phone TEXT NOT NULL,
        specialty TEXT NOT NULL,
        bio TEXT NOT NULL DEFAULT '',
        years_experience INTEGER
    );

    CREATE TABLE IF NOT EXISTS members (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        phone TEXT NOT NULL,
        membership_plan TEXT NOT NULL,
        notes TEXT NOT NULL DEFAULT ''
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

    migrations = """
    ALTER TABLE trainers ADD COLUMN IF NOT EXISTS email TEXT;
    ALTER TABLE trainers ADD COLUMN IF NOT EXISTS phone TEXT;
    ALTER TABLE trainers ADD COLUMN IF NOT EXISTS specialty TEXT;
    ALTER TABLE trainers ADD COLUMN IF NOT EXISTS bio TEXT NOT NULL DEFAULT '';
    ALTER TABLE trainers ADD COLUMN IF NOT EXISTS years_experience INTEGER;

    UPDATE trainers
    SET email = 'trainer' || id || '@gym.local'
    WHERE email IS NULL OR email = '';

    UPDATE trainers
    SET phone = '0000000'
    WHERE phone IS NULL OR phone = '';

    UPDATE trainers
    SET specialty = 'General'
    WHERE specialty IS NULL OR specialty = '';

    UPDATE trainers
    SET bio = ''
    WHERE bio IS NULL;

    CREATE UNIQUE INDEX IF NOT EXISTS trainers_email_unique ON trainers (email);

    ALTER TABLE members ADD COLUMN IF NOT EXISTS email TEXT;
    ALTER TABLE members ADD COLUMN IF NOT EXISTS phone TEXT;
    ALTER TABLE members ADD COLUMN IF NOT EXISTS membership_plan TEXT;
    ALTER TABLE members ADD COLUMN IF NOT EXISTS notes TEXT NOT NULL DEFAULT '';

    UPDATE members
    SET email = 'member' || id || '@gym.local'
    WHERE email IS NULL OR email = '';

    UPDATE members
    SET phone = '0000000'
    WHERE phone IS NULL OR phone = '';

    UPDATE members
    SET membership_plan = 'Standard'
    WHERE membership_plan IS NULL OR membership_plan = '';

    UPDATE members
    SET notes = ''
    WHERE notes IS NULL;

    CREATE UNIQUE INDEX IF NOT EXISTS members_email_unique ON members (email);
    """

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(ddl)
            cur.execute(migrations)

