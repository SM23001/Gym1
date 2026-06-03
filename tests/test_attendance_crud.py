from datetime import time

import pytest

from db import init_schema, get_connection
import service


@pytest.fixture(autouse=True)
def clean_db():
    init_schema()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "TRUNCATE attendance, enrollments, classes, members, trainers RESTART IDENTITY"
            )
    yield


def _setup_attendance():
    trainer = service.create_trainer("T")
    member = service.create_member("M")
    gym_class = service.create_class(
        "Spinning",
        trainer.id,
        day_of_week=0,
        start_time=time(9, 0),
        end_time=time(10, 0),
        capacity=5,
    )
    service.enroll_member(gym_class.id, member.id)
    service.mark_attendance(gym_class.id, member.id)
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
    trainer = service.create_trainer("T")
    member = service.create_member("M")
    gym_class = service.create_class(
        "Yoga",
        trainer.id,
        day_of_week=1,
        start_time=time(11, 0),
        end_time=time(12, 0),
        capacity=5,
    )
    assert service.has_attendance(gym_class.id, member.id) is False


def test_has_attendance_invalid_class():
    member = service.create_member("M")
    with pytest.raises(service.BusinessError, match="Clase no existe"):
        service.has_attendance(999, member.id)


def test_has_attendance_invalid_member():
    trainer = service.create_trainer("T")
    gym_class = service.create_class(
        "Clase",
        trainer.id,
        day_of_week=0,
        start_time=time(9, 0),
        end_time=time(10, 0),
        capacity=5,
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
    trainer = service.create_trainer("T")
    member = service.create_member("M")
    gym_class = service.create_class(
        "Clase",
        trainer.id,
        day_of_week=0,
        start_time=time(9, 0),
        end_time=time(10, 0),
        capacity=5,
    )
    from datetime import datetime

    with pytest.raises(service.BusinessError, match="no encontrado"):
        service.delete_attendance(
            gym_class.id, member.id, datetime(2020, 1, 1, 12, 0, 0)
        )


def test_mark_attendance_invalid_class():
    member = service.create_member("M")
    with pytest.raises(service.BusinessError, match="Clase no existe"):
        service.mark_attendance(999, member.id)


def test_mark_attendance_invalid_member():
    trainer = service.create_trainer("T")
    gym_class = service.create_class(
        "Clase",
        trainer.id,
        day_of_week=0,
        start_time=time(9, 0),
        end_time=time(10, 0),
        capacity=5,
    )
    with pytest.raises(service.BusinessError, match="Miembro no existe"):
        service.mark_attendance(gym_class.id, 999)
