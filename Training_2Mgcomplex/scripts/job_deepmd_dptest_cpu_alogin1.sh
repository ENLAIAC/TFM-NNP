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
#SBATCH --account=uv36
# QoS/Partition/SubPartition
#SBATCH --qos=acc_interactive
#SBATCH --partition=acc
# Number of Nodes/MPIperNodes/OpenMPperMPI/GPU
#SBATCH --ntasks-per-node 1
#SBATCH --cpus-per-task 1
# Walltime
#-SBATCH -t 01:00:00
# Merge Output/Error
#SBATCH --output=dptest_output.txt
#SBATCH -e DeepMD_Test.%j
# Name of job
#SBATCH -J DeepMD_Test
# Email
#SBATCH --mail-type FAIL,BEGIN,END,ALL
#-SBATCH --mail-user _R_EMAIL_
#

DeepMD_MODEL_VERSION="2.2"
DeepMD_MODEL_FILE="/gpfs/scratch/uv36/elia/Training_2Mgcomplex/validation_set/NNP/graph_1_005_compressed.pb"

# Go where the job has been launched
cd "${SLURM_SUBMIT_DIR}" || { echo "Could not go to ${SLURM_SUBMIT_DIR}. Aborting..."; exit 1; }

# Check
[ -f ${DeepMD_MODEL_FILE} ] || { echo "${DeepMD_MODEL_FILE} does not exist. Aborting..."; exit 1; }

# Example to use the DeepMD_MODEL_VERSION variable
if [ ${DeepMD_MODEL_VERSION} == "2.2" ]; then
	module purge
        module load cuda/12.3 cudnn/9.6.0-cuda12 openmpi/4.1.5-gcc fftw/3.3.10-gcc-ompi miniforge/24.3.0-0 gsl/2.8-gcc deepmd-kit/2.2.9-plumed-gcc-ompi
else
    echo "DeepMD version ${DeepMD_MODEL_VERSION} is not available. Aborting..."; exit 1
fi

# Run the DeepMD test
echo "# [$(date)] Running DeepMD test..."
dataset="../03_dataset"
if [[ -d "${dataset}" ]]; then
	dataset_name=validation_set_pp
        echo "Processing dataset: ${dataset_name}"
        dp test -m ${DeepMD_MODEL_FILE} -s "${dataset}" -n 800 -d "${dataset_name}"
        grep 'DEEPMD INFO' "${dataset_name}.out" > "${dataset_name}.log"
        echo "Done processing dataset: ${dataset_name}"
    fi
echo "# [$(date)] DeepMD test finished."

sleep 2
exit
