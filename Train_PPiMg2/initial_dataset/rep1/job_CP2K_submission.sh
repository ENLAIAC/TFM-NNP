#!/bin/bash
#SBATCH --job-name=CP2K_Label_800
#SBATCH --qos=class_t
#SBATCH --ntasks=144
#SBATCH --cpus-per-task=1
#SBATCH -t 01:30:00
#SBATCH --array=1-82%10
#SBATCH -o logs/CP2K.%A_%a.out
#SBATCH -e logs/CP2K.%A_%a.err
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=elia.cazzanti@studenti.unipg.it

# 1. Environment Setup
ulimit -s unlimited
module purge
module load oneapi/2025.1.3 mpi/2021.15 cp2k/2025.2

# Set OpenMP threads based on Slurm allocation
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK}

# 2. Path Management
PADDED_ID=$(printf "%05d" ${SLURM_ARRAY_TASK_ID})
JOB_PATH="${SLURM_SUBMIT_DIR}/${PADDED_ID}"
SCRATCH_BASE="/storage/scratch/lv87/lv87680/visitors/elia/validation_set_elia/pph3/JOBS"
WORK_DIR="${SCRATCH_BASE}/JOB_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"

mkdir -p ${WORK_DIR}
mkdir -p logs  # Ensure log directory exists

# 3. Executable Selection (Prefer psmp for hybrid performance)
if [ "$(command -v cp2k.psmp)" ]; then
    CP2K_EXE=$(command -v cp2k.psmp)
else
    echo "Hybrid executable cp2k.psmp not found. Optimization failed."
    exit 1
fi

# 4. Data Transfer
cd ${JOB_PATH} || { echo "Directory ${JOB_PATH} not found"; exit 1; }
cp *.inp *.xyz ${WORK_DIR}

# 5. Execution
cd ${WORK_DIR}
echo "Starting Task ${PADDED_ID} on $(hostname) at $(date)"

# Run first labeling input
srun --hint=nomultithread ${CP2K_EXE} -i 1_labeling_${PADDED_ID}.inp > 1_labeling_${PADDED_ID}.out

# Run second labeling input
srun --hint=nomultithread ${CP2K_EXE} -i 2_labeling_${PADDED_ID}.inp > 2_labeling_${PADDED_ID}.out

# 6. Cleanup & Retrieval
cp ${WORK_DIR}/* ${JOB_PATH}/
cd ${JOB_PATH}
rm -rf ${WORK_DIR}

echo "Task ${PADDED_ID} completed at $(date)"
