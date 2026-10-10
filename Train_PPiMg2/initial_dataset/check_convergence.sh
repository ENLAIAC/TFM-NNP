#!/bin/bash

HERE=$PWD

CONV=0
NOT_CONV=0
MANUAL_CHECK=0
ERROR=0
FAILED_CALC_FILE="$PWD/failed_calculation.txt"
MANUAL_CHECK_FILE="$PWD/manual_check_file.txt"
MISSING_OUTPUT_FILE="$PWD/missing_out_file.txt"
SKIPPED=0
SKIPPED_FILE="$PWD/skipped_calc.txt" 
rm -rf ${FAILED_CALC_FILE} ${MANUAL_CHECK_FILE} ${MISSING_OUTPUT_FILE} selected.txt ${SKIPPED_FILE}

touch ${FAILED_CALC_FILE} ${MANUAL_CHECK_FILE} ${MISSING_OUTPUT_FILE} selected.txt # ${SKIPPED_FILE}

for DIR in *; do
	if [ -d ${DIR} ]; then
		cd ${DIR} 
		FILE="labeling_${DIR}"
		if [ -f "skip" ]; then
			SKIPPED=$(( SKIPPED + 1 ))
			echo "$PWD" >> "${SKIPPED_FILE}"
		elif [ -f "2_${FILE}.out" ]; then
			if grep -q "SCF run NOT converged" "2_${FILE}.out"; then
				echo -n "Run ${DIR} not converged. The job path will be copied in ${FAILED_CALC_FILE}"
				echo
				NOT_CONV=$(( NOT_CONV + 1 ))
				echo "${PWD}" >> "${FAILED_CALC_FILE}"
			elif grep -q "Cholesky decomposition failed" "2_${FILE}.out"; then
				echo -n "WARNING: Choolesky decomposition failed in job ${DIR}"
				NOT_CONV=$(( NOT_CONV + 1 ))
				echo "${PWD}" >> "${FAILED_CALC_FILE}"
			elif grep -q "SCF run converged" "2_${FILE}.out"; then
				CONV=$(( CONV + 1 ))
				echo "Job ${DIR} was a success"
				echo ${DIR} >> "${HERE}/selected.txt"
			else
				echo "JOB-${DIR}: Unknown error. Check manually"
				MANUAL_CHECK=$(( MANUAL_CHECK + 1 ))
				echo "${PWD}" >> "${MANUAL_CHECK_FILE}"
			fi
		else 
		echo "ERROR: No output file found in ${DIR}"
		ERROR=$(( ERROR + 1 ))
		echo "${PWD}" >> "${MISSING_OUTPUT_FILE}"
		fi
	else
		continue
	fi
	cd $HERE
done

echo ""
echo "-------------------------------------------------------------------"
echo "RESUME:"
echo "Converged calculation: ${CONV}"
echo "Not converged calculation: ${NOT_CONV}"
if [ ${NOT_CONV} -ne 0 ]; then
	echo "More information about failed calculation can be found in: ${FAILED_CALC_FILE}"
fi
echo "Manual check required: ${MANUAL_CHECK}"
if [ ${MANUAL_CHECK} -ne 0 ]; then
	echo "More information about files to check manually can be found in: ${MANUAL_CHECK_FILE}"
fi
echo "Skipped calculations: ${SKIPPED}"
if [ ${SKIPPED} -ne 0 ]; then
	echo "More information about skipped calculation can be found in: ${SKIPPED_FILE}"
fi
echo "Errors: ${ERROR}"
if [ ${ERROR} -ne 0 ]; then
	echo "More information about error can be found in: ${MISSING_OUTPUT_FILE}"
fi






