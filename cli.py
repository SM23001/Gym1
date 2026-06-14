import calendar
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from getpass import getpass

import psycopg2

from colors import CYAN, GREEN, YELLOW, c
from db import init_schema
from models import AppUser, UserRole
import service
from ui import (
    clear_screen,
    pause,
    print_banner,
    print_trainer_banner,
    print_member_banner,
    print_class_banner,
    print_enrollment_banner,
    print_attendance_banner,
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


def prompt_date(label: str) -> date:
    while True:
        raw = input(c(f"  {label} (YYYY-MM-DD): ", CYAN)).strip()
        try:
            return parse_date(raw)
        except ValueError:
            print_error("Invalid format. Use YYYY-MM-DD, e.g. 2026-06-10.")


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
        ["ID", "Name", "Specialty", "Email", "Phone", "Exp (yrs)", "Bio"],
        [
            [
                str(trainer.id),
                trainer.name,
                trainer.specialty,
                trainer.email,
                trainer.phone,
                str(trainer.years_experience) if trainer.years_experience is not None else "—",
                trainer.bio if trainer.bio else "—",
            ]
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


MEMBER_TABLE_HEADERS = ["ID", "Name", "Plan", "Email", "Phone", "Notes"]


def member_table_row(member) -> list[str]:
    notes = member.notes if member.notes else "(not set)"
    return [
        str(member.id),
        member.name,
        member.membership_plan,
        member.email,
        member.phone,
        notes,
    ]


def show_members() -> None:
    members = service.list_members()
    if not members:
        print_empty("(no members registered)")
        return
    print_table(
        MEMBER_TABLE_HEADERS,
        [member_table_row(member) for member in members],
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
        MEMBER_TABLE_HEADERS,
        [member_table_row(member) for member in members],
    )


def format_class_schedule_cell(gym_class) -> str:
    return service.format_class_schedules(gym_class)


def prompt_class_schedule(gym_class):
    schedules = sorted(
        gym_class.schedules, key=lambda s: (s.day_of_week, s.start_time)
    )
    if not schedules:
        print_empty("(no schedule slots for this class)")
        return None
    if len(schedules) == 1:
        print_section("Schedule slot")
        print_success(service.format_schedule_slot(schedules[0]))
        return schedules[0]
    print_section("Select schedule slot")
    for index, schedule in enumerate(schedules, start=1):
        print(
            c(f"  [{index}] {service.format_schedule_slot(schedule)}", CYAN)
        )
    index = prompt_int("Slot", min_value=1, max_value=len(schedules))
    return schedules[index - 1]


_WEEKDAY_HEADERS = (" Mo", " Tu", " We", " Th", " Fr", " Sa", " Su")


def _calendar_header_line() -> str:
    return "  " + " ".join(_WEEKDAY_HEADERS)


def _print_month_calendar(
    year: int, month: int, valid_dates: set[date]
) -> None:
    header_line = _calendar_header_line()
    title = f"{calendar.month_name[month]} {year}"
    left_pad = max(0, (len(header_line) - len(title)) // 2)
    print(c(" " * left_pad + title, CYAN))
    print(c(header_line, CYAN))
    for week in calendar.monthcalendar(year, month):
        cells = []
        for day in week:
            if day == 0:
                cells.append("   ")
                continue
            session_date = date(year, month, day)
            if session_date in valid_dates:
                cells.append(c(f"*{day:2d}", GREEN))
            else:
                cells.append(f" {day:2d}")
        print(header_line[:2] + " ".join(cells))


def show_session_calendar(gym_class, schedule) -> list[date]:
    valid_dates = service.list_valid_session_dates(gym_class, schedule)
    print_section("Session calendar")
    print(
        f"  Class period: {service.format_class_date(gym_class.start_date)}"
        f" → {service.format_class_date(gym_class.end_date)}"
    )
    print(f"  Schedule:     {service.format_schedule_slot(schedule)}")
    print()
    if not valid_dates:
        print_empty("(no session dates match this schedule in the class period)")
        return valid_dates

    valid_set = set(valid_dates)
    start = gym_class.start_date
    end = gym_class.end_date
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        _print_month_calendar(year, month, valid_set)
        print()
        month += 1
        if month > 12:
            month = 1
            year += 1

    print(c("  * = valid session date", YELLOW))
    print()
    print(c("  Valid session dates:", CYAN))
    for index, session_date in enumerate(valid_dates, start=1):
        print(f"    [{index}] {session_date.isoformat()}")
    return valid_dates


def prompt_session_date(gym_class, schedule) -> date | None:
    valid_dates = show_session_calendar(gym_class, schedule)
    if not valid_dates:
        if gym_class.start_date is None or gym_class.end_date is None:
            return prompt_date("Session date")
        return None

    hint = c(f" [1-{len(valid_dates)} or YYYY-MM-DD]", CYAN)
    while True:
        raw = input(c(f"  Session date{hint}: ", CYAN)).strip()
        if raw.isdigit():
            index = int(raw)
            if 1 <= index <= len(valid_dates):
                return valid_dates[index - 1]
            print_error(f"Enter a number between 1 and {len(valid_dates)}.")
            continue
        try:
            session_date = parse_date(raw)
        except ValueError:
            print_error("Enter a list number or a date (YYYY-MM-DD).")
            continue
        if session_date not in valid_dates:
            print_error("That date is not a valid session for this schedule.")
            continue
        return session_date


def prompt_class_session(gym_class):
    schedule = prompt_class_schedule(gym_class)
    if schedule is None:
        return None, None
    session_date = prompt_session_date(gym_class, schedule)
    if session_date is None:
        return None, None
    print_success(session_date.isoformat())
    return schedule, session_date


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


def prompt_enrolled_member_id(action: str, class_id: int) -> int | None:
    print_section(action)
    members = service.list_class_members(class_id)
    if not members:
        print_empty("(no members enrolled in this class)")
        return None
    show_member_rows(members)
    return prompt_int("Member id", min_value=1)


def prompt_available_member_id(action: str, class_id: int) -> int | None:
    print_section(action)
    enrolled_ids = {member.id for member in service.list_class_members(class_id)}
    members = [
        member
        for member in service.list_members()
        if member.id not in enrolled_ids
    ]
    if not members:
        print_empty("(no members available for this class)")
        return None
    show_member_rows(members)
    return prompt_int("Member id", min_value=1)


def prompt_member_with_classes_id(action: str) -> int | None:
    print_section(action)
    enrolled_ids = {enrollment.member_id for enrollment in service.list_enrollments()}
    members = [
        member
        for member in service.list_members()
        if member.id in enrolled_ids
    ]
    if not members:
        print_empty("(no members enrolled in any class)")
        return None
    show_member_rows(members)
    return prompt_int("Member id", min_value=1)


def prompt_class_id(action: str) -> int:
    print_section(action)
    show_classes()
    return prompt_int("Class id", min_value=1)


def prompt_class_id_from_list(action: str, classes) -> int | None:
    print_section(action)
    if not classes:
        print_empty("(no classes available)")
        return None
    show_class_rows(classes)
    class_ids = {gym_class.id for gym_class in classes}
    while True:
        class_id = prompt_int("Class id", min_value=1)
        if class_id in class_ids:
            return class_id
        print_error("Invalid class id.")


def prompt_password(label: str = "Password") -> str:
    while True:
        value = getpass(c(f"  {label}: ", CYAN))
        if value:
            return value
        print_error("This field is required.")


def format_user_label(user: AppUser) -> str:
    return f"{user.username} ({user.role.value})"


def run_login() -> AppUser | None:
    while True:
        clear_screen()
        print_banner()
        print_header("Login")
        print("  1. Sign in")
        print("  0. Exit")
        option = prompt_option()

        if option == "0":
            return None
        if option != "1":
            print_error("Invalid option.")
            pause()
            continue

        username = prompt_text("Username")
        password = prompt_password()
        try:
            user = service.authenticate(username, password)
            print_success(f"Welcome, {format_user_label(user)}")
            pause()
            return user
        except service.BusinessError as e:
            print_error(str(e))
            pause()


def run_bootstrap_admin() -> None:
    clear_screen()
    print_banner()
    print_header("First-time setup")
    print("  No users found. Create the first administrator account.")
    print()
    username = prompt_text("Admin username")
    password = prompt_password("Password")
    confirm = prompt_password("Confirm password")
    if password != confirm:
        print_error("Passwords do not match.")
        pause()
        return
    try:
        service.bootstrap_admin(username, password)
        print_success("Administrator created. Sign in to continue.")
    except service.BusinessError as e:
        print_error(str(e))
    pause()


def run_users_menu(actor: AppUser) -> None:
    options = [
        ("1", "List users"),
        ("2", "Create user"),
        ("3", "Deactivate user"),
        ("4", "Activate user"),
        ("0", "Back"),
    ]
    while True:
        clear_screen()
        print_banner()
        print_header("Users")
        print_menu(options)
        option = prompt_option()

        try:
            if option == "1":
                print_section("App users")
                users = service.list_app_users(actor)
                if not users:
                    print_empty("(no users)")
                else:
                    for user in users:
                        print(f"    {service.format_app_user(user)}")
                pause()

            elif option == "2":
                username = prompt_text("Username")
                password = prompt_password("Password")
                print("  Role: 1=admin  2=trainer  3=member")
                role_choice = prompt_int("Role", min_value=1, max_value=3)
                role_map = {
                    1: UserRole.ADMIN,
                    2: UserRole.TRAINER,
                    3: UserRole.MEMBER,
                }
                role = role_map[role_choice]
                trainer_id = None
                member_id = None
                if role == UserRole.TRAINER:
                    trainer_id = prompt_trainer_id("Link to trainer profile")
                elif role == UserRole.MEMBER:
                    member_id = prompt_member_id("Link to member profile")
                user = service.create_app_user(
                    actor,
                    username,
                    password,
                    role,
                    trainer_id=trainer_id,
                    member_id=member_id,
                )
                print_success(f"User created: {service.format_app_user(user)}")
                pause()

            elif option == "3":
                user_id = prompt_int("User id to deactivate", min_value=1)
                user = service.deactivate_app_user(actor, user_id)
                print_success(f"Deactivated: {service.format_app_user(user)}")
                pause()

            elif option == "4":
                user_id = prompt_int("User id to activate", min_value=1)
                user = service.activate_app_user(actor, user_id)
                print_success(f"Activated: {service.format_app_user(user)}")
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


def run_trainer_portal(actor: AppUser) -> None:
    options = [
        ("1", "My classes"),
        ("2", "Members of class"),
        ("3", "Record attendance"),
        ("4", "Class attendance roster"),
        ("0", "Logout"),
    ]
    while True:
        clear_screen()
        print_banner()
        print_header(f"Trainer — {format_user_label(actor)}")
        print_menu(options)
        option = prompt_option()

        try:
            classes = service.list_classes_for_actor(actor)

            if option == "1":
                print_section("My classes")
                show_class_rows(
                    classes,
                    empty_message="(no classes assigned)",
                )
                pause()

            elif option == "2":
                class_id = prompt_class_id_from_list("Select a class", classes)
                if class_id is None:
                    pause()
                    continue
                gym_class = service.get_class_for_actor(actor, class_id)
                print_section(f"Members of [{gym_class.id}] {gym_class.name}")
                members = service.list_class_members(class_id)
                if not members:
                    print_empty("(no members enrolled in this class)")
                else:
                    show_member_rows(members)
                pause()

            elif option == "3":
                class_id = prompt_class_id_from_list("Class", classes)
                if class_id is None:
                    pause()
                    continue
                gym_class = service.get_class_for_actor(actor, class_id)
                schedule, session_date = prompt_class_session(gym_class)
                if schedule is None:
                    pause()
                    continue
                member_id = prompt_roster_member_id(
                    gym_class, class_id, session_date, schedule=schedule
                )
                if member_id is None:
                    pause()
                    continue
                service.mark_attendance(
                    class_id,
                    member_id,
                    schedule_id=schedule.id,
                    session_date=session_date,
                    actor=actor,
                )
                print_success("Attendance recorded")
                pause()

            elif option == "4":
                class_id = prompt_class_id_from_list("Select a class", classes)
                if class_id is None:
                    pause()
                    continue
                gym_class = service.get_class_for_actor(actor, class_id)
                schedule, session_date = prompt_class_session(gym_class)
                if schedule is None:
                    pause()
                    continue
                show_class_attendance_header(
                    gym_class, session_date, schedule=schedule
                )
                show_class_attendance_roster(
                    service.list_class_attendance_roster(class_id, session_date)
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


def run_member_portal(actor: AppUser) -> None:
    options = [
        ("1", "My classes"),
        ("2", "My attendance"),
        ("3", "Enroll in class"),
        ("4", "Unenroll from class"),
        ("0", "Logout"),
    ]
    while True:
        clear_screen()
        print_banner()
        print_header(f"Member — {format_user_label(actor)}")
        print_menu(options)
        option = prompt_option()

        try:
            member_id = actor.member_id
            if member_id is None:
                raise service.BusinessError("Cuenta de miembro sin perfil vinculado")

            if option == "1":
                print_section("My classes")
                show_class_rows(
                    service.list_member_classes(member_id),
                    empty_message="(not enrolled in any class)",
                )
                pause()

            elif option == "2":
                m = service.get_member(member_id)
                print_section(f"Attendance for [{m.id}] {m.name}")
                show_attendance_records(
                    service.list_attendance_by_member(member_id)
                )
                pause()

            elif option == "3":
                enrolled_ids = {
                    gym_class.id
                    for gym_class in service.list_member_classes(member_id)
                }
                available = [
                    gym_class
                    for gym_class in service.list_classes()
                    if gym_class.id not in enrolled_ids
                ]
                class_id = prompt_class_id_from_list(
                    "Class to enroll in", available
                )
                if class_id is None:
                    pause()
                    continue
                service.enroll_member(class_id, member_id, actor=actor)
                print_success("Enrolled successfully")
                pause()

            elif option == "4":
                my_classes = service.list_member_classes(member_id)
                class_id = prompt_class_id_from_list(
                    "Class to unenroll from", my_classes
                )
                if class_id is None:
                    pause()
                    continue
                service.unenroll_member(class_id, member_id, actor=actor)
                print_success("Unenrolled successfully")
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


def run_admin_main(actor: AppUser) -> None:
    main_options = [
        ("1", "Trainers"),
        ("2", "Members"),
        ("3", "Classes"),
        ("4", "Enrollment"),
        ("5", "Attendance"),
        ("6", "Users"),
        ("0", "Logout"),
    ]

    while True:
        clear_screen()
        print_banner()
        print_header(f"Admin — {format_user_label(actor)}")
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
        elif option == "6":
            run_users_menu(actor)
        elif option == "0":
            return
        else:
            print_error("Invalid option.")
            pause()


def run_trainer_menu() -> None:
    options = [
        ("1", "Add trainer"),
        ("2", "List trainers"),
        ("3", "View by id"),
        ("4", "Update"),
        ("5", "Delete"),
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
        ("6", "Classes of trainer"),
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


def run_enrollment_menu() -> None:
    options = [
        ("1", "Enroll member in class"),
        ("2", "List enrollments"),
        ("3", "Unenroll member"),
        ("4", "Members of class"),
        ("5", "Classes of member"),
        ("0", "Back"),
    ]
    while True:
        clear_screen()
        print_enrollment_banner()
        print_menu(options)
        option = prompt_option()

        try:
            if option == "1":
                class_id = prompt_class_id("Class for enrollment")
                member_id = prompt_available_member_id(
                    "Member to enroll", class_id
                )
                if member_id is None:
                    pause()
                    continue
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
                class_id = prompt_class_id("Class to unenroll from")
                member_id = prompt_enrolled_member_id(
                    "Member to unenroll", class_id
                )
                if member_id is None:
                    pause()
                    continue
                service.unenroll_member(class_id, member_id)
                print_success("Member unenrolled successfully")
                pause()

            elif option == "4":
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

            elif option == "5":
                member_id = prompt_member_with_classes_id("Select a member")
                if member_id is None:
                    pause()
                    continue
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


def show_class_attendance_header(gym_class, session_date, *, schedule=None) -> None:
    print_section(f"Attendance Roster — [{gym_class.id}] {gym_class.name}")
    print(f"  Class:   [{gym_class.id}] {gym_class.name}")
    if schedule is not None:
        time_label = service.format_schedule_slot(schedule)
    else:
        time_label = service.format_class_schedules(gym_class)
    print(f"  Time:    {time_label}")
    print(f"  Date:    {session_date.strftime('%Y-%m-%d')}")
    print()


def show_class_attendance_roster(rows) -> None:
    if not rows:
        print_empty("(no members enrolled in this class)")
        return
    print_table(
        ["ID", "Member", "Present", "Plan", "Email"],
        [
            [
                str(row.member_id),
                row.member_name,
                "✓" if row.attended_at else "—",
                row.membership_plan,
                row.email,
            ]
            for row in rows
        ],
    )


def prompt_roster_member_id(
    gym_class, class_id: int, session_date: date, *, schedule=None
) -> int | None:
    rows = service.list_class_attendance_roster(class_id, session_date)
    if not rows:
        print_empty("(no members enrolled in this class)")
        return None
    show_class_attendance_header(gym_class, session_date, schedule=schedule)
    show_class_attendance_roster(rows)
    member_ids = {row.member_id for row in rows}
    while True:
        member_id = prompt_int("Member id", min_value=1)
        if member_id in member_ids:
            return member_id
        print_error("Member is not enrolled in this class.")


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
        print_attendance_banner()
        print_menu(options)
        option = prompt_option()

        try:
            if option == "1":
                class_id = prompt_class_id("Class")
                gym_class = service.get_class(class_id)
                if gym_class is None:
                    print_error("Class not found")
                    pause()
                    continue
                schedule, session_date = prompt_class_session(gym_class)
                if schedule is None:
                    pause()
                    continue
                member_id = prompt_roster_member_id(
                    gym_class, class_id, session_date, schedule=schedule
                )
                if member_id is None:
                    pause()
                    continue
                service.mark_attendance(
                    class_id,
                    member_id,
                    schedule_id=schedule.id,
                    session_date=session_date,
                )
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
                    pause()
                    continue
                schedule, session_date = prompt_class_session(gym_class)
                if schedule is None:
                    pause()
                    continue
                show_class_attendance_header(
                    gym_class, session_date, schedule=schedule
                )
                show_class_attendance_roster(
                    service.list_class_attendance_roster(class_id, session_date)
                )
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

    while True:
        if service.count_app_users() == 0:
            run_bootstrap_admin()
            continue

        user = run_login()
        if user is None:
            print()
            print_success("Goodbye.")
            break

        if user.role == UserRole.ADMIN:
            run_admin_main(user)
        elif user.role == UserRole.TRAINER:
            run_trainer_portal(user)
        elif user.role == UserRole.MEMBER:
            run_member_portal(user)
        else:
            print_error("Unsupported role.")
            pause()


if __name__ == "__main__":
    main()
