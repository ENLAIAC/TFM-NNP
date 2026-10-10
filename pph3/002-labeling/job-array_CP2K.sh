#!/bin/bash
#Run on tirant
# Project
# QoS and Partition
#SBATCH --qos=class_t
# Directives
#SBATCH --nodes 1 
#SBATCH --ntasks 48
#SBATCH --cpus-per-task 1
# Time option
#SBATCH -t 01:00:00
# Project Name
#SBATCH -J CP2K_validation
# ERRORS AND LOG
#SBATCH -o CP2K.%A_%a
#SBATCH -e CP2K.%A_%a
# E-MAIL
#SBATCH --mail-type FAIL,BEGIN,END,ALL
#SBATCH --mail-user=elia.cazzanti@studenti.unipg.it
# Array
#SBATCH --array=600-800%10

ulimit -s unlimited
module purge
module load oneapi/2025.1.3 mpi/2021.15 cp2k/2025.2

DIR=$( printf "%05d" ${SLURM_ARRAY_TASK_ID} )

echo ${DIR}

echo "Submission of work ${DIR}"
cd ${DIR}
./"job_script_"${DIR}".sh" || ( echo "JOB_${SLURM_JOBID}_${SLURM_ARRAY_TASK_ID} not submitted"; touch skip )

echo "Have a good day!"
