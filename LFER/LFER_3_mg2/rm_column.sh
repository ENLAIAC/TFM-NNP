#!/bin/bash

# Loop from 0 to 99
for i in {0..99}; do
    # Format the current number as a 3-digit zero-padded string (000, 001, ..., 099)
    file_num=$((i + 1))
    file_path="CV${file_num}"

    # Check if the file exists to avoid errors
    if [ -f "$file_path" ]; then
        # Use awk to remove the 2nd column.
        # This loops through all columns and prints everything EXCEPT column 2.
        awk '{
            for(j=1; j<=NF; j++) {
                if(j!=2) {
                    # Print the column and follow it with a space (OFS) or a newline (ORS)
                    printf "%s%s", $j, (j==NF ? ORS : OFS)
                }
            }
        }' "$file_path" > "${file_path}.tmp"

        # Overwrite the original file with the modified temporary file
        mv "${file_path}.tmp" "$file_path"

        echo "Successfully processed: $file_path"
    else
        echo "Skipped: $file_path (File not found)"
    fi
done
