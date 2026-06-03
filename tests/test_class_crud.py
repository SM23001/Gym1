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


def _create_class(name="Spinning", capacity=10):
    trainer = service.create_trainer("T")
    return service.create_class(
        name,
        trainer.id,
        day_of_week=0,
        start_time=time(9, 0),
        end_time=time(10, 0),
        capacity=capacity,
    )


def test_create_class():
    gym_class = _create_class()
    assert gym_class.id == 1
    assert gym_class.name == "Spinning"
    assert gym_class.capacity == 10


def test_create_class_empty_name():
    trainer = service.create_trainer("T")
    with pytest.raises(service.BusinessError, match="nombre no puede estar vacío"):
        service.create_class(
            "  ",
            trainer.id,
            0,
            time(9, 0),
            time(10, 0),
            10,
        )


def test_create_class_invalid_trainer():
    with pytest.raises(service.BusinessError, match="entrenador no existe"):
        service.create_class(
            "Yoga",
            999,
            0,
            time(9, 0),
            time(10, 0),
            10,
        )


def test_create_class_invalid_time():
    trainer = service.create_trainer("T")
    with pytest.raises(service.BusinessError, match="hora de fin"):
        service.create_class(
            "Yoga",
            trainer.id,
            0,
            time(10, 0),
            time(9, 0),
            10,
        )


def test_get_class():
    created = _create_class()
    found = service.get_class(created.id)
    assert found == created


def test_get_class_not_found():
    assert service.get_class(999) is None


def test_list_classes():
    _create_class("A")
    _create_class("B")
    classes = service.list_classes()
    assert len(classes) == 2
    assert [c.name for c in classes] == ["A", "B"]


def test_list_class_members():
    gym_class = _create_class("Spinning")
    m1 = service.create_member("Juan")
    service.create_member("María")
    service.enroll_member(gym_class.id, m1.id)
    members = service.list_class_members(gym_class.id)
    assert len(members) == 1
    assert members[0].id == m1.id
    assert members[0].name == "Juan"
    other = _create_class("Yoga")
    assert service.list_class_members(other.id) == []


def test_update_class():
    gym_class = _create_class("Original")
    trainer = service.create_trainer("Nuevo T")
    updated = service.update_class(
        gym_class.id,
        "Nuevo nombre",
        trainer.id,
        day_of_week=1,
        start_time=time(18, 0),
        end_time=time(19, 0),
        capacity=20,
    )
    assert updated.name == "Nuevo nombre"
    assert updated.trainer_id == trainer.id
    assert updated.day_of_week == 1
    assert updated.capacity == 20


def test_update_class_not_found():
    trainer = service.create_trainer("T")
    with pytest.raises(service.BusinessError, match="no existe"):
        service.update_class(
            999,
            "X",
            trainer.id,
            0,
            time(9, 0),
            time(10, 0),
            10,
        )


def test_update_class_capacity_below_enrollments():
    gym_class = _create_class(capacity=5)
    service.enroll_member(gym_class.id, service.create_member("M1").id)
    service.enroll_member(gym_class.id, service.create_member("M2").id)
    trainer = service.get_trainer(gym_class.trainer_id)
    with pytest.raises(service.BusinessError, match="inscripciones actuales"):
        service.update_class(
            gym_class.id,
            gym_class.name,
            trainer.id,
            gym_class.day_of_week,
            gym_class.start_time,
            gym_class.end_time,
            capacity=1,
        )


def test_delete_class():
    gym_class = _create_class()
    service.delete_class(gym_class.id)
    assert service.get_class(gym_class.id) is None


def test_delete_class_not_found():
    with pytest.raises(service.BusinessError, match="no existe"):
        service.delete_class(999)


def test_delete_class_cascades_enrollments():
    gym_class = _create_class()
    member = service.create_member("M")
    service.enroll_member(gym_class.id, member.id)
    service.delete_class(gym_class.id)

    assert service.get_class(gym_class.id) is None
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM enrollments WHERE class_id = %s",
                (gym_class.id,),
            )
            (count,) = cur.fetchone()
    assert count == 0
