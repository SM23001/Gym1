from datetime import date, datetime, time
from decimal import Decimal
from typing import List, Optional

from psycopg2.extras import RealDictCursor

from db import get_connection
from models import (
    Trainer,
    Member,
    GymClass,
    ClassSchedule,
    Enrollment,
    Attendance,
    AttendanceRosterRow,
    AppUser,
    UserRole,
)

_TRAINER_COLUMNS = (
    "id, name, email, phone, specialty, bio, years_experience"
)

_MEMBER_COLUMNS = (
    "id, name, email, phone, membership_plan, notes"
)

_CLASS_SELECT = """
    c.id, c.name, c.trainer_id, c.capacity,
    c.start_date, c.end_date, c.price, c.status,
    t.name AS trainer_name
"""

_CLASS_RETURNING = """
    id, name, trainer_id, capacity,
    start_date, end_date, price, status,
    (SELECT name FROM trainers WHERE id = trainer_id) AS trainer_name
"""

_SCHEDULE_COLUMNS = "id, class_id, day_of_week, start_time, end_time"

_CLASS_ORDER = """
    ORDER BY first_slot.day_of_week NULLS LAST,
             first_slot.start_time NULLS LAST,
             c.id
"""

_CLASS_FROM = """
    FROM classes c
    JOIN trainers t ON t.id = c.trainer_id
    LEFT JOIN LATERAL (
        SELECT s.day_of_week, s.start_time
        FROM class_schedules s
        WHERE s.class_id = c.id
        ORDER BY s.day_of_week, s.start_time
        LIMIT 1
    ) first_slot ON true
"""


def _schedule_from_row(row) -> ClassSchedule:
    return ClassSchedule(
        id=row["id"],
        class_id=row["class_id"],
        day_of_week=row["day_of_week"],
        start_time=row["start_time"],
        end_time=row["end_time"],
    )


def _class_from_row(row, schedules: list[ClassSchedule] | None = None) -> GymClass:
    price = row.get("price")
    return GymClass(
        id=row["id"],
        name=row["name"],
        trainer_id=row["trainer_id"],
        capacity=row["capacity"],
        trainer_name=row.get("trainer_name") or "",
        schedules=schedules or [],
        start_date=row.get("start_date"),
        end_date=row.get("end_date"),
        price=price if price is not None else Decimal("0"),
        status=row.get("status") or "scheduled",
    )


def _fetch_schedules_by_class_ids(class_ids: list[int]) -> dict[int, list[ClassSchedule]]:
    if not class_ids:
        return {}
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT {_SCHEDULE_COLUMNS}
                FROM class_schedules
                WHERE class_id = ANY(%s)
                ORDER BY class_id, day_of_week, start_time
                """,
                (class_ids,),
            )
            rows = cur.fetchall()
    grouped: dict[int, list[ClassSchedule]] = {class_id: [] for class_id in class_ids}
    for row in rows:
        schedule = _schedule_from_row(row)
        grouped[schedule.class_id].append(schedule)
    return grouped


def _attach_schedules(classes: list[GymClass]) -> list[GymClass]:
    if not classes:
        return classes
    schedules_by_id = _fetch_schedules_by_class_ids([c.id for c in classes])
    for gym_class in classes:
        gym_class.schedules = schedules_by_id.get(gym_class.id, [])
    return classes


def _insert_schedules(cur, class_id: int, schedules: list[tuple[int, time, time]]) -> None:
    for day_of_week, start_time, end_time in schedules:
        cur.execute(
            """
            INSERT INTO class_schedules
                (class_id, day_of_week, start_time, end_time)
            VALUES (%s, %s, %s, %s)
            """,
            (class_id, day_of_week, start_time, end_time),
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
    capacity: int,
    schedules: list[tuple[int, time, time]],
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    price: Decimal = Decimal("0"),
    status: str = "scheduled",
) -> GymClass:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                INSERT INTO classes
                    (name, trainer_id, capacity, start_date, end_date, price, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING {_CLASS_RETURNING}
                """,
                (name, trainer_id, capacity, start_date, end_date, price, status),
            )
            row = cur.fetchone()
            if not row:
                raise RuntimeError("INSERT INTO classes no devolvió fila")
            class_id = row["id"]
            _insert_schedules(cur, class_id, schedules)
    return get_class(class_id)


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
                {_CLASS_FROM}
                WHERE c.trainer_id = %s
                {_CLASS_ORDER}
                """,
                (trainer_id,),
            )
            rows = cur.fetchall()
    return _attach_schedules([_class_from_row(r) for r in rows])


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
                {_CLASS_FROM}
                WHERE c.id = %s
                """,
                (class_id,),
            )
            row = cur.fetchone()
    if not row:
        return None
    gym_class = _class_from_row(row)
    schedules_by_id = _fetch_schedules_by_class_ids([class_id])
    gym_class.schedules = schedules_by_id.get(class_id, [])
    return gym_class


def list_classes() -> List[GymClass]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT {_CLASS_SELECT}
                {_CLASS_FROM}
                {_CLASS_ORDER}
                """
            )
            rows = cur.fetchall()
    return _attach_schedules([_class_from_row(r) for r in rows])


def update_class(
    class_id: int,
    name: str,
    trainer_id: int,
    capacity: int,
    schedules: list[tuple[int, time, time]],
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    price: Decimal = Decimal("0"),
    status: str = "scheduled",
) -> Optional[GymClass]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                UPDATE classes
                SET name = %s,
                    trainer_id = %s,
                    capacity = %s,
                    start_date = %s,
                    end_date = %s,
                    price = %s,
                    status = %s
                WHERE id = %s
                RETURNING {_CLASS_RETURNING}
                """,
                (
                    name,
                    trainer_id,
                    capacity,
                    start_date,
                    end_date,
                    price,
                    status,
                    class_id,
                ),
            )
            row = cur.fetchone()
            if not row:
                return None
            cur.execute(
                "DELETE FROM class_schedules WHERE class_id = %s",
                (class_id,),
            )
            _insert_schedules(cur, class_id, schedules)
    return get_class(class_id)


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
                {_CLASS_FROM}
                JOIN enrollments e ON e.class_id = c.id
                WHERE e.member_id = %s
                {_CLASS_ORDER}
                """,
                (member_id,),
            )
            rows = cur.fetchall()
    return _attach_schedules([_class_from_row(r) for r in rows])


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


def mark_attendance(class_id: int, member_id: int, attended_at: datetime) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO attendance (class_id, member_id, attended_at)
                VALUES (%s, %s, %s)
                """,
                (class_id, member_id, attended_at),
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


def list_class_attendance_roster(class_id: int, session_date: date) -> List[AttendanceRosterRow]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT m.id          AS member_id,
                       m.name        AS member_name,
                       m.membership_plan,
                       m.email,
                       a.attended_at
                FROM enrollments e
                JOIN members m ON m.id = e.member_id
                LEFT JOIN attendance a
                       ON a.member_id = m.id
                      AND a.class_id  = e.class_id
                      AND DATE(a.attended_at) = %(session_date)s
                WHERE e.class_id = %(class_id)s
                ORDER BY m.name, a.attended_at DESC
                """,
                {"class_id": class_id, "session_date": session_date},
            )
            rows = cur.fetchall()
    seen = set()
    result = []
    for r in rows:
        key = r["member_id"]
        if key not in seen:
            seen.add(key)
            result.append(AttendanceRosterRow(**r))
    return result


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


def has_attendance_on_date(
    class_id: int, member_id: int, session_date: date
) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM attendance
                WHERE class_id = %s AND member_id = %s AND DATE(attended_at) = %s
                LIMIT 1
                """,
                (class_id, member_id, session_date),
            )
            return cur.fetchone() is not None


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


_APP_USER_COLUMNS = (
    "id, username, role, trainer_id, member_id, active"
)


def _app_user_from_row(row) -> AppUser:
    return AppUser(
        id=row["id"],
        username=row["username"],
        role=UserRole(row["role"]),
        trainer_id=row.get("trainer_id"),
        member_id=row.get("member_id"),
        active=row["active"],
    )


def count_app_users() -> int:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM app_users")
            return cur.fetchone()[0]


def get_app_user_by_username(username: str) -> Optional[dict]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, username, password_hash, role,
                       trainer_id, member_id, active
                FROM app_users
                WHERE username = %s
                """,
                (username,),
            )
            row = cur.fetchone()
            return dict(row) if row else None


def get_app_user(user_id: int) -> Optional[AppUser]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"SELECT {_APP_USER_COLUMNS} FROM app_users WHERE id = %s",
                (user_id,),
            )
            row = cur.fetchone()
            return _app_user_from_row(row) if row else None


def list_app_users() -> List[AppUser]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"SELECT {_APP_USER_COLUMNS} FROM app_users ORDER BY id"
            )
            rows = cur.fetchall()
    return [_app_user_from_row(row) for row in rows]


def username_taken(username: str, *, exclude_id: int | None = None) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            if exclude_id is None:
                cur.execute(
                    "SELECT 1 FROM app_users WHERE username = %s LIMIT 1",
                    (username,),
                )
            else:
                cur.execute(
                    """
                    SELECT 1 FROM app_users
                    WHERE username = %s AND id <> %s
                    LIMIT 1
                    """,
                    (username, exclude_id),
                )
            return cur.fetchone() is not None


def create_app_user(
    username: str,
    password_hash: str,
    role: str,
    *,
    trainer_id: int | None = None,
    member_id: int | None = None,
) -> AppUser:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO app_users (
                    username, password_hash, role, trainer_id, member_id
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, username, role, trainer_id, member_id, active
                """,
                (username, password_hash, role, trainer_id, member_id),
            )
            row = cur.fetchone()
    return _app_user_from_row(row)


def set_app_user_active(user_id: int, active: bool) -> Optional[AppUser]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                UPDATE app_users
                SET active = %s
                WHERE id = %s
                RETURNING {_APP_USER_COLUMNS}
                """,
                (active, user_id),
            )
            row = cur.fetchone()
    return _app_user_from_row(row) if row else None

