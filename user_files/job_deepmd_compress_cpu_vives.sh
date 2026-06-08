#!/bin/bash
#----------------------------------------------------------------------------------------------------#
#   ArcaNN: Automatic training of Reactive Chemical Architecture with Neural Networks                #
#   Copyright 2023 ArcaNN developers group <https://github.com/arcann-chem>                          #
#                                                                                                    #
#   SPDX-License-Identifier: AGPL-3.0-only                                                           #
#----------------------------------------------------------------------------------------------------#
# Created: 2022/01/01
# Last modified: 2023/09/06
# Project/Account
#-SBATCH --account=_R_PROJECT_@_R_ALLOC_
# QoS/Partition/SubPartition
#-SBATCH --qos=thin_emedio
#-SBATCH --partition=emedio
#-SBATCH -C _R_SUBPARTITION_
# Number of Nodes/MPIperNodes/OpenMPperMPI/GPU
#SBATCH --ntasks-per-node 1
#SBATCH --cpus-per-task 4
# Walltime
#SBATCH -t _R_WALLTIME_
# Merge Output/Error
#SBATCH -o DeepMD_Compress.%j
#SBATCH -e DeepMD_Compress.%j
# Name of job
#SBATCH -J DeepMD_Compress
# Email
#-SBATCH --mail-type FAIL,BEGIN,END,ALL
#-SBATCH --mail-user _R_EMAIL_
#
#SBATCH --exclude=t[155-156]

# Input files
DeepMD_MODEL_VERSION="_R_DEEPMD_VERSION_"
DeepMD_MODEL_FILE="_R_DEEPMD_MODEL_FILE_"
DeepMD_COMPRESSED_MODEL_FILE="_R_DEEPMD_COMPRESSED_MODEL_FILE_"
DeepMD_LOG_FILE="_R_DEEPMD_LOG_FILE_"
DeepMD_OUT_FILE="_R_DEEPMD_OUTPUT_FILE_"

#----------------------------------------------
# Nothing needed to be changed past this point

#Adrian: Comment weird stuff below and write my own definition of scratch
# Project Switch and update SCRATCH
#PROJECT_NAME=${SLURM_JOB_ACCOUNT:0:3}
#eval "$(idrenv -d "${PROJECT_NAME}")"
# Compare PROJECT_NAME and IDRPROJ for inequality
#if [[ "${PROJECT_NAME}" != "${IDRPROJ}" ]]; then
#    SCRATCH=${SCRATCH/${IDRPROJ}/${PROJECT_NAME}}
#fi
SCRATCH=/storage/scratch/lv87/lv87908/job_dir #Elia's scratch folder path

# Go where the job has been launched
cd "${SLURM_SUBMIT_DIR}" || { echo "Could not go to ${SLURM_SUBMIT_DIR}. Aborting..."; exit 1; }

# Load the environment depending on the version
if [ "${SLURM_JOB_QOS}" == "thin" ]; then
    if [ "${DeepMD_MODEL_VERSION}" == "2.1" ]; then
        module purge
    . /storage/scratch/lv87/lv87680/toolbox/deepmd-kit-cpu/etc/profile.d/conda.sh #Adrian: Changed jz instalation by vives instalation
        conda activate /storage/scratch/lv87/lv87680/toolbox/deepmd-kit-cpu  
        log="--log-path ${DeepMD_LOG_FILE}"
    else
        echo "DeePMD ${DeepMD_MODEL_VERSION} is not installed on ${SLURM_JOB_QOS}. Aborting..."; exit 1
    fi
elif [ "${SLURM_JOB_QOS:3:4}" == "cpu" ]; then
    echo "GPU on a CPU partition?? Aborting..."; exit 1
else
    echo "There is no ${SLURM_JOB_QOS}. Aborting..."; exit 1
fi
DeepMD_EXE=$(command -v dp) ||  ( echo "Executable (dp) not found. Aborting..."; exit 1 )

# Test if input file is present
[ -f ${DeepMD_MODEL_FILE} ] || { echo "${DeepMD_MODEL_FILE} does not exist. Aborting..."; exit 1; }

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

# Launch command #Adrian: Deleted --nodes=${SLURM_NNODES}
SRUN_DeepMD_EXE="srun --export=ALL --mpi=pmix --ntasks=${SLURM_NTASKS} --ntasks-per-node=${SLURM_NTASKS_PER_NODE} --cpus-per-task=${SLURM_CPUS_PER_TASK} ${DeepMD_EXE}"
LAUNCH_CMD="${SRUN_DeepMD_EXE} compress -i ${DeepMD_MODEL_FILE} -o ${DeepMD_COMPRESSED_MODEL_FILE} ${log}"

${LAUNCH_CMD} >"${DeepMD_OUT_FILE}" 2>&1 || export EXIT_CODE="1"
echo "# [$(date)] Ended"

if [ -f compress.json ]; then rm compress.json; fi

# Done
echo "Have a nice day !"

# A small pause before SLURM savage clean-up
sleep 5
exit ${EXIT_CODE}
