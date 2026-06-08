#!/bin/bash
#Slurm file to launch DeePMD lammps exploration jobs in Vives
#SBATCH --qos=cuerda
#SBATCH --partition=cuerda
#SBATCH --nodes 1
#SBATCH --ntasks-per-node 1
#SBATCH --cpus-per-task 8
#SBATCH --hint=nomultithread
#SBATCH --gres=gpu:1
#SBATCH -o LAMMPS_DeepMD.%j
#SBATCH -e LAMMPS_DeepMD.%j
#-SBATCH -t 10:00:00
#SBATCH -J LAMMPS_DeepMD

LAMMPS_INPUT="pp_3h_steered_md"
#LAMMPS_INPUT="lammps"

module purge
. /storage/scratch/lv87/lv87680/toolbox/deepmd-kit-2.1.4-cuda11.6/etc/profile.d/conda.sh
conda activate /storage/scratch/lv87/lv87680/toolbox/deepmd-kit-2.1.4-cuda11.6 

srun lmp -in ${LAMMPS_INPUT}.in -log ${LAMMPS_INPUT}.log -screen none

# Done
echo "Have a nice day !"
