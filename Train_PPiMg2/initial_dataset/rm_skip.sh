#!/bin/bash
HERE=$PWD

for DIR in *; do
	echo ${DIR}
	if [[ -d ${DIR} ]]; then
		echo "Moving into ${DIR}"
		cd ${DIR}
		if [[ -f "skip" ]]; then
			echo "Removing skip"
			rm -f skip
		fi
	fi
	cd $HERE
done
