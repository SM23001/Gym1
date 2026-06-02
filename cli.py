from datetime import datetime

import psycopg2

from colors import c, BOLD, CYAN, GREEN, RED, YELLOW
from db import init_schema
import service


def parse_time(hhmm: str):
    return datetime.strptime(hhmm, "%H:%M").time()


def prompt_class_fields():
    name = input("Nombre de la clase: ")
    trainer_id = int(input("Id entrenador: "))
    day = int(input("Día de la semana (0=lunes ... 6=domingo): "))
    start = parse_time(input("Hora inicio (HH:MM): "))
    end = parse_time(input("Hora fin (HH:MM): "))
    capacity = int(input("Cupo máximo: "))
    return name, trainer_id, day, start, end, capacity


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
        print(c("8.", YELLOW), "Ver entrenador por id")
        print(c("9.", YELLOW), "Modificar entrenador")
        print(c("10.", YELLOW), "Eliminar entrenador")
        print(c("11.", YELLOW), "Listar miembros")
        print(c("12.", YELLOW), "Ver miembro por id")
        print(c("13.", YELLOW), "Modificar miembro")
        print(c("14.", YELLOW), "Eliminar miembro")
        print(c("15.", YELLOW), "Ver clase por id")
        print(c("16.", YELLOW), "Modificar clase")
        print(c("17.", YELLOW), "Eliminar clase")
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
                fields = prompt_class_fields()
                c_obj = service.create_class(*fields)
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
                    print(f"  {service.format_class(c_obj)}")

            elif option == "7":
                print()
                print(c("Entrenadores:", YELLOW))
                for t in service.list_trainers():
                    print(f"  [{t.id}] {t.name}")

            elif option == "8":
                trainer_id = int(input("Id del entrenador: "))
                t = service.get_trainer(trainer_id)
                if t is None:
                    print(c("Entrenador no encontrado", RED))
                else:
                    print(c(f"  [{t.id}] {t.name}", GREEN))

            elif option == "9":
                trainer_id = int(input("Id del entrenador: "))
                name = input("Nuevo nombre: ")
                t = service.update_trainer(trainer_id, name)
                print(c(f"Entrenador actualizado: [{t.id}] {t.name}", GREEN))

            elif option == "10":
                trainer_id = int(input("Id del entrenador: "))
                service.delete_trainer(trainer_id)
                print(c("Entrenador eliminado", GREEN))

            elif option == "11":
                print()
                print(c("Miembros:", YELLOW))
                for m in service.list_members():
                    print(f"  [{m.id}] {m.name}")

            elif option == "12":
                member_id = int(input("Id del miembro: "))
                m = service.get_member(member_id)
                if m is None:
                    print(c("Miembro no encontrado", RED))
                else:
                    print(c(f"  [{m.id}] {m.name}", GREEN))

            elif option == "13":
                member_id = int(input("Id del miembro: "))
                name = input("Nuevo nombre: ")
                m = service.update_member(member_id, name)
                print(c(f"Miembro actualizado: [{m.id}] {m.name}", GREEN))

            elif option == "14":
                member_id = int(input("Id del miembro: "))
                service.delete_member(member_id)
                print(c("Miembro eliminado", GREEN))

            elif option == "15":
                class_id = int(input("Id de la clase: "))
                c_obj = service.get_class(class_id)
                if c_obj is None:
                    print(c("Clase no encontrada", RED))
                else:
                    print(c(f"  {service.format_class(c_obj)}", GREEN))

            elif option == "16":
                class_id = int(input("Id de la clase: "))
                fields = prompt_class_fields()
                c_obj = service.update_class(class_id, *fields)
                print(c(f"Clase actualizada: {service.format_class(c_obj)}", GREEN))

            elif option == "17":
                class_id = int(input("Id de la clase: "))
                service.delete_class(class_id)
                print(c("Clase eliminada", GREEN))

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

