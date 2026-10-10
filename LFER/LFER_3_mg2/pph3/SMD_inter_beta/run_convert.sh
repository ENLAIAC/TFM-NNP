#!/bin/bash
#SBATCH --job-name=conv-TS1_TS2
#SBATCH --qos=cuerda
#SBATCH --partition=cuerda
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --hint=nomultithread
#SBATCH --time=04:00:00

HERE=$PWD

module purge
. /storage/scratch/lv87/lv87680/toolbox/deepmd-kit-2.1.4-cuda11.6/etc/profile.d/conda.sh
conda activate /storage/scratch/lv87/lv87680/toolbox/deepmd-kit-2.1.4-cuda11.6

python3 convert_restart_to_lmp.py

