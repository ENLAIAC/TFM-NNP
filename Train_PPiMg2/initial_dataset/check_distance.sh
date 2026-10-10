#!/bin/bash
SHRT_DIST_FILE="short_distance_error.txt"

HERE=$PWD
touch ${SHRT_DIST_FILE}
ERR=0


for DIR in *
do
	if [[ -d ${DIR} ]]; then
		cd ${DIR}
		echo "Entering ${DIR}"
		ID_PADDED=$(basename $DIR)
		OUT_FILE="2_labeling_${ID_PADDED}.out"
		if grep "SCF run converged" ${OUT_FILE}; then
	 		if grep "The distance between the atoms" ${OUT_FILE}; then
				echo "${DIR}/${OUT_FILE}" >> $HERE/${SHRT_DIST_FILE}
				touch skip
				ERR=$(( ERR + 1 ))
			else
				echo "${DIR}/${OUT_FILE} converged correctly"
			fi
		fi
	fi
	cd $HERE
done

echo "RESUME"
echo "------------------------------------------------------"
echo "Count of errors: ${ERR}"
