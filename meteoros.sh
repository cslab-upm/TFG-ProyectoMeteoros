#!/bin/bash

finError() {
	echo "LOG: Hora de finalizacion: $HoraFinal" >> $flogs
	echo "LOG: Duracion: $HORA horas, $MINS minutos y $SEGS segundos" >> $flogs
	echo "LOG: El script ha terminado con ERROR"
   	echo "LOG: El script ha terminado con ERROR" >> $flogs
	echo "-----------------------------------------------------------------------------------" >> $flogs
	echo "################################## FIN DEL SCRIPT #################################" >> $flogs
	exit -1 
}

finExito() {
	echo "LOG: Hora de finalizacion: $HoraFinal" >> $flogs
	echo "LOG: Duracion: $HORA horas, $MINS minutos y $SEGS segundos" >> $flogs
	echo "LOG: El script ha terminado con EXITO"
   	echo "LOG: El script ha terminado con EXITO" >> $flogs
	echo "-----------------------------------------------------------------------------------" >> $flogs
	echo "################################## FIN DEL SCRIPT #################################" >> $flogs
	exit 0
}

if [ $# -ne 2 ]; then
	echo "Es necesario introducir 2 parámetros: $0 [fuenlabrada|e-eye] YYYY-MM-DD"
	exit -1
else
	flogs=./Logs/$2.log
	if [ -f $flogs ];
	then 
		rm -r $flogs
	fi
	touch $flogs
	STARTTIME=$(date +%s)
	echo "################################ INICIO DEL SCRIPT ###############################" >> $flogs
	echo "----------------------------------------------------------------------------------" >> $flogs
	HoraInicio=`date +"%H:%M:%S"`
	echo "LOG: Hora de inicio: $HoraInicio" >> $flogs
	echo "LOG: Fecha introducida: $2" >> $flogs
fi

python3 meteoros.py $1 $2
resultado=$?
ENDTIME=$(date +%s)
HoraFinal=`date +"%H:%M:%S"`
DURACION=$(($ENDTIME - $STARTTIME))
HORA=$(($DURACION/3600))
MINS=$((($DURACION%3600)/60))
SEGS=$(($DURACION%60))
if [ $resultado == 0 ]
then
	finExito
else
	finError
fi
