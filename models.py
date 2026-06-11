from dataclasses import dataclass, field
from datetime import date, datetime, time
from decimal import Decimal


@dataclass
class Trainer:
    id: int
    name: str
    email: str
    phone: str
    specialty: str
    bio: str = ""
    years_experience: int | None = None


@dataclass
class Member:
    id: int
    name: str
    email: str
    phone: str
    membership_plan: str
    notes: str = ""


@dataclass
class ClassSchedule:
    id: int
    class_id: int
    day_of_week: int
    start_time: time
    end_time: time


@dataclass
class GymClass:
    id: int
    name: str
    trainer_id: int
    capacity: int
    trainer_name: str = ""
    schedules: list[ClassSchedule] = field(default_factory=list)
    start_date: date | None = None
    end_date: date | None = None
    price: Decimal = Decimal("0")
    status: str = "scheduled"


@dataclass
class Enrollment:
    class_id: int
    member_id: int
    class_name: str
    member_name: str


@dataclass
class Attendance:
    class_id: int
    member_id: int
    attended_at: datetime
    class_name: str
    member_name: str


@dataclass
class AttendanceRosterRow:
    member_id: int
    member_name: str
    membership_plan: str
    email: str
    attended_at: datetime | None = None
