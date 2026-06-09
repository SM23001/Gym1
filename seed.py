"""Load demo data into the gym database via the service layer."""
import argparse
import sys
from datetime import time

from config import get_settings
from db import get_connection, init_schema
import service

_TRUNCATE_SQL = (
    "TRUNCATE attendance, enrollments, class_schedules, classes, "
    "members, trainers RESTART IDENTITY CASCADE"
)


def reset_data() -> None:
    init_schema()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(_TRUNCATE_SQL)


def seed_data() -> None:
    ana = service.create_trainer(
        "Ana Ruiz",
        "ana.ruiz@gym.com",
        "5551001",
        "Spinning",
        bio="Indoor cycling specialist.",
        years_experience=5,
    )
    carlos = service.create_trainer(
        "Carlos Vega",
        "carlos.vega@gym.com",
        "5551002",
        "Yoga",
        bio="RYT-500 certified.",
        years_experience=8,
    )
    laura = service.create_trainer(
        "Laura Méndez",
        "laura.mendez@gym.com",
        "5551003",
        "CrossFit",
        years_experience=3,
    )

    juan = service.create_member(
        "Juan Pérez", "juan.perez@gym.com", "5552001", "Premium"
    )
    maria = service.create_member(
        "María López", "maria.lopez@gym.com", "5552002", "Standard"
    )
    pedro = service.create_member(
        "Pedro Sánchez",
        "pedro.sanchez@gym.com",
        "5552003",
        "Standard",
        notes="Morning member",
    )
    sofia = service.create_member(
        "Sofía Torres", "sofia.torres@gym.com", "5552004", "Premium"
    )

    spinning = service.create_class(
        "Spinning",
        ana.id,
        10,
        [(0, time(9, 0), time(10, 0))],
    )
    fitness = service.create_class(
        "Fitness",
        ana.id,
        20,
        [(day, time(19, 0), time(20, 0)) for day in range(5)]
        + [(5, time(6, 0), time(7, 0)), (6, time(6, 0), time(7, 0))],
    )
    yoga = service.create_class(
        "Yoga",
        carlos.id,
        8,
        [
            (0, time(18, 0), time(19, 0)),
            (4, time(18, 0), time(19, 0)),
        ],
    )
    crossfit = service.create_class(
        "CrossFit",
        laura.id,
        12,
        [(2, time(7, 0), time(8, 0))],
    )

    service.enroll_member(spinning.id, juan.id)
    service.enroll_member(spinning.id, maria.id)
    service.enroll_member(spinning.id, pedro.id)
    service.enroll_member(fitness.id, juan.id)
    service.enroll_member(yoga.id, maria.id)
    service.enroll_member(yoga.id, sofia.id)
    service.enroll_member(crossfit.id, juan.id)

    service.mark_attendance(spinning.id, juan.id)
    service.mark_attendance(spinning.id, maria.id)
    service.mark_attendance(yoga.id, sofia.id)


def main() -> int:
    parser = argparse.ArgumentParser(description="Load demo data into the gym database.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear all gym tables before seeding.",
    )
    args = parser.parse_args()

    settings = get_settings()
    if settings.db_name == "gymdb_test":
        print(
            "Refusing to seed gymdb_test. Set GYM_DB_NAME=gymdb in .env.",
            file=sys.stderr,
        )
        return 1

    init_schema()

    if service.list_trainers():
        if args.reset:
            reset_data()
        else:
            print("Database already has data. Use --reset to truncate and reseed.")
            return 0

    seed_data()
    print(
        f"Seed complete ({settings.db_name}): "
        f"{len(service.list_trainers())} trainers, "
        f"{len(service.list_members())} members, "
        f"{len(service.list_classes())} classes."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
