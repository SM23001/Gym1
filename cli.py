from datetime import datetime

from db import init_schema
import service


def parse_time(hhmm: str):
    return datetime.strptime(hhmm, "%H:%M").time()


def main():
    init_schema()

    while True:
        print("\n=== Gestión de Gimnasio ===")
        print("1. Alta entrenador")
        print("2. Alta miembro")
        print("3. Alta clase")
        print("4. Inscribir miembro en clase")
        print("5. Registrar asistencia")
        print("6. Listar clases")
        print("0. Salir")

        option = input("Opción: ").strip()

        try:
            if option == "1":
                name = input("Nombre del entrenador: ")
                t = service.create_trainer(name)
                print(f"Entrenador creado con id {t.id}")

            elif option == "2":
                name = input("Nombre del miembro: ")
                m = service.create_member(name)
                print(f"Miembro creado con id {m.id}")

            elif option == "3":
                name = input("Nombre de la clase: ")
                trainer_id = int(input("Id entrenador: "))
                day = int(input("Día de la semana (0=lunes ... 6=domingo): "))
                start = parse_time(input("Hora inicio (HH:MM): "))
                end = parse_time(input("Hora fin (HH:MM): "))
                capacity = int(input("Cupo máximo: "))

                c = service.create_class(name, trainer_id, day, start, end, capacity)
                print(f"Clase creada con id {c.id}")

            elif option == "4":
                class_id = int(input("Id de la clase: "))
                member_id = int(input("Id del miembro: "))
                service.enroll_member(class_id, member_id)
                print("Miembro inscrito correctamente")

            elif option == "5":
                class_id = int(input("Id de la clase: "))
                member_id = int(input("Id del miembro: "))
                service.mark_attendance(class_id, member_id)
                print("Asistencia registrada")

            elif option == "6":
                print("\nClases:")
                for c in service.list_classes():
                    print(
                        f"[{c.id}] {c.name} - Entrenador {c.trainer_id} - "
                        f"Día: {c.day_of_week} {c.start_time}-{c.end_time} "
                        f"Cupo: {c.capacity}"
                    )

            elif option == "0":
                print("Hasta luego.")
                break

            else:
                print("Opción no válida.")

        except service.BusinessError as e:
            print(f"Error de negocio: {e}")
        except ValueError as e:
            print(f"Error de entrada: {e}")


if __name__ == "__main__":
    main()

