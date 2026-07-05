import os
import subprocess

# Read the numbers from selected.txt into a set
with open("selected.txt") as f:
    selected = {line.strip() for line in f if line.strip()}

# Loop through the expected range
for i in range(1, 801):
    num_str = f"{i:05d}"  # zero-padded to 5 digits
    if num_str not in selected:
        folder = num_str
        job_script = f"job_script_{num_str}.sh"
        
        # Check if folder and script exist
        if os.path.isdir(folder) and os.path.isfile(os.path.join(folder, job_script)):
            print(f"Submitting {job_script} in {folder}...")
            subprocess.run(["sbatch", job_script], cwd=folder)
        else:
            print(f"⚠️  Skipping {folder} — folder or script not found.")

