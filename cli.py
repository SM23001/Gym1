from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation

import psycopg2

from colors import CYAN, YELLOW, c
from db import init_schema
import service
from ui import (
    clear_screen,
    pause,
    print_banner,
    print_trainer_banner,
    print_member_banner,
    print_class_banner,
    print_empty,
    print_error,
    print_header,
    print_menu,
    print_section,
    print_success,
    print_table,
    prompt_option,
)

DAY_NAMES = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)


CLASS_STATUS_OPTIONS = service.CLASS_STATUSES


def parse_time(hhmm: str) -> time:
    return datetime.strptime(hhmm.strip(), "%H:%M").time()


def parse_date(value: str) -> date:
    return datetime.strptime(value.strip(), "%Y-%m-%d").date()


def prompt_text(label: str, *, required: bool = True) -> str:
    while True:
        value = input(c(f"  {label}: ", CYAN)).strip()
        if value or not required:
            return value
        print_error("This field is required.")


def prompt_int(
    label: str,
    *,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    while True:
        raw = input(c(f"  {label}: ", CYAN)).strip()
        try:
            value = int(raw)
        except ValueError:
            print_error("Enter a valid integer.")
            continue
        if min_value is not None and value < min_value:
            print_error(f"Minimum value is {min_value}.")
            continue
        if max_value is not None and value > max_value:
            print_error(f"Maximum value is {max_value}.")
            continue
        return value


def prompt_time(label: str) -> time:
    while True:
        raw = input(c(f"  {label} (HH:MM): ", CYAN)).strip()
        try:
            return parse_time(raw)
        except ValueError:
            print_error("Invalid format. Use HH:MM, e.g. 09:30.")


def prompt_optional_date(label: str, *, required: bool = False) -> date | None:
    hint = c(" [YYYY-MM-DD, Enter = skip]", CYAN)
    while True:
        raw = input(c(f"  {label}{hint}: ", CYAN)).strip()
        if not raw:
            if required:
                print_error("This field is required.")
                continue
            return None
        try:
            return parse_date(raw)
        except ValueError:
            print_error("Invalid format. Use YYYY-MM-DD, e.g. 2026-06-01.")


def prompt_decimal(label: str, *, min_value: Decimal | None = None) -> Decimal:
    while True:
        raw = input(c(f"  {label}: ", CYAN)).strip()
        try:
            value = Decimal(raw)
        except InvalidOperation:
            print_error("Enter a valid amount, e.g. 19.99.")
            continue
        if min_value is not None and value < min_value:
            print_error(f"Minimum value is {min_value}.")
            continue
        return value


def prompt_status(label: str) -> str:
    options = " / ".join(CLASS_STATUS_OPTIONS)
    while True:
        raw = input(c(f"  {label} ({options}): ", CYAN)).strip().lower()
        if raw in CLASS_STATUS_OPTIONS:
            return raw
        print_error(f"Choose one of: {options}.")


def prompt_optional_text(label: str, current: str) -> str:
    hint = c(f" [Enter = '{current}']", CYAN)
    value = input(c(f"  {label}{hint}: ", CYAN)).strip()
    return value if value else current


def prompt_optional_int(label: str, current: int, **kwargs) -> int:
    hint = c(f" [Enter = {current}]", CYAN)
    raw = input(c(f"  {label}{hint}: ", CYAN)).strip()
    if not raw:
        return current
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(f"{label}: expected an integer")
    min_value = kwargs.get("min_value")
    max_value = kwargs.get("max_value")
    if min_value is not None and value < min_value:
        raise ValueError(f"{label}: minimum value is {min_value}")
    if max_value is not None and value > max_value:
        raise ValueError(f"{label}: maximum value is {max_value}")
    return value


def prompt_optional_time(label: str, current: time) -> time:
    hint = c(f" [Enter = {current.strftime('%H:%M')}]", CYAN)
    raw = input(c(f"  {label}{hint}: ", CYAN)).strip()
    if not raw:
        return current
    return parse_time(raw)


def prompt_optional_class_date(label: str, current: date | None) -> date | None:
    shown = current.strftime("%Y-%m-%d") if current else "skip"
    hint = c(f" [YYYY-MM-DD, Enter = {shown}, '-' = clear]", CYAN)
    raw = input(c(f"  {label}{hint}: ", CYAN)).strip()
    if not raw:
        return current
    if raw == "-":
        return None
    try:
        return parse_date(raw)
    except ValueError:
        raise ValueError(f"{label}: use YYYY-MM-DD")


def prompt_optional_decimal(
    label: str, current: Decimal, *, min_value: Decimal | None = None
) -> Decimal:
    hint = c(f" [Enter = {current}]", CYAN)
    raw = input(c(f"  {label}{hint}: ", CYAN)).strip()
    if not raw:
        return current
    try:
        value = Decimal(raw)
    except InvalidOperation:
        raise ValueError(f"{label}: expected a number")
    if min_value is not None and value < min_value:
        raise ValueError(f"{label}: minimum value is {min_value}")
    return value


def prompt_optional_status(label: str, current: str) -> str:
    options = " / ".join(CLASS_STATUS_OPTIONS)
    hint = c(f" [{options}, Enter = {current}]", CYAN)
    raw = input(c(f"  {label}{hint}: ", CYAN)).strip().lower()
    if not raw:
        return current
    if raw not in CLASS_STATUS_OPTIONS:
        raise ValueError(f"{label}: choose one of {options}")
    return raw


def show_trainers() -> None:
    trainers = service.list_trainers()
    if not trainers:
        print_empty("(no trainers registered)")
        return
    print_table(
        ["ID", "Name", "Specialty", "Email"],
        [
            [str(trainer.id), trainer.name, trainer.specialty, trainer.email]
            for trainer in trainers
        ],
    )


def show_trainer_profile(trainer) -> None:
    years = (
        str(trainer.years_experience)
        if trainer.years_experience is not None
        else "(not set)"
    )
    bio = trainer.bio if trainer.bio else "(not set)"
    print_success(f"[{trainer.id}] {trainer.name}")
    print(f"  Email:       {trainer.email}")
    print(f"  Phone:       {trainer.phone}")
    print(f"  Specialty:   {trainer.specialty}")
    print(f"  Experience:  {years} years")
    print(f"  Bio:         {bio}")


def show_members() -> None:
    members = service.list_members()
    if not members:
        print_empty("(no members registered)")
        return
    print_table(
        ["ID", "Name", "Plan", "Email"],
        [
            [
                str(member.id),
                member.name,
                member.membership_plan,
                member.email,
            ]
            for member in members
        ],
    )


def show_member_profile(member) -> None:
    notes = member.notes if member.notes else "(not set)"
    print_success(f"[{member.id}] {member.name}")
    print(f"  Email:     {member.email}")
    print(f"  Phone:     {member.phone}")
    print(f"  Plan:      {member.membership_plan}")
    print(f"  Notes:     {notes}")


CLASS_TABLE_HEADERS = [
    "ID",
    "Name",
    "Trainer",
    "Schedule",
    "Capacity",
    "Price",
    "Status",
    "Start",
    "End",
]


def class_table_row(gym_class) -> list[str]:
    return [
        str(gym_class.id),
        gym_class.name,
        gym_class.trainer_name,
        format_class_schedule_cell(gym_class),
        str(gym_class.capacity),
        service.format_class_price(gym_class),
        gym_class.status,
        service.format_class_date(gym_class.start_date),
        service.format_class_date(gym_class.end_date),
    ]


def show_classes() -> None:
    classes = service.list_classes()
    if not classes:
        print_empty("(no classes registered)")
        return
    print_table(
        CLASS_TABLE_HEADERS,
        [class_table_row(gym_class) for gym_class in classes],
    )


def show_class_rows(classes, *, empty_message: str = "(no classes)") -> None:
    if not classes:
        print_empty(empty_message)
        return
    print_table(
        CLASS_TABLE_HEADERS,
        [class_table_row(gym_class) for gym_class in classes],
    )


def show_member_rows(members, *, empty_message: str = "(no members)") -> None:
    if not members:
        print_empty(empty_message)
        return
    print_table(
        ["ID", "Name", "Plan", "Email"],
        [
            [
                str(member.id),
                member.name,
                member.membership_plan,
                member.email,
            ]
            for member in members
        ],
    )


def format_class_schedule_cell(gym_class) -> str:
    return service.format_class_schedules(gym_class)


def prompt_schedules(*, existing=None):
    if existing is not None and existing.schedules:
        print(c("  Current schedule:", CYAN))
        for schedule in sorted(
            existing.schedules, key=lambda s: (s.day_of_week, s.start_time)
        ):
            print(
                f"    {DAY_NAMES[schedule.day_of_week]} "
                f"{schedule.start_time.strftime('%H:%M')}-"
                f"{schedule.end_time.strftime('%H:%M')}"
            )
        print(c("  Enter a new schedule (replaces all slots).", YELLOW))

    schedules = []
    print(c("  Schedule slots (at least one required)", CYAN))
    while True:
        print(c("  1 = Add one day  2 = Add Mon–Fri  3 = Finish", CYAN))
        choice = input(c("  Option: ", CYAN)).strip()
        if choice == "3":
            if schedules:
                return schedules
            print_error("Add at least one schedule slot.")
            continue
        if choice == "1":
            print(c("  Days: 0=Monday … 6=Sunday", CYAN))
            day = prompt_int("Day of week", min_value=0, max_value=6)
            start = prompt_time("Start time")
            end = prompt_time("End time")
            schedules.append((day, start, end))
            print_success(
                f"Added {DAY_NAMES[day]} "
                f"{start.strftime('%H:%M')}-{end.strftime('%H:%M')}"
            )
            continue
        if choice == "2":
            start = prompt_time("Start time")
            end = prompt_time("End time")
            for day in range(5):
                schedules.append((day, start, end))
            print_success(
                f"Added Mon–Fri {start.strftime('%H:%M')}-{end.strftime('%H:%M')}"
            )
            continue
        print_error("Invalid option. Enter 1, 2, or 3.")


def prompt_class_fields(*, existing=None):
    if existing is None:
        name = prompt_text("Class name")
        print(c("  Available trainers:", YELLOW))
        show_trainers()
        trainer_id = prompt_int("Trainer id", min_value=1)
        capacity = prompt_int("Max capacity", min_value=1)
        price = prompt_decimal("Price ($)", min_value=Decimal("0"))
        status = prompt_status("Status")
        start_date = prompt_optional_date("Start date")
        end_date = prompt_optional_date("End date")
        schedules = prompt_schedules()
        return {
            "name": name,
            "trainer_id": trainer_id,
            "capacity": capacity,
            "schedules": schedules,
            "start_date": start_date,
            "end_date": end_date,
            "price": price,
            "status": status,
        }

    name = prompt_optional_text("Class name", existing.name)
    print(c("  Available trainers:", YELLOW))
    show_trainers()
    trainer_id = prompt_optional_int(
        "Trainer id", existing.trainer_id, min_value=1
    )
    capacity = prompt_optional_int("Max capacity", existing.capacity, min_value=1)
    price = prompt_optional_decimal(
        "Price ($)", existing.price, min_value=Decimal("0")
    )
    status = prompt_optional_status("Status", existing.status)
    start_date = prompt_optional_class_date("Start date", existing.start_date)
    end_date = prompt_optional_class_date("End date", existing.end_date)
    schedules = prompt_schedules(existing=existing)
    return {
        "name": name,
        "trainer_id": trainer_id,
        "capacity": capacity,
        "schedules": schedules,
        "start_date": start_date,
        "end_date": end_date,
        "price": price,
        "status": status,
    }


def prompt_optional_years_experience(
    label: str, current: int | None = None
) -> int | None:
    if current is None:
        hint = c(" [Enter = skip]", CYAN)
    else:
        hint = c(f" [Enter = {current}]", CYAN)
    raw = input(c(f"  {label}{hint}: ", CYAN)).strip()
    if not raw:
        return current
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"{label}: expected an integer or empty")


def prompt_trainer_fields(*, existing=None):
    if existing is None:
        name = prompt_text("Trainer name")
        email = prompt_text("Email")
        phone = prompt_text("Phone")
        specialty = prompt_text("Specialty")
        bio = prompt_text("Bio", required=False)
        years_experience = prompt_optional_years_experience("Years of experience")
        return name, email, phone, specialty, bio, years_experience

    name = prompt_optional_text("Trainer name", existing.name)
    email = prompt_optional_text("Email", existing.email)
    phone = prompt_optional_text("Phone", existing.phone)
    specialty = prompt_optional_text("Specialty", existing.specialty)
    bio = prompt_optional_text("Bio", existing.bio)
    years_experience = prompt_optional_years_experience(
        "Years of experience", existing.years_experience
    )
    return name, email, phone, specialty, bio, years_experience


def prompt_member_fields(*, existing=None):
    if existing is None:
        name = prompt_text("Member name")
        email = prompt_text("Email")
        phone = prompt_text("Phone")
        membership_plan = prompt_text("Membership plan")
        notes = prompt_text("Notes", required=False)
        return name, email, phone, membership_plan, notes

    name = prompt_optional_text("Member name", existing.name)
    email = prompt_optional_text("Email", existing.email)
    phone = prompt_optional_text("Phone", existing.phone)
    membership_plan = prompt_optional_text(
        "Membership plan", existing.membership_plan
    )
    notes = prompt_optional_text("Notes", existing.notes)
    return name, email, phone, membership_plan, notes


def prompt_trainer_id(action: str) -> int:
    print_section(action)
    show_trainers()
    return prompt_int("Trainer id", min_value=1)


def prompt_member_id(action: str) -> int:
    print_section(action)
    show_members()
    return prompt_int("Member id", min_value=1)


def prompt_class_id(action: str) -> int:
    print_section(action)
    show_classes()
    return prompt_int("Class id", min_value=1)


def run_trainer_menu() -> None:
    options = [
        ("1", "Add trainer"),
        ("2", "List trainers"),
        ("3", "View by id"),
        ("4", "Update"),
        ("5", "Delete"),
        ("6", "Classes of trainer"),
        ("0", "Back"),
    ]
    while True:
        clear_screen()
        print_trainer_banner()
        print_menu(options)
        option = prompt_option()

        try:
            if option == "1":
                (
                    name,
                    email,
                    phone,
                    specialty,
                    bio,
                    years_experience,
                ) = prompt_trainer_fields()
                t = service.create_trainer(
                    name,
                    email,
                    phone,
                    specialty,
                    bio=bio,
                    years_experience=years_experience,
                )
                print_success(f"Trainer created with id {t.id}")
                pause()

            elif option == "2":
                print_section("Trainers")
                show_trainers()
                pause()

            elif option == "3":
                trainer_id = prompt_trainer_id("Select a trainer")
                t = service.get_trainer(trainer_id)
                if t is None:
                    print_error("Trainer not found")
                else:
                    print_section("Trainer profile")
                    show_trainer_profile(t)
                pause()

            elif option == "4":
                trainer_id = prompt_trainer_id("Trainer to update")
                existing = service.get_trainer(trainer_id)
                if existing is None:
                    print_error("Trainer not found")
                else:
                    (
                        name,
                        email,
                        phone,
                        specialty,
                        bio,
                        years_experience,
                    ) = prompt_trainer_fields(existing=existing)
                    t = service.update_trainer(
                        trainer_id,
                        name,
                        email,
                        phone,
                        specialty,
                        bio=bio,
                        years_experience=years_experience,
                    )
                    print_success(f"Trainer updated: [{t.id}] {t.name}")
                pause()

            elif option == "5":
                trainer_id = prompt_trainer_id("Trainer to delete")
                service.delete_trainer(trainer_id)
                print_success("Trainer deleted")
                pause()

            elif option == "6":
                trainer_id = prompt_trainer_id("Select a trainer")
                t = service.get_trainer(trainer_id)
                if t is None:
                    print_error("Trainer not found")
                else:
                    print_section(f"Classes for [{t.id}] {t.name}")
                    show_class_rows(
                        service.list_classes_by_trainer(trainer_id),
                        empty_message="(no classes for this trainer)",
                    )
                pause()

            elif option == "0":
                return

            else:
                print_error("Invalid option.")

        except service.BusinessError as e:
            print_error(str(e))
            pause()
        except ValueError as e:
            print_error(str(e))
            pause()
        except psycopg2.Error as e:
            print_error(f"Database: {e}")
            pause()


def run_member_menu() -> None:
    options = [
        ("1", "Add member"),
        ("2", "List members"),
        ("3", "View by id"),
        ("4", "Update"),
        ("5", "Delete"),
        ("6", "Classes of member"),
        ("0", "Back"),
    ]
    while True:
        clear_screen()
        print_member_banner()
        print_menu(options)
        option = prompt_option()

        try:
            if option == "1":
                (
                    name,
                    email,
                    phone,
                    membership_plan,
                    notes,
                ) = prompt_member_fields()
                m = service.create_member(
                    name,
                    email,
                    phone,
                    membership_plan,
                    notes=notes,
                )
                print_success(f"Member created with id {m.id}")
                pause()

            elif option == "2":
                print_section("Members")
                show_members()
                pause()

            elif option == "3":
                member_id = prompt_member_id("Select a member")
                m = service.get_member(member_id)
                if m is None:
                    print_error("Member not found")
                else:
                    print_section("Member profile")
                    show_member_profile(m)
                pause()

            elif option == "4":
                member_id = prompt_member_id("Member to update")
                existing = service.get_member(member_id)
                if existing is None:
                    print_error("Member not found")
                else:
                    (
                        name,
                        email,
                        phone,
                        membership_plan,
                        notes,
                    ) = prompt_member_fields(existing=existing)
                    m = service.update_member(
                        member_id,
                        name,
                        email,
                        phone,
                        membership_plan,
                        notes=notes,
                    )
                    print_success(f"Member updated: [{m.id}] {m.name}")
                pause()

            elif option == "5":
                member_id = prompt_member_id("Member to delete")
                service.delete_member(member_id)
                print_success("Member deleted")
                pause()

            elif option == "6":
                member_id = prompt_member_id("Select a member")
                m = service.get_member(member_id)
                if m is None:
                    print_error("Member not found")
                else:
                    print_section(f"Classes for [{m.id}] {m.name}")
                    show_class_rows(
                        service.list_member_classes(member_id),
                        empty_message="(no classes for this member)",
                    )
                pause()

            elif option == "0":
                return

            else:
                print_error("Invalid option.")

        except service.BusinessError as e:
            print_error(str(e))
            pause()
        except ValueError as e:
            print_error(str(e))
            pause()
        except psycopg2.Error as e:
            print_error(f"Database: {e}")
            pause()


def run_class_menu() -> None:
    options = [
        ("1", "Add class"),
        ("2", "List classes"),
        ("3", "View by id"),
        ("4", "Update"),
        ("5", "Delete"),
        ("6", "Members of class"),
        ("0", "Back"),
    ]
    while True:
        clear_screen()
        print_class_banner()
        print_menu(options)
        option = prompt_option()

        try:
            if option == "1":
                fields = prompt_class_fields()
                gym_class = service.create_class(**fields)
                print_success(f"Class created with id {gym_class.id}")
                pause()

            elif option == "2":
                print_section("Classes")
                show_classes()
                pause()

            elif option == "3":
                class_id = prompt_class_id("Select a class")
                gym_class = service.get_class(class_id)
                if gym_class is None:
                    print_error("Class not found")
                else:
                    print_success(service.format_class(gym_class))
                pause()

            elif option == "4":
                class_id = prompt_class_id("Class to update")
                existing = service.get_class(class_id)
                if existing is None:
                    print_error("Class not found")
                    pause()
                    continue
                fields = prompt_class_fields(existing=existing)
                gym_class = service.update_class(class_id, **fields)
                print_success(f"Class updated: {service.format_class(gym_class)}")
                pause()

            elif option == "5":
                class_id = prompt_class_id("Class to delete")
                service.delete_class(class_id)
                print_success("Class deleted")
                pause()

            elif option == "6":
                class_id = prompt_class_id("Select a class")
                gym_class = service.get_class(class_id)
                if gym_class is None:
                    print_error("Class not found")
                else:
                    print_section(f"Members of [{gym_class.id}] {gym_class.name}")
                    members = service.list_class_members(class_id)
                    if not members:
                        print_empty("(no members enrolled in this class)")
                    else:
                        show_member_rows(members)
                pause()

            elif option == "0":
                return

            else:
                print_error("Invalid option.")

        except service.BusinessError as e:
            print_error(str(e))
            pause()
        except ValueError as e:
            print_error(str(e))
            pause()
        except psycopg2.Error as e:
            print_error(f"Database: {e}")
            pause()


def run_enrollment_menu() -> None:
    options = [
        ("1", "Enroll member in class"),
        ("2", "List enrollments"),
        ("3", "View enrollment"),
        ("4", "Unenroll member"),
        ("5", "Members of class"),
        ("6", "Classes of member"),
        ("0", "Back"),
    ]
    while True:
        clear_screen()
        print_header("Enrollment")
        print_menu(options)
        option = prompt_option()

        try:
            if option == "1":
                class_id = prompt_class_id("Class for enrollment")
                member_id = prompt_member_id("Member to enroll")
                service.enroll_member(class_id, member_id)
                print_success("Member enrolled successfully")
                pause()

            elif option == "2":
                print_section("Enrollments")
                enrollments = service.list_enrollments()
                if not enrollments:
                    print_empty("(no enrollments)")
                else:
                    print_table(
                        ["Class", "Member"],
                        [
                            [
                                f"[{enrollment.class_id}] {enrollment.class_name}",
                                f"[{enrollment.member_id}] {enrollment.member_name}",
                            ]
                            for enrollment in enrollments
                        ],
                    )
                pause()

            elif option == "3":
                class_id = prompt_class_id("Class")
                member_id = prompt_member_id("Member")
                if service.is_enrolled(class_id, member_id):
                    print_success("Member is enrolled in this class")
                else:
                    print_error("Member is not enrolled in this class")
                pause()

            elif option == "4":
                class_id = prompt_class_id("Class to unenroll from")
                member_id = prompt_member_id("Member to unenroll")
                service.unenroll_member(class_id, member_id)
                print_success("Member unenrolled successfully")
                pause()

            elif option == "5":
                class_id = prompt_class_id("Select a class")
                gym_class = service.get_class(class_id)
                if gym_class is None:
                    print_error("Class not found")
                else:
                    print_section(f"Members of [{gym_class.id}] {gym_class.name}")
                    members = service.list_class_members(class_id)
                    if not members:
                        print_empty("(no members enrolled in this class)")
                    else:
                        show_member_rows(members)
                pause()

            elif option == "6":
                member_id = prompt_member_id("Select a member")
                m = service.get_member(member_id)
                if m is None:
                    print_error("Member not found")
                else:
                    print_section(f"Classes for [{m.id}] {m.name}")
                    show_class_rows(
                        service.list_member_classes(member_id),
                        empty_message="(no classes for this member)",
                    )
                pause()

            elif option == "0":
                return

            else:
                print_error("Invalid option.")

        except service.BusinessError as e:
            print_error(str(e))
            pause()
        except ValueError as e:
            print_error(str(e))
            pause()
        except psycopg2.Error as e:
            print_error(f"Database: {e}")
            pause()


def show_attendance_records(records) -> None:
    if not records:
        print_empty("(no attendance records)")
        return
    print_table(
        ["Class", "Member", "Attended at"],
        [
            [
                f"[{record.class_id}] {record.class_name}",
                f"[{record.member_id}] {record.member_name}",
                record.attended_at.strftime("%Y-%m-%d %H:%M:%S"),
            ]
            for record in records
        ],
    )


def prompt_attendance_to_delete(class_id: int, member_id: int):
    records = service.list_attendance_for_pair(class_id, member_id)
    if not records:
        raise service.BusinessError("No attendance records for this class and member")
    if len(records) == 1:
        return records[0].attended_at
    print_section("Records for this class and member")
    for index, record in enumerate(records, start=1):
        print(f"    {index}. {service.format_attendance(record)}")
    index = prompt_int("Record number to delete", min_value=1, max_value=len(records))
    return records[index - 1].attended_at


def run_attendance_menu() -> None:
    options = [
        ("1", "Record attendance"),
        ("2", "List attendance"),
        ("3", "View attendance"),
        ("4", "Delete attendance record"),
        ("5", "Attendance by class"),
        ("6", "Attendance by member"),
        ("0", "Back"),
    ]
    while True:
        clear_screen()
        print_header("Attendance")
        print_menu(options)
        option = prompt_option()

        try:
            if option == "1":
                class_id = prompt_class_id("Class")
                member_id = prompt_member_id("Member")
                service.mark_attendance(class_id, member_id)
                print_success("Attendance recorded")
                pause()

            elif option == "2":
                print_section("Attendance")
                show_attendance_records(service.list_attendance())
                pause()

            elif option == "3":
                class_id = prompt_class_id("Class")
                member_id = prompt_member_id("Member")
                records = service.list_attendance_for_pair(class_id, member_id)
                if not records:
                    print_error("No attendance records for this class and member")
                else:
                    print_section("Attendance records")
                    show_attendance_records(records)
                pause()

            elif option == "4":
                class_id = prompt_class_id("Class")
                member_id = prompt_member_id("Member")
                attended_at = prompt_attendance_to_delete(class_id, member_id)
                service.delete_attendance(class_id, member_id, attended_at)
                print_success("Attendance record deleted")
                pause()

            elif option == "5":
                class_id = prompt_class_id("Select a class")
                gym_class = service.get_class(class_id)
                if gym_class is None:
                    print_error("Class not found")
                else:
                    print_section(
                        f"Attendance for [{gym_class.id}] {gym_class.name}"
                    )
                    show_attendance_records(
                        service.list_attendance_by_class(class_id)
                    )
                    print_section(
                        f"Enrolled members of [{gym_class.id}] {gym_class.name}"
                    )
                    members = service.list_class_members(class_id)
                    if not members:
                        print_empty("(no members enrolled in this class)")
                    else:
                        show_member_rows(members)
                pause()

            elif option == "6":
                member_id = prompt_member_id("Select a member")
                m = service.get_member(member_id)
                if m is None:
                    print_error("Member not found")
                else:
                    print_section(f"Attendance for [{m.id}] {m.name}")
                    show_attendance_records(
                        service.list_attendance_by_member(member_id)
                    )
                pause()

            elif option == "0":
                return

            else:
                print_error("Invalid option.")

        except service.BusinessError as e:
            print_error(str(e))
            pause()
        except ValueError as e:
            print_error(str(e))
            pause()
        except psycopg2.Error as e:
            print_error(f"Database: {e}")
            pause()


def main() -> None:
    init_schema()

    main_options = [
        ("1", "Trainers"),
        ("2", "Members"),
        ("3", "Classes"),
        ("4", "Enrollment"),
        ("5", "Attendance"),
        ("0", "Exit"),
    ]

    while True:
        clear_screen()
        print_banner()
        print_header("Gym Management")
        print_menu(main_options)
        option = prompt_option()

        if option == "1":
            run_trainer_menu()
        elif option == "2":
            run_member_menu()
        elif option == "3":
            run_class_menu()
        elif option == "4":
            run_enrollment_menu()
        elif option == "5":
            run_attendance_menu()
        elif option == "0":
            print()
            print_success("Goodbye.")
            break
        else:
            print_error("Invalid option.")
            pause()


if __name__ == "__main__":
    main()
