from datetime import datetime, time

import psycopg2

from colors import (
    BOLD,
    BRIGHT_CYAN,
    CYAN,
    GREEN,
    RED,
    YELLOW,
    c,
)
from db import init_schema
import service

DAY_NAMES = (
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo",
)


def parse_time(hhmm: str) -> time:
    return datetime.strptime(hhmm.strip(), "%H:%M").time()


def print_header(title: str) -> None:
    width = max(len(title) + 4, 40)
    line = "─" * width
    print()
    print(c(line, CYAN))
    print(c(f"  {title}", BOLD + BRIGHT_CYAN))
    print(c(line, CYAN))


def print_menu(options: list[tuple[str, str]]) -> None:
    for key, label in options:
        print(c(f"  {key}.", YELLOW), label)


def pause() -> None:
    input(c("\n  Pulsa Enter para continuar… ", CYAN))


def print_success(message: str) -> None:
    print(c(f"  ✓ {message}", GREEN))


def print_error(message: str) -> None:
    print(c(f"  ✗ {message}", RED))


def prompt_text(label: str, *, required: bool = True) -> str:
    while True:
        value = input(c(f"  {label}: ", CYAN)).strip()
        if value or not required:
            return value
        print_error("Este campo es obligatorio.")


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
            print_error("Introduce un número entero válido.")
            continue
        if min_value is not None and value < min_value:
            print_error(f"El valor mínimo es {min_value}.")
            continue
        if max_value is not None and value > max_value:
            print_error(f"El valor máximo es {max_value}.")
            continue
        return value


def prompt_time(label: str) -> time:
    while True:
        raw = input(c(f"  {label} (HH:MM): ", CYAN)).strip()
        try:
            return parse_time(raw)
        except ValueError:
            print_error("Formato inválido. Usa HH:MM, por ejemplo 09:30.")


def prompt_optional_text(label: str, current: str) -> str:
    hint = c(f" [Enter = «{current}»]", CYAN)
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
        raise ValueError(f"{label}: se esperaba un número entero")
    min_value = kwargs.get("min_value")
    max_value = kwargs.get("max_value")
    if min_value is not None and value < min_value:
        raise ValueError(f"{label}: el valor mínimo es {min_value}")
    if max_value is not None and value > max_value:
        raise ValueError(f"{label}: el valor máximo es {max_value}")
    return value


def prompt_optional_time(label: str, current: time) -> time:
    hint = c(f" [Enter = {current.strftime('%H:%M')}]", CYAN)
    raw = input(c(f"  {label}{hint}: ", CYAN)).strip()
    if not raw:
        return current
    return parse_time(raw)


def show_trainers() -> None:
    trainers = service.list_trainers()
    if not trainers:
        print(c("  (sin entrenadores registrados)", CYAN))
        return
    for t in trainers:
        print(f"    [{t.id}] {t.name}")


def show_members() -> None:
    members = service.list_members()
    if not members:
        print(c("  (sin miembros registrados)", CYAN))
        return
    for m in members:
        print(f"    [{m.id}] {m.name}")


def show_classes() -> None:
    classes = service.list_classes()
    if not classes:
        print(c("  (sin clases registradas)", CYAN))
        return
    for gym_class in classes:
        print(f"    {service.format_class(gym_class)}")


def prompt_class_fields(*, existing=None):
    if existing is None:
        name = prompt_text("Nombre de la clase")
        print(c("  Entrenadores disponibles:", YELLOW))
        show_trainers()
        trainer_id = prompt_int("Id entrenador", min_value=1)
        print(c("  Días: 0=lunes … 6=domingo", CYAN))
        for i, day_name in enumerate(DAY_NAMES):
            print(f"    {i} = {day_name}")
        day = prompt_int("Día de la semana", min_value=0, max_value=6)
        start = prompt_time("Hora inicio")
        end = prompt_time("Hora fin")
        capacity = prompt_int("Cupo máximo", min_value=1)
        return name, trainer_id, day, start, end, capacity

    name = prompt_optional_text("Nombre de la clase", existing.name)
    print(c("  Entrenadores disponibles:", YELLOW))
    show_trainers()
    trainer_id = prompt_optional_int(
        "Id entrenador", existing.trainer_id, min_value=1
    )
    print(c("  Días: 0=lunes … 6=domingo", CYAN))
    for i, day_name in enumerate(DAY_NAMES):
        print(f"    {i} = {day_name}")
    day = prompt_optional_int(
        "Día de la semana", existing.day_of_week, min_value=0, max_value=6
    )
    start = prompt_optional_time("Hora inicio", existing.start_time)
    end = prompt_optional_time("Hora fin", existing.end_time)
    capacity = prompt_optional_int("Cupo máximo", existing.capacity, min_value=1)
    return name, trainer_id, day, start, end, capacity


def prompt_trainer_id(action: str) -> int:
    print(c(f"  {action}", YELLOW))
    show_trainers()
    return prompt_int("Id del entrenador", min_value=1)


def prompt_member_id(action: str) -> int:
    print(c(f"  {action}", YELLOW))
    show_members()
    return prompt_int("Id del miembro", min_value=1)


def prompt_class_id(action: str) -> int:
    print(c(f"  {action}", YELLOW))
    show_classes()
    return prompt_int("Id de la clase", min_value=1)


def run_trainer_menu() -> None:
    options = [
        ("1", "Alta entrenador"),
        ("2", "Listar entrenadores"),
        ("3", "Ver por id"),
        ("4", "Modificar"),
        ("5", "Eliminar"),
        ("0", "Volver"),
    ]
    while True:
        print_header("Entrenadores")
        print_menu(options)
        option = input(c("\n  Opción: ", CYAN)).strip()

        try:
            if option == "1":
                name = prompt_text("Nombre del entrenador")
                t = service.create_trainer(name)
                print_success(f"Entrenador creado con id {t.id}")
                pause()

            elif option == "2":
                print()
                print(c("  Entrenadores:", YELLOW))
                show_trainers()
                pause()

            elif option == "3":
                trainer_id = prompt_trainer_id("Selecciona un entrenador")
                t = service.get_trainer(trainer_id)
                if t is None:
                    print_error("Entrenador no encontrado")
                else:
                    print_success(f"[{t.id}] {t.name}")
                pause()

            elif option == "4":
                trainer_id = prompt_trainer_id("Entrenador a modificar")
                name = prompt_text("Nuevo nombre")
                t = service.update_trainer(trainer_id, name)
                print_success(f"Entrenador actualizado: [{t.id}] {t.name}")
                pause()

            elif option == "5":
                trainer_id = prompt_trainer_id("Entrenador a eliminar")
                service.delete_trainer(trainer_id)
                print_success("Entrenador eliminado")
                pause()

            elif option == "0":
                return

            else:
                print_error("Opción no válida.")

        except service.BusinessError as e:
            print_error(str(e))
            pause()
        except ValueError as e:
            print_error(str(e))
            pause()
        except psycopg2.Error as e:
            print_error(f"Base de datos: {e}")
            pause()


def run_member_menu() -> None:
    options = [
        ("1", "Alta miembro"),
        ("2", "Listar miembros"),
        ("3", "Ver por id"),
        ("4", "Modificar"),
        ("5", "Eliminar"),
        ("0", "Volver"),
    ]
    while True:
        print_header("Miembros")
        print_menu(options)
        option = input(c("\n  Opción: ", CYAN)).strip()

        try:
            if option == "1":
                name = prompt_text("Nombre del miembro")
                m = service.create_member(name)
                print_success(f"Miembro creado con id {m.id}")
                pause()

            elif option == "2":
                print()
                print(c("  Miembros:", YELLOW))
                show_members()
                pause()

            elif option == "3":
                member_id = prompt_member_id("Selecciona un miembro")
                m = service.get_member(member_id)
                if m is None:
                    print_error("Miembro no encontrado")
                else:
                    print_success(f"[{m.id}] {m.name}")
                pause()

            elif option == "4":
                member_id = prompt_member_id("Miembro a modificar")
                name = prompt_text("Nuevo nombre")
                m = service.update_member(member_id, name)
                print_success(f"Miembro actualizado: [{m.id}] {m.name}")
                pause()

            elif option == "5":
                member_id = prompt_member_id("Miembro a eliminar")
                service.delete_member(member_id)
                print_success("Miembro eliminado")
                pause()

            elif option == "0":
                return

            else:
                print_error("Opción no válida.")

        except service.BusinessError as e:
            print_error(str(e))
            pause()
        except ValueError as e:
            print_error(str(e))
            pause()
        except psycopg2.Error as e:
            print_error(f"Base de datos: {e}")
            pause()


def run_class_menu() -> None:
    options = [
        ("1", "Alta clase"),
        ("2", "Listar clases"),
        ("3", "Ver por id"),
        ("4", "Modificar"),
        ("5", "Eliminar"),
        ("0", "Volver"),
    ]
    while True:
        print_header("Clases")
        print_menu(options)
        option = input(c("\n  Opción: ", CYAN)).strip()

        try:
            if option == "1":
                fields = prompt_class_fields()
                gym_class = service.create_class(*fields)
                print_success(f"Clase creada con id {gym_class.id}")
                pause()

            elif option == "2":
                print()
                print(c("  Clases:", YELLOW))
                show_classes()
                pause()

            elif option == "3":
                class_id = prompt_class_id("Selecciona una clase")
                gym_class = service.get_class(class_id)
                if gym_class is None:
                    print_error("Clase no encontrada")
                else:
                    print_success(service.format_class(gym_class))
                pause()

            elif option == "4":
                class_id = prompt_class_id("Clase a modificar")
                existing = service.get_class(class_id)
                if existing is None:
                    print_error("Clase no encontrada")
                    pause()
                    continue
                fields = prompt_class_fields(existing=existing)
                gym_class = service.update_class(class_id, *fields)
                print_success(f"Clase actualizada: {service.format_class(gym_class)}")
                pause()

            elif option == "5":
                class_id = prompt_class_id("Clase a eliminar")
                service.delete_class(class_id)
                print_success("Clase eliminada")
                pause()

            elif option == "0":
                return

            else:
                print_error("Opción no válida.")

        except service.BusinessError as e:
            print_error(str(e))
            pause()
        except ValueError as e:
            print_error(str(e))
            pause()
        except psycopg2.Error as e:
            print_error(f"Base de datos: {e}")
            pause()


def run_operations_menu() -> None:
    options = [
        ("1", "Inscribir miembro en clase"),
        ("2", "Registrar asistencia"),
        ("0", "Volver"),
    ]
    while True:
        print_header("Inscripciones y asistencia")
        print_menu(options)
        option = input(c("\n  Opción: ", CYAN)).strip()

        try:
            if option == "1":
                class_id = prompt_class_id("Clase para inscripción")
                member_id = prompt_member_id("Miembro a inscribir")
                service.enroll_member(class_id, member_id)
                print_success("Miembro inscrito correctamente")
                pause()

            elif option == "2":
                class_id = prompt_class_id("Clase")
                member_id = prompt_member_id("Miembro")
                service.mark_attendance(class_id, member_id)
                print_success("Asistencia registrada")
                pause()

            elif option == "0":
                return

            else:
                print_error("Opción no válida.")

        except service.BusinessError as e:
            print_error(str(e))
            pause()
        except ValueError as e:
            print_error(str(e))
            pause()
        except psycopg2.Error as e:
            print_error(f"Base de datos: {e}")
            pause()


def main() -> None:
    init_schema()

    main_options = [
        ("1", "Entrenadores"),
        ("2", "Miembros"),
        ("3", "Clases"),
        ("4", "Inscripciones y asistencia"),
        ("0", "Salir"),
    ]

    while True:
        print_header("Gestión de Gimnasio")
        print_menu(main_options)
        option = input(c("\n  Opción: ", CYAN)).strip()

        if option == "1":
            run_trainer_menu()
        elif option == "2":
            run_member_menu()
        elif option == "3":
            run_class_menu()
        elif option == "4":
            run_operations_menu()
        elif option == "0":
            print()
            print_success("Hasta luego.")
            break
        else:
            print_error("Opción no válida.")
            pause()


if __name__ == "__main__":
    main()
