#!/bin/bash

trajectory_file='../01_SMD/SMD_dD_pp_traj.xyz'
lines_per_configuration=520

for i in {1..800}; do
    folder=$(printf "%05d" $i)
    mkdir $folder
done

for i in {1..800}; do
    folder=$(printf "%05d" $((i)))
    output_file="labeling_${folder}.xyz"
    
    # Calculate line range for the current configuration
    start_line=$(( (i - 1) * lines_per_configuration + 1 ))
    end_line=$(( i * lines_per_configuration ))

    # Extract lines for the current configuration and save to the output file
    sed -n "${start_line},${end_line}p" $trajectory_file > "${folder}/${output_file}"

    # Copy template input files into the folder

    cp 1_labeling_XXXXX.inp ${folder}/1_labeling_${folder}.inp
    sed -i 's/XXXXX/'${folder}'/g' ${folder}/1_labeling_${folder}.inp
    cp 2_labeling_XXXXX.inp ${folder}/2_labeling_${folder}.inp
    sed -i 's/XXXXX/'${folder}'/g' ${folder}/2_labeling_${folder}.inp    
    cp job_script_XXXXX.sh ${folder}/job_script_${folder}.sh
    sed -i 's/XXXXX/'${folder}'/g' ${folder}/job_script_${folder}.sh

    echo "Folder ${folder} processed"

done

cd ../
