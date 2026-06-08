import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

Eh_to_Kcal=627.5
namesystem="PPiMg2_sides"

#GREPPING
energy = open(f"{namesystem}-Energy.en", 'r')
print(f"File readability: {energy.readable()}")
line=energy.readline()
K_index=line.index("Kin.[a.u.]")
P_index=line.index("Pot.[a.u.]")
T_energy=np.array([])
for line in energy.readlines():
    K_energy=float(line[K_index:K_index+10])
    P_energy=float(line[P_index-5:P_index+10])
    T_energy=np.append(T_energy,P_energy+K_energy).astype(float)
mu, sigma=np.mean(T_energy), np.std(T_energy)

#Displaying
#norm_energy=abs((T_energy-np.min(T_energy))/(np.max(T_energy)-np.min(T_energy)))
plt.hist(T_energy, bins=200, density=True, label="Total energies distribution (Eh)")
#p = 1/(sigma * np.sqrt(2 * np.pi)) * np.exp(- (T_energy - mu)**2 / (2 * sigma**2))
#plt.plot(norm_energy,p,lw=2)
plt.xlabel("Total Energy (a.u.)")
plt.ylabel("Frequency")
plt.title(f"Normalized total energy distribution - {namesystem}")
plt.legend()
plt.tight_layout()
plt.savefig(f"energy_distribution_{namesystem}.png", dpi=150)
plt.close()

#Energy conversion
T_energy_Kcal=T_energy*Eh_to_Kcal
mu, sigma=np.mean(T_energy_Kcal), np.std(T_energy_Kcal)

#Displaying
#norm_energy=abs((T_energy_Kcal-np.min(T_energy_Kcal))/(np.max(T_energy_Kcal)-np.min(T_energy_Kcal)))
plt.hist(T_energy_Kcal, bins=200, density=True, label="Total energies distribution (Kcal)")
##p = 1/(sigma * np.sqrt(2 * np.pi)) * np.exp(- (T_energy_Kcal - mu)**2 / (2 * sigma**2))
#plt.plot(norm_energy,p,lw=2)
plt.xlabel("Total Energy (a.u.)")
plt.ylabel("Frequency")
plt.title(f"Normalized total Energy distribution - {namesystem}")
plt.legend()
plt.tight_layout()
plt.savefig("energy_distribution_Kcal.png", dpi=150)
plt.close()