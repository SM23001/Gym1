from datetime import time

import pytest

from conftest import create_test_trainer
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


def test_create_member():
    m = service.create_member("Juan")
    assert m.id == 1
    assert m.name == "Juan"


def test_create_member_empty_name():
    with pytest.raises(service.BusinessError, match="nombre no puede estar vacío"):
        service.create_member("   ")


def test_get_member():
    created = service.create_member("María")
    found = service.get_member(created.id)
    assert found == created


def test_get_member_not_found():
    assert service.get_member(999) is None


def test_list_members():
    service.create_member("A")
    service.create_member("B")
    members = service.list_members()
    assert len(members) == 2
    assert [m.name for m in members] == ["A", "B"]


def test_update_member():
    m = service.create_member("Original")
    updated = service.update_member(m.id, "Nuevo nombre")
    assert updated.id == m.id
    assert updated.name == "Nuevo nombre"
    assert service.get_member(m.id).name == "Nuevo nombre"


def test_update_member_not_found():
    with pytest.raises(service.BusinessError, match="no existe"):
        service.update_member(999, "X")


def test_update_member_empty_name():
    m = service.create_member("Ana")
    with pytest.raises(service.BusinessError, match="nombre no puede estar vacío"):
        service.update_member(m.id, "")


def test_delete_member():
    m = service.create_member("Para borrar")
    service.delete_member(m.id)
    assert service.get_member(m.id) is None


def test_delete_member_not_found():
    with pytest.raises(service.BusinessError, match="no existe"):
        service.delete_member(999)


def test_list_member_classes():
    trainer = create_test_trainer("Ana")
    m1 = service.create_member("Juan")
    m2 = service.create_member("María")
    c1 = service.create_class(
        "Spinning",
        trainer.id,
        day_of_week=0,
        start_time=time(9, 0),
        end_time=time(10, 0),
        capacity=10,
    )
    service.create_class(
        "Yoga",
        trainer.id,
        day_of_week=1,
        start_time=time(11, 0),
        end_time=time(12, 0),
        capacity=8,
    )
    service.enroll_member(c1.id, m1.id)
    classes = service.list_member_classes(m1.id)
    assert len(classes) == 1
    assert classes[0].id == c1.id
    assert classes[0].name == "Spinning"
    assert service.list_member_classes(m2.id) == []


def test_delete_member_cascades_enrollments():
    trainer = create_test_trainer("T")
    member = service.create_member("M")
    gym_class = service.create_class(
        "Clase",
        trainer.id,
        day_of_week=0,
        start_time=time(9, 0),
        end_time=time(10, 0),
        capacity=5,
    )
    service.enroll_member(gym_class.id, member.id)
    service.delete_member(member.id)

    assert service.get_member(member.id) is None
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM enrollments WHERE member_id = %s",
                (member.id,),
            )
            (count,) = cur.fetchone()
    assert count == 0
