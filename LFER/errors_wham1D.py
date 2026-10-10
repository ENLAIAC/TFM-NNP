"""
MdelaPuente, June 2021
Calculation of errors on the free energy profile computed with a WHAM procedure as defined by 
Zhu and Hummer (J. Comp. Chem., 2011). Expected input is the same as the one for calculating
the FEP with wham1D.py script. It works for both in kcal/mol and eV.
"""

########## PACKAGES
import numpy as np
import os
########


########## INPUT

try:
    inp = os.sys.argv[1]
    print("List of files, centers of windows and force constants read from "+inp)
except:
    print("No input file was given, \'input.txt\' used by default\n")
    inp = "input.txt"

unit = input("Unit: eV (0), kcal/mol (1)\n>> ")
if unit == "0":
    factor = 23.0
elif unit == "1":
    factor = 1.0
else:
    print("Bad unit. EXIT")
    exit
########    
    
    
######### READ AND ORGANIZE INPUT 
with open(inp,'r') as inp:
    pre = inp.readlines()
    if pre[0][0] == "#":
        params = pre[0].split()
        L      = pre[1:]
    else:
        params = ["#", "0"]
        L      = pre 

print("Windows sorted by increasing value of the collective variable:")
unsorted_colvars, unsorted_s_k, unsorted_kappas = [], [], []
for line in L:
    unsorted_colvars.append(line.split()[0])
    unsorted_s_k.append(round(float(line.split()[1]),4))
    unsorted_kappas.append(round(float(line.split()[2]),4))

# Sort lists by increasing values of s_k
zipped_lists = zip(unsorted_s_k, unsorted_colvars, unsorted_kappas)
sorted_zipped_lists = sorted(zipped_lists)
colvars = [element for _, element, _ in sorted_zipped_lists]
s_k = [element for element, _, _ in sorted_zipped_lists]
kappas = [element for _, _, element in sorted_zipped_lists]

print("Paths to CV files: ", colvars, "\n")
print("Centers of windows: ", s_k, "\n")
print("Force constants applied: ", kappas, "\n")
########



######### PARAMETERS
nw = len(s_k)                                             # number of windows
kT = 0.593/factor                                         # in US units at 300K (like KAPPAS !)
β = 1.686*factor                                          # in US units at 300K (like KAPPAS !)
EQUIL_FRAMES = int(params[1])                             # number of equilibration frames in window simulations
#EQUIL_FRAMES = 40001                                      # number of equilibration frames in window simulations
n_blocks = 8                                              # number of blocks for block averaging
print("We will use n =",n_blocks," blocks for computing errors")
ΔCV_list = [round(s_k[i+1]-s_k[i],6) for i in range(len(s_k)-1)]  # in CV units
print("Spacement between neighbouring windows: ", ΔCV_list, "\n")
########


######### READ CV FILES
print("Start reading CV files:\n")
q= []
for i in range(nw):
    q.append(np.asarray(np.genfromtxt(colvars[i]).transpose()[1][EQUIL_FRAMES:].tolist(), dtype=np.float128 ))
print("Done. "+str(len(q))+" files read.")
########


######## COMPUTE VARIANCE OF MEAN CV (eq35)
var_x = np.asarray([0 for i in range(0,nw)], dtype=np.float128)   # List that will contain variance of mean(x) in simulation i as i-th entry

means_x = np.asarray([np.mean(q[w]) for w in range(0,nw)], dtype=np.float128)
print("Mean values of the CV in each window: ", means_x, "\n")

def cut_window_in_blocks(window, n_b):
    subwindow = window.copy()
    n_data_block = len(subwindow)//n_b
    return [subwindow[i*n_data_block:(i+1)*n_data_block] for i in range(n_b)]

cut_CV = [[] for i in range(n_blocks)]
for window in q:
    blocks = cut_window_in_blocks(window, n_blocks)
    for elt in range(len(cut_CV)):
        cut_CV[elt].append(blocks[elt])
# cut_CV contains n_blocks lists. Each list contains nw lists of m entries with the cv values of the window and block  


pref = 1/(n_blocks*(n_blocks-1))

for i in range(len(var_x)):
    for b in range(n_blocks):
        # Values of interest are in cut_CV[b][i] ie: i-th window of b-th block
        var_x[i] += pref*(np.mean(np.asarray(cut_CV[b][i])-means_x[i])**2)
########
        
        


######## COMPUTE VARIANCE OF ADIMENSIONAL FREE-ENERGY PARAMETERS {gi}
print("Variances of the mean CV in each window from a block averaging with ", n_blocks, " blocks:\n",var_x,"\n")

def var_gj(x_vars, j, k_list=np.asarray(kappas, dtype=np.float128), r_list=np.asarray(ΔCV_list), dtype=np.float128):
    return (( 0.25*(x_vars[0]*(k_list[0]*r_list[0])**2  +  x_vars[j]*(k_list[j]*r_list[j])**2 ) + np.sum( x_vars[1:j]*(kappas[1:j]*r_list[1:j])**2 ) )*(β**2))

print("Variances of the free-energy coefficients estimated from cumulative variances of the mean CV over consecutive windows")
var_g = np.asarray([0.0]+[var_gj(var_x, j) for j in range(0,nw-1)], dtype=np.float128)
# G = kT*g --> var G = (kT)^2 var(g) --> s(G)=kTs(g)
errors_G = factor*kT*np.sqrt(var_g)
########



######### OUTPUT
try:
    suffix = os.sys.argv[2]
    print("Errors written to errors_hummer"+suffix+".out\nExit 0")
except:
    suffix = ""
    print("Errors written by default to errors_hummer"+suffix+".out\nExit 0")
########



######## WRITE OUTPUT FILE
with open("errors_hummer"+suffix+".out",'w') as out:
    out.write("# CV value, error in kcal/mol\n")
    for i in range(len(s_k)):
        out.write("{0:.5f}".format(s_k[i])+"  "+"{0:.5f}".format(errors_G[i])+"\n")

######################################################## EOF ########################################################
