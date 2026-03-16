from datetime import time

import pytest

from db import init_schema, get_connection
import service
import repository as repo


@pytest.fixture(autouse=True)
def clean_db():
    init_schema()
    # limpiar tablas antes de cada test
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE attendance, enrollments, classes, members, trainers RESTART IDENTITY")
    yield


def test_enroll_member_capacity_and_overlap():
    trainer = service.create_trainer("Entrenador 1")
    m1 = service.create_member("Miembro 1")
    m2 = service.create_member("Miembro 2")

    c1 = service.create_class(
        "Spinning",
        trainer.id,
        day_of_week=0,
        start_time=time(9, 0),
        end_time=time(10, 0),
        capacity=1,
    )
    c2 = service.create_class(
        "Yoga",
        trainer.id,
        day_of_week=0,
        start_time=time(9, 30),
        end_time=time(10, 30),
        capacity=10,
    )

    # primer miembro se inscribe bien
    service.enroll_member(c1.id, m1.id)

    # segundo miembro no puede por cupo
    with pytest.raises(service.BusinessError, match="Cupo completo"):
        service.enroll_member(c1.id, m2.id)

    # mismo miembro no puede por choque de horario
    with pytest.raises(service.BusinessError, match="Choque de horario"):
        service.enroll_member(c2.id, m1.id)


def test_mark_attendance_requires_enrollment():
    trainer = service.create_trainer("T")
    member = service.create_member("M")
    gym_class = service.create_class(
        "Clase",
        trainer.id,
        day_of_week=1,
        start_time=time(18, 0),
        end_time=time(19, 0),
        capacity=5,
    )

    # no inscrito -> error
    with pytest.raises(service.BusinessError):
        service.mark_attendance(gym_class.id, member.id)

    # inscrito -> ok
    service.enroll_member(gym_class.id, member.id)
    service.mark_attendance(gym_class.id, member.id)

    # confirmar que se registró algo en attendance
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM attendance WHERE class_id=%s AND member_id=%s",
                (gym_class.id, member.id),
            )
            (count,) = cur.fetchone()
    assert count >= 1

