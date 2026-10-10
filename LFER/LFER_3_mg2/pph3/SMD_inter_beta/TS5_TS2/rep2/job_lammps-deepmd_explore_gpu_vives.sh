#!/bin/bash
#----------------------------------------------------------------------------------------------------#
#   ArcaNN: Automatic training of Reactive Chemical Architecture with Neural Networks                #
#   Copyright 2023 ArcaNN developers group <https://github.com/arcann-chem>                          #
#                                                                                                    #
#   SPDX-License-Identifier: AGPL-3.0-only                                                           #
#----------------------------------------------------------------------------------------------------#
# QoS/Partition/SubPartition
#SBATCH --qos=cuerda
#SBATCH --partition=cuerda
# Number of Nodes/MPIperNodes/OpenMPperMPI/GPU
#SBATCH --nodes 1
#SBATCH --ntasks-per-node 1
#SBATCH --cpus-per-task 8
#SBATCH --gres=gpu:1
#SBATCH --hint=nomultithread
# Walltime
#SBATCH -t 01:00:00
# Merge Output/Error
#SBATCH -o LAMMPS_DeepMD.%j
#SBATCH -e LAMMPS_DeepMD.%j
# Name of job
#SBATCH -J LAMMPS_DeepMD

SYSTEM="SMD_pph3-rep2"
DeepMD_MODEL_VERSION="2.1"
DeepMD_MODEL=("/storage/scratch/lv87/lv87908/DeepMD_pyro/LFER/NNP/graph_3_005_compressed.pb" "/storage/scratch/lv87/lv87908/DeepMD_pyro/LFER/NNP/graph_1_005_compressed.pb" "/storage/scratch/lv87/lv87908/DeepMD_pyro/LFER/NNP/graph_2_005_compressed.pb")
LAMMPS_IN_FILE="${SYSTEM}.in"
LAMMPS_LOG_FILE="${SYSTEM}.log"
LAMMPS_OUT_FILE="${SYSTEM}.out"
EXTRA_FILES=("TS5_rep2.lmp" "plumed_${SYSTEM}.dat" "${SYSTEM}.restart")

#----------------------------------------------
# Nothing needed to be changed past this point

SCRATCH=/storage/scratch/lv87/lv87908/DeepMD_pyro/JOBS

# Go where the job has been launched
cd "${SLURM_SUBMIT_DIR}" || exit 1

# Load the environment depending on the version
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
ln -s "${TEMPWORKDIR}" "${SLURM_SUBMIT_DIR}"/JOB-"${SLURM_JOBID}"

# Copy files to the temporary work directory
cp "${LAMMPS_IN_FILE}" "${TEMPWORKDIR}" && echo "${LAMMPS_IN_FILE} copied successfully"
cp "${LAMMPS_IN_FILE}" "${LAMMPS_IN_FILE}"."${SLURM_JOBID}"
for f in "${EXTRA_FILES[@]}"; do [ -f "${f}" ] && cp "${f}" "${TEMPWORKDIR}" && echo "${f} copied successfully"; done
for f in "${DeepMD_MODEL[@]}"; do [ -f "${f}" ] && ln -s "$(realpath "${f}")" "${TEMPWORKDIR}" && echo "${f} linked successfully"; done
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
SRUN_LAMMPS_EXE="srun --ntasks=${SLURM_NTASKS} --nodes=${SLURM_NNODES} --ntasks-per-node=${SLURM_NTASKS_PER_NODE} --cpus-per-task=${SLURM_CPUS_PER_TASK} ${LAMMPS_EXE}"
LAUNCH_CMD="${SRUN_LAMMPS_EXE} -in ${LAMMPS_IN_FILE} -log ${LAMMPS_LOG_FILE} -screen none"

echo "${LAUNCH_CMD}"
${LAUNCH_CMD} || export EXIT_CODE="1"
echo "# [$(date)] Ended"

# Move back data from the temporary work directory and scratch, and clean-up
if [ -f log.cite ]; then rm log.cite ; fi
find ./ -type l -delete
mv ./* "${SLURM_SUBMIT_DIR}"
cd "${SLURM_SUBMIT_DIR}" || exit 1
rmdir "${TEMPWORKDIR}" 2> /dev/null || echo "Leftover files on ${TEMPWORKDIR}"
[ ! -d "${TEMPWORKDIR}" ] && { [ -h JOB-"${SLURM_JOBID}" ] && rm JOB-"${SLURM_JOBID}"; }
rm "${LAMMPS_IN_FILE}"."${SLURM_JOBID}"

# Done
echo "Have a nice day !"

# A small pause before SLURM savage clean-up
sleep 5
exit ${EXIT_CODE}
