#!/bin/bash
#SBATCH --job-name=conv-TS1_TS3
#SBATCH --account=uv01
#SBATCH --qos=acc_resa
#SBATCH --partition=acc
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=20
#SBATCH --time=02:00:00

HERE=$PWD

module purge
module load cuda/12.3 cudnn/9.6.0-cuda12 openmpi/4.1.5-gcc fftw/3.3.10-gcc-ompi miniforge/24.3.0-0 gsl/2.8-gcc deepmd-kit/2.2.9-plumed-gcc-ompi

for dir in *; do
	if [ -d $dir ]; then
		sed -e "s/_REPLICA_/$(basename $dir)/g" convert_restart_to_lmp.py > "$dir/convert_restart_to_lmp.py"
	fi
        cd $dir
	python3 convert_restart_to_lmp.py
	cd $HERE
done

