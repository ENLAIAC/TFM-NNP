#!/bin/bash
#SBATCH --ntasks-per-node 1
#SBATCH --cpus-per-task 4
#SBATCH --output=dptest_output.txt
#SBATCH --mem=32G

module purge
. /storage/scratch/lv87/lv87680/toolbox/deepmd-kit-cpu/etc/profile.d/conda.sh
conda activate /storage/scratch/lv87/lv87680/toolbox/deepmd-kit-cpu 

dp test -m ../../../OPES/NNP/graph_1_011_compressed.pb -s ../03_dataset/ -n 800 -d validation_set_pp
