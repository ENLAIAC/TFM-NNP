#!/bin/bash

HERE=$PWD
DATA_DIR="data"
DATA_DIR_NUM=0
DIFF_DIR="$HERE/missing_folders.txt"
MATCHES=0

rm $DIFF_DIR
touch $DIFF_DIR

for i in "training" "Training_2Mgcomplex"; do
	if [[ -d "$i" ]]; then
		echo "Entering: $i"
		cd "$i/${DATA_DIR}"
		rm "$HERE/$i.txt"
		touch "$HERE/$i.txt"
		for DIR in *; do
			if [[ -d $DIR ]]; then
				DATA_DIR_NUM=$(( DATA_DIR_NUM + 1 ))
				echo "$( basename $DIR )" >> "$HERE/$i.txt"
			fi
		done
		echo "Amount of folders in $i: $DATA_DIR_NUM"
	fi
	cd $HERE
	DATA_DIR_NUM=0
done

for i in $( grep "init_" "Training_2Mgcomplex.txt" ); do
	if [[ -d "training/${DATA_DIR}/$i" ]]; then
		MATCHES=$(( MATCHES +1 ))
	else 
		echo "$i" >> "$DIFF_DIR"
	fi
done

	
