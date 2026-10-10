#Made by Elia C. on 31-07-2026
import numpy as np
import pandas as pd
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

#Dictionary of species
SPECIES = {
    "mgpp":     dict(label=r"$\mathrm{MgP_2O_7^{2-}}$", color="blue"),
    "mghpp":    dict(label=r"$\mathrm{MgHP_2O_7^{-}}$", color="green"),
    "mg2pp":    dict(label=r"$\mathrm{Mg_2P_2O_7}$", color="red"),
    "pp":       dict(label=r"$\mathrm{P_2O_7^{4-}}$", color="orange"),
    "hpp":      dict(label=r"$\mathrm{HP_2O_7^{3-}}$", color="purple"),
    "h2pp":     dict(label=r"$\mathrm{H_2P_2O_7^{2-}}$", color="magenta"),
    "h3pp":     dict(label=r"$\mathrm{H_3P_2O_7^{-}}$", color="teal"),
    "h4pp":     dict(label=r"$\mathrm{H_4P_2O_7}$", color="goldenrod"),
}

#files
energies=Path(f"{sys.argv[1]}").resolve()
conc=Path(f"{sys.argv[2]}").resolve()
resume_file=Path(f"").resolve().parent / "delta_G_resume.txt"

#Reactivity groupings
non_catalyzed=["pp", "hpp", "h2pp", "h3pp", "h4pp"]
catalyzed=["mgpp", "mghpp", "mg2pp"]
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
    min_energy = np.stack((pp_energies, mg_energies)).min()*0.9
    max_energy = np.stack((pp_energies, mg_energies)).max()*1.1
    pH_series=np.loadtxt(conc,unpack=True)[0]
    plt.plot(pH_series,pp_energies,ls='-',color='r',label="Non-catalyzed")
    plt.plot(pH_series,mg_energies,ls='-',color='purple', label="Mg-catalyzed")
    plt.xticks(np.arange(0,14.01,1),fontsize=8)
    plt.xlim(0,14)
    plt.ylim(min_energy,max_energy)
    plt.xlabel("pH")
    plt.ylabel(r"Energy (Kcal$\cdot$ mol$^{-1}$)")
    plt.title("Activation energy vs pH",fontsize=16)
    plt.legend(fontsize=12, loc="upper right")
    plt.savefig("Energy_vs_pH.png", dpi=600)
    plt.close()

def plot_keff_trend(pp_keff,mg_keff):
    min_k = np.stack((pp_keff, mg_keff)).min()*0.9
    max_k = np.stack((pp_keff, mg_keff)).max()*1.1
    pH_series=np.loadtxt(conc,unpack=True)[0]
    plt.plot(pH_series,pp_keff,ls='-',color='r',label="Non-catalyzed")
    plt.plot(pH_series,mg_keff,ls='-',color='purple', label="Mg-catalyzed")
    plt.xticks(np.arange(0,14.01,1),fontsize=8)
    plt.xlim(0,14)
    plt.ylim(min_k,max_k)
    plt.xlabel("pH")
    plt.ylabel(r"Rate constant")
    plt.title(r"Rate constant (K$_{eff}$ vs pH",fontsize=16)
    plt.legend(fontsize=12, loc="upper right")
    plt.savefig("Keff_vs_pH.png", dpi=600)
    plt.close()

def main():
    if len(sys.argv) != 3:
        print("Usage: python Delta_G.py <energy_filename> <concentration_filename>")
        sys.exit(1)
    pp_ratios=ratio(conc,non_catalyzed)
    mg_ratios=ratio(conc,catalyzed)
    pp_ener=reorder(energies,non_catalyzed)
    mg_ener=reorder(energies,catalyzed)
    pp_deltaG=G_eff(pp_ratios,pp_ener)
    mg_deltaG=G_eff(mg_ratios,mg_ener)
    pp_keff=A*np.exp(-pp_deltaG/(R*T))
    mg_keff=A*np.exp(-mg_deltaG/(R*T))
    delta_G=np.array([pH_series,pp_deltaG,pp_keff,mg_deltaG,mg_keff])
    np.savetxt("DeltaG_resume.txt",np.transpose(delta_G),fmt='%2.8f',header="pH non_catalyzed catalyzed", comments="#")
    plot_energy_trend(pp_deltaG,mg_deltaG)
    plot_keff_trend(pp_keff,mg_keff)

if __name__ == "__main__":
    main()
