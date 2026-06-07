from datetime import time
from typing import List, Optional

from psycopg2.extras import RealDictCursor

from db import get_connection
from models import Trainer, Member, GymClass, Enrollment, Attendance

_TRAINER_COLUMNS = (
    "id, name, email, phone, specialty, bio, years_experience"
)

_MEMBER_COLUMNS = (
    "id, name, email, phone, membership_plan, notes"
)

_CLASS_SELECT = """
    c.id, c.name, c.trainer_id, c.day_of_week, c.start_time, c.end_time, c.capacity,
    t.name AS trainer_name
"""

_CLASS_RETURNING = """
    id, name, trainer_id, day_of_week, start_time, end_time, capacity,
    (SELECT name FROM trainers WHERE id = trainer_id) AS trainer_name
"""


def _class_from_row(row) -> GymClass:
    return GymClass(
        id=row["id"],
        name=row["name"],
        trainer_id=row["trainer_id"],
        day_of_week=row["day_of_week"],
        start_time=row["start_time"],
        end_time=row["end_time"],
        capacity=row["capacity"],
        trainer_name=row.get("trainer_name") or "",
    )


def _trainer_from_row(row) -> Trainer:
    return Trainer(
        id=row["id"],
        name=row["name"],
        email=row["email"],
        phone=row["phone"],
        specialty=row["specialty"],
        bio=row["bio"] or "",
        years_experience=row["years_experience"],
    )


def create_trainer(
    name: str,
    email: str,
    phone: str,
    specialty: str,
    *,
    bio: str = "",
    years_experience: int | None = None,
) -> Trainer:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                INSERT INTO trainers
                    (name, email, phone, specialty, bio, years_experience)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING {_TRAINER_COLUMNS}
                """,
                (name, email, phone, specialty, bio, years_experience),
            )
            row = cur.fetchone()
    return _trainer_from_row(row)


def _member_from_row(row) -> Member:
    return Member(
        id=row["id"],
        name=row["name"],
        email=row["email"],
        phone=row["phone"],
        membership_plan=row["membership_plan"],
        notes=row["notes"] or "",
    )


def create_member(
    name: str,
    email: str,
    phone: str,
    membership_plan: str,
    *,
    notes: str = "",
) -> Member:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                INSERT INTO members
                    (name, email, phone, membership_plan, notes)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING {_MEMBER_COLUMNS}
                """,
                (name, email, phone, membership_plan, notes),
            )
            row = cur.fetchone()
    return _member_from_row(row)


def create_class(
    name: str,
    trainer_id: int,
    day_of_week: int,
    start_time: time,
    end_time: time,
    capacity: int,
) -> GymClass:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                INSERT INTO classes
                    (name, trainer_id, day_of_week, start_time, end_time, capacity)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING {_CLASS_RETURNING}
                """,
                (name, trainer_id, day_of_week, start_time, end_time, capacity),
            )
            row = cur.fetchone()
            if not row:
                raise RuntimeError("INSERT INTO classes no devolvió fila")
    return _class_from_row(row)


def get_trainer(trainer_id: int) -> Optional[Trainer]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"SELECT {_TRAINER_COLUMNS} FROM trainers WHERE id=%s",
                (trainer_id,),
            )
            row = cur.fetchone()
    return _trainer_from_row(row) if row else None


def list_trainers() -> List[Trainer]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"SELECT {_TRAINER_COLUMNS} FROM trainers ORDER BY id"
            )
            rows = cur.fetchall()
    return [_trainer_from_row(r) for r in rows]


def trainer_email_taken(email: str, *, exclude_id: int | None = None) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            if exclude_id is None:
                cur.execute(
                    "SELECT 1 FROM trainers WHERE email = %s LIMIT 1",
                    (email,),
                )
            else:
                cur.execute(
                    "SELECT 1 FROM trainers WHERE email = %s AND id <> %s LIMIT 1",
                    (email, exclude_id),
                )
            return cur.fetchone() is not None


def update_trainer(
    trainer_id: int,
    name: str,
    email: str,
    phone: str,
    specialty: str,
    *,
    bio: str = "",
    years_experience: int | None = None,
) -> Optional[Trainer]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                UPDATE trainers
                SET name = %s,
                    email = %s,
                    phone = %s,
                    specialty = %s,
                    bio = %s,
                    years_experience = %s
                WHERE id = %s
                RETURNING {_TRAINER_COLUMNS}
                """,
                (
                    name,
                    email,
                    phone,
                    specialty,
                    bio,
                    years_experience,
                    trainer_id,
                ),
            )
            row = cur.fetchone()
    return _trainer_from_row(row) if row else None


def delete_trainer(trainer_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM trainers WHERE id = %s", (trainer_id,))
            return cur.rowcount > 0


def count_classes_by_trainer(trainer_id: int) -> int:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM classes WHERE trainer_id = %s",
                (trainer_id,),
            )
            (count,) = cur.fetchone()
    return int(count)


def list_classes_by_trainer(trainer_id: int) -> List[GymClass]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT {_CLASS_SELECT}
                FROM classes c
                JOIN trainers t ON t.id = c.trainer_id
                WHERE c.trainer_id = %s
                ORDER BY c.day_of_week, c.start_time
                """,
                (trainer_id,),
            )
            rows = cur.fetchall()
    return [_class_from_row(r) for r in rows]


def get_member(member_id: int) -> Optional[Member]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"SELECT {_MEMBER_COLUMNS} FROM members WHERE id=%s",
                (member_id,),
            )
            row = cur.fetchone()
    return _member_from_row(row) if row else None


def list_members() -> List[Member]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"SELECT {_MEMBER_COLUMNS} FROM members ORDER BY id"
            )
            rows = cur.fetchall()
    return [_member_from_row(r) for r in rows]


def member_email_taken(email: str, *, exclude_id: int | None = None) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            if exclude_id is None:
                cur.execute(
                    "SELECT 1 FROM members WHERE email = %s LIMIT 1",
                    (email,),
                )
            else:
                cur.execute(
                    "SELECT 1 FROM members WHERE email = %s AND id <> %s LIMIT 1",
                    (email, exclude_id),
                )
            return cur.fetchone() is not None


def update_member(
    member_id: int,
    name: str,
    email: str,
    phone: str,
    membership_plan: str,
    *,
    notes: str = "",
) -> Optional[Member]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                UPDATE members
                SET name = %s,
                    email = %s,
                    phone = %s,
                    membership_plan = %s,
                    notes = %s
                WHERE id = %s
                RETURNING {_MEMBER_COLUMNS}
                """,
                (name, email, phone, membership_plan, notes, member_id),
            )
            row = cur.fetchone()
    return _member_from_row(row) if row else None


def delete_member(member_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM members WHERE id = %s", (member_id,))
            return cur.rowcount > 0


def get_class(class_id: int) -> Optional[GymClass]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT {_CLASS_SELECT}
                FROM classes c
                JOIN trainers t ON t.id = c.trainer_id
                WHERE c.id = %s
                """,
                (class_id,),
            )
            row = cur.fetchone()
    return _class_from_row(row) if row else None


def list_classes() -> List[GymClass]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT {_CLASS_SELECT}
                FROM classes c
                JOIN trainers t ON t.id = c.trainer_id
                ORDER BY c.day_of_week, c.start_time
                """
            )
            rows = cur.fetchall()
    return [_class_from_row(r) for r in rows]


def update_class(
    class_id: int,
    name: str,
    trainer_id: int,
    day_of_week: int,
    start_time: time,
    end_time: time,
    capacity: int,
) -> Optional[GymClass]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                UPDATE classes
                SET name = %s,
                    trainer_id = %s,
                    day_of_week = %s,
                    start_time = %s,
                    end_time = %s,
                    capacity = %s
                WHERE id = %s
                RETURNING {_CLASS_RETURNING}
                """,
                (
                    name,
                    trainer_id,
                    day_of_week,
                    start_time,
                    end_time,
                    capacity,
                    class_id,
                ),
            )
            row = cur.fetchone()
    return _class_from_row(row) if row else None


def delete_class(class_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM classes WHERE id = %s", (class_id,))
            return cur.rowcount > 0


def count_enrollments(class_id: int) -> int:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM enrollments WHERE class_id=%s", (class_id,)
            )
            (count,) = cur.fetchone()
    return int(count)


def is_member_enrolled(class_id: int, member_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM enrollments
                WHERE class_id=%s AND member_id=%s
                """,
                (class_id, member_id),
            )
            return cur.fetchone() is not None


def enroll_member(class_id: int, member_id: int) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO enrollments (class_id, member_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (class_id, member_id),
            )


def list_enrollments() -> List[Enrollment]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT e.class_id,
                       e.member_id,
                       c.name AS class_name,
                       m.name AS member_name
                FROM enrollments e
                JOIN classes c ON c.id = e.class_id
                JOIN members m ON m.id = e.member_id
                ORDER BY e.class_id, e.member_id
                """
            )
            rows = cur.fetchall()
    return [Enrollment(**r) for r in rows]


def delete_enrollment(class_id: int, member_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM enrollments
                WHERE class_id = %s AND member_id = %s
                """,
                (class_id, member_id),
            )
            return cur.rowcount > 0


def list_member_classes(member_id: int) -> List[GymClass]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT {_CLASS_SELECT}
                FROM classes c
                JOIN trainers t ON t.id = c.trainer_id
                JOIN enrollments e ON e.class_id = c.id
                WHERE e.member_id = %s
                ORDER BY c.day_of_week, c.start_time
                """,
                (member_id,),
            )
            rows = cur.fetchall()
    return [_class_from_row(r) for r in rows]


def list_class_members(class_id: int) -> List[Member]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT m.id, m.name, m.email, m.phone, m.membership_plan, m.notes
                FROM members m
                JOIN enrollments e ON e.member_id = m.id
                WHERE e.class_id = %s
                ORDER BY m.id
                """,
                (class_id,),
            )
            rows = cur.fetchall()
    return [_member_from_row(r) for r in rows]


def _attendance_select() -> str:
    return """
        SELECT a.class_id,
               a.member_id,
               a.attended_at,
               c.name AS class_name,
               m.name AS member_name
        FROM attendance a
        JOIN classes c ON c.id = a.class_id
        JOIN members m ON m.id = a.member_id
    """


def mark_attendance(class_id: int, member_id: int) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO attendance (class_id, member_id)
                VALUES (%s, %s)
                """,
                (class_id, member_id),
            )


def list_attendance() -> List[Attendance]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                _attendance_select() + " ORDER BY a.attended_at DESC, a.class_id, a.member_id"
            )
            rows = cur.fetchall()
    return [Attendance(**r) for r in rows]


def list_attendance_by_class(class_id: int) -> List[Attendance]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                _attendance_select()
                + " WHERE a.class_id = %s ORDER BY a.attended_at DESC, a.member_id",
                (class_id,),
            )
            rows = cur.fetchall()
    return [Attendance(**r) for r in rows]


def list_attendance_by_member(member_id: int) -> List[Attendance]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                _attendance_select()
                + " WHERE a.member_id = %s ORDER BY a.attended_at DESC, a.class_id",
                (member_id,),
            )
            rows = cur.fetchall()
    return [Attendance(**r) for r in rows]


def list_attendance_for_pair(class_id: int, member_id: int) -> List[Attendance]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                _attendance_select()
                + """
                WHERE a.class_id = %s AND a.member_id = %s
                ORDER BY a.attended_at DESC
                """,
                (class_id, member_id),
            )
            rows = cur.fetchall()
    return [Attendance(**r) for r in rows]


def has_attendance(class_id: int, member_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM attendance
                WHERE class_id = %s AND member_id = %s
                LIMIT 1
                """,
                (class_id, member_id),
            )
            return cur.fetchone() is not None


def delete_attendance(class_id: int, member_id: int, attended_at) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM attendance
                WHERE class_id = %s AND member_id = %s AND attended_at = %s
                """,
                (class_id, member_id, attended_at),
            )
            return cur.rowcount > 0

