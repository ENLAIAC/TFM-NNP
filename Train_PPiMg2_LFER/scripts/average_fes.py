import numpy as np
import os

# Folders to process
folders = ['rep_1', 'rep_2','rep_3']

# List to store FES data arrays
fes_list = []

# Load data
for folder in folders:
    file_path = os.path.join(folder, 'fes-rew.dat')
    if os.path.exists(file_path):
        data = np.loadtxt(file_path)
        fes_list.append(data)
        print(f"Loaded {file_path}")
    else:
        raise FileNotFoundError(f"{file_path} not found!")

# Check if all files have the same shape
shapes = [fes.shape for fes in fes_list]
if not all(shape == shapes[0] for shape in shapes):
    raise ValueError("FES files do not have matching bin grids!")

# Stack all FES data for averaging
fes_stack = np.stack(fes_list)  # shape: (4, N, 3)

# Average the free energy (3rd column, index 2)
avg_bins_y = fes_stack[0,:,0]  # Y-axis bin centers
avg_bins_x = fes_stack[0,:,1]  # X-axis bin centers
avg_fes = np.mean(fes_stack[:,:,2], axis=0)  # Average over the 4 datasets

# Combine for output
averaged_data = np.column_stack((avg_bins_y, avg_bins_x, avg_fes))

# Save result
output_file = 'fes-rew.dat'
np.savetxt(output_file, averaged_data, fmt='%.6f')

print(f"Averaged FES written to {output_file}")
