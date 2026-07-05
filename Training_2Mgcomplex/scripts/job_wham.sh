#!/bin/bash
#SBATCH --job-name=wham
#SBATCH --account=uv36
#SBATCH --qos=gp_resa
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH -o slurm.out
#SBATCH -e slurm.err
#SBATCH --time=4:00:00

module purge

# Pass SLURM_ARRAY_TASK_ID as argument
python /gpfs/scratch/uv36/elia/Training_2Mgcomplex/NNP_select/Adrian_TS1/WHAM_files/wham1D.py input.txt dD_pp
