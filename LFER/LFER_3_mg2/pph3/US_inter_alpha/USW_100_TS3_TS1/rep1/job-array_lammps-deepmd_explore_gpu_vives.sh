#!/bin/bash
#----------------------------------------------------------------------------------------------------#
#   ArcaNN: Automatic training of Reactive Chemical Architecture with Neural Networks                #
#   Copyright 2023 ArcaNN developers group <https://github.com/arcann-chem>                          #
#                                                                                                    #
#   SPDX-License-Identifier: AGPL-3.0-only                                                           #
#----------------------------------------------------------------------------------------------------#
# You must keep the name file as job-array_lammps-deepmd_explore_ARCHTYPE_myHPCkeyword.sh.
#----------------------------------------------
# QoS/Partition/SubPartition
#SBATCH --qos=cuerda
#SBATCH --partition=cuerda
# Number of Nodes/MPIperNodes/OpenMPperMPI/GPU
#SBATCH --ntasks-per-node 1
#SBATCH --cpus-per-task 8
#SBATCH --gres=gpu:1
#SBATCH --hint=nomultithread
# Walltime
#SBATCH -t 03:00:00
# Merge Output/Error
#SBATCH -o LAMMPS_DeepMD.%A_%a
#SBATCH -e LAMMPS_DeepMD.%A_%a
# Name of job
#SBATCH -J US_rep1_TS3_TS1
#
# One array task per window (000-099); %10 caps concurrent running tasks - adjust to taste,
# or resubmit a subset (e.g. --array=37,52,90) to redo specific windows.
#SBATCH --array=0-99%10
#

SLURM_ARRAY_TASK_ID_PADDED=$(printf "%03d\n" "${SLURM_ARRAY_TASK_ID}")
JOB_PATH=${SLURM_ARRAY_TASK_ID_PADDED}

DeepMD_MODEL_VERSION="2.1"
LAMMPS_IN_FILE="US_lammps.in"
LAMMPS_LOG_FILE="US_lammps.log"
EXTRA_FILES=("USW_${SLURM_ARRAY_TASK_ID_PADDED}.lmp" "plumed_USW_${SLURM_ARRAY_TASK_ID_PADDED}.dat")

SCRATCH=/storage/scratch/lv87/lv87908/DeepMD_pyro/JOBS

# Go where the job has been launched, then into this array task's window folder
cd "${SLURM_SUBMIT_DIR}" || { echo "Could not go to ${SLURM_SUBMIT_DIR}. Aborting..."; exit 1; }
cd "${JOB_PATH}" || { echo "I can't reach the Job folder: ${JOB_PATH}. Aborting..."; exit 1; }

if [ "${SLURM_JOB_QOS}" == "cuerda" ]; then
    if [ "${DeepMD_MODEL_VERSION}" == "2.1" ]; then
        module purge
        . /storage/scratch/lv87/lv87680/toolbox/deepmd-kit-2.1.4-cuda11.6/etc/profile.d/conda.sh
        conda activate /storage/scratch/lv87/lv87680/toolbox/deepmd-kit-2.1.4-cuda11.6
    else
        echo "DeePMD ${DeepMD_MODEL_VERSION} is not installed on ${SLURM_JOB_QOS}. Aborting..."; exit 1
    fi
elif [ "${SLURM_JOB_QOS:3:4}" == "cpu" ]; then
    echo "GPU on a CPU partition?? Aborting..."; exit 1
else
    echo "There is no ${SLURM_JOB_QOS}. Aborting..."; exit 1
fi
LAMMPS_EXE=$(command -v lmp) || ( echo "Executable (lmp) not found. Aborting..."; exit 1 )

# Test if input file is present
if [ ! -f "${LAMMPS_IN_FILE}" ]; then echo "No input file found. Aborting..."; exit 1; fi

# Set the temporary work directory
export TEMPWORKDIR=${SCRATCH}/JOB-${SLURM_JOBID}
mkdir -p "${TEMPWORKDIR}"
ln -s "${TEMPWORKDIR}" "${SLURM_SUBMIT_DIR}/${JOB_PATH}/JOB-${SLURM_JOBID}"

# Copy files to the temporary work directory
# NNP graph paths are already absolute inside US_lammps.in, so no model symlinking is needed here
cp "${LAMMPS_IN_FILE}" "${TEMPWORKDIR}" && echo "${LAMMPS_IN_FILE} copied successfully"
cp "${LAMMPS_IN_FILE}" "${LAMMPS_IN_FILE}"."${SLURM_JOBID}"
for f in "${EXTRA_FILES[@]}"; do [ -f "${f}" ] && cp "${f}" "${TEMPWORKDIR}" && echo "${f} copied successfully"; done
cd "${TEMPWORKDIR}" || { echo "Could not go to ${TEMPWORKDIR}. Aborting..."; exit 1; }

# MPI/OpenMP setup
echo "# [$(date)] Started"
export EXIT_CODE="0"
echo "Running on node(s): ${SLURM_NODELIST}"
echo "Running on ${SLURM_NNODES} node(s)."
if [ -z "${SLURM_NTASKS}" ]; then
    export SLURM_NTASKS=$(( SLURM_NTASKS_PER_NODE * SLURM_NNODES))
fi
if [ -z "${SLURM_NTASKS_PER_NODE}" ]; then
    export SLURM_NTASKS_PER_NODE=$(( SLURM_NTASKS / SLURM_NNODES ))
fi
echo "Running ${SLURM_NTASKS} task(s), with ${SLURM_NTASKS_PER_NODE} task(s) per node."
echo "Running with ${SLURM_CPUS_PER_TASK} thread(s) per task."
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK}

# Launch command
SRUN_LAMMPS_EXE="srun --ntasks=${SLURM_NTASKS} --nodes=${SLURM_NNODES} --ntasks-per-node=${SLURM_NTASKS_PER_NODE} --cpus-per-task=${SLURM_CPUS_PER_TASK} ${LAMMPS_EXE}"
LAUNCH_CMD="${SRUN_LAMMPS_EXE} -in ${LAMMPS_IN_FILE} -log ${LAMMPS_LOG_FILE} -screen none"

echo "${LAUNCH_CMD}"
${LAUNCH_CMD} || export EXIT_CODE="1"
echo "# [$(date)] Ended"

# Move back data from the temporary work directory and scratch, and clean-up
if [ -f log.cite ]; then rm log.cite ; fi
find ./ -type l -delete
mv ./* "${SLURM_SUBMIT_DIR}/${JOB_PATH}"
cd "${SLURM_SUBMIT_DIR}/${JOB_PATH}" || exit 1
rmdir "${TEMPWORKDIR}" 2> /dev/null || echo "Leftover files on ${TEMPWORKDIR}"
[ ! -d "${TEMPWORKDIR}" ] && { [ -h JOB-"${SLURM_JOBID}" ] && rm JOB-"${SLURM_JOBID}"; }
rm "${LAMMPS_IN_FILE}"."${SLURM_JOBID}"

# Done
echo "Have a nice day !"
sleep 5
exit ${EXIT_CODE}
