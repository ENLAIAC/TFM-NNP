#!/bin/bash
#SBATCH --ntasks-per-node 1
#SBATCH --cpus-per-task 4
#SBATCH --output=dptest_output.txt
#SBATCH --mem=32G

. /storage/scratch/lv87/lv87680/toolbox/deepmd-kit-cpu/etc/profile.d/conda.sh #Adrian: Changed jz instalation by vives instalation
conda activate /storage/scratch/lv87/lv87680/toolbox/deepmd-kit-cpu  

dp test -m _NNP_ -s _SYSTEM-PATH_ -n _NCONF_ -d _DETAIL-FILE_
