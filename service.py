from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation

from models import GymClass, ClassSchedule, Enrollment, Attendance
import repository as repo


class BusinessError(Exception):
    pass


DAY_NAMES = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)

CLASS_STATUSES = ("scheduled", "started", "ended")

ScheduleSlot = tuple[int, time, time]


def _validate_email(email: str) -> str:
    email = email.strip().lower()
    if not email or "@" not in email or "." not in email.split("@")[-1]:
        raise BusinessError("El email no es válido")
    return email


def _validate_phone(phone: str) -> str:
    phone = phone.strip()
    digits = sum(ch.isdigit() for ch in phone)
    if digits < 7:
        raise BusinessError("El teléfono no es válido")
    return phone


def _validate_specialty(specialty: str) -> str:
    specialty = specialty.strip()
    if not specialty:
        raise BusinessError("La especialidad no puede estar vacía")
    return specialty


def _validate_years_experience(years_experience: int | None) -> int | None:
    if years_experience is not None and years_experience < 0:
        raise BusinessError("Los años de experiencia no pueden ser negativos")
    return years_experience


def _normalize_trainer_fields(
    name: str,
    email: str,
    phone: str,
    specialty: str,
    *,
    bio: str = "",
    years_experience: int | None = None,
) -> tuple[str, str, str, str, str, int | None]:
    name = name.strip()
    if not name:
        raise BusinessError("El nombre no puede estar vacío")
    email = _validate_email(email)
    phone = _validate_phone(phone)
    specialty = _validate_specialty(specialty)
    bio = bio.strip()
    years_experience = _validate_years_experience(years_experience)
    return name, email, phone, specialty, bio, years_experience


def create_trainer(
    name: str,
    email: str,
    phone: str,
    specialty: str,
    *,
    bio: str = "",
    years_experience: int | None = None,
):
    name, email, phone, specialty, bio, years_experience = _normalize_trainer_fields(
        name, email, phone, specialty, bio=bio, years_experience=years_experience
    )
    if repo.trainer_email_taken(email):
        raise BusinessError("El email ya está registrado")
    return repo.create_trainer(
        name,
        email,
        phone,
        specialty,
        bio=bio,
        years_experience=years_experience,
    )


def get_trainer(trainer_id: int):
    return repo.get_trainer(trainer_id)


def update_trainer(
    trainer_id: int,
    name: str,
    email: str,
    phone: str,
    specialty: str,
    *,
    bio: str = "",
    years_experience: int | None = None,
):
    name, email, phone, specialty, bio, years_experience = _normalize_trainer_fields(
        name, email, phone, specialty, bio=bio, years_experience=years_experience
    )
    if repo.get_trainer(trainer_id) is None:
        raise BusinessError("Entrenador no existe")
    if repo.trainer_email_taken(email, exclude_id=trainer_id):
        raise BusinessError("El email ya está registrado")
    trainer = repo.update_trainer(
        trainer_id,
        name,
        email,
        phone,
        specialty,
        bio=bio,
        years_experience=years_experience,
    )
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


def _validate_membership_plan(membership_plan: str) -> str:
    membership_plan = membership_plan.strip()
    if not membership_plan:
        raise BusinessError("El plan de membresía no puede estar vacío")
    return membership_plan


def _normalize_member_fields(
    name: str,
    email: str,
    phone: str,
    membership_plan: str,
    *,
    notes: str = "",
) -> tuple[str, str, str, str, str]:
    name = name.strip()
    if not name:
        raise BusinessError("El nombre no puede estar vacío")
    email = _validate_email(email)
    phone = _validate_phone(phone)
    membership_plan = _validate_membership_plan(membership_plan)
    notes = notes.strip()
    return name, email, phone, membership_plan, notes


def create_member(
    name: str,
    email: str,
    phone: str,
    membership_plan: str,
    *,
    notes: str = "",
):
    name, email, phone, membership_plan, notes = _normalize_member_fields(
        name, email, phone, membership_plan, notes=notes
    )
    if repo.member_email_taken(email):
        raise BusinessError("El email ya está registrado")
    return repo.create_member(
        name,
        email,
        phone,
        membership_plan,
        notes=notes,
    )


def get_member(member_id: int):
    return repo.get_member(member_id)


def update_member(
    member_id: int,
    name: str,
    email: str,
    phone: str,
    membership_plan: str,
    *,
    notes: str = "",
):
    name, email, phone, membership_plan, notes = _normalize_member_fields(
        name, email, phone, membership_plan, notes=notes
    )
    if repo.get_member(member_id) is None:
        raise BusinessError("Miembro no existe")
    if repo.member_email_taken(email, exclude_id=member_id):
        raise BusinessError("El email ya está registrado")
    member = repo.update_member(
        member_id,
        name,
        email,
        phone,
        membership_plan,
        notes=notes,
    )
    if member is None:
        raise BusinessError("Miembro no existe")
    return member


def delete_member(member_id: int) -> None:
    if repo.get_member(member_id) is None:
        raise BusinessError("Miembro no existe")
    repo.delete_member(member_id)


def _validate_schedule_slot(
    day_of_week: int,
    start_time: time,
    end_time: time,
) -> None:
    if not 0 <= day_of_week <= 6:
        raise BusinessError("El día de la semana debe estar entre 0 y 6")
    if end_time <= start_time:
        raise BusinessError("La hora de fin debe ser posterior a la de inicio")


def _validate_schedules(schedules: list[ScheduleSlot]) -> None:
    if not schedules:
        raise BusinessError("La clase debe tener al menos un horario")
    seen: set[ScheduleSlot] = set()
    for day_of_week, start_time, end_time in schedules:
        _validate_schedule_slot(day_of_week, start_time, end_time)
        slot = (day_of_week, start_time, end_time)
        if slot in seen:
            raise BusinessError("Horario duplicado en la misma clase")
        seen.add(slot)
    for i, slot_a in enumerate(schedules):
        for slot_b in schedules[i + 1 :]:
            if _slots_overlap(slot_a, slot_b):
                raise BusinessError(
                    "Los horarios de la clase se solapan en el mismo día"
                )


def _validate_price(price) -> Decimal:
    try:
        price = Decimal(str(price))
    except (InvalidOperation, ValueError, TypeError):
        raise BusinessError("El precio no es válido")
    if price < 0:
        raise BusinessError("El precio no puede ser negativo")
    return price.quantize(Decimal("0.01"))


def _validate_status(status: str) -> str:
    status = (status or "").strip().lower()
    if status not in CLASS_STATUSES:
        raise BusinessError(
            "El estado debe ser scheduled, started o ended"
        )
    return status


def _validate_class_dates(
    start_date: date | None,
    end_date: date | None,
) -> tuple[date | None, date | None]:
    if start_date and end_date and end_date < start_date:
        raise BusinessError(
            "La fecha de fin no puede ser anterior a la de inicio"
        )
    return start_date, end_date


def _validate_class_fields(
    name: str,
    trainer_id: int,
    capacity: int,
    schedules: list[ScheduleSlot],
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    price=Decimal("0"),
    status: str = "scheduled",
) -> tuple[str, date | None, date | None, Decimal, str]:
    name = name.strip()
    if not name:
        raise BusinessError("El nombre no puede estar vacío")
    if repo.get_trainer(trainer_id) is None:
        raise BusinessError("El entrenador no existe")
    if capacity <= 0:
        raise BusinessError("El cupo debe ser mayor que cero")
    _validate_schedules(schedules)
    start_date, end_date = _validate_class_dates(start_date, end_date)
    price = _validate_price(price)
    status = _validate_status(status)
    return name, start_date, end_date, price, status


def create_class(
    name: str,
    trainer_id: int,
    capacity: int,
    schedules: list[ScheduleSlot],
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    price=Decimal("0"),
    status: str = "scheduled",
) -> GymClass:
    name, start_date, end_date, price, status = _validate_class_fields(
        name,
        trainer_id,
        capacity,
        schedules,
        start_date=start_date,
        end_date=end_date,
        price=price,
        status=status,
    )
    return repo.create_class(
        name=name,
        trainer_id=trainer_id,
        capacity=capacity,
        schedules=schedules,
        start_date=start_date,
        end_date=end_date,
        price=price,
        status=status,
    )


def get_class(class_id: int):
    return repo.get_class(class_id)


def update_class(
    class_id: int,
    name: str,
    trainer_id: int,
    capacity: int,
    schedules: list[ScheduleSlot],
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    price=Decimal("0"),
    status: str = "scheduled",
) -> GymClass:
    if repo.get_class(class_id) is None:
        raise BusinessError("Clase no existe")
    name, start_date, end_date, price, status = _validate_class_fields(
        name,
        trainer_id,
        capacity,
        schedules,
        start_date=start_date,
        end_date=end_date,
        price=price,
        status=status,
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
        capacity=capacity,
        schedules=schedules,
        start_date=start_date,
        end_date=end_date,
        price=price,
        status=status,
    )
    if gym_class is None:
        raise BusinessError("Clase no existe")
    return gym_class


def delete_class(class_id: int) -> None:
    if repo.get_class(class_id) is None:
        raise BusinessError("Clase no existe")
    repo.delete_class(class_id)


def _slot_key(slot: ScheduleSlot | ClassSchedule) -> tuple[int, time, time]:
    if isinstance(slot, ClassSchedule):
        return (slot.day_of_week, slot.start_time, slot.end_time)
    return slot


def _slots_overlap(
    slot_a: ScheduleSlot | ClassSchedule,
    slot_b: ScheduleSlot | ClassSchedule,
) -> bool:
    day_a, start_a, end_a = _slot_key(slot_a)
    day_b, start_b, end_b = _slot_key(slot_b)
    if day_a != day_b:
        return False
    return not (end_a <= start_b or end_b <= start_a)


def _classes_overlap(c1: GymClass, c2: GymClass) -> bool:
    return any(
        _slots_overlap(slot_a, slot_b)
        for slot_a in c1.schedules
        for slot_b in c2.schedules
    )


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
        if other.id == class_id:
            continue
        if _classes_overlap(gym_class, other):
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


def _find_class_schedule(gym_class: GymClass, schedule_id: int) -> ClassSchedule:
    for schedule in gym_class.schedules:
        if schedule.id == schedule_id:
            return schedule
    raise BusinessError("El horario no pertenece a esta clase")


def mark_attendance(
    class_id: int,
    member_id: int,
    *,
    schedule_id: int,
    session_date: date,
) -> None:
    gym_class = repo.get_class(class_id)
    if gym_class is None:
        raise BusinessError("Clase no existe")
    if not repo.get_member(member_id):
        raise BusinessError("Miembro no existe")
    if not repo.is_member_enrolled(class_id, member_id):
        raise BusinessError("El miembro no está inscrito en esta clase")

    schedule = _find_class_schedule(gym_class, schedule_id)
    if session_date.weekday() != schedule.day_of_week:
        raise BusinessError("La fecha no coincide con el día del horario")
    if gym_class.start_date and session_date < gym_class.start_date:
        raise BusinessError("La fecha está fuera del período de la clase")
    if gym_class.end_date and session_date > gym_class.end_date:
        raise BusinessError("La fecha está fuera del período de la clase")
    if repo.has_attendance_on_date(class_id, member_id, session_date):
        raise BusinessError("El miembro ya tiene asistencia registrada en esta fecha")

    attended_at = datetime.combine(session_date, schedule.start_time)
    repo.mark_attendance(class_id, member_id, attended_at)


def list_attendance():
    return repo.list_attendance()


def list_attendance_by_class(class_id: int):
    if repo.get_class(class_id) is None:
        raise BusinessError("Clase no existe")
    return repo.list_attendance_by_class(class_id)


def list_class_attendance_roster(class_id: int, session_date):
    if repo.get_class(class_id) is None:
        raise BusinessError("Clase no existe")
    return repo.list_class_attendance_roster(class_id, session_date)


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


def format_schedule_slot(schedule: ClassSchedule) -> str:
    return (
        f"{DAY_NAMES[schedule.day_of_week]} "
        f"{schedule.start_time.strftime('%H:%M')}-"
        f"{schedule.end_time.strftime('%H:%M')}"
    )


def format_class_schedules(gym_class: GymClass) -> str:
    if not gym_class.schedules:
        return "(no schedule)"
    parts = []
    for schedule in sorted(
        gym_class.schedules, key=lambda s: (s.day_of_week, s.start_time)
    ):
        parts.append(format_schedule_slot(schedule))
    return ", ".join(parts)


def format_class_price(gym_class: GymClass) -> str:
    return f"${gym_class.price:.2f}"


def format_class_date(value: date | None) -> str:
    return value.strftime("%Y-%m-%d") if value else "-"


def format_class_period(gym_class: GymClass) -> str:
    return (
        f"{format_class_date(gym_class.start_date)} → "
        f"{format_class_date(gym_class.end_date)}"
    )


def format_class(gym_class: GymClass) -> str:
    trainer_label = gym_class.trainer_name or str(gym_class.trainer_id)
    return (
        f"[{gym_class.id}] {gym_class.name} - Entrenador {trainer_label} - "
        f"Horario: {format_class_schedules(gym_class)} "
        f"Cupo: {gym_class.capacity} - "
        f"Precio: {format_class_price(gym_class)} - "
        f"Estado: {gym_class.status} - "
        f"Periodo: {format_class_period(gym_class)}"
    )


def list_trainers():
    return repo.list_trainers()


def list_members():
    return repo.list_members()

