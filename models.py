from dataclasses import dataclass
from datetime import time


@dataclass
class Trainer:
    id: int
    name: str


@dataclass
class Member:
    id: int
    name: str


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

