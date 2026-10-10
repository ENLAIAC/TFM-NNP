"""
mdelapuente, 03-2021
WHAM procedure for obtaining free energy profile from US calculation biasing a single collective variable
The script expects an input file containing, in every line, the relative path to the US output file (array with 
values of the collective variable in different lines), the center of the biasing potential (in eV) and the force
constant used in the given window. It calculates the full profile, the partial profiles of each window and the 
probability distributions of every simulation.
"""
#------------------------------------------------------------------------------------------------------------#
#                                        Import packages                                                     #
#------------------------------------------------------------------------------------------------------------#

import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import simps

#------------------------------------------------------------------------------------------------------------#
#                                        END packages                                                        #
#------------------------------------------------------------------------------------------------------------#



#------------------------------------------------------------------------------------------------------------#
#                                        Handle input                                                        #
#------------------------------------------------------------------------------------------------------------#


try:
    inp = os.sys.argv[1]
    print("Read ",inp, " as input file\n")
except:
    print("No input file was given, \'input.txt\' used by default\n")
    inp = "input.txt"


with open(inp,'r') as f:
    pre = f.readlines()
    if pre[0][0] == '#':
        params = pre[0].split()
        L = pre[1:]
    else:
        params = ["#", "0", "0.1", "-1.0", "240"]
        L = pre

# Organize input data:
colvars, s_k, kappas = [], [], []
for line in L:
    colvars.append(line.split()[0])
    s_k.append(round(float(line.split()[1]),4))
    kappas.append(round(float(line.split()[2]),4))

# Read parameters from first line:
EQUIL_FRAMES = int(params[1])                       # Number of equilibration frames in window simulations
Δq           = float(params[2])                     # bin width in CV units
qmin         = float(params[3])                     # minimal CV value (CV unit)
Nb           = int(params[4])                       # number of bins between qmin and (Δq*Nb - qmin)
    
print("Paths to CV files: ", colvars, "\n")
print("Centers of windows: ", s_k, "\n")
print("Force constants applied: ", kappas, "\n")

#------------------------------------------------------------------------------------------------------------#
#                                           END input                                                        #
#------------------------------------------------------------------------------------------------------------#



#------------------------------------------------------------------------------------------------------------#
#                                        Handle output                                                       #
#------------------------------------------------------------------------------------------------------------#

suffix = os.sys.argv[2]

CVG_out = "wham_cvg"+ suffix +".png"
P_windows_out = "wham_biased_P_windows"+ suffix +".png"
F_windows_out = "wham_F_windows"+ suffix +".png"
F_image_out = "wham_F_profile"+suffix+".png"
FEP_out = "fep"+ suffix +".out"

#------------------------------------------------------------------------------------------------------------#
#                                           END output                                                       #
#------------------------------------------------------------------------------------------------------------#



#------------------------------------------------------------------------------------------------------------#
#                                Define parameters and recover data                                          #
#------------------------------------------------------------------------------------------------------------#

#EQUIL_FRAMES = 40001                                # Number of equilibration frames in window simulations
nw           = len(s_k)                             # number of windows
#Δq           = 0.05                                 # bin width in CV units
#qmin         = -1.0                                 # minimal CV value (CV unit)
#Nb           = 240                                  # number of bins between qmin and (Δq*Nb - qmin)
#kT           = 0.025851                             # in eV at 300K
#β            = 38.6832                              # eV-1
kT           = 298.15 * 1.987207 * 0.001             # in kcal/mol at 298.15K
β            = 1.6878                               # (kcal/mol)-1
grid = [round(qmin+i*Δq+Δq/2,5) for i in range(Nb)] # The centers of each bin

print("Analyze ", nw, " windows with kT = ", kT," eV","in a grid with ", Nb, "bins",\
      "\nCV Grid: ",grid,"\n")

# List containing all realizations of the collective variable in every window
q= []
for i in range(nw):
    q.append(np.asarray(np.genfromtxt(colvars[i]).transpose()[1][EQUIL_FRAMES:].tolist(), dtype=np.float128 ))
    


N_data = [len(q[i]) for i in range(len(q))]
for i in range(len(N_data)):
    print(N_data[i], "configurations analyzed in window "+str(i))
print("\n")
#------------------------------------------------------------------------------------------------------------#
#                                       END definitions and data                                             #
#------------------------------------------------------------------------------------------------------------#



#------------------------------------------------------------------------------------------------------------#
#                             Initialize functions and variables                                             #
#------------------------------------------------------------------------------------------------------------#

def bias(s, s0, κ=100):
    return 0.5*κ*(s-s0)**2


# Bias functions applied in each window:
W = [bias(np.asarray(grid, dtype=np.float128 ), s_k[i], κ=kappas[i]) for i in range(nw)]


# Biased distributions:
P_bias_w = [[0 for i in range(Nb)] for window in q]
for window in range(len(q)):
    for cv in q[window]:
        # Care with Python numbering
        P_bias_w[window][int((cv-qmin)/Δq)]+=1/(N_data[window]*Δq)
# Make into arrays
P_bias_w = [np.asarray(w, dtype=np.float128 ) for w in P_bias_w]


# Initial free-energy coefficients (initialized at Ak=0 for every k)
A = np.asarray([0 for i in range(nw)], dtype=np.float128 )
old_A = np.ones(A.shape, dtype=np.float128 ) # dummy A for convergence evaluation


# Initial full probability (initialized at 0 for every q)
full_probability = np.asarray([0 for i in range(Nb)], dtype=np.float128)

#------------------------------------------------------------------------------------------------------------#
#                                          END initialization                                                #
#------------------------------------------------------------------------------------------------------------#



#------------------------------------------------------------------------------------------------------------#
#                                             WHAM SCF cycle                                                 #
#------------------------------------------------------------------------------------------------------------#


limit = 0
convergence = []
cvg_criterion = 1.0e-5 # eV, arbitrary but seems to work

print("Convergence criterion on maximum evolution of free-energy coefficients (<"\
      +"{:e}".format(cvg_criterion)+" at convergence)\n")
print("\n\nStart of WHAM self consistent cycle\n\n")
print("-------------------------------------------------------------------------------------------------")
#print("# Step max(ΔF) min(ΔF)")
print("# Step max(F) min(F)")


print_ind = 0
while limit < 10000 :
    limit += 1
    if print_ind%10 == 0:
        print(print_ind, " ", round(max(abs(A-old_A)),9) , " ", round(min(abs(A-old_A)),9))
    print_ind +=1
        
    if max(abs(A-old_A)) > cvg_criterion:
        convergence.append(max(abs(A-old_A)))
        old_A = A.copy()

        # Update probability (eq1):
        for b in range(Nb):
            num = 0
            den = 0
            for w in range(nw):
                num += (P_bias_w[w][b] * N_data[w])
            for w in range(nw):
                den += (np.exp(β*A[w]-β*np.mean(old_A))*np.exp(-β*W[w][b]))*N_data[w]
            full_probability[b] = (num / den)
        
        # Update free energy coefficients (eq2) taking mean of old_A as the new offset A0:
        for w in range(nw):
            A[w] = np.mean(old_A) - kT*np.log(simps(full_probability*np.exp(-β*W[w]), x=grid)) 
        
    else:
        convergence.append(max(abs(A-old_A)))
        print(print_ind, " ", max(abs(A-old_A)) ," ", min(abs(A-old_A)), '\n')
        break

print("\n END of WHAM cycle\n")
print("-------------------------------------------------------------------------------------------------")

#------------------------------------------------------------------------------------------------------------#
#                                             END WHAM cycle                                                 #
#------------------------------------------------------------------------------------------------------------#


#------------------------------------------------------------------------------------------------------------#
#                                               Save data                                                    #
#------------------------------------------------------------------------------------------------------------#


def unbias_windows(P_bias_w, A):
    return [(np.exp(-β*A[k])*np.exp(β*W[k])*P_bias_w[k]) for k in range(nw)]

P_unbiased_w = unbias_windows(P_bias_w, A)

def free_energy(P):
    return -kT*np.log(P)

A_profile = free_energy(full_probability)

print("\nFull free-energy profile saved to "+ FEP_out +"\n\nEOF")
with open(FEP_out,'w') as out:
    out.write('# CV, Free-energy in eV, Free-energy in kcal/mol \n')
    for i in range(Nb):
        out.write(str(grid[i])+' '+str(A_profile[i]-min(A_profile))+\
#                  ' '+str((A_profile[i]-min(A_profile))*23.061)+'\n')
                  ' '+str((A_profile[i]-min(A_profile)))+'\n')


#------------------------------------------------------------------------------------------------------------#
#                                               END DATA                                                     #
#------------------------------------------------------------------------------------------------------------#


#------------------------------------------------------------------------------------------------------------#
#                                              MAKE FIGURES                                                  #
#------------------------------------------------------------------------------------------------------------#

### Convergence:
print("\nConvergence of WHAM saved to --> "+CVG_out+"\n")
Fig = plt.figure(figsize=(12,8))
fig = Fig.add_subplot((111))

fig.plot(convergence)
fig.set_xlabel('Number of WHAM iterations', size=20)
fig.set_ylabel('max|A(k)- A(k-1)|', size=20)
fig.set_title('Convergence of WHAM algorithm', size=20)
plt.xticks(size=18)
plt.yticks(size=18)
plt.yscale('log')
plt.grid(linestyle='-', linewidth=1)
plt.savefig(CVG_out, bbox_inches='tight')


### Biased distributions:
print("\nBiased distributions saved to -->" + P_windows_out + "\n")
Fig = plt.figure(figsize=(12,8))
fig = Fig.add_subplot((111))
j=0
for i in range(len(P_bias_w)):
    print("Window number ", i," normalized to ", round(np.sum(P_bias_w[i])*Δq,8))
    fig.plot(grid,P_bias_w[i],label=colvars[j])
    j +=1
#fig.legend(prop={'size':12})
plt.xticks(size=18)
plt.yticks(size=18)
fig.set_xlabel('Collective variable', size=18)
fig.set_ylabel(r'$\tilde{P}_k(q)$', size=18)
fig.set_title('Biased window distributions', size=20)
plt.grid(linestyle='-', linewidth=1)
plt.savefig(P_windows_out, bbox_inches='tight')



### Window free-energy profiles:
print("\nWindow free-energy profiles saved to --> " + F_windows_out + "\n")
Fig = plt.figure(figsize=(12,8))
fig = Fig.add_subplot((111))
j=0
labels = [str(20-i) for i in range(1,20)]
for i in P_unbiased_w:
    fig.plot(grid,-kT*np.log(i))#,label=colvars[j])
    j +=1
#fig.legend(prop={'size':12})
plt.xticks(size=18)
plt.yticks(size=18)
fig.set_xlabel('Collective variable', size=18)
fig.set_ylabel('Free-energies (eV)', size=18)
fig.set_title('Unbiased window free-energy profiles', size=20)
plt.grid(linestyle='-', linewidth=1)
plt.savefig(F_windows_out,bbox_inches='tight')



### Full free-energy profile:
print("\nFull free-energy profile saved to --> "+ F_image_out +"\n")

Fig = plt.figure(figsize=(12,8))
fig = Fig.add_subplot()
#fig.plot(grid,A_profile*23.061-23.061*min(A_profile))
fig.plot(grid,A_profile-min(A_profile))
fig.set_xlabel('Collective variable', size=18)
fig.set_ylabel('Free-energy (kcal/mol)', size=18)
#fig.set_title('Free-energy profile of solvation', size=18)
plt.xticks(size=18)
plt.yticks(size=18)
plt.grid(linestyle='-', linewidth=1)
plt.savefig(F_image_out,bbox_inches='tight')

#------------------------------------------------------------------------------------------------------------#
#                                             END FIGURES                                                    #
#------------------------------------------------------------------------------------------------------------#

###########################################       EOF       ##################################################
