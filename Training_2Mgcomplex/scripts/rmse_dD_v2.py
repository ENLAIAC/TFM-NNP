import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import sys

# Define the bins for reaction coordinate ΔD
reaction_coordinate_bins = np.arange(-2.0, 2.1, 0.1)  # bins from -2 to 2 with step 0.1
print(f"Bin structure: {reaction_coordinate_bins}")

def load_reaction_coordinates(file_path, num_atoms):
    """Load ΔD values from the 10th column, skip first two lines, repeat for each atom."""
    with open(file_path, 'r') as f:
        lines = f.readlines()[2:]  # skip header and second line
    data = np.loadtxt(lines)
    dD_per_structure = data[:, 9]  # column index 9 = 10th column
    # Repeat each structure's ΔD value num_atoms times
    return np.repeat(dD_per_structure, num_atoms)

def bin_reaction_coordinates(reaction_coordinates):
    """Assign each ΔD value to a bin index."""
    return np.digitize(reaction_coordinates, reaction_coordinate_bins) - 1

def calculate_rmse_for_bin(structures, actual_forces, predicted_forces):
    """Calculate RMSE for all atoms in a bin."""
    bin_actual_forces = actual_forces[structures]
    bin_predicted_forces = predicted_forces[structures]
    rmse = np.sqrt(np.mean((bin_predicted_forces - bin_actual_forces) ** 2))
    return rmse

def process_system(reaction_coordinates, actual_forces, predicted_forces):
    """Process the system data and return RMSE values for each ΔD bin."""
    binned_structures = bin_reaction_coordinates(reaction_coordinates)
    rmse_per_bin = []
    for bin_idx in range(len(reaction_coordinate_bins) - 1):
        atoms_in_bin = np.where(binned_structures == bin_idx)[0]
       #print(f"For bin index={bin_idx} and bin={reaction_coordinate_bins[bin_idx]}, {atoms_in_bin} is the list of atoms belonging to such bin.")
        if len(atoms_in_bin) > 0:
            rmse = calculate_rmse_for_bin(atoms_in_bin, actual_forces, predicted_forces)
        else:
            rmse = np.nan
            print(f"No atoms in bin {bin_idx}")
        rmse_per_bin.append(rmse)
    return rmse_per_bin

def plot_and_save_results(rmse_values, output_prefix):
    """Plot RMSE vs ΔD and save both PNG and TXT."""
    bin_centers = 0.5 * (reaction_coordinate_bins[:-1] + reaction_coordinate_bins[1:])
    plt.figure(figsize=(8, 6))
    plt.plot(bin_centers, rmse_values, marker='o', linestyle='-', color='b')
    plt.title("RMSE vs Reaction Coordinate ΔD")
    plt.xlabel('ΔD (Å)')
    plt.ylabel('RMSE (eV/Å)')
    plt.ylim(0, 0.1)
    plt.grid(True)
    plt.savefig(f"{output_prefix}.png", format='png')
    plt.close()

    np.savetxt(f"{output_prefix}.txt",
               np.c_[bin_centers, rmse_values],
               fmt='%e',
               header='Reaction Coordinate (ΔD)    RMSE')

def main():
    if len(sys.argv) != 5:
        print(f"Usage: python {sys.argv[0]} <reaction_coordinate_file> <forces_file> <num_atoms> <output_prefix>")
        sys.exit(1)

    rc_file = sys.argv[1]
    forces_file = sys.argv[2]
    num_atoms = int(sys.argv[3])
    output_prefix = sys.argv[4]

    # Load ΔD data, repeated for each atom
    reaction_coordinates = load_reaction_coordinates(rc_file, num_atoms)


    # Load force data (one line per atom)
    data = np.loadtxt(forces_file)
    actual_forces = data[:, :3]
    predicted_forces = data[:, 3:]
    
    # Check consistency
    if len(reaction_coordinates) != len(actual_forces):
        raise ValueError("Mismatch: number of ΔD entries does not match number of atom force lines.")

    # Compute RMSE per bin
    rmse_values = process_system(reaction_coordinates, actual_forces, predicted_forces)

    # Plot and save
    plot_and_save_results(rmse_values, output_prefix)

if __name__ == '__main__':
    main()

