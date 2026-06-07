from dataclasses import dataclass
from datetime import datetime, time


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
class GymClass:
    id: int
    name: str
    trainer_id: int
    day_of_week: int
    start_time: time
    end_time: time
    capacity: int


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

