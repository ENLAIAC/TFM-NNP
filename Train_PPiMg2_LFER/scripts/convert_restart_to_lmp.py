import os
import subprocess
from pathlib import Path
import re
import csv
import numpy as np
import sys

# Settings
lmp_exec = "lmp_mpi"  # Your LAMMPS executable
restart_pattern = "pph4-react-TS1.restart.*"
output_folder = Path("lmp_files")
output_folder.mkdir(exist_ok=True)
metadata_path = output_folder / "metadata.csv"
COLVAR_file="COLVAR" #Adapt to your file containing the collective variables
CV="dD" #To change according to the CV that will be sammpled in the US

# Get and sort restart files by timestep
def extract_timestep(filename):
    match = re.search(r"pph4-react-TS1\.restart\.(\d+)", filename)
    return int(match.group(1)) if match else float("inf")

restart_files = sorted(Path(".").glob(restart_pattern), key=lambda f: extract_timestep(f.name))
if not restart_files:
    raise FileNotFoundError("No restart files found matching pattern pph4-react-TS1*.restart")

with open(COLVAR_file, "r") as f:
    cv_index=f.readline().split().index(CV)-2

cv=np.loadtxt(COLVAR_file,skiprows=1)[:,cv_index]

# Open CSV log file
with open(metadata_path, "w", newline="") as metafile:
    writer = csv.writer(metafile)
    writer.writerow(["lmp_file_name", "restart_file_name", "timestep", f"{CV}"])

    # Process each restart
    for idx, rfile, cobh in zip(range(len(restart_files)),restart_files,cv):
        restart_name = rfile.name
        timestep = extract_timestep(restart_name)
        lmp_filename = f"USW_{idx:03d}.lmp"
        input_filename = f"convert_{idx:03d}.in"

        # Write temporary LAMMPS input
        with open(input_filename, "w") as f:
            f.write(f"""clear
units metal
atom_style atomic

read_restart {restart_name}

pair_style deepmd /gpfs/scratch/uv36/adrian/deepmd-training/Train_PPiMg2/LFER_3_mg2/NNP/graph_3_005_compressed.pb /gpfs/scratch/uv36/adrian/deepmd-training/Train_PPiMg2/LFER_3_mg2/NNP/graph_1_005_compressed.pb /gpfs/scratch/uv36/adrian/deepmd-training/Train_PPiMg2/LFER_3_mg2/NNP/graph_2_005_compressed.pb out_freq 100 out_file model_devi_pyro.out
pair_coeff * *
write_data {output_folder / lmp_filename}
""")

        # Run LAMMPS
        print(f"Converting {restart_name} to {output_folder / lmp_filename}")
        subprocess.run([lmp_exec, "-in", input_filename], check=True)

        # Log metadata
        writer.writerow([lmp_filename, restart_name, timestep, -cv[idx]])

        # Clean up
        os.remove(input_filename)

print(f"✅ All restart files converted and logged to '{metadata_path}'")

