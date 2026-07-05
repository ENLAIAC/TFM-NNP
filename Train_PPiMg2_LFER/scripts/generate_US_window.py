#Done by Elia: 11/06/2026
#The idea is to generate 100 homogeneous windows to perform the US calculation. The file takes the file from the input directory, and copies it in each window directory.

from pathlib import Path
import os
import re
import sys
import shutil
import numpy as np
import random

WRK_dir = Path.cwd()
input_dir = Path(f"{WRK_dir}/inputs")
lmp_files = Path(f"{input_dir}/lmp_files")

# WHAM parameters
EQUIL_FRAMES = 100
CV_BIN_WIDTH = 0.01
MIN_CV_VALUE = -2.2
NUMBER_OF_CV_BINS = 300


def create_folders(n_window):
    min_cv =  -2.0
    max_cv =  0.3
    kappa = 300  # kcal/mol

    windows = np.linspace(min_cv, max_cv, n_window)

    COLVAR_dir = Path(f"{Path.cwd()}/COLVAR")
    COLVAR_dir.mkdir(exist_ok=True)

    for win_id in range(n_window):
        center = windows[win_id]
        new_folder = Path(f"{Path.cwd()}/{win_id:03d}")
        new_folder.mkdir(exist_ok=True)

        # --- Generate PLUMED file ---
        plumed_file = new_folder / f"plumed_USW_{win_id:03d}.dat"
        with open(f"{input_dir}/plumed_USW_XX.dat", 'r') as f:
            plumed_content = f.read()
        # Use absolute path so the file is found when LAMMPS runs in TEMPWORKDIR
        plumed_content = plumed_content.replace("../inputs/", f"{input_dir}/")
        plumed_content = plumed_content.replace("AT=XX", f"AT={center:.4f}")
        plumed_content = plumed_content.replace("XX", f"{win_id:03d}")
        plumed_content = plumed_content.replace("USDATA", f"CV{win_id + 1}")
        plumed_content = plumed_content.replace("KAPPA_kcal", str(kappa))
        with open(plumed_file, 'w') as f:
            f.write(plumed_content)

        # --- Copy LAMMPS data file ---
        lmp_conf = lmp_files / f"USW_{win_id:03d}.lmp"
        if not lmp_conf.is_file():
            raise FileNotFoundError(f"[✗] Missing LMP data file: {lmp_conf}")
        shutil.copy(str(lmp_conf), str(new_folder))

        # --- Generate LAMMPS input file ---
        with open(f"{input_dir}/US_lammps.in", "r") as f:
            lammps_content = f.read()
        lammps_content = lammps_content.replace("USW_XX", f"USW_{win_id:03d}")
        lammps_content = lammps_content.replace("LMP_FILE", f"USW_{win_id:03d}.lmp")
        lammps_content = lammps_content.replace("NNP1_path", "/gpfs/scratch/uv36/adrian/deepmd-training/Train_PPiMg2/LFER_3_mg2/NNP/graph_3_005_compressed.pb")
        lammps_content = lammps_content.replace("NNP2_path", "/gpfs/scratch/uv36/adrian/deepmd-training/Train_PPiMg2/LFER_3_mg2/NNP/graph_1_005_compressed.pb")
        lammps_content = lammps_content.replace("NNP3_path", "/gpfs/scratch/uv36/adrian/deepmd-training/Train_PPiMg2/LFER_3_mg2/NNP/graph_2_005_compressed.pb")
        rand_num = random.randint(1000000, 9999999)
        lammps_content = lammps_content.replace("RANDOM", str(rand_num))
        with open(f"{new_folder}/US_lammps.in", "w") as f:
            f.write(lammps_content)

        # --- Copy job submission script ---
        shutil.copy(
            str(input_dir / "job_lammps-deepmd.sh"),
            str(new_folder / "job_lammps-deepmd.sh")
        )

        print(f"[✓] Window {win_id:03d} set at AT={center:.4f}")

    # === Create WHAM folder and input file ===
    WHAM_gen_dir= Path(f"{Path.cwd().parent.parent}/WHAM_files")
    WHAM_dir = Path(f"{Path.cwd()}/WHAM")
    WHAM_dir.mkdir(exist_ok=True)
    wham_job= WHAM_gen_dir / "job_wham.sh"
    shutil.copy(str(wham_job), str(WHAM_dir))
    wham_input = WHAM_dir / "input.txt"
    with open(wham_input, "w") as f:
        f.write(f"# {EQUIL_FRAMES} {CV_BIN_WIDTH} {MIN_CV_VALUE} {NUMBER_OF_CV_BINS}\n")
        for i, center in enumerate(windows, start=1):
            f.write(f"../COLVAR/CV{i} {center:.4f} {kappa}\n")
    print(f"[✓] WHAM input written to {wham_input}")


def main():
    if len(sys.argv) < 1:
        print("Usage: python generate_US_window.py <number_of_windows> ")
        sys.exit(1)

    create_folders(int(sys.argv[1]))


if __name__ == "__main__":
    main()
