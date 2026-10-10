#!/bin/bash

HERE=$PWD

cd "speciation"
for i in $(seq 5 5 100); do
	for j in $(seq 5 5 100); do
	iter="0$( printf "%03d" $i )_0$(printf "%03d" $j)"
	mkdir $iter
	conc_mg=$( printf "%03d" $i)
	conc_pp=$( printf "%03d" $j)
	sed -e "s/c1 = x/c1=0.$conc_mg/g" speciation.py > "temp"
	sed -e "s/c2 = y/c2=0.$conc_pp/g" "temp" > "$iter/speciation.py"
	cd $iter
	python3 speciation.py
	cd ..
done
done

