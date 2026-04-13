Proceso GymMain
    Definir op Como Entero
    Definir name, msg Como Cadena
    Definir id, trainer, day, hh1, mm1, hh2, mm2, startM, endM, cap, classIdNew, classIn, memberIn Como Entero
    Definir ok Como Logico

    initRepo()

    Repetir
        Escribir "=== Gym Management (PSeInt) ==="
        Escribir "1) Create trainer"
        Escribir "2) Create member"
        Escribir "3) Create class"
        Escribir "4) Enroll member in class"
        Escribir "0) Exit"
        Leer op

        Segun op Hacer
            1:
                Escribir "Trainer name:"
                Leer name
                repoCreateTrainer(name, id)
                Escribir "Trainer created. ID=", id
            2:
                Escribir "Member name:"
                Leer name
                repoCreateMember(name, id)
                Escribir "Member created. ID=", id
            3:
                Escribir "Class name:"; Leer name
                Escribir "Trainer ID:"; Leer trainer
                Escribir "Day (0=Mon..6=Sun):"; Leer day
                Escribir "Start hh mm:"; Leer hh1, mm1
                Escribir "End hh mm:"; Leer hh2, mm2
                Escribir "Capacity:"; Leer cap

                hhmmToMinutes(hh1, mm1, startM)
                hhmmToMinutes(hh2, mm2, endM)

                serviceCreateClass(name, trainer, day, startM, endM, cap, ok, msg, classIdNew)
                Escribir msg
                Si ok Entonces
                    Escribir "Class ID=", classIdNew
                FinSi
            4:
                Escribir "Class ID:"; Leer classIn
                Escribir "Member ID:"; Leer memberIn
                serviceEnrollMember(classIn, memberIn, ok, msg)
                Escribir msg
            0:
                Escribir "Bye!"
            De Otro Modo:
                Escribir "Invalid option"
        FinSegun
    Hasta Que op = 0
FinProceso