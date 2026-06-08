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
# You must keep the name file as job_deepmd_test_ARCHTYPE_myHPCkeyword.sh.
#----------------------------------------------
# Project/Account
#SBATCH --account=_R_PROJECT_@_R_ALLOC_
# QoS/Partition/SubPartition
#SBATCH --qos=_R_QOS_
#SBATCH --partition=_R_PARTITION_
#SBATCH -C _R_SUBPARTITION_
# Number of Nodes/MPIperNodes/OpenMPperMPI/GPU
#-SBATCH --nodes 1
#SBATCH --ntasks_per_node 1  !!! IN MARENOSTRUM THEY ASK FOR THE NTASK SPECIFICATION MANDATORY
#SBATCH --cpus-per-task 4
# Walltime
#SBATCH -t _R_WALLTIME_
# Merge Output/Error
#SBATCH --output=dptest_output.txt
#SBATCH -e DeepMD_Test.%j
# Name of job
#SBATCH -J DeepMD_Test
# Email
#SBATCH --mail-type FAIL,BEGIN,END,ALL
#SBATCH --mail-user _R_EMAIL_
#

DeepMD_MODEL_VERSION="_R_DEEPMD_VERSION_"
DeepMD_MODEL_FILE="_R_DEEPMD_MODEL_FILE_"

#----------------------------------------------
# Adapt the following lines to your HPC system
#----------------------------------------------

# Go where the job has been launched
cd "${SLURM_SUBMIT_DIR}" || { echo "Could not go to ${SLURM_SUBMIT_DIR}. Aborting..."; exit 1; }

# Check
[ -f ${DeepMD_MODEL_FILE} ] || { echo "${DeepMD_MODEL_FILE} does not exist. Aborting..."; exit 1; }

# Example to use the DeepMD_MODEL_VERSION variable
if [ ${DeepMD_MODEL_VERSION} == "2.2" ]; then
	module purge
        module load deepmd-kit/2.2.9-plumed-gcc-ompi
else
    echo "DeepMD version ${DeepMD_MODEL_VERSION} is not available. Aborting..."; exit 1
fi

# Run the DeepMD test
echo "# [$(date)] Running DeepMD test..."
for dataset in data/*/ ; do
    if [[ -d "${dataset%/}" ]]; then
        dataset_name=$(basename "${dataset%/}")
        echo "Processing dataset: ${dataset_name}"
        dp test -m ${DeepMD_MODEL_FILE} -s "${dataset%/}" -d "${dataset_name}" -n 100000000 > "${dataset_name}.out" 2>&1
        grep 'DEEPMD INFO' "${dataset_name}.out" > "${dataset_name}.log"
        echo "Done processing dataset: ${dataset_name}"
    fi
done
echo "# [$(date)] DeepMD test finished."

sleep 2
exit
