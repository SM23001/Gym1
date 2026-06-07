from datetime import time

import pytest

from conftest import create_test_member, create_test_trainer
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
    m = service.create_member(
        "Juan",
        "juan@gym.com",
        "71234567",
        "Monthly",
        notes="Prefiere clases matutinas",
    )
    assert m.id == 1
    assert m.name == "Juan"
    assert m.email == "juan@gym.com"
    assert m.phone == "71234567"
    assert m.membership_plan == "Monthly"
    assert m.notes == "Prefiere clases matutinas"


def test_create_member_empty_name():
    with pytest.raises(service.BusinessError, match="nombre no puede estar vacío"):
        service.create_member("   ", "a@gym.com", "71234567", "Monthly")


def test_create_member_invalid_email():
    with pytest.raises(service.BusinessError, match="email no es válido"):
        service.create_member("Juan", "not-an-email", "71234567", "Monthly")


def test_create_member_invalid_phone():
    with pytest.raises(service.BusinessError, match="teléfono no es válido"):
        service.create_member("Juan", "juan@gym.com", "123", "Monthly")


def test_create_member_empty_membership_plan():
    with pytest.raises(
        service.BusinessError, match="plan de membresía no puede estar vacío"
    ):
        service.create_member("Juan", "juan@gym.com", "71234567", "   ")


def test_create_member_duplicate_email():
    service.create_member("A", "same@gym.com", "71234567", "Monthly")
    with pytest.raises(service.BusinessError, match="email ya está registrado"):
        service.create_member("B", "same@gym.com", "79876543", "Annual")


def test_get_member():
    created = create_test_member("María", email="maria@gym.com")
    found = service.get_member(created.id)
    assert found == created


def test_get_member_not_found():
    assert service.get_member(999) is None


def test_list_members():
    create_test_member("A", email="a@gym.com")
    create_test_member("B", email="b@gym.com")
    members = service.list_members()
    assert len(members) == 2
    assert [m.name for m in members] == ["A", "B"]


def test_update_member():
    m = create_test_member("Original", email="orig@gym.com")
    updated = service.update_member(
        m.id,
        "Nuevo nombre",
        "nuevo@gym.com",
        "79998877",
        "Annual",
        notes="Actualizado",
    )
    assert updated.id == m.id
    assert updated.name == "Nuevo nombre"
    assert updated.email == "nuevo@gym.com"
    assert updated.membership_plan == "Annual"
    assert service.get_member(m.id).name == "Nuevo nombre"


def test_update_member_not_found():
    with pytest.raises(service.BusinessError, match="no existe"):
        service.update_member(999, "X", "x@gym.com", "71234567", "Monthly")


def test_update_member_empty_name():
    m = create_test_member("Ana", email="ana@gym.com")
    with pytest.raises(service.BusinessError, match="nombre no puede estar vacío"):
        service.update_member(m.id, "", "ana@gym.com", "71234567", "Monthly")


def test_update_member_duplicate_email():
    m1 = create_test_member("A", email="a@gym.com")
    create_test_member("B", email="b@gym.com")
    with pytest.raises(service.BusinessError, match="email ya está registrado"):
        service.update_member(m1.id, "A", "b@gym.com", "71234567", "Monthly")


def test_delete_member():
    m = create_test_member("Para borrar", email="del@gym.com")
    service.delete_member(m.id)
    assert service.get_member(m.id) is None


def test_delete_member_not_found():
    with pytest.raises(service.BusinessError, match="no existe"):
        service.delete_member(999)


def test_list_member_classes():
    trainer = create_test_trainer("Ana")
    m1 = create_test_member("Juan", email="juan@gym.com")
    m2 = create_test_member("María", email="maria@gym.com")
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
    member = create_test_member("M", email="m@gym.com")
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
