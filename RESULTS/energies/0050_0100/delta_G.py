#Made by Elia C. on 31-07-2026
import numpy as np
import pandas as pd
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

#files
energies=Path(f"{sys.argv[1]}").resolve()
conc=Path(f"{sys.argv[2]}").resolve()
wolf_data="wolfend_data.txt"
resume_file=Path(f"").resolve().parent / "delta_G_resume.txt"

#Reactivity groupings
non_catalyzed=["pp", "hpp", "h2pp", "h3pp", "h4pp"]
catalyzed=["pp", "hpp", "h2pp", "h3pp", "h4pp","mgpp", "mghpp", "mg2pp"]
pH_series=np.loadtxt(conc, unpack=True)[0]


#constants
R = 1.987e-3  # Kcal/(mol*K)
T = 298.15    # 25C
h=6.62607015e-34  # Planck's constant in J*s
kb=1.380649e-23  # Boltzmann constant in J/K
A=kb*T/h  # Pre-exponential factor in s^-1

def reorder(file,species):
    with open(file, "r") as f:
        header=f.readline().strip("#").split()
    idx=[header.index(i) for i in species]
    data=np.loadtxt(file,unpack=True)
    reordered=list([data[i] for i in idx])
    return np.array(reordered)

def ratio(file,species):
    C=np.transpose(reorder(file,species))
    tot_conc=np.sum(C, axis=1)
    ratios = [np.divide(C[i],tot_conc[i]) for i in range(len(C))]
    return ratios
    
def G_eff(ratios,ener):
    boltz_factor=np.exp(-ener/(R*T))
    weighted_en=np.sum(ratios*boltz_factor,axis=1)
    en_gibbs=-R*T*np.log(weighted_en)
    return en_gibbs

def plot_energy_trend(pp_energies,mg_energies):
    ph_wolf_data=np.loadtxt(wolf_data,unpack=True)[0]
    dG_wolf_data=np.loadtxt(wolf_data,unpack=True)[1]
    min_energy = np.stack((pp_energies, mg_energies)).min()*0.8
    max_energy = np.stack((pp_energies, mg_energies)).max()*1.1
    pH_series=np.loadtxt(conc,unpack=True)[0]
    plt.plot(pH_series,pp_energies,ls='-',color='brown',marker='v',markevery=10, label="Non-catalyzed")
    plt.plot(ph_wolf_data, dG_wolf_data,ls='-',color='deepskyblue',marker='v',markevery=10,label="Experimental data")
    plt.plot(pH_series,mg_energies,ls='--',color='goldenrod', label="Mg-catalyzed")
    plt.plot
    plt.xticks(np.arange(0,14.01,1),fontsize=8)
    plt.xlim(0,14)
    plt.ylim(min_energy,max_energy)
    plt.xlabel("pH")
    plt.ylabel(r"Energy (Kcal$\cdot$ mol$^{-1}$)")
    plt.title("Activation energy vs pH",fontsize=16)
    plt.grid(alpha=0.25)
    plt.legend(fontsize=12, loc="upper left")
    plt.savefig("Energy_vs_pH.png", dpi=600)
    plt.close()

    plt.figure()
    mask_ph=(pH_series >= 5 ) & (pH_series <= 12)
    mask_pH_wolf=ph_wolf_data<12
    pp_energies=pp_energies[mask_ph]
    mg_energies=mg_energies[mask_ph]
    dG_wolf_data=dG_wolf_data[mask_pH_wolf]
    min_energy = np.stack((pp_energies, mg_energies)).min()*0.95
    max_energy = np.stack((pp_energies, mg_energies)).max()*1.05
    plt.plot(pH_series[mask_ph], pp_energies,marker='v', markevery=10, ls='-', color='brown')
    plt.plot(ph_wolf_data[mask_pH_wolf], dG_wolf_data, ls='-', marker='o', markevery=10, color='deepskyblue')
    plt.plot(pH_series[mask_ph], mg_energies, ls='--', color='goldenrod')
    plt.xticks(np.arange(5, 12.01, 1), fontsize=8)
    plt.yticks(fontsize=8)          # match the style on Y if you want
    plt.xlim(5, 12)
    plt.ylim(min_energy, max_energy)
    plt.axis('off')
    plt.grid(alpha=0.25)
    plt.savefig("Energy_vs_pH_snippet.png", dpi=600)
    plt.close()

def plot_k_trend(k_pp,k_mg):
    min_k = np.stack((np.log(k_pp), np.log(k_mg))).min()*0.9
    max_k = np.stack((np.log(k_pp), np.log(k_mg))).max()*1.1
    pH_series=np.loadtxt(conc,unpack=True)[0]
    plt.plot(pH_series,np.log(k_pp),ls='-',color='r',label="Non-catalyzed")
    plt.plot(pH_series,np.log(k_mg),ls='-',color='purple', label="Mg-catalyzed")
    plt.xticks(np.arange(0,14.01,1),fontsize=8)
    plt.xlim(0,14)
    plt.ylim(min_k,max_k)
    plt.xlabel("pH")
    plt.ylabel(r"\ln(k) (s$^{-1}$)")
    plt.title("Rate constant vs pH",fontsize=16)
    plt.legend(fontsize=12, loc="upper right")
    plt.savefig("K_vs_pH.png", dpi=600)
    plt.close()

def main():
    if len(sys.argv) != 3:
        print("Usage: python Delta_G.py <energy_filename> <concentration_filename>")
        sys.exit(1)
    pp_ratios=ratio(conc,non_catalyzed)
    np.savetxt("ratios_pp.txt",pp_ratios)
    mg_ratios=ratio(conc,catalyzed)
    np.savetxt("ratios_mg.txt",mg_ratios)
    pp_ener=reorder(energies,non_catalyzed)
    mg_ener=reorder(energies,catalyzed)
    pp_k=A*np.exp(-pp_ener/(R*T))
    mg_k=A*np.exp(-mg_ener/(R*T))
    np.savetxt("pp_K_per_species.txt", pp_k.reshape(1,-1), fmt='%2.15f', header=' '.join(non_catalyzed), comments="#")
    np.savetxt("mg_K_per_species.txt", mg_k.reshape(1,-1), fmt='%2.15f', header=' '.join(catalyzed), comments="#")
    pp_deltaG=G_eff(pp_ratios,pp_ener)
    mg_deltaG=G_eff(mg_ratios,mg_ener)
    pp_keff=A*np.exp(-pp_deltaG/(R*T))
    mg_keff=A*np.exp(-mg_deltaG/(R*T))
    delta_G=np.array([pH_series,pp_deltaG,pp_keff,mg_deltaG,mg_keff])
    np.savetxt("DeltaG_resume.txt",np.transpose(delta_G),fmt='%2.15f',header="pH non_catalyzed k_non_catalyzed catalyzed k_catalyzed", comments="#")
    plot_energy_trend(pp_deltaG,mg_deltaG)
    plot_k_trend(pp_keff,mg_keff)



if __name__ == "__main__":
    main()
