SubProceso initRepo()
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
FinSubProceso

SubProceso repoCreateTrainer(name, outId Por Referencia)
    nTrainers <- nTrainers + 1
    trainerId[nTrainers] <- nextTrainerId
    trainerName[nTrainers] <- name
    outId <- nextTrainerId
    nextTrainerId <- nextTrainerId + 1
FinSubProceso

SubProceso repoCreateMember(name, outId Por Referencia)
    nMembers <- nMembers + 1
    memberId[nMembers] <- nextMemberId
    memberName[nMembers] <- name
    outId <- nextMemberId
    nextMemberId <- nextMemberId + 1
FinSubProceso

SubProceso repoFindTrainer(id, exists Por Referencia)
    exists <- Falso
    Para i <- 1 Hasta nTrainers Hacer
        Si trainerId[i] = id Entonces
            exists <- Verdadero
        FinSi
    FinPara
FinSubProceso

SubProceso repoFindMember(id, exists Por Referencia)
    exists <- Falso
    Para i <- 1 Hasta nMembers Hacer
        Si memberId[i] = id Entonces
            exists <- Verdadero
        FinSi
    FinPara
FinSubProceso

SubProceso repoCreateClass(name, trainerIdIn, day, startMin, endMin, capacity, outId Por Referencia)
    nClasses <- nClasses + 1
    classId[nClasses] <- nextClassId
    className[nClasses] <- name
    classTrainerId[nClasses] <- trainerIdIn
    classDay[nClasses] <- day
    classStart[nClasses] <- startMin
    classEnd[nClasses] <- endMin
    classCapacity[nClasses] <- capacity
    outId <- nextClassId
    nextClassId <- nextClassId + 1
FinSubProceso