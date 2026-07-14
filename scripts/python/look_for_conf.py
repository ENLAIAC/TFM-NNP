import  os
import sys
import numpy as np
from pathlib import Path
import argparse

OPERATIONS = {
        'lt' : np.less,
        'gt' : np.greater,
        'le' : np.less_equal,
        'ge' : np.greater_equal,
        'eq' : np.equal
        }

parser=argparse.ArgumentParser(description='Select the CV and their values to extract configurations from the COLVAR file',formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('--file', '-f', dest='COLVAR', type=str, default="COLVAR", help='Provide the name of the file to look through')
parser.add_argument('--colvar', '-cv', dest='cv', nargs='+', type=str, help='Provide a list of the collective variable to filter the selection')
parser.add_argument('--threshold','-t', dest='values', nargs='+', type=float, help='Provide a list of the values associated to the CVs. The order must be consistent with the \'--colvar\' argument specification')
parser.add_argument('--instruction', '-i', dest='instructions', nargs='+', type=str, 
        help="Provide the kind of condition the thresholds should among the following:\n -\'lt\': lower than" 
                                                                                      "\n -\'le\':lower equal"
                                                                                      "\n -\'gt\': greater than"
                                                                                      "\n -\'ge\': greater equal"
                                                                                      "\n -\'eq\': equal" )
args=parser.parse_args() 
COLVAR_file=args.COLVAR
CV=args.cv
values=args.values
operations=args.instructions


def idx_search(cv:list=CV):
    with open (COLVAR_file, "r") as file:
        fields=file.readline().split()
        idxs=[fields.index(i)-2 for i in cv]
        return idxs

def find_conf(idxs:list,thres:list=values,operations:list=operations):
    if not (len(idxs) == len(thres) == len(operations)):
        print(f"Argument number mismatch: {len(idxs)} {len(thres)} {len(operations)}")
        sys.exit(1)

    op_func=[OPERATIONS.get(i) for i in operations]
    col_var=np.loadtxt(COLVAR_file, skiprows=1)
    combined_mask=np.ones(col_var.shape[0], dtype=bool)
    for idx,t,op in zip(idxs,thres,op_func):
        if op is None:
            print(f"Not known operation: {op}")
        mask=op(col_var[:,idx], t)
        combined_mask = combined_mask & mask
    filtered_data = col_var[combined_mask]
    print(f"Found {len(filtered_data)} valid configurations.")

    np.savetxt("Valid_configurations.txt", filtered_data, fmt='%.9f')

def main():
    if len(sys.argv)==1:
        parser.print_help()
        sys.exit()
    elif not(os.path.isfile("COLVAR")):
        print("WARNING: file is defaulted to COLVAR, but it does not exist in the current directory. Please provide a valid file name.")
        parser.print_help()
        sys.exit()
    idxs=idx_search()
    find_conf(idxs)

        

if __name__=="__main__":
    main()
