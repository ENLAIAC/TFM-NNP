#!/bin/bash
#Slurm file to launch DeePMD lammps jobs MN5
#SBATCH --account=uv36
#SBATCH --qos=acc_resa
#-SBATCH --qos=acc_debug
#SBATCH --partition=acc
#SBATCH --cpus-per-task=20
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH -o LAMMPS_DeepMD.%j
#SBATCH -e LAMMPS_DeepMD.%j
#SBATCH -t 03:00:00
#SBATCH -J US

LAMMPS_INPUT="US_lammps"

module purge
module load cuda/12.3 cudnn/9.6.0-cuda12 openmpi/4.1.5-gcc fftw/3.3.10-gcc-ompi miniforge/24.3.0-0 gsl/2.8-gcc deepmd-kit/2.2.9-plumed-gcc-ompi

export DP_INTER_OP_PARALLELISM_THREADS=20
export SLURM_CPU_BIND=none

mpirun --bind-to none lmp_mpi -in ${LAMMPS_INPUT}.in -log ${LAMMPS_INPUT}.log -screen none
# Done
echo "Have a nice day !"
