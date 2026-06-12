from datetime import time

import pytest

from conftest import TRUNCATE_GYM_TABLES, create_test_member, create_test_trainer
from db import init_schema, get_connection
import service


@pytest.fixture(autouse=True)
def clean_db():
    init_schema()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(TRUNCATE_GYM_TABLES)
    yield


def test_enroll_member_capacity_and_overlap():
    trainer = create_test_trainer("Entrenador 1")
    m1 = create_test_member("Miembro 1", email="m1@gym.com")
    m2 = create_test_member("Miembro 2", email="m2@gym.com")

    c1 = service.create_class(
        "Spinning",
        trainer.id,
        1,
        [(0, time(9, 0), time(10, 0))],
    )
    c2 = service.create_class(
        "Yoga",
        trainer.id,
        10,
        [(0, time(9, 30), time(10, 30))],
    )

    service.enroll_member(c1.id, m1.id)

    with pytest.raises(service.BusinessError, match="Cupo completo"):
        service.enroll_member(c1.id, m2.id)

    with pytest.raises(service.BusinessError, match="Choque de horario"):
        service.enroll_member(c2.id, m1.id)


def test_mark_attendance_requires_enrollment():
    from datetime import date

    trainer = create_test_trainer("T")
    member = create_test_member("M", email="m@gym.com")
    gym_class = service.create_class(
        "Clase",
        trainer.id,
        5,
        [(1, time(18, 0), time(19, 0))],
    )
    schedule = gym_class.schedules[0]
    session_date = date(2026, 1, 6)

    with pytest.raises(service.BusinessError):
        service.mark_attendance(
            gym_class.id,
            member.id,
            schedule_id=schedule.id,
            session_date=session_date,
        )

    service.enroll_member(gym_class.id, member.id)
    service.mark_attendance(
        gym_class.id,
        member.id,
        schedule_id=schedule.id,
        session_date=session_date,
    )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM attendance WHERE class_id=%s AND member_id=%s",
                (gym_class.id, member.id),
            )
            (count,) = cur.fetchone()
    assert count >= 1
