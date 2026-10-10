#!/bin/bash
#SBATCH --job-name=wham_gfix
#SBATCH --account=uv36
#SBATCH --qos=gp_resa
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH -o slurm_test.out
#SBATCH -e slurm_test.err
#SBATCH --time=1:00:00
module purge
python /gpfs/scratch/uv36/adrian/deepmd-training/Train_PPiMg2/NNP_LFER_choice/WHAM_files/wham1D_copy.py input.txt _GRIDFIX
