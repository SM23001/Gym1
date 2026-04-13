SubProceso serviceCreateClass(name, trainerIdIn, day, startMin, endMin, capacity, ok Por Referencia, msg Por Referencia, classNewId Por Referencia)
    Definir trainerExists Como Logico
    repoFindTrainer(trainerIdIn, trainerExists)

    Si NO trainerExists Entonces
        ok <- Falso
        msg <- "Trainer does not exist"
        classNewId <- -1
        Salir
    FinSi

    Si endMin <= startMin Entonces
        ok <- Falso
        msg <- "End time must be greater than start time"
        classNewId <- -1
        Salir
    FinSi

    repoCreateClass(name, trainerIdIn, day, startMin, endMin, capacity, classNewId)
    ok <- Verdadero
    msg <- "Class created"
FinSubProceso

SubProceso serviceEnrollMember(classIn, memberIn, ok Por Referencia, msg Por Referencia)
    Definir classExists, memberExists Como Logico
    classExists <- Falso
    memberExists <- Falso

    Para i <- 1 Hasta nClasses Hacer
        Si classId[i] = classIn Entonces
            classExists <- Verdadero
        FinSi
    FinPara

    repoFindMember(memberIn, memberExists)

    Si NO classExists Entonces
        ok <- Falso
        msg <- "Class does not exist"
        Salir
    FinSi

    Si NO memberExists Entonces
        ok <- Falso
        msg <- "Member does not exist"
        Salir
    FinSi

    // duplicate enrollment
    Para i <- 1 Hasta nEnroll Hacer
        Si enrollClassId[i] = classIn Y enrollMemberId[i] = memberIn Entonces
            ok <- Falso
            msg <- "Member already enrolled"
            Salir
        FinSi
    FinPara

    // capacity
    count <- 0
    cap <- 0
    dayC <- 0
    startC <- 0
    endC <- 0

    Para i <- 1 Hasta nClasses Hacer
        Si classId[i] = classIn Entonces
            cap <- classCapacity[i]
            dayC <- classDay[i]
            startC <- classStart[i]
            endC <- classEnd[i]
        FinSi
    FinPara

    Para i <- 1 Hasta nEnroll Hacer
        Si enrollClassId[i] = classIn Entonces
            count <- count + 1
        FinSi
    FinPara

    Si count >= cap Entonces
        ok <- Falso
        msg <- "Class full"
        Salir
    FinSi

    // schedule overlap with other member classes
    Para i <- 1 Hasta nEnroll Hacer
        Si enrollMemberId[i] = memberIn Entonces
            otherClass <- enrollClassId[i]

            Para j <- 1 Hasta nClasses Hacer
                Si classId[j] = otherClass Entonces
                    Definir isOverlap Como Logico
                    overlaps(dayC, startC, endC, classDay[j], classStart[j], classEnd[j], isOverlap)
                    Si isOverlap Entonces
                        ok <- Falso
                        msg <- "Schedule conflict"
                        Salir
                    FinSi
                FinSi
            FinPara
        FinSi
    FinPara

    nEnroll <- nEnroll + 1
    enrollClassId[nEnroll] <- classIn
    enrollMemberId[nEnroll] <- memberIn
    ok <- Verdadero
    msg <- "Enrolled successfully"
FinSubProceso