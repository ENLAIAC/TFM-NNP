#!/bin/bash
#-SBATCH --account=uv36
#SBATCH --qos=class_t
#SBATCH --nodes=1
#SBATCH --ntasks-per-node 48
#SBATCH --cpus-per-task 1
# Walltime
#SBATCH -t 1:30:00
# Merge Output/Error
#SBATCH -o CP2K.%A_%a
#SBATCH -e CP2K.%A_%a


SLURM_ARRAY_TASK_ID_PADDED=$( printf "%05d" ${SLURM_ARRAY_TASK_ID} )

FILE_IN_1="1_labeling_${SLURM_ARRAY_TASK_ID_PADDED}.inp"
FILE_IN_2="2_labeling_${SLURM_ARRAY_TASK_ID_PADDED}.inp"
FILE_OUT_1="1_labeling_${SLURM_ARRAY_TASK_ID_PADDED}.out"
FILE_OUT_2="2_labeling_${SLURM_ARRAY_TASK_ID_PADDED}.out"

JOB_PATH=$PWD/
# Load the environment depending on the version
echo "Submission slurm directory: ${JOB_PATH}"

ulimit -s unlimited
module purge
module load oneapi/2025.1.3 mpi/2021.15 cp2k/2025.2

SCRATCH=/storage/scratch/lv87/lv87680/visitors/elia/validation_set_elia/pph3/JOBS

if [ "$(command -v cp2k.psmp)" ]; then
	CP2K_EXE=$(command -v cp2k.psmp)
elif [ "$(command -v cp2k.popt)" ]; then
	if [ "${SLURM_CPUS_PER_TASK}" -lt 2 ]; then
		CP2K_EXE=$(command -v cp2k.popt)
	else
		echo "Only executable (cp2k.popt) was found and OpenMP was requested. Aborting..."
	fi
else
	echo "Executable (cp2k.popt/cp2k.psmp) not found. Aborting..."
fi

export WORK_DIR="${SCRATCH}/JOB_${SLURM_JOBID}"

mkdir -p ${WORK_DIR}

ln -s ${WORK_DIR} "${JOB_PATH}/JOB_${SLURM_JOBID}"
echo "Copying input and geometry files..."
cp *.inp ${WORK_DIR} || ( echo "The copy of the input files failed. Aborting..."; exit 1 )
cp *.xyz ${WORK_DIR} || ( echo "The copy of the geometry file failed. Aborting..."; exit 1)
cd ${WORK_DIR}
# This assumes you are in the corresponding folder for each array task
# You can use $SLURM_ARRAY_TASK_ID to differentiate between tasks
echo "Running CP2K calculation for folder ${SLURM_ARRAY_TASK_ID_PADDED}"
echo "Running CP2K calculation for folder ${SLURM_ARRAY_TASK_ID_PADDED}"
echo "Calculation features:"
echo "-- Amount of tasks: ${SLURM_NTASKS}"
echo "-- Amount of nodes occupied: ${SLURM_NNODES}"
echo "-- Tasks per node: ${SLURM_NTASKS_PER_NODE}"
echo "-- CPU-per-tasked used: ${SLURM_CPU_PER_TASKS}"

SRUN_EXE="srun --ntasks=${SLURM_NTASKS} --nodes=${SLURM_NNODES} --ntasks-per-node=${SLURM_NTASKS_PER_NODE} --cpus-per-task=${SLURM_CPUS_PER_TASK} ${CP2K_EXE}"

# Run the CP2K calculation with the input file
${SRUN_EXE} -i ${FILE_IN_1} > ${FILE_OUT_1} || ( echo "It was not possible to submit the calculation"; exit 1 )
${SRUN_EXE} -i ${FILE_IN_2} > ${FILE_OUT_2} || ( echo "It was not possible to submit the calculation"; exit 1 )

echo "Calculation are finished. Proceed to copy the output files..."

cp ${WORK_DIR}/* ${JOB_PATH} || ( echo "Copying the output file in the ${JOB_PATH} directory encountered an error. Aborting..."; exit 1 ) 
cd ${JOB_PATH} || ( echo "Failed to move in the ${JOB_PATH}. Aborting..."; exit 1)
rm -rf ${WORK_DIR}
rm -rf "${JOB_PATH}/JOB_${SLURM_JOBID}"
# End of the script
