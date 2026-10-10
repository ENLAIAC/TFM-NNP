#!/bin/bash

TMP_FILE="temp"

for i in $(seq 1 100); do
	head -n 8002 "CV${i}" > "${TMP_FILE}"
	mv "${TMP_FILE}" "CV${i}"
done
