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


def test_create_trainer():
    t = service.create_trainer("Ana")
    assert t.id == 1
    assert t.name == "Ana"


def test_create_trainer_empty_name():
    with pytest.raises(service.BusinessError, match="nombre no puede estar vacío"):
        service.create_trainer("   ")


def test_get_trainer():
    created = service.create_trainer("Luis")
    found = service.get_trainer(created.id)
    assert found == created


def test_get_trainer_not_found():
    assert service.get_trainer(999) is None


def test_list_trainers():
    service.create_trainer("A")
    service.create_trainer("B")
    trainers = service.list_trainers()
    assert len(trainers) == 2
    assert [t.name for t in trainers] == ["A", "B"]


def test_update_trainer():
    t = service.create_trainer("Original")
    updated = service.update_trainer(t.id, "Nuevo nombre")
    assert updated.id == t.id
    assert updated.name == "Nuevo nombre"
    assert service.get_trainer(t.id).name == "Nuevo nombre"


def test_update_trainer_not_found():
    with pytest.raises(service.BusinessError, match="no existe"):
        service.update_trainer(999, "X")


def test_update_trainer_empty_name():
    t = service.create_trainer("Ana")
    with pytest.raises(service.BusinessError, match="nombre no puede estar vacío"):
        service.update_trainer(t.id, "")


def test_delete_trainer():
    t = service.create_trainer("Para borrar")
    service.delete_trainer(t.id)
    assert service.get_trainer(t.id) is None


def test_delete_trainer_not_found():
    with pytest.raises(service.BusinessError, match="no existe"):
        service.delete_trainer(999)


def test_list_classes_by_trainer():
    t1 = service.create_trainer("Ana")
    t2 = service.create_trainer("Luis")
    c1 = service.create_class(
        "Spinning",
        t1.id,
        day_of_week=0,
        start_time=time(9, 0),
        end_time=time(10, 0),
        capacity=10,
    )
    service.create_class(
        "Yoga",
        t2.id,
        day_of_week=1,
        start_time=time(11, 0),
        end_time=time(12, 0),
        capacity=8,
    )
    classes = service.list_classes_by_trainer(t1.id)
    assert len(classes) == 1
    assert classes[0].id == c1.id
    assert classes[0].name == "Spinning"
    assert service.list_classes_by_trainer(t2.id)[0].name == "Yoga"
    assert service.list_classes_by_trainer(service.create_trainer("Solo").id) == []


def test_delete_trainer_with_classes():
    trainer = service.create_trainer("Con clases")
    service.create_class(
        "Spinning",
        trainer.id,
        day_of_week=0,
        start_time=time(9, 0),
        end_time=time(10, 0),
        capacity=10,
    )
    with pytest.raises(service.BusinessError, match="clases asignadas"):
        service.delete_trainer(trainer.id)
    assert service.get_trainer(trainer.id) is not None
