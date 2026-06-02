from datetime import time

from models import GymClass
import repository as repo


class BusinessError(Exception):
    pass


def create_trainer(name: str):
    name = name.strip()
    if not name:
        raise BusinessError("El nombre no puede estar vacío")
    return repo.create_trainer(name)


def get_trainer(trainer_id: int):
    return repo.get_trainer(trainer_id)


def update_trainer(trainer_id: int, name: str):
    name = name.strip()
    if not name:
        raise BusinessError("El nombre no puede estar vacío")
    trainer = repo.update_trainer(trainer_id, name)
    if trainer is None:
        raise BusinessError("Entrenador no existe")
    return trainer


def delete_trainer(trainer_id: int) -> None:
    if repo.get_trainer(trainer_id) is None:
        raise BusinessError("Entrenador no existe")
    if repo.count_classes_by_trainer(trainer_id) > 0:
        raise BusinessError(
            "No se puede eliminar: el entrenador tiene clases asignadas"
        )
    repo.delete_trainer(trainer_id)


def create_member(name: str):
    name = name.strip()
    if not name:
        raise BusinessError("El nombre no puede estar vacío")
    return repo.create_member(name)


def get_member(member_id: int):
    return repo.get_member(member_id)


def update_member(member_id: int, name: str):
    name = name.strip()
    if not name:
        raise BusinessError("El nombre no puede estar vacío")
    member = repo.update_member(member_id, name)
    if member is None:
        raise BusinessError("Miembro no existe")
    return member


def delete_member(member_id: int) -> None:
    if repo.get_member(member_id) is None:
        raise BusinessError("Miembro no existe")
    repo.delete_member(member_id)


def create_class(
    name: str,
    trainer_id: int,
    day_of_week: int,
    start_time: time,
    end_time: time,
    capacity: int,
) -> GymClass:
    if repo.get_trainer(trainer_id) is None:
        raise BusinessError("El entrenador no existe. Cree primero un entrenador (opción 1).")
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


def list_trainers():
    return repo.list_trainers()


def list_members():
    return repo.list_members()

