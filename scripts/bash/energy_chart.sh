#!/bin/bash

HOME_DIR=$PWD
MASTER_FILE="all_energies_long.dat"

# Initialize the file with a header
echo "System Energy" > "${MASTER_FILE}"

for WORK_DIR in "${HOME_DIR}"/PPiMg2* ; do
    [ -d "${WORK_DIR}" ] || continue 
    
    SYS_NAME=$(basename "${WORK_DIR}")
    FILE_EN="${WORK_DIR}/${SYS_NAME}-Energy.en"
    
    if [ -f "${FILE_EN}" ]; then
        echo "Extracting energies from: ${SYS_NAME}"
        
        # We use awk to print the system name and the energy sum on every line
        # This creates a 'Label Value' pair for every single data point
        tr -d '\r' < "${FILE_EN}" | awk -v label="${SYS_NAME}" '
            NR > 1 && $3 ~ /^-?[0-9.]/ { 
                printf "%12s %.8f\n", label, $3+$5 
            }' >> "${MASTER_FILE}"
    else
        echo "Skip: ${SYS_NAME} (Energy file not found)"
    fi
done

echo "---"
echo "Success! Data consolidated in ${MASTER_FILE}"
