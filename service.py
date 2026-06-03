from datetime import time

from models import GymClass, Enrollment, Attendance
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


def _validate_class_fields(
    name: str,
    trainer_id: int,
    day_of_week: int,
    start_time: time,
    end_time: time,
    capacity: int,
) -> str:
    name = name.strip()
    if not name:
        raise BusinessError("El nombre no puede estar vacío")
    if repo.get_trainer(trainer_id) is None:
        raise BusinessError("El entrenador no existe")
    if not 0 <= day_of_week <= 6:
        raise BusinessError("El día de la semana debe estar entre 0 y 6")
    if end_time <= start_time:
        raise BusinessError("La hora de fin debe ser posterior a la de inicio")
    if capacity <= 0:
        raise BusinessError("El cupo debe ser mayor que cero")
    return name


def create_class(
    name: str,
    trainer_id: int,
    day_of_week: int,
    start_time: time,
    end_time: time,
    capacity: int,
) -> GymClass:
    name = _validate_class_fields(
        name, trainer_id, day_of_week, start_time, end_time, capacity
    )
    return repo.create_class(
        name=name,
        trainer_id=trainer_id,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        capacity=capacity,
    )


def get_class(class_id: int):
    return repo.get_class(class_id)


def update_class(
    class_id: int,
    name: str,
    trainer_id: int,
    day_of_week: int,
    start_time: time,
    end_time: time,
    capacity: int,
) -> GymClass:
    if repo.get_class(class_id) is None:
        raise BusinessError("Clase no existe")
    name = _validate_class_fields(
        name, trainer_id, day_of_week, start_time, end_time, capacity
    )
    enrolled = repo.count_enrollments(class_id)
    if capacity < enrolled:
        raise BusinessError(
            f"El cupo no puede ser menor que las inscripciones actuales ({enrolled})"
        )
    gym_class = repo.update_class(
        class_id=class_id,
        name=name,
        trainer_id=trainer_id,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        capacity=capacity,
    )
    if gym_class is None:
        raise BusinessError("Clase no existe")
    return gym_class


def delete_class(class_id: int) -> None:
    if repo.get_class(class_id) is None:
        raise BusinessError("Clase no existe")
    repo.delete_class(class_id)


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


def unenroll_member(class_id: int, member_id: int) -> None:
    if repo.get_class(class_id) is None:
        raise BusinessError("Clase no existe")
    if not repo.get_member(member_id):
        raise BusinessError("Miembro no existe")
    if not repo.is_member_enrolled(class_id, member_id):
        raise BusinessError("El miembro no está inscrito en esta clase")
    repo.delete_enrollment(class_id, member_id)


def is_enrolled(class_id: int, member_id: int) -> bool:
    if repo.get_class(class_id) is None:
        raise BusinessError("Clase no existe")
    if not repo.get_member(member_id):
        raise BusinessError("Miembro no existe")
    return repo.is_member_enrolled(class_id, member_id)


def list_enrollments():
    return repo.list_enrollments()


def format_enrollment(enrollment: Enrollment) -> str:
    return (
        f"Class [{enrollment.class_id}] {enrollment.class_name} — "
        f"Member [{enrollment.member_id}] {enrollment.member_name}"
    )


def mark_attendance(class_id: int, member_id: int) -> None:
    if repo.get_class(class_id) is None:
        raise BusinessError("Clase no existe")
    if not repo.get_member(member_id):
        raise BusinessError("Miembro no existe")
    if not repo.is_member_enrolled(class_id, member_id):
        raise BusinessError("El miembro no está inscrito en esta clase")
    repo.mark_attendance(class_id, member_id)


def list_attendance():
    return repo.list_attendance()


def list_attendance_by_class(class_id: int):
    if repo.get_class(class_id) is None:
        raise BusinessError("Clase no existe")
    return repo.list_attendance_by_class(class_id)


def list_attendance_by_member(member_id: int):
    if not repo.get_member(member_id):
        raise BusinessError("Miembro no existe")
    return repo.list_attendance_by_member(member_id)


def has_attendance(class_id: int, member_id: int) -> bool:
    if repo.get_class(class_id) is None:
        raise BusinessError("Clase no existe")
    if not repo.get_member(member_id):
        raise BusinessError("Miembro no existe")
    return repo.has_attendance(class_id, member_id)


def list_attendance_for_pair(class_id: int, member_id: int):
    if repo.get_class(class_id) is None:
        raise BusinessError("Clase no existe")
    if not repo.get_member(member_id):
        raise BusinessError("Miembro no existe")
    return repo.list_attendance_for_pair(class_id, member_id)


def delete_attendance(class_id: int, member_id: int, attended_at) -> None:
    if repo.get_class(class_id) is None:
        raise BusinessError("Clase no existe")
    if not repo.get_member(member_id):
        raise BusinessError("Miembro no existe")
    if not repo.delete_attendance(class_id, member_id, attended_at):
        raise BusinessError("Registro de asistencia no encontrado")


def format_attendance(record: Attendance) -> str:
    when = record.attended_at.strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"Class [{record.class_id}] {record.class_name} — "
        f"Member [{record.member_id}] {record.member_name} — "
        f"{when}"
    )


def list_classes():
    return repo.list_classes()


def list_classes_by_trainer(trainer_id: int):
    return repo.list_classes_by_trainer(trainer_id)


def list_member_classes(member_id: int):
    return repo.list_member_classes(member_id)


def list_class_members(class_id: int):
    return repo.list_class_members(class_id)


def format_class(gym_class: GymClass) -> str:
    return (
        f"[{gym_class.id}] {gym_class.name} - Entrenador {gym_class.trainer_id} - "
        f"Día: {gym_class.day_of_week} {gym_class.start_time}-{gym_class.end_time} "
        f"Cupo: {gym_class.capacity}"
    )


def list_trainers():
    return repo.list_trainers()


def list_members():
    return repo.list_members()

