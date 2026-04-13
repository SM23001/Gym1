SubProceso hhmmToMinutes(hh, mm, totalMin Por Referencia)
    totalMin <- hh * 60 + mm
FinSubProceso

SubProceso isValidDay(day, ok Por Referencia)
    ok <- day >= 0 Y day <= 6
FinSubProceso

SubProceso isValidHourMinute(hh, mm, ok Por Referencia)
    ok <- (hh >= 0 Y hh <= 23) Y (mm >= 0 Y mm <= 59)
FinSubProceso

SubProceso overlaps(day1, start1, end1, day2, start2, end2, outOverlap Por Referencia)
    Si day1 <> day2 Entonces
        outOverlap <- Falso
    SiNo
        Si end1 <= start2 O end2 <= start1 Entonces
            outOverlap <- Falso
        SiNo
            outOverlap <- Verdadero
        FinSi
    FinSi
FinSubProceso