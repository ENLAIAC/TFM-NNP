#!/bin/bash
#SBATCH --job-name=PPiMg2_sides
#SBATCH --output=PPiMg2_sides.%j
#SBATCH --error=PPiMg2_sides.%j
#SBATCH --qos=class_t
#SBATCH --ntasks=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=8

HERE=$PWD
SYS="PPiMg2_sides"
IN_FILE="${SYS}-MD.restart"
OUT_FILE="${SYS}.out"
LOG_FILE="${SYS}.log"

module purge
module load oneapi/2025.1.3 mpi/2021.15 cp2k/2025.2

if [ "$(command -v cp2k.psmp)" ]; then
    CP2K_EXE=$(command -v cp2k.psmp)
elif [ "$(command -v cp2k.popt)" ]; then
    if [ "${SLURM_CPUS_PER_TASK}" -lt 2 ]; then
        CP2K_EXE=$(command -v cp2k.popt)
    else
        echo "Only executable (cp2k.popt) was found and OpenMP was requested. Aborting..."
        exit 1
    fi
else
    echo "Executable (cp2k.popt/cp2k.psmp) not found. Aborting..."
    exit 1
fi

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK}
export OMP_STACKSIZE=64M
ulimit -s unlimited

SRUN_CP2K_EXE="srun --ntasks=${SLURM_NTASKS} --nodes=${SLURM_NNODES} --ntasks-per-node=${SLURM_NTASKS_PER_NODE} --cpus-per-task=${SLURM_CPUS_PER_TASK} ${CP2K_EXE}"
${SRUN_CP2K_EXE} -i ${IN_FILE} > ${OUT_FILE}
