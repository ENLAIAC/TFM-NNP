#!/bin/bash
#----------------------------------------------------------------------------------------------------#
#   ArcaNN: Automatic training of Reactive Chemical Architecture with Neural Networks                #
#   Copyright 2022-2024 ArcaNN developers group <https://github.com/arcann-chem>                     #
#                                                                                                    #
#   SPDX-License-Identifier: AGPL-3.0-only                                                           #
#----------------------------------------------------------------------------------------------------#
# Created: 2022/01/01
# Last modified: 2024/05/15
#----------------------------------------------
# You must keep the _R_VARIABLES_ in the file.
# You must keep the name file as job_deepmd_compress_ARCHTYPE_myHPCkeyword.sh.
#----------------------------------------------
# Project/Account
#SBATCH --account=_R_PROJECT_@_R_ALLOC_
# QoS/Partition/SubPartition
#SBATCH --qos=_R_QOS_
#SBATCH --partition=_R_PARTITION_
#SBATCH -C _R_SUBPARTITION_
# Number of Nodes/MPIperNodes/OpenMPperMPI/GPU
#-SBATCH --nodes 1
#SBATCH --ntasks 1
#SBATCH --cpus-per-task 20
#SBATCH --hint=nomultithread
#SBATCH gres=gpu:1
# Walltime
#SBATCH -t _R_WALLTIME_
# Merge Output/Error
#SBATCH -o DeepMD_Train.%j
#SBATCH -e DeepMD_Train.%j
# Name of job
#SBATCH -J DeepMD_Train
# Email
#SBATCH --mail-type FAIL,BEGIN,END,ALL
#SBATCH --mail-user _R_EMAIL_
#

DeepMD_MODEL_VERSION="_R_DEEPMD_VERSION_"
DeepMD_CHKPT_FILE="_R_CHECKPOINT_"
DeepMD_INPUT="training"
DeepMD_DATA_DIR="../data"

SCRATCH=/gpfs/scratch/uv36/adrian/deepmd-training/DeepMD_pyro/JOBS/

# Go where the job has been launched
cd "${SLURM_SUBMIT_DIR}" || { echo "Could not go to ${SLURM_SUBMIT_DIR}. Aborting..."; exit 1; }

if [ "${SLURM_JOB_QOS}" == "acc" ]; then # Example to use the DeepMD_MODEL_VERSION variable
        if [ "${DeepMD_MODEL_VERSION}" == "2.2" ]; then
                module purge
                module load deepmd-kit/2.2.9-plumed-gcc-ompi
		log="--log-path ${DeepMD_LOG_FILE}"
        else
                echo "DeepMD version ${DeepMD_MODEL_VERSION} is not installed in {SLURM_JOB_QOS}. Aborting..."; exit 1
        fi
elif [ "${SLURM_JOB_QOS:3:4}" == "gpp" ]; then
                echo "GPU on a CPU partition? Hell NAH! Aborting..."; exit 1
else
        echo "There is no ${SLURM_JOB_QOS}. Aborting..."; exit 1;
fi

DeepMD_EXE=$(command -v dp) ||  ( echo "Executable (dp) not found. Aborting..."; exit 1 )

# Test if input file is present
if [ ! -f ${DeepMD_INPUT}.json ]; then echo "No input file found. Aborting..."; exit 1; fi

# Set the temporary work directory
export TEMPWORKDIR=${SCRATCH}/JOB-${SLURM_JOBID}
mkdir -p "${TEMPWORKDIR}"
ln -s "${TEMPWORKDIR}" "${SLURM_SUBMIT_DIR}"/JOB-"${SLURM_JOBID}"

# Copy files to the temporary work directory
cp ${DeepMD_INPUT}.json "${TEMPWORKDIR}" && echo "${DeepMD_INPUT}.json copied successfully"
for f in "${DeepMD_CHKPT}"* ; do [ -f "${f}" ] && cp "${f}" "${TEMPWORKDIR}" && echo "${f} copied successfully"; done
[ -d ${DeepMD_DATA_DIR} ] && mkdir -p "${TEMPWORKDIR}"/data && cp -r ${DeepMD_DATA_DIR}/* "${TEMPWORKDIR}"/data && echo "${DeepMD_DATA_DIR} copied successfully"
cd "${TEMPWORKDIR}" || exit 1

# MPI/OpenMP setup
echo "# [$(date)] Started"
export EXIT_CODE="0"
echo "Running on node(s): ${SLURM_NODELIST}"
echo "Running on ${SLURM_NNODES} node(s)."
# Calculate missing values
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
SRUN_DeepMD_EXE="srun --export=ALL --mpi=pmi2 --ntasks=${SLURM_NTASKS} --nodes=${SLURM_NNODES} --ntasks-per-node=${SLURM_NTASKS_PER_NODE} --cpus-per-task=${SLURM_CPUS_PER_TASK} ${DeepMD_EXE}"
if [ -f ${DeepMD_CHKPT}.index ]
then
    LAUNCH_CMD="${SRUN_DeepMD_EXE} train ${DeepMD_INPUT}.json --restart ${DeepMD_CHKPT} ${log}"
    echo "${LAUNCH_CMD}"
    export EXIT_CODE="0"
    ${LAUNCH_CMD} > ${DeepMD_INPUT}.out 2>&1 || export EXIT_CODE="1"
else
    LAUNCH_CMD="${SRUN_DeepMD_EXE} train ${DeepMD_INPUT}.json ${log}"
    echo "${LAUNCH_CMD}"
    export EXIT_CODE="0"
    ${LAUNCH_CMD} > ${DeepMD_INPUT}.out 2>&1 || export EXIT_CODE="1"
fi
echo "# [$(date)] Ended"

# Move back data from the temporary work directory and scratch, and clean-up
if [ -f out.json ]; then rm out.json; fi
if [ -f input_v2_compat.json ]; then rm input_v2_compat.json; fi
rm -rf "${TEMPWORKDIR}"/data
mv ./* "${SLURM_SUBMIT_DIR}"
cd "${SLURM_SUBMIT_DIR}" || exit 1
rmdir "${TEMPWORKDIR}" 2> /dev/null || echo "Leftover files on ${TEMPWORKDIR}"
[ ! -d "${TEMPWORKDIR}" ] && { [ -h JOB-"${SLURM_JOBID}" ] && rm JOB-"${SLURM_JOBID}"; }

# Done
echo "Have a nice day !"

# A small pause before SLURM savage clean-up
sleep 5
exit ${EXIT_CODE}
