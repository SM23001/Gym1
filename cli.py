from datetime import datetime

import psycopg2

from colors import c, BOLD, CYAN, GREEN, RED, YELLOW
from db import init_schema
import service


def parse_time(hhmm: str):
    return datetime.strptime(hhmm, "%H:%M").time()


def main():
    init_schema()

    while True:
        print()
        print(c("=== Gestión de Gimnasio ===", BOLD + CYAN))
        print(c("1.", YELLOW), "Alta entrenador")
        print(c("2.", YELLOW), "Alta miembro")
        print(c("3.", YELLOW), "Alta clase")
        print(c("4.", YELLOW), "Inscribir miembro en clase")
        print(c("5.", YELLOW), "Registrar asistencia")
        print(c("6.", YELLOW), "Listar clases")
        print(c("7.", YELLOW), "Listar entrenadores")
        print(c("8.", YELLOW), "Listar miembros")
        print(c("0.", YELLOW), "Salir")

        option = input(c("Opción: ", CYAN)).strip()

        try:
            if option == "1":
                name = input("Nombre del entrenador: ")
                t = service.create_trainer(name)
                print(c(f"Entrenador creado con id {t.id}", GREEN))

            elif option == "2":
                name = input("Nombre del miembro: ")
                m = service.create_member(name)
                print(c(f"Miembro creado con id {m.id}", GREEN))

            elif option == "3":
                name = input("Nombre de la clase: ")
                trainer_id = int(input("Id entrenador: "))
                day = int(input("Día de la semana (0=lunes ... 6=domingo): "))
                start = parse_time(input("Hora inicio (HH:MM): "))
                end = parse_time(input("Hora fin (HH:MM): "))
                capacity = int(input("Cupo máximo: "))

                c_obj = service.create_class(name, trainer_id, day, start, end, capacity)
                print(c(f"Clase creada con id {c_obj.id}", GREEN))

            elif option == "4":
                class_id = int(input("Id de la clase: "))
                member_id = int(input("Id del miembro: "))
                service.enroll_member(class_id, member_id)
                print(c("Miembro inscrito correctamente", GREEN))

            elif option == "5":
                class_id = int(input("Id de la clase: "))
                member_id = int(input("Id del miembro: "))
                service.mark_attendance(class_id, member_id)
                print(c("Asistencia registrada", GREEN))

            elif option == "6":
                print()
                print(c("Clases:", YELLOW))
                for c_obj in service.list_classes():
                    print(
                        f"  [{c_obj.id}] {c_obj.name} - Entrenador {c_obj.trainer_id} - "
                        f"Día: {c_obj.day_of_week} {c_obj.start_time}-{c_obj.end_time} "
                        f"Cupo: {c_obj.capacity}"
                    )

            elif option == "7":
                print()
                print(c("Entrenadores:", YELLOW))
                for t in service.list_trainers():
                    print(f"  [{t.id}] {t.name}")

            elif option == "8":
                print()
                print(c("Miembros:", YELLOW))
                for m in service.list_members():
                    print(f"  [{m.id}] {m.name}")

            elif option == "0":
                print(c("Hasta luego.", GREEN))
                break

            else:
                print(c("Opción no válida.", RED))

        except service.BusinessError as e:
            print(c(f"Error de negocio: {e}", RED))
        except ValueError as e:
            print(c(f"Error de entrada: {e}", RED))
        except psycopg2.Error as e:
            print(c(f"Error de base de datos: {e}", RED))


if __name__ == "__main__":
    main()

