from db import init_schema, get_connection
import service
from seed import seed_data


def test_seed_data_populates_demo_records():
    init_schema()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "TRUNCATE attendance, enrollments, classes, members, trainers "
                "RESTART IDENTITY"
            )

    seed_data()

    assert len(service.list_trainers()) == 3
    assert len(service.list_members()) == 4
    assert len(service.list_classes()) == 4
    assert len(service.list_enrollments()) == 7
    assert len(service.list_attendance()) == 3

    spinning = service.list_classes()[0]
    assert spinning.trainer_name == "Ana Ruiz"
