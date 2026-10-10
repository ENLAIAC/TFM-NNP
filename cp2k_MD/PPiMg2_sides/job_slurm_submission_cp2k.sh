#!/bin/bash
#Slurm file to launch CP2K jobs MN5
#SBATCH --account=uv36
#SBATCH --qos=gp_resa
#-SBATCH --qos=gp_debug
#SBATCH --partition=gpp
#SBATCH --cpus-per-task=1
#SBATCH --ntasks=36
#SBATCH -o PPiMg2_sides.%j
#SBATCH -e PPiMg2_sides.%j
#SBATCH -t 36:00:00
#SBATCH -J PPiMg2_sides


HERE=$PWD
SYS="PPiMg2_sides"
IN_FILE="${SYS}.inp"
OUT_FILE="${SYS}.out"
XYZ_FILE="${SYS}.xyz"

module purge
module load impi mkl intel boost cp2k/2023.1

srun cp2k.popt -i $IN_FILE -o $OUT_FILE
