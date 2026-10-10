#!/bin/bash

HERE=$PWD

for folder in "rep_1/pph3-included" "rep_2/pph3-included" "rep_3/pph3-included" ; do
    echo "Processing folder: $folder"
    if [[ ! -f "$folder/KERNELS" ]]; then
        echo "Warning: KERNELS file not found in $folder. Skipping."
        continue
    fi

    sigma_value=$(awk '{print $6}' "$folder/KERNELS" | tail -n 1)

    if [[ -z "$sigma_value" ]]; then
        echo "Warning: No sigma value found in $folder/KERNELS. Skipping."
        continue
    fi

    echo "Sigma value for $folder: $sigma_value"

    cd "$folder"

    # Create COLVAR_mod
    if [[ ! -f COLVAR ]]; then
        echo "Warning: COLVAR file not found in $folder. Skipping."
        cd ..
        continue
    fi

    echo "Modifying COLVAR into COLVAR_mod..."
    awk '
    BEGIN {dC_col=0; dD_col=0}
    NR==1 {
        for (i=3; i<=NF; i++) {
            if ($i == "dC") dC_col=i
            if ($i == "dD") dD_col=i
        }
        if (dC_col == 0 || dD_col == 0) {
            print "Error: dC or dD column not found in header."
            exit 1
        }
        print $0, "dCi", "dDi"
        dC_col -= 2; dD_col -= 2  # Adjust for data row indexing
        next
    }
    {
        print $0, -$dC_col, -$dD_col
    }' COLVAR > COLVAR_mod

    echo "Created COLVAR_mod with inverted dC and dD."

    echo "Running FES_from_Reweighting.py in $folder..."
    python ../../../codes/FES_from_Reweighting.py \
        --sigma "${sigma_value},${sigma_value}" \
        --cv 15,16 \
        --temp 298.15 \
        --max 2.5,2.4 \
        --min=-1.5,-2.4 \
        --bin 150,150 \
        --blocks 2 \
        --colvar COLVAR_mod || { echo "Error running FES_from_Reweighting.py in $folder"; exit 1; }
    echo "Finished FES_from_Reweighting.py in $folder."

    cd $HERE

    echo "Completed processing $folder."
    echo "-----------------------------------"
done

echo "All folders processed!"
