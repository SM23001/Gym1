from datetime import date, time

import pytest

from conftest import (
    TRUNCATE_GYM_TABLES,
    create_test_class,
    create_test_member,
    create_test_trainer,
)
from db import get_connection, init_schema
from models import UserRole
import service


@pytest.fixture(autouse=True)
def clean_db():
    init_schema()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(TRUNCATE_GYM_TABLES)
    yield


def test_bootstrap_admin_creates_first_user():
    admin = service.bootstrap_admin("admin", "secret12")
    assert admin.role == UserRole.ADMIN
    assert admin.username == "admin"
    assert service.count_app_users() == 1


def test_bootstrap_admin_rejects_when_users_exist():
    service.bootstrap_admin("admin", "secret12")
    with pytest.raises(service.BusinessError, match="Ya existen usuarios"):
        service.bootstrap_admin("other", "secret12")


def test_authenticate_success():
    service.register_app_user("admin", "secret12", UserRole.ADMIN)
    user = service.authenticate("admin", "secret12")
    assert user.username == "admin"
    assert user.role == UserRole.ADMIN


def test_authenticate_wrong_password():
    service.register_app_user("admin", "secret12", UserRole.ADMIN)
    with pytest.raises(service.BusinessError, match="Usuario o contraseña inválidos"):
        service.authenticate("admin", "wrongpass")


def test_authenticate_inactive_user():
    admin = service.register_app_user("admin", "secret12", UserRole.ADMIN)
    target = service.create_app_user(admin, "inactive", "secret12", UserRole.ADMIN)
    service.deactivate_app_user(admin, target.id)
    with pytest.raises(service.BusinessError, match="Usuario o contraseña inválidos"):
        service.authenticate("inactive", "secret12")


def test_create_app_user_requires_admin():
    trainer = create_test_trainer("Ana")
    member = create_test_member("Juan")
    with pytest.raises(service.BusinessError, match="Debe iniciar sesión"):
        service.create_app_user(
            None,
            "trainer1",
            "secret12",
            UserRole.TRAINER,
            trainer_id=trainer.id,
        )

    admin = service.register_app_user("admin", "secret12", UserRole.ADMIN)
    created = service.create_app_user(
        admin,
        "trainer1",
        "secret12",
        UserRole.TRAINER,
        trainer_id=trainer.id,
    )
    assert created.trainer_id == trainer.id

    member_user = service.create_app_user(
        admin,
        "member1",
        "secret12",
        UserRole.MEMBER,
        member_id=member.id,
    )
    assert member_user.member_id == member.id


def test_member_can_enroll_self_only():
    trainer = create_test_trainer("Ana")
    member_a = create_test_member("Juan")
    member_b = create_test_member("Maria")
    gym_class = create_test_class(trainer=trainer)

    member_user = service.register_app_user(
        "juan",
        "secret12",
        UserRole.MEMBER,
        member_id=member_a.id,
    )

    service.enroll_member(gym_class.id, member_a.id, actor=member_user)

    with pytest.raises(service.BusinessError, match="No tiene permiso"):
        service.enroll_member(gym_class.id, member_b.id, actor=member_user)


def test_trainer_mark_attendance_own_class_only():
    trainer = create_test_trainer("Ana")
    other_trainer = create_test_trainer("Bob")
    member = create_test_member("Juan")
    own_class = create_test_class(
        name="Own",
        trainer=trainer,
        schedules=[(0, time(9, 0), time(10, 0))],
    )
    other_class = create_test_class(
        name="Other",
        trainer=other_trainer,
        schedules=[(1, time(9, 0), time(10, 0))],
    )

    service.enroll_member(own_class.id, member.id)
    service.enroll_member(other_class.id, member.id)

    trainer_user = service.register_app_user(
        "ana",
        "secret12",
        UserRole.TRAINER,
        trainer_id=trainer.id,
    )
    schedule = own_class.schedules[0]

    service.mark_attendance(
        own_class.id,
        member.id,
        schedule_id=schedule.id,
        session_date=date(2026, 1, 5),
        actor=trainer_user,
    )

    other_schedule = other_class.schedules[0]
    with pytest.raises(service.BusinessError, match="No tiene permiso"):
        service.mark_attendance(
            other_class.id,
            member.id,
            schedule_id=other_schedule.id,
            session_date=date(2026, 1, 6),
            actor=trainer_user,
        )


def test_register_app_user_validates_role_links():
    trainer = create_test_trainer("Ana")
    with pytest.raises(service.BusinessError, match="debe estar vinculado"):
        service.register_app_user("bad", "secret12", UserRole.TRAINER)

    with pytest.raises(service.BusinessError, match="no debe estar vinculado"):
        service.register_app_user(
            "bad-admin",
            "secret12",
            UserRole.ADMIN,
            trainer_id=trainer.id,
        )
