#!/bin/bash
HERE=$PWD
ENERGY_FILE="Energies.txt"
CONFIG_FILE="selected_configurations.txt"
CONFIG_PATH="${HERE}/${CONFIG_FILE}"
DISCARDED_FILE="discarded_configurations.txt"
DISCARDED_PATH="${HERE}/${DISCARDED_FILE}"   # BUG 1: was CONFIG_PATH, shadowing the real CONFIG_PATH
ENERGY_COUNT=0
DISCARDED_COUNT=0
ERR_CONV_FILE="Error_conv.err"
ERR_DIST_FILE="Error_dist.err"
ALL_ENERGY_FILE="Energy_dist.txt"

rm ${CONFIG_FILE} ${DISCARDD_FILE} ${ALL_ENERGY_FILE}
touch ${CONFIG_FILE} ${DISCARDED_FILE} ${ALL_ENERGY_FILE}

for SYS in *; do
        if [[ -d ${SYS} ]]; then
                cd ${SYS}
                rm ${ENERGY_FILE}
                touch ${ENERGY_FILE} ${ERR_DIST_FILE} ${ERR_CONV_FILE}
                echo "Processing ${SYS}:"
                ./check_distance.sh > "Distances_check_rsm_${SYS}.txt"
                ./check_convergence.sh > "Convergence_resume_${SYS}.txt"
                CONV_CALC=$(cat "selected.txt")
                for DIR in ${CONV_CALC}; do
                        if [[ -d ${DIR} ]]; then
                                cd ${DIR}
                                echo "Entering ${DIR}"
                                if [[ -f skip ]]; then
                                        echo "Skipping folder ${DIR}"
                                        cd ${HERE}/${SYS} 
                                else
                                        OUT_FILE="2_labeling_$(basename $DIR).out"
                                        if [[ -f ${OUT_FILE} ]]; then
                                                energy=$(awk '/Total energy:/ { last_energy = $NF } /outer SCF loop converged/ { print last_energy }' "$OUT_FILE") \
                                                        || { echo ${DIR} >> ${DISCARDED_PATH}; DISCARDED_COUNT=$(( DISCARDED_COUNT + 1 )); }

                                                if [[ -z "$energy" ]]; then
                                                        echo "No converged SCF energy found in ${OUT_FILE}."
                                                        exit 1
                                                elif (( $(echo "$energy < -3166.9" | bc -l) )); then
                                                        ENERGY_COUNT=$(( ENERGY_COUNT + 1 ))
                                                        echo "$HERE/${SYS}/$DIR" >> ${CONFIG_PATH}
							echo "$energy grepped"
					        	echo "$energy" >> "${HERE}/${ALL_ENERGY_FILE}"
						else
                                                        DISCARDED_COUNT=$(( DISCARDED_COUNT + 1 ))
                                                        echo "${HERE}/${SYS}/$DIR" >> ${DISCARDED_PATH}

                                                fi

                                                echo "$energy" >> "Energy_$(basename $DIR).txt"
                                                echo "$energy" >> "${HERE}/${SYS}/${ENERGY_FILE}"
                                        fi
                                fi
                        fi
                        cd ${HERE}/${SYS}
                done
        fi
        cd ${HERE}
done

echo "TOTAL CONFIGURATIONS: ${ENERGY_COUNT}"
echo "TOTAL DISCARDED: ${DISCARDED_COUNT}"
