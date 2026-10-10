#!/bin/bash

# Usage: ./grep_energy.sh <cp2k_output_file>
# Extracts the Total energy from CP2K output after outer SCF convergence

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <cp2k_output_file>"
    exit 1
fi

FILE="$1"

if [[ ! -f "$FILE" ]]; then
    echo "Error: File '$FILE' not found."
    exit 1
fi

# Look backwards from "outer SCF loop converged" to find the nearest "Total energy:"
energy=$(awk '
    /Total energy:/ { last_energy = $NF }
    /outer SCF loop converged/ { print last_energy }
' "$FILE")

if [[ -z "$energy" ]]; then
    echo "No converged outer SCF energy found in '$FILE'."
    exit 1
fi

echo "$energy"
