from datetime import time
from typing import List, Optional

from psycopg2.extras import RealDictCursor

from db import get_connection
from models import Trainer, Member, GymClass


def create_trainer(name: str) -> Trainer:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO trainers (name) VALUES (%s) RETURNING id, name",
                (name,),
            )
            row = cur.fetchone()
    return Trainer(id=row["id"], name=row["name"])


def create_member(name: str) -> Member:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO members (name) VALUES (%s) RETURNING id, name",
                (name,),
            )
            row = cur.fetchone()
    return Member(id=row["id"], name=row["name"])


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
                """
                INSERT INTO classes
                    (name, trainer_id, day_of_week, start_time, end_time, capacity)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, name, trainer_id, day_of_week, start_time, end_time, capacity
                """,
                (name, trainer_id, day_of_week, start_time, end_time, capacity),
            )
            row = cur.fetchone()
            if not row:
                raise RuntimeError("INSERT INTO classes no devolvió fila")
    return GymClass(
        id=row["id"],
        name=row["name"],
        trainer_id=row["trainer_id"],
        day_of_week=row["day_of_week"],
        start_time=row["start_time"],
        end_time=row["end_time"],
        capacity=row["capacity"],
    )


def get_trainer(trainer_id: int) -> Optional[Trainer]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, name FROM trainers WHERE id=%s", (trainer_id,))
            row = cur.fetchone()
    return Trainer(**row) if row else None


def list_trainers() -> List[Trainer]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, name FROM trainers ORDER BY id")
            rows = cur.fetchall()
    return [Trainer(**r) for r in rows]


def update_trainer(trainer_id: int, name: str) -> Optional[Trainer]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE trainers SET name = %s
                WHERE id = %s
                RETURNING id, name
                """,
                (name, trainer_id),
            )
            row = cur.fetchone()
    return Trainer(**row) if row else None


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
                """
                SELECT id, name, trainer_id, day_of_week, start_time, end_time, capacity
                FROM classes
                WHERE trainer_id = %s
                ORDER BY day_of_week, start_time
                """,
                (trainer_id,),
            )
            rows = cur.fetchall()
    return [GymClass(**r) for r in rows]


def get_member(member_id: int) -> Optional[Member]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, name FROM members WHERE id=%s", (member_id,))
            row = cur.fetchone()
    return Member(**row) if row else None


def list_members() -> List[Member]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, name FROM members ORDER BY id")
            rows = cur.fetchall()
    return [Member(**r) for r in rows]


def update_member(member_id: int, name: str) -> Optional[Member]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE members SET name = %s
                WHERE id = %s
                RETURNING id, name
                """,
                (name, member_id),
            )
            row = cur.fetchone()
    return Member(**row) if row else None


def delete_member(member_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM members WHERE id = %s", (member_id,))
            return cur.rowcount > 0


def get_class(class_id: int) -> Optional[GymClass]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, name, trainer_id, day_of_week, start_time, end_time, capacity
                FROM classes
                WHERE id=%s
                """,
                (class_id,),
            )
            row = cur.fetchone()
    return GymClass(**row) if row else None


def list_classes() -> List[GymClass]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, name, trainer_id, day_of_week, start_time, end_time, capacity
                FROM classes
                ORDER BY day_of_week, start_time
                """
            )
            rows = cur.fetchall()
    return [GymClass(**r) for r in rows]


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
                """
                UPDATE classes
                SET name = %s,
                    trainer_id = %s,
                    day_of_week = %s,
                    start_time = %s,
                    end_time = %s,
                    capacity = %s
                WHERE id = %s
                RETURNING id, name, trainer_id, day_of_week, start_time, end_time, capacity
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
    return GymClass(**row) if row else None


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


def list_member_classes(member_id: int) -> List[GymClass]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT c.id,
                       c.name,
                       c.trainer_id,
                       c.day_of_week,
                       c.start_time,
                       c.end_time,
                       c.capacity
                FROM classes c
                JOIN enrollments e ON e.class_id = c.id
                WHERE e.member_id = %s
                """,
                (member_id,),
            )
            rows = cur.fetchall()
    return [GymClass(**r) for r in rows]


def list_class_members(class_id: int) -> List[Member]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT m.id, m.name
                FROM members m
                JOIN enrollments e ON e.member_id = m.id
                WHERE e.class_id = %s
                ORDER BY m.id
                """,
                (class_id,),
            )
            rows = cur.fetchall()
    return [Member(**r) for r in rows]


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

