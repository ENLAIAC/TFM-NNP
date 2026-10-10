#!/bin/bash
for i in {1..100}; do	
    file_path="CV${i}"

    tail -n 8002 "CV${i}_thin" > "CV${i}"
    if [ -f "${file_path}" ]; then
        awk '{print $1, $2, $NF}' "${file_path}" > "${file_path}.tmp" \
            && mv "${file_path}.tmp" "$file_path"
        echo "Processed: $file_path"
    else
        echo "Skipped: $file_path (not found)"
    fi
done
