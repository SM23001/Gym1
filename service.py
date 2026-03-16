from datetime import time

from models import GymClass
import repository as repo


class BusinessError(Exception):
    pass


def create_trainer(name: str):
    return repo.create_trainer(name)


def create_member(name: str):
    return repo.create_member(name)


def create_class(
    name: str,
    trainer_id: int,
    day_of_week: int,
    start_time: time,
    end_time: time,
    capacity: int,
) -> GymClass:
    if end_time <= start_time:
        raise BusinessError("La hora de fin debe ser posterior a la de inicio")
    return repo.create_class(
        name=name,
        trainer_id=trainer_id,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        capacity=capacity,
    )


def _overlaps(c1: GymClass, c2: GymClass) -> bool:
    if c1.day_of_week != c2.day_of_week:
        return False
    return not (c1.end_time <= c2.start_time or c2.end_time <= c1.start_time)


def enroll_member(class_id: int, member_id: int) -> None:
    gym_class = repo.get_class(class_id)
    if not gym_class:
        raise BusinessError("Clase no existe")
    if not repo.get_member(member_id):
        raise BusinessError("Miembro no existe")

    if repo.count_enrollments(class_id) >= gym_class.capacity:
        raise BusinessError("Cupo completo para esta clase")

    if repo.is_member_enrolled(class_id, member_id):
        raise BusinessError("Miembro ya inscrito en esta clase")

    for other in repo.list_member_classes(member_id):
        if _overlaps(gym_class, other):
            raise BusinessError(
                f"Choque de horario con la clase {other.id} - {other.name}"
            )

    repo.enroll_member(class_id, member_id)


def mark_attendance(class_id: int, member_id: int) -> None:
    if not repo.is_member_enrolled(class_id, member_id):
        raise BusinessError("El miembro no está inscrito en esta clase")
    repo.mark_attendance(class_id, member_id)


def list_classes():
    return repo.list_classes()

