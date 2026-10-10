import numpy as np
import os
import shutil
import random

# Settings
n_windows = 100
start = -2.0
end = 2.0

EQUIL_FRAMES = 100
CV_BIN_WIDTH = 0.01
MIN_CV_VALUE = -2.1
NUMBER_OF_CV_BINS = 220
kappa = 300  # in kcal/mol

centers = np.linspace(start, end, n_windows)

plumed_template = "inputs/plumed_USW_XX.dat"
lammps_template = "inputs/US_lammps.in"
LMP_FILE= "../inputs/ppmg_r_1.lmp"

os.makedirs("COLVAR", exist_ok=True)

for i, center in enumerate(centers):
    win_id = f"{i:03d}"
    prev_id = f"{i-1:03d}" if i > 0 else None
    folder = win_id
    os.makedirs(folder, exist_ok=True)

    # --- Generate PLUMED file ---
    with open(plumed_template, "r") as f:
        plumed_contents = f.read()
    plumed_contents = plumed_contents.replace("AT=XX", f"AT={center:.4f}")
    plumed_contents = plumed_contents.replace("XX", win_id)
    plumed_contents = plumed_contents.replace("USDATA", f"CV{i+1}")
    plumed_contents = plumed_contents.replace("KAPPA_kcal", f"{kappa}")
    plumed_out = os.path.join(folder, f"plumed_USW_{win_id}.dat")
    with open(plumed_out, "w") as f:
        f.write(plumed_contents)

    # --- Generate LAMMPS input file ---
    with open(lammps_template, "r") as f:
        lammps_contents = f.read()

    # Replace all occurrences of XX with current win_id
    lammps_contents = lammps_contents.replace("USW_XX", f"USW_{win_id}")

    # Path to unique LMP file for this window
    lmp_file_path = os.path.join("lmp_files", f"USW_{win_id}.lmp")
    if not os.path.isfile(f'inputs/{lmp_file_path}'):
        raise FileNotFoundError(f"[✗] Missing LMP file: {lmp_file_path}")
    lammps_contents = lammps_contents.replace("LMP_FILE", lmp_file_path)

    # Random seed for each window
    rand_num = random.randint(1000000, 9999999)
    lammps_contents = lammps_contents.replace("RANDOM", str(rand_num))

    lammps_out = os.path.join(folder, "US_lammps.in")
    with open(lammps_out, "w") as f:
        f.write(lammps_contents)

    # Copy job submission script
    shutil.copy("inputs/job_lammps-deepmd.sh", os.path.join(folder, "job_lammps-deepmd.sh"))        

    print(f"[✓] Window {win_id} set at AT={center:.4f}")


# WHAM input files

# === Create WHAM folder ===
os.makedirs("WHAM", exist_ok=True)
# === Write WHAM input file ===

wham_file_path = os.path.join("WHAM", "input.txt")
with open(wham_file_path, "w") as f:
    # Write header line
    f.write(f"# {EQUIL_FRAMES} {CV_BIN_WIDTH} {MIN_CV_VALUE} {NUMBER_OF_CV_BINS}\n")
    # Write data lines
    for i, center in enumerate(centers, start=1):
        cv_path = f"../COLVAR/CV{i}"
        f.write(f"{cv_path} {center:.4f} {kappa}\n")
