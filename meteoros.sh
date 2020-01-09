#!/bin/bash

finError() {
	echo "LOG: Hora de finalizacion: $HoraFinal" >> $flogs
	echo "LOG: Duracion: $HORA horas, $MINS minutos y $SEGS segundos" >> $flogs
	echo "LOG: El script ha terminado con ERROR"
   	echo "LOG: El script ha terminado con ERROR" >> $flogs
	echo "-------------------------------------------------------------------------------" >> $flogs
	echo "################################ FIN DEL SCRIPT ###############################" >> $flogs
	exit -1 
}

finExito() {
	echo "LOG: Hora de finalizacion: $HoraFinal" >> $flogs
	echo "LOG: Duracion: $HORA horas, $MINS minutos y $SEGS segundos" >> $flogs
	echo "LOG: El script ha terminado con EXITO"
   	echo "LOG: El script ha terminado con EXITO" >> $flogs
	echo "-------------------------------------------------------------------------------" >> $flogs
	echo "################################ FIN DEL SCRIPT ###############################" >> $flogs
	exit 0
}

if [ -z "$1" ]
then
    echo "ERROR: No se ha introducido fecha como argumento"
	exit -1
else
	flogs=./Logs/$1.log
	if [ -f $flogs ];
	then 
		rm -r $flogs
	fi
	touch $flogs
	STARTTIME=$(date +%s)
	echo "############################## INICIO DEL SCRIPT #############################" >> $flogs
	echo "------------------------------------------------------------------------------" >> $flogs
	HoraInicio=`date +"%H:%M:%S"`
	echo "LOG: Hora de inicio: $HoraInicio" >> $flogs
	echo "LOG: Fecha introducida: $1" >> $flogs
fi

echo "LOG: Leyendo fichero de propiedades..."
python3 meteoros.py $1
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
