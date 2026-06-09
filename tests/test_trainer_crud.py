from datetime import time

import pytest

from conftest import TRUNCATE_GYM_TABLES, create_test_trainer
from db import init_schema, get_connection
import service


@pytest.fixture(autouse=True)
def clean_db():
    init_schema()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(TRUNCATE_GYM_TABLES)
    yield


def test_create_trainer():
    t = service.create_trainer(
        "Ana",
        "ana@gym.com",
        "71234567",
        "Yoga",
        bio="Instructora certificada",
        years_experience=5,
    )
    assert t.id == 1
    assert t.name == "Ana"
    assert t.email == "ana@gym.com"
    assert t.phone == "71234567"
    assert t.specialty == "Yoga"
    assert t.bio == "Instructora certificada"
    assert t.years_experience == 5


def test_create_trainer_empty_name():
    with pytest.raises(service.BusinessError, match="nombre no puede estar vacío"):
        service.create_trainer("   ", "a@gym.com", "71234567", "Yoga")


def test_create_trainer_invalid_email():
    with pytest.raises(service.BusinessError, match="email no es válido"):
        service.create_trainer("Ana", "not-an-email", "71234567", "Yoga")


def test_create_trainer_invalid_phone():
    with pytest.raises(service.BusinessError, match="teléfono no es válido"):
        service.create_trainer("Ana", "ana@gym.com", "123", "Yoga")


def test_create_trainer_empty_specialty():
    with pytest.raises(service.BusinessError, match="especialidad no puede estar vacía"):
        service.create_trainer("Ana", "ana@gym.com", "71234567", "   ")


def test_create_trainer_duplicate_email():
    service.create_trainer("A", "same@gym.com", "71234567", "Yoga")
    with pytest.raises(service.BusinessError, match="email ya está registrado"):
        service.create_trainer("B", "same@gym.com", "79876543", "CrossFit")


def test_create_trainer_negative_experience():
    with pytest.raises(
        service.BusinessError, match="años de experiencia no pueden ser negativos"
    ):
        service.create_trainer(
            "Ana", "ana@gym.com", "71234567", "Yoga", years_experience=-1
        )


def test_get_trainer():
    created = create_test_trainer("Luis", email="luis@gym.com")
    found = service.get_trainer(created.id)
    assert found == created


def test_get_trainer_not_found():
    assert service.get_trainer(999) is None


def test_list_trainers():
    create_test_trainer("A", email="a@gym.com")
    create_test_trainer("B", email="b@gym.com")
    trainers = service.list_trainers()
    assert len(trainers) == 2
    assert [t.name for t in trainers] == ["A", "B"]


def test_update_trainer():
    t = create_test_trainer("Original", email="orig@gym.com")
    updated = service.update_trainer(
        t.id,
        "Nuevo nombre",
        "nuevo@gym.com",
        "79998877",
        "Pilates",
        bio="Nueva bio",
        years_experience=3,
    )
    assert updated.id == t.id
    assert updated.name == "Nuevo nombre"
    assert updated.email == "nuevo@gym.com"
    assert updated.specialty == "Pilates"
    assert service.get_trainer(t.id).name == "Nuevo nombre"


def test_update_trainer_not_found():
    with pytest.raises(service.BusinessError, match="no existe"):
        service.update_trainer(999, "X", "x@gym.com", "71234567", "Yoga")


def test_update_trainer_empty_name():
    t = create_test_trainer("Ana", email="ana@gym.com")
    with pytest.raises(service.BusinessError, match="nombre no puede estar vacío"):
        service.update_trainer(t.id, "", "ana@gym.com", "71234567", "Yoga")


def test_update_trainer_duplicate_email():
    t1 = create_test_trainer("A", email="a@gym.com")
    create_test_trainer("B", email="b@gym.com")
    with pytest.raises(service.BusinessError, match="email ya está registrado"):
        service.update_trainer(t1.id, "A", "b@gym.com", "71234567", "Yoga")


def test_delete_trainer():
    t = create_test_trainer("Para borrar", email="del@gym.com")
    service.delete_trainer(t.id)
    assert service.get_trainer(t.id) is None


def test_delete_trainer_not_found():
    with pytest.raises(service.BusinessError, match="no existe"):
        service.delete_trainer(999)


def test_list_classes_by_trainer():
    t1 = create_test_trainer("Ana", email="ana@gym.com")
    t2 = create_test_trainer("Luis", email="luis@gym.com")
    c1 = service.create_class(
        "Spinning",
        t1.id,
        10,
        [(0, time(9, 0), time(10, 0))],
    )
    service.create_class(
        "Yoga",
        t2.id,
        8,
        [(1, time(11, 0), time(12, 0))],
    )
    classes = service.list_classes_by_trainer(t1.id)
    assert len(classes) == 1
    assert classes[0].id == c1.id
    assert classes[0].name == "Spinning"
    assert service.list_classes_by_trainer(t2.id)[0].name == "Yoga"
    solo = create_test_trainer("Solo", email="solo@gym.com")
    assert service.list_classes_by_trainer(solo.id) == []


def test_delete_trainer_with_classes():
    trainer = create_test_trainer("Con clases", email="clases@gym.com")
    service.create_class(
        "Spinning",
        trainer.id,
        10,
        [(0, time(9, 0), time(10, 0))],
    )
    with pytest.raises(service.BusinessError, match="clases asignadas"):
        service.delete_trainer(trainer.id)
    assert service.get_trainer(trainer.id) is not None
