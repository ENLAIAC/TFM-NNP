#!/bin/bash

HERE=$PWD
ENERGY_FILE=${PWD}/Energies.txt
CONV_CALC=$(cat "selected.txt")
rm ${ENERGY_FILE}
touch ${ENERGY_FILE}



for DIR in ${CONV_CALC}; do
	if [[ -d ${DIR} ]]; then
		cd ${DIR}
		echo "Entering ${DIR}"
		if [[ -f skip ]]; then
			echo "Skipping folder ${DIR}"
			cd ${HERE}
		else
			OUT_FILE="2_labeling_$(basename $DIR).out"
			if [[ -f ${OUT_FILE} ]]; then
				energy=$(awk '/Total energy:/ { last_energy = $NF }/outer SCF loop converged/ { print last_energy }' "$OUT_FILE")
				if [[ -z "$energy" ]]; then
			    		echo "No converged SCF energy found in ${OUT_FILE}."
			       		exit 1
				fi
				echo "$energy" >> "Energy_$(basename $DIR).txt"
				echo "$energy" >> ${ENERGY_FILE}
			fi				
		fi
	fi
	cd ${HERE}
done

