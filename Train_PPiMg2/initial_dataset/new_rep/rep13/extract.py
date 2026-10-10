#Done by Elia - date: 17/05/2026

import numpy as np
import os
import sys
from pathlib import Path

trj_file="rep13-Trajectory.xyz"


#updates the debug 
def debug(message:str,filename:str="debug.txt"): 
    with open(filename, 'a') as deb:
        deb.write(f"{message}")

def get_int_input(atoms):
    try:
        if (atoms>0):
            debug(f"STEP - Found {atoms} atoms. Proceed to extract the analyze the '.xyz' file\n")
            return atoms
        else:
            debug(f"WARNING:{atoms} is not a valid number of atoms. Provide positive quantity\n")
            sys.exit(1)
    except:
        debug(f"WARNING: {atoms} is not a number. Provide a positive number of atoms\n")

def extract_xyz(xyz_file_path:str):
    # Check whether the file exists, if not it prints a warning messa in the debug file
    filename=Path(xyz_file_path)
    if not filename.is_file():
        debug(f"FILE NOT FOUND - {xyz_file_path} doesn't exists\n")
        sys.exit(1)
    else:
        debug(f"STEP - Loading {xyz_file_path}\n")
    
    #Opens the coordinate file and extract the lines
    with open(filename,'r') as geom_xyz:
        lines=geom_xyz.readlines()
        if (len(lines)==0):
            debug(f"WARNING - {filename} file is empty. Check it manually\n")
            sys.exit(1)
        else:
            return lines

#Computes the amount of configurations and checks whether the amount of lines in the coordinate file matches
def configurations(coordinates:list, natoms:int):
    if (len(coordinates)%(natoms+2)!=0):
        debug(f"WARNING - Coordinate amount mismatch. nlines/natoms={len(coordinates)/(natoms+2)} is not a INTEGER number\n")
        sys.exit(1)
    else:
        n_config = len(coordinates) // (natoms+2)
        debug(f"STEP - Found {n_config} configurations. Proceeding to extract and generate the '.xyz' files\n")
        return n_config

# Generates the file in the configuration directory
def generate_xyz_file(coordinates:list,natoms:int,n_config:int):
    base=Path('./configurations')
    for config in range(0,n_config,9):
        filename= f"./{trj_file}"
        debug(f"EXTRACTION - Configuration number: {config}\n")
        with open(filename,'a') as iter_file:
            iter_coord=coordinates[config*(natoms+2):(config+1)*(natoms+2)]
            iter_file.writelines(iter_coord)
        debug(f"INFO - Extraction of configuration {config} succesfully achieved\n")

def main():

    # Checking whether the correct amount of arguments have been passed. If not an information message is printed
    if len(sys.argv) != 3:
            print(f"Usage: <python_cmd> extract.py <coordinate_file_path> <number of atoms>")
            sys.exit(1)

    os.system("rm -f debug.txt")
    # Taking the number of atoms from input as first argument after the executable command
    natoms=get_int_input(int(sys.argv[2]))

    coordinates=extract_xyz(sys.argv[1])

    # Creating the configurations directory where the optimization iteration xyz file will be saved
    os.system("mkdir -p configurations")
    os.system("rm -f ./configurations/*")
    os.system(f"touch {trj_file}")

    # Computing the number of configurations
    n_config=configurations(coordinates,natoms)

    #Running through configurations, printing them and saving the files 
    generate_xyz_file(coordinates,natoms,n_config)

    debug("Extraction procedure completed")
    print(f"Extraction procedure completed.\nHave a good day!")

if __name__ == "__main__":
    main()        
