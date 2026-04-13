Proceso GymMain
    Definir op Como Entero
    Definir name, msg, hIni, hFin Como Cadena
    Definir id, trainer, day, hh1, mm1, hh2, mm2, startM, endM, cap, classIdNew, classIn, memberIn Como Entero
    Definir ok Como Logico

    // Extra variables (strict mode friendly)
    Definir i, j, count, idxClass, otherClass, dayC, startC, endC Como Entero
    Definir trainerExists, classExists, memberExists, alreadyEnrolled, isOverlap, enrolled Como Logico

    // ----- Global data arrays -----
    Dimension trainerId[100], trainerName[100]
    Dimension memberId[200], memberName[200]

    Dimension classId[300], className[300], classTrainerId[300]
    Dimension classDay[300], classStart[300], classEnd[300], classCapacity[300]

    Dimension enrollClassId[1000], enrollMemberId[1000]
    Dimension attClassId[2000], attMemberId[2000]

    nTrainers <- 0
    nMembers <- 0
    nClasses <- 0
    nEnroll <- 0
    nAtt <- 0

    nextTrainerId <- 1
    nextMemberId <- 1
    nextClassId <- 1

    Repetir
        Escribir ""
        Escribir "=== Gym Management (PSeInt) ==="
        Escribir "1) Create trainer"
        Escribir "2) Create member"
        Escribir "3) Create class"
        Escribir "4) Enroll member in class"
        Escribir "5) Mark attendance"
        Escribir "6) List classes"
        Escribir "0) Exit"
        Leer op

        Segun op Hacer
            1:
                Escribir "Trainer name:"
                Leer name

                nTrainers <- nTrainers + 1
                trainerId[nTrainers] <- nextTrainerId
                trainerName[nTrainers] <- name

                id <- nextTrainerId
                nextTrainerId <- nextTrainerId + 1

                Escribir "Trainer created. ID=", id

            2:
                Escribir "Member name:"
                Leer name

                nMembers <- nMembers + 1
                memberId[nMembers] <- nextMemberId
                memberName[nMembers] <- name

                id <- nextMemberId
                nextMemberId <- nextMemberId + 1

                Escribir "Member created. ID=", id

            3:
                Escribir "Class name:"
                Leer name

                Escribir "Trainer ID:"
                Leer trainer

                Escribir "Day (0=Mon..6=Sun):"
                Leer day

                Escribir "Start hour (0..23):"
                Leer hh1
                Escribir "Start minute (0..59):"
                Leer mm1

                Escribir "End hour (0..23):"
                Leer hh2
                Escribir "End minute (0..59):"
                Leer mm2

                Escribir "Capacity:"
                Leer cap

                // Validation
                ok <- Verdadero
                msg <- "Class created"

                trainerExists <- Falso
                Si nTrainers > 0 Entonces
                    Para i <- 1 Hasta nTrainers Hacer
                        Si trainerId[i] = trainer Entonces
                            trainerExists <- Verdadero
                        FinSi
                    FinPara
                FinSi

                Si NO trainerExists Entonces
                    ok <- Falso
                    msg <- "Trainer does not exist"
                FinSi

                Si day < 0 O day > 6 Entonces
                    ok <- Falso
                    msg <- "Invalid day (use 0..6)"
                FinSi

                Si hh1 < 0 O hh1 > 23 O mm1 < 0 O mm1 > 59 O hh2 < 0 O hh2 > 23 O mm2 < 0 O mm2 > 59 Entonces
                    ok <- Falso
                    msg <- "Invalid hour/minute"
                FinSi

                startM <- hh1 * 60 + mm1
                endM <- hh2 * 60 + mm2

                Si endM <= startM Entonces
                    ok <- Falso
                    msg <- "End time must be greater than start time"
                FinSi

                Si cap <= 0 Entonces
                    ok <- Falso
                    msg <- "Capacity must be > 0"
                FinSi

                Si ok Entonces
                    nClasses <- nClasses + 1
                    classId[nClasses] <- nextClassId
                    className[nClasses] <- name
                    classTrainerId[nClasses] <- trainer
                    classDay[nClasses] <- day
                    classStart[nClasses] <- startM
                    classEnd[nClasses] <- endM
                    classCapacity[nClasses] <- cap

                    classIdNew <- nextClassId
                    nextClassId <- nextClassId + 1

                    Escribir msg
                    Escribir "Class ID=", classIdNew
                SiNo
                    Escribir msg
                FinSi

            4:
                Escribir "Class ID:"
                Leer classIn
                Escribir "Member ID:"
                Leer memberIn

                ok <- Verdadero
                msg <- "Enrolled successfully"

                classExists <- Falso
                idxClass <- -1
                Si nClasses > 0 Entonces
                    Para i <- 1 Hasta nClasses Hacer
                        Si classId[i] = classIn Entonces
                            classExists <- Verdadero
                            idxClass <- i
                        FinSi
                    FinPara
                FinSi

                memberExists <- Falso
                Si nMembers > 0 Entonces
                    Para i <- 1 Hasta nMembers Hacer
                        Si memberId[i] = memberIn Entonces
                            memberExists <- Verdadero
                        FinSi
                    FinPara
                FinSi

                Si NO classExists Entonces
                    ok <- Falso
                    msg <- "Class does not exist"
                FinSi

                Si ok Y NO memberExists Entonces
                    ok <- Falso
                    msg <- "Member does not exist"
                FinSi

                // duplicate enrollment
                Si ok Entonces
                    alreadyEnrolled <- Falso
                    Si nEnroll > 0 Entonces
                        Para i <- 1 Hasta nEnroll Hacer
                            Si enrollClassId[i] = classIn Y enrollMemberId[i] = memberIn Entonces
                                alreadyEnrolled <- Verdadero
                            FinSi
                        FinPara
                    FinSi

                    Si alreadyEnrolled Entonces
                        ok <- Falso
                        msg <- "Member already enrolled"
                    FinSi
                FinSi

                // capacity
                Si ok Entonces
                    count <- 0
                    Si nEnroll > 0 Entonces
                        Para i <- 1 Hasta nEnroll Hacer
                            Si enrollClassId[i] = classIn Entonces
                                count <- count + 1
                            FinSi
                        FinPara
                    FinSi

                    Si count >= classCapacity[idxClass] Entonces
                        ok <- Falso
                        msg <- "Class full"
                    FinSi
                FinSi

                // schedule overlap
                Si ok Entonces
                    dayC <- classDay[idxClass]
                    startC <- classStart[idxClass]
                    endC <- classEnd[idxClass]

                    Si nEnroll > 0 Y nClasses > 0 Entonces
                        Para i <- 1 Hasta nEnroll Hacer
                            Si enrollMemberId[i] = memberIn Entonces
                                otherClass <- enrollClassId[i]

                                Para j <- 1 Hasta nClasses Hacer
                                    Si classId[j] = otherClass Entonces
                                        isOverlap <- Falso
                                        Si dayC = classDay[j] Entonces
                                            Si NO (endC <= classStart[j] O classEnd[j] <= startC) Entonces
                                                isOverlap <- Verdadero
                                            FinSi
                                        FinSi

                                        Si isOverlap Entonces
                                            ok <- Falso
                                            msg <- "Schedule conflict"
                                        FinSi
                                    FinSi
                                FinPara
                            FinSi
                        FinPara
                    FinSi
                FinSi

                Si ok Entonces
                    nEnroll <- nEnroll + 1
                    enrollClassId[nEnroll] <- classIn
                    enrollMemberId[nEnroll] <- memberIn
                FinSi

                Escribir msg

            5:
                Escribir "Class ID:"
                Leer classIn
                Escribir "Member ID:"
                Leer memberIn

                enrolled <- Falso
                Si nEnroll > 0 Entonces
                    Para i <- 1 Hasta nEnroll Hacer
                        Si enrollClassId[i] = classIn Y enrollMemberId[i] = memberIn Entonces
                            enrolled <- Verdadero
                        FinSi
                    FinPara
                FinSi

                Si NO enrolled Entonces
                    Escribir "Member is not enrolled in that class"
                SiNo
                    nAtt <- nAtt + 1
                    attClassId[nAtt] <- classIn
                    attMemberId[nAtt] <- memberIn
                    Escribir "Attendance registered"
                FinSi

            6:
                Escribir "---- Classes ----"
                Si nClasses = 0 Entonces
                    Escribir "No classes registered"
                SiNo
                    Para i <- 1 Hasta nClasses Hacer
                        minutesToHHMM(classStart[i], hIni)
                        minutesToHHMM(classEnd[i], hFin)

                        Escribir "[", classId[i], "] ", className[i], " | Trainer:", classTrainerId[i], " | Day:", classDay[i], " | ", hIni, "-", hFin, " | Cap:", classCapacity[i]
                    FinPara
                FinSi

            0:
                Escribir "Bye!"

            De Otro Modo:
                Escribir "Invalid option"
        FinSegun
    Hasta Que op = 0
FinProceso

SubProceso minutesToHHMM(totalMin, txtHora Por Referencia)
    Definir hh, mm Como Entero
    Definir sh, sm Como Cadena

    hh <- trunc(totalMin / 60)
    mm <- totalMin MOD 60

    Si hh < 10 Entonces
        sh <- "0" + ConvertirATexto(hh)
    SiNo
        sh <- ConvertirATexto(hh)
    FinSi

    Si mm < 10 Entonces
        sm <- "0" + ConvertirATexto(mm)
    SiNo
        sm <- ConvertirATexto(mm)
    FinSi

    txtHora <- sh + ":" + sm
FinSubProceso