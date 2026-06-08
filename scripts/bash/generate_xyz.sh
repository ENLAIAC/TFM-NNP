#!/bin/bash

HERE=$PWD
SYSNAME="rep13-Trajectory"
TRJ_FILE="${SYSNAME}.xyz"

[ -f ${TRJ_FILE} ] || ( echo "Trajectory file not existing. Aborting ....!; exit 1" )

for i in $(seq 1 209); do
	DIR=$( printf "%05d" $((i)))
	mkdir ${DIR}
	INPUT_FILE="labeling_${DIR}"
	echo "Copying the input file..."
	cp "1_labeling_XXXXX.inp" "${DIR}/1_${INPUT_FILE}.inp" || { echo "Copy of INPUT FILE 1 failed. Aborting..." ; exit 1; }
	sed -i "s/XXXXX/${DIR}/g" ${DIR}/1_${INPUT_FILE}.inp
	echo "Copyng the input file..."
	cp "2_labeling_XXXXX.inp" ${DIR}/2_${INPUT_FILE}.inp || { echo "Copy of INPUT FILE 2 failed. Aborting..." ; exit 1; }
	sed -i "s/XXXXX/${DIR}/g" ${DIR}/2_${INPUT_FILE}.inp

	# Creating XYZ FILES FROM TRAJECTORY
	
	LINE_PER_TRJ=520
	XYZ_FILE="${DIR}/labeling_${DIR}.xyz"
	start_conf=$(( (i - 1)  * LINE_PER_TRJ + 1))
	end_conf=$(( i * LINE_PER_TRJ ))

	#Grep lines
	echo "Extracting lines ${start_conf} to ${end_conf} from ${TRJ_FILE} into ${XYZ_FILE}"	
	sed -n "${start_conf},${end_conf}p" ${TRJ_FILE} > "${XYZ_FILE}"
	
	echo "Folder ${DIR} processed. It contains the following files:"
	ls ${DIR}

done

echo "Have a good day!"
