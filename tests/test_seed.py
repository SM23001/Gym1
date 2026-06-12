from conftest import TRUNCATE_GYM_TABLES
from db import init_schema, get_connection
import service
from datetime import date

from seed import _one_month_period, seed_data


def test_one_month_period():
    start, end = _one_month_period(date(2026, 5, 10))
    assert start == date(2026, 5, 10)
    assert end == date(2026, 6, 9)


def test_seed_data_populates_demo_records():
    init_schema()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(TRUNCATE_GYM_TABLES)

    seed_data()

    assert len(service.list_trainers()) == 3
    assert len(service.list_members()) == 4
    assert len(service.list_classes()) == 4
    assert len(service.list_enrollments()) == 7
    assert len(service.list_attendance()) == 3

    fitness = next(c for c in service.list_classes() if c.name == "Fitness")
    assert fitness.trainer_name == "Ana Ruiz"
    assert len(fitness.schedules) == 7
