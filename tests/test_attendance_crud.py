from datetime import date, datetime, time

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


def _mark_attendance(
    gym_class,
    member,
    *,
    session_date: date | None = None,
    schedule_index: int = 0,
):
    schedule = gym_class.schedules[schedule_index]
    if session_date is None:
        session_date = date(2026, 1, 5)
    service.mark_attendance(
        gym_class.id,
        member.id,
        schedule_id=schedule.id,
        session_date=session_date,
    )


def _setup_attendance():
    trainer = create_test_trainer("T")
    member = create_test_member("M", email="m@gym.com")
    gym_class = service.create_class(
        "Spinning",
        trainer.id,
        5,
        [(0, time(9, 0), time(10, 0))],
    )
    service.enroll_member(gym_class.id, member.id)
    _mark_attendance(gym_class, member)
    return gym_class, member


def test_list_attendance_empty():
    assert service.list_attendance() == []


def test_list_attendance_after_record():
    gym_class, member = _setup_attendance()
    records = service.list_attendance()
    assert len(records) == 1
    assert records[0].class_id == gym_class.id
    assert records[0].member_id == member.id
    assert records[0].class_name == "Spinning"
    assert records[0].member_name == "M"
    assert records[0].attended_at is not None


def test_has_attendance_true():
    gym_class, member = _setup_attendance()
    assert service.has_attendance(gym_class.id, member.id) is True


def test_has_attendance_false():
    trainer = create_test_trainer("T")
    member = create_test_member("M", email="m@gym.com")
    gym_class = service.create_class(
        "Yoga",
        trainer.id,
        5,
        [(1, time(11, 0), time(12, 0))],
    )
    assert service.has_attendance(gym_class.id, member.id) is False


def test_has_attendance_invalid_class():
    member = create_test_member("M", email="m@gym.com")
    with pytest.raises(service.BusinessError, match="Clase no existe"):
        service.has_attendance(999, member.id)


def test_has_attendance_invalid_member():
    trainer = create_test_trainer("T")
    gym_class = service.create_class(
        "Clase",
        trainer.id,
        5,
        [(0, time(9, 0), time(10, 0))],
    )
    with pytest.raises(service.BusinessError, match="Miembro no existe"):
        service.has_attendance(gym_class.id, 999)


def test_list_attendance_for_pair():
    gym_class, member = _setup_attendance()
    records = service.list_attendance_for_pair(gym_class.id, member.id)
    assert len(records) == 1


def test_list_attendance_by_class():
    gym_class, member = _setup_attendance()
    records = service.list_attendance_by_class(gym_class.id)
    assert len(records) == 1
    assert records[0].member_id == member.id


def test_list_attendance_by_member():
    gym_class, member = _setup_attendance()
    records = service.list_attendance_by_member(member.id)
    assert len(records) == 1
    assert records[0].class_id == gym_class.id


def test_delete_attendance():
    gym_class, member = _setup_attendance()
    records = service.list_attendance_for_pair(gym_class.id, member.id)
    service.delete_attendance(gym_class.id, member.id, records[0].attended_at)
    assert service.has_attendance(gym_class.id, member.id) is False
    assert service.list_attendance() == []


def test_delete_attendance_not_found():
    trainer = create_test_trainer("T")
    member = create_test_member("M", email="m@gym.com")
    gym_class = service.create_class(
        "Clase",
        trainer.id,
        5,
        [(0, time(9, 0), time(10, 0))],
    )
    from datetime import datetime

    with pytest.raises(service.BusinessError, match="no encontrado"):
        service.delete_attendance(
            gym_class.id, member.id, datetime(2020, 1, 1, 12, 0, 0)
        )


def test_mark_attendance_invalid_class():
    member = create_test_member("M", email="m@gym.com")
    with pytest.raises(service.BusinessError, match="Clase no existe"):
        service.mark_attendance(
            999,
            member.id,
            schedule_id=1,
            session_date=date(2026, 1, 5),
        )


def test_mark_attendance_invalid_member():
    trainer = create_test_trainer("T")
    gym_class = service.create_class(
        "Clase",
        trainer.id,
        5,
        [(0, time(9, 0), time(10, 0))],
    )
    with pytest.raises(service.BusinessError, match="Miembro no existe"):
        service.mark_attendance(
            gym_class.id,
            999,
            schedule_id=gym_class.schedules[0].id,
            session_date=date(2026, 1, 5),
        )


def test_mark_attendance_wrong_weekday():
    trainer = create_test_trainer("T")
    member = create_test_member("M", email="m@gym.com")
    gym_class = service.create_class(
        "Spinning",
        trainer.id,
        5,
        [(0, time(9, 0), time(10, 0))],
    )
    service.enroll_member(gym_class.id, member.id)
    with pytest.raises(service.BusinessError, match="día del horario"):
        service.mark_attendance(
            gym_class.id,
            member.id,
            schedule_id=gym_class.schedules[0].id,
            session_date=date(2026, 1, 6),
        )


def test_mark_attendance_outside_class_period():
    trainer = create_test_trainer("T")
    member = create_test_member("M", email="m@gym.com")
    gym_class = service.create_class(
        "Yoga",
        trainer.id,
        5,
        [(0, time(18, 0), time(19, 0))],
        start_date=date(2026, 2, 1),
        end_date=date(2026, 6, 30),
    )
    service.enroll_member(gym_class.id, member.id)
    with pytest.raises(service.BusinessError, match="período"):
        service.mark_attendance(
            gym_class.id,
            member.id,
            schedule_id=gym_class.schedules[0].id,
            session_date=date(2026, 1, 5),
        )


def test_mark_attendance_duplicate_same_date():
    gym_class, member = _setup_attendance()
    with pytest.raises(service.BusinessError, match="ya tiene asistencia"):
        _mark_attendance(gym_class, member, session_date=date(2026, 1, 5))


def test_mark_attendance_stores_session_datetime():
    trainer = create_test_trainer("T")
    member = create_test_member("M", email="m@gym.com")
    gym_class = service.create_class(
        "Spinning",
        trainer.id,
        5,
        [(0, time(9, 0), time(10, 0))],
    )
    service.enroll_member(gym_class.id, member.id)
    _mark_attendance(gym_class, member, session_date=date(2026, 1, 5))
    records = service.list_attendance_for_pair(gym_class.id, member.id)
    assert records[0].attended_at == datetime(2026, 1, 5, 9, 0, 0)
