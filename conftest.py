"""Pytest configuration: ensure project root is on sys.path for imports like 'db', 'service'."""
import itertools
import sys
from datetime import time
from decimal import Decimal
from pathlib import Path

import service

root = Path(__file__).resolve().parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

_trainer_counter = itertools.count(1)
_member_counter = itertools.count(1)

TRUNCATE_GYM_TABLES = (
    "TRUNCATE attendance, enrollments, class_schedules, classes, "
    "members, trainers RESTART IDENTITY CASCADE"
)


def create_test_trainer(
    name="T",
    *,
    email=None,
    phone="5550001",
    specialty="General",
    bio="",
    years_experience=None,
):
    n = next(_trainer_counter)
    if email is None:
        email = f"trainer{n}@gym.test"
    return service.create_trainer(
        name,
        email,
        phone,
        specialty,
        bio=bio,
        years_experience=years_experience,
    )


def create_test_member(
    name="M",
    *,
    email=None,
    phone="5550001",
    membership_plan="Standard",
    notes="",
):
    n = next(_member_counter)
    if email is None:
        email = f"member{n}@gym.test"
    return service.create_member(
        name,
        email,
        phone,
        membership_plan,
        notes=notes,
    )


def create_test_class(
    name="Spinning",
    *,
    trainer=None,
    capacity=10,
    schedules=None,
    start_date=None,
    end_date=None,
    price=Decimal("0"),
    status="scheduled",
):
    if trainer is None:
        trainer = create_test_trainer("T")
    if schedules is None:
        schedules = [(0, time(9, 0), time(10, 0))]
    return service.create_class(
        name,
        trainer.id,
        capacity,
        schedules,
        start_date=start_date,
        end_date=end_date,
        price=price,
        status=status,
    )
