import os
import sys
import numpy as np

#Atom types dictionary
atom_types = {'H': '0', 'O': '1', 'Mg': '2', 'P': '3'}
#Name of the system
sys_name=os.sys.argv[1]

#Some conversion factors
au_to_ang=0.5291772109
au_to_eV=27.211386246
#au_to_ang=1
#au_to_eV=1
au_to_force=au_to_eV/au_to_ang


#Function to read number of atoms and coordinates from xyz file
def make_array(f):
    with open(f,'r') as i_f:      #Open the xyz file in read mode
        L = i_f.readlines()       #Reads all lines from the xyz file and store them in a list L
    n_at = int(L.pop(0))          #Remove the first element of the list L and converts it to integer. That is the number of atoms.
    #Array of size (n_at,4) stores the coordinates of the systems. The variable j goes over every column (atom type and xyz coordinates)
    #using split to store each value separately. The variable i goes over every line, skipping the header of the xyz file.
    coords = np.asarray([[L[i].split()[j] for j in range(1,4)] for i in range(1,n_at+1)])
    #The xyz coordinates of each atom are concatenated (" " is the separator) in a list of strings. That list of string is then concatenated into a single string (text_coord)
    text_coord = " ".join([" ".join(coords[i]) for i in range(n_at)])
    #Output of the make_array function
    return (n_at, text_coord)

#Retrieves command-line argument 1, asigning it to variable folder
folder=os.sys.argv[1]
print(f"Folder: {folder}")
#The number of the configurations that will be used for the training are stored in file "selected.txt"
with open("selected_configurations.txt", "r") as conv_conf:
    list_conf=conv_conf.readlines()
#"Origin" variable stores the current working directory
origin=os.getcwd()
#Changes current directory to "folder" directory
os.chdir(folder)
#Initialization of empty strings
text_coord=""
text_box=""
text_energy=""
text_force=""
atom_type_line=""

for dir_path in list_conf:
    config_path=dir_path.split('\n')[0]
    print(config_path)
    #Changes directory to the subdirectory of each configuration
    os.chdir(config_path)
    print(f"Working on {config_path} directory")
    config_path=config_path.split("/")[-1]
    #Sends xyz file of the current configuration to the make_array function. This I need to change to my personal input file naming
    nb_atoms, frame_text = make_array(f"labeling_{config_path}.xyz")
    #The concatenated coordinates of the current configuration are stored in text_coord. The next configuration is stored in the next line.
    text_coord+=frame_text+"\n"
    #The box size of the current configuration is stored in the same way
    text_box+="17.200 0.000 0.000 0.000 17.200 0.000 0.000 0.000 17.200\n"
    #Reading the output energy and force
    with open (f"2_labeling_{config_path}-Force_Eval.fe") as e_out:
        e_out.readline()
        line=e_out.readline()
        text_energy+=str(float(line.split()[8])*au_to_eV)+"\n"
    with open (f"2_labeling_{config_path}-Forces.for") as f_out:
        f_out.readline()
        f_out.readline()
        f_out.readline()
        f_out.readline()
        forces=[]
        for i in range(nb_atoms):
            line=f_out.readline()
            line_split=line.split()[3:]
            for val in line_split:
                forces.append(str(float(val)*au_to_force))
        text_force+=" ".join(forces)+"\n"
    os.chdir("..")

#Export atom types
with open(sys_name+"/00001/labeling_00001.xyz") as xyz_file:
    atom_type_line = " ".join([atom_types[line.split()[0]] for line in xyz_file.readlines()[2:]]) + "\n"


os.chdir(origin)
with open("coord.raw","a") as f:
    f.write(text_coord)
with open("box.raw","a") as f:
    f.write(text_box)
with open("energy.raw","a") as f:
    f.write(text_energy)
with open("force.raw","a") as f:
    f.write(text_force)
with open("type.raw", "w") as f:
    f.write(atom_type_line)


