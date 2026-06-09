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
        capacity INTEGER NOT NULL,
        start_date DATE,
        end_date DATE,
        price NUMERIC(10, 2) NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'scheduled',
        CONSTRAINT classes_price_check CHECK (price >= 0),
        CONSTRAINT classes_status_check
            CHECK (status IN ('scheduled', 'started', 'ended')),
        CONSTRAINT classes_dates_check
            CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date)
    );

    CREATE TABLE IF NOT EXISTS class_schedules (
        id SERIAL PRIMARY KEY,
        class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
        day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
        start_time TIME NOT NULL,
        end_time TIME NOT NULL,
        CHECK (end_time > start_time),
        UNIQUE (class_id, day_of_week, start_time, end_time)
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

    ALTER TABLE classes ADD COLUMN IF NOT EXISTS start_date DATE;
    ALTER TABLE classes ADD COLUMN IF NOT EXISTS end_date DATE;
    ALTER TABLE classes ADD COLUMN IF NOT EXISTS price NUMERIC(10, 2) NOT NULL DEFAULT 0;
    ALTER TABLE classes ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'scheduled';

    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'classes_price_check'
        ) THEN
            ALTER TABLE classes
                ADD CONSTRAINT classes_price_check CHECK (price >= 0);
        END IF;
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'classes_status_check'
        ) THEN
            ALTER TABLE classes
                ADD CONSTRAINT classes_status_check
                CHECK (status IN ('scheduled', 'started', 'ended'));
        END IF;
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'classes_dates_check'
        ) THEN
            ALTER TABLE classes
                ADD CONSTRAINT classes_dates_check
                CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date);
        END IF;
    END $$;

    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = 'classes'
              AND column_name = 'day_of_week'
        ) THEN
            INSERT INTO class_schedules (class_id, day_of_week, start_time, end_time)
            SELECT id, day_of_week, start_time, end_time FROM classes
            ON CONFLICT DO NOTHING;

            ALTER TABLE classes DROP COLUMN day_of_week;
            ALTER TABLE classes DROP COLUMN start_time;
            ALTER TABLE classes DROP COLUMN end_time;
        END IF;
    END $$;
    """

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(ddl)
            cur.execute(migrations)

