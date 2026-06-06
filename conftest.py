"""Pytest configuration: ensure project root is on sys.path for imports like 'db', 'service'."""
import itertools
import sys
from pathlib import Path

import service

root = Path(__file__).resolve().parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

_trainer_counter = itertools.count(1)


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
