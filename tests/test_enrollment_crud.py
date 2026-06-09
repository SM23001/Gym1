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


def _setup_enrollment():
    trainer = create_test_trainer("T")
    member = create_test_member("M", email="m@gym.com")
    gym_class = service.create_class(
        "Spinning",
        trainer.id,
        5,
        [(0, time(9, 0), time(10, 0))],
    )
    service.enroll_member(gym_class.id, member.id)
    return gym_class, member


def test_list_enrollments_empty():
    assert service.list_enrollments() == []


def test_list_enrollments_after_enroll():
    gym_class, member = _setup_enrollment()
    enrollments = service.list_enrollments()
    assert len(enrollments) == 1
    assert enrollments[0].class_id == gym_class.id
    assert enrollments[0].member_id == member.id
    assert enrollments[0].class_name == "Spinning"
    assert enrollments[0].member_name == "M"


def test_is_enrolled_true():
    gym_class, member = _setup_enrollment()
    assert service.is_enrolled(gym_class.id, member.id) is True


def test_is_enrolled_false():
    trainer = create_test_trainer("T")
    member = create_test_member("M", email="m@gym.com")
    gym_class = service.create_class(
        "Yoga",
        trainer.id,
        5,
        [(1, time(11, 0), time(12, 0))],
    )
    assert service.is_enrolled(gym_class.id, member.id) is False


def test_is_enrolled_invalid_class():
    member = create_test_member("M", email="m@gym.com")
    with pytest.raises(service.BusinessError, match="Clase no existe"):
        service.is_enrolled(999, member.id)


def test_is_enrolled_invalid_member():
    trainer = create_test_trainer("T")
    gym_class = service.create_class(
        "Clase",
        trainer.id,
        5,
        [(0, time(9, 0), time(10, 0))],
    )
    with pytest.raises(service.BusinessError, match="Miembro no existe"):
        service.is_enrolled(gym_class.id, 999)


def test_unenroll_member():
    gym_class, member = _setup_enrollment()
    service.unenroll_member(gym_class.id, member.id)
    assert service.is_enrolled(gym_class.id, member.id) is False
    assert service.list_enrollments() == []


def test_unenroll_not_enrolled():
    trainer = create_test_trainer("T")
    member = create_test_member("M", email="m@gym.com")
    gym_class = service.create_class(
        "Clase",
        trainer.id,
        5,
        [(0, time(9, 0), time(10, 0))],
    )
    with pytest.raises(service.BusinessError, match="no está inscrito"):
        service.unenroll_member(gym_class.id, member.id)


def test_unenroll_invalid_class():
    member = create_test_member("M", email="m@gym.com")
    with pytest.raises(service.BusinessError, match="Clase no existe"):
        service.unenroll_member(999, member.id)


def test_unenroll_invalid_member():
    trainer = create_test_trainer("T")
    gym_class = service.create_class(
        "Clase",
        trainer.id,
        5,
        [(0, time(9, 0), time(10, 0))],
    )
    with pytest.raises(service.BusinessError, match="Miembro no existe"):
        service.unenroll_member(gym_class.id, 999)
