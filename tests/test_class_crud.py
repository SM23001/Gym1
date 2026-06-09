from datetime import time

import pytest

from conftest import TRUNCATE_GYM_TABLES, create_test_class, create_test_member, create_test_trainer
from db import init_schema, get_connection
import service


@pytest.fixture(autouse=True)
def clean_db():
    init_schema()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(TRUNCATE_GYM_TABLES)
    yield


def test_create_class():
    gym_class = create_test_class()
    assert gym_class.id == 1
    assert gym_class.name == "Spinning"
    assert gym_class.capacity == 10
    assert len(gym_class.schedules) == 1


def test_create_class_multi_schedule():
    trainer = create_test_trainer("Ana")
    gym_class = service.create_class(
        "Yoga",
        trainer.id,
        8,
        [
            (0, time(18, 0), time(19, 0)),
            (4, time(18, 0), time(19, 0)),
        ],
    )
    assert len(gym_class.schedules) == 2
    days = [schedule.day_of_week for schedule in gym_class.schedules]
    assert days == [0, 4]


def test_create_class_empty_name():
    trainer = create_test_trainer("T")
    with pytest.raises(service.BusinessError, match="nombre no puede estar vacío"):
        service.create_class(
            "  ",
            trainer.id,
            10,
            [(0, time(9, 0), time(10, 0))],
        )


def test_create_class_no_schedules():
    trainer = create_test_trainer("T")
    with pytest.raises(service.BusinessError, match="al menos un horario"):
        service.create_class("Yoga", trainer.id, 10, [])


def test_create_class_invalid_trainer():
    with pytest.raises(service.BusinessError, match="entrenador no existe"):
        service.create_class(
            "Yoga",
            999,
            10,
            [(0, time(9, 0), time(10, 0))],
        )


def test_create_class_invalid_time():
    trainer = create_test_trainer("T")
    with pytest.raises(service.BusinessError, match="hora de fin"):
        service.create_class(
            "Yoga",
            trainer.id,
            10,
            [(0, time(10, 0), time(9, 0))],
        )


def test_create_class_overlapping_slots():
    trainer = create_test_trainer("T")
    with pytest.raises(service.BusinessError, match="se solapan"):
        service.create_class(
            "Yoga",
            trainer.id,
            10,
            [
                (0, time(9, 0), time(10, 0)),
                (0, time(9, 30), time(10, 30)),
            ],
        )


def test_get_class():
    created = create_test_class()
    found = service.get_class(created.id)
    assert found == created


def test_get_class_not_found():
    assert service.get_class(999) is None


def test_list_classes():
    trainer = create_test_trainer("Ana")
    service.create_class(
        "A",
        trainer.id,
        10,
        [(0, time(9, 0), time(10, 0))],
    )
    service.create_class(
        "B",
        trainer.id,
        10,
        [(1, time(9, 0), time(10, 0))],
    )
    classes = service.list_classes()
    assert len(classes) == 2
    assert [c.name for c in classes] == ["A", "B"]
    assert all(c.trainer_name == "Ana" for c in classes)


def test_list_class_members():
    gym_class = create_test_class("Spinning")
    m1 = create_test_member("Juan", email="juan@gym.com")
    create_test_member("María", email="maria@gym.com")
    service.enroll_member(gym_class.id, m1.id)
    members = service.list_class_members(gym_class.id)
    assert len(members) == 1
    assert members[0].id == m1.id
    assert members[0].name == "Juan"
    other = create_test_class("Yoga")
    assert service.list_class_members(other.id) == []


def test_update_class():
    gym_class = create_test_class("Original")
    trainer = create_test_trainer("Nuevo T")
    updated = service.update_class(
        gym_class.id,
        "Nuevo nombre",
        trainer.id,
        20,
        [(1, time(18, 0), time(19, 0))],
    )
    assert updated.name == "Nuevo nombre"
    assert updated.trainer_id == trainer.id
    assert updated.capacity == 20
    assert len(updated.schedules) == 1
    assert updated.schedules[0].day_of_week == 1


def test_update_class_not_found():
    trainer = create_test_trainer("T")
    with pytest.raises(service.BusinessError, match="no existe"):
        service.update_class(
            999,
            "X",
            trainer.id,
            10,
            [(0, time(9, 0), time(10, 0))],
        )


def test_update_class_capacity_below_enrollments():
    gym_class = create_test_class(capacity=5)
    service.enroll_member(gym_class.id, create_test_member("M1", email="m1@gym.com").id)
    service.enroll_member(gym_class.id, create_test_member("M2", email="m2@gym.com").id)
    trainer = service.get_trainer(gym_class.trainer_id)
    with pytest.raises(service.BusinessError, match="inscripciones actuales"):
        service.update_class(
            gym_class.id,
            gym_class.name,
            trainer.id,
            1,
            [(0, time(9, 0), time(10, 0))],
        )


def test_delete_class():
    gym_class = create_test_class()
    service.delete_class(gym_class.id)
    assert service.get_class(gym_class.id) is None


def test_delete_class_not_found():
    with pytest.raises(service.BusinessError, match="no existe"):
        service.delete_class(999)


def test_delete_class_cascades_enrollments():
    gym_class = create_test_class()
    member = create_test_member("M", email="m@gym.com")
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
