import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import matplotlib.ticker as ticker
import sys

# Folders containing replicas
base_folders = ["rep1/WHAM", "rep2/WHAM", "rep3/WHAM"]

all_pmfs = []

# Load PMF data from all files
for folder in base_folders:
    folder_path = Path(folder)
    for file in sorted(folder_path.glob("fep*.out")):
        data = np.loadtxt(file, skiprows=1)  # Skip header
        all_pmfs.append(data[:, 1])  # Free energy column

all_pmfs = np.array(all_pmfs)  # shape: (n_files_total, n_points)
all_pmfs[np.isinf(all_pmfs)] = np.nan
average_pmf = np.nanmean(all_pmfs, axis=0)
std_pmf = np.nanstd(all_pmfs, axis=0)

# Assume reaction coordinate is same in all files
reaction_path = data[:, 0]

# Save averaged data
output_file = Path("average_pmf_noerror.dat")
np.savetxt(output_file,
           np.column_stack([reaction_path, average_pmf, std_pmf]),
           header="ReactionPath AveragePMF(kcal/mol) StdDev(kcal/mol)",
           fmt="%.6f")


# --- Plot ---
plt.figure(figsize=(8,6), dpi=600)

valid=np.isfinite(average_pmf)
average_pmf=average_pmf[valid]
std_pmf=std_pmf[valid]
reaction_path=reaction_path[valid]

err_step = 20
x_max = 0.4
x_min =-2.0

mask=(reaction_path>=x_min) & (reaction_path<=x_max)
plt.plot(reaction_path[mask], average_pmf[mask],
         color='#3399CC', lw=2, label=r"React $\rightarrow$ TS1")

# Error bars only every err_step points, cropped at 1.5
mask_err = (reaction_path[::err_step] <= x_max) & (reaction_path[::err_step] >= x_min)
plt.errorbar(reaction_path[::err_step][mask_err],
             average_pmf[::err_step][mask_err],
             yerr=std_pmf[::err_step][mask_err],
             fmt='none', ecolor='black', elinewidth=0.5, capsize=4)

# Last point of the curve
x_last = reaction_path[mask][-1]
y_last = average_pmf[mask][-1]

dx = 0.05
dy = 2.0
gap = 0.08  # horizontal shift only

plt.plot([x_last - dx, x_last + dx],
         [y_last - dy, y_last + dy],
         color="black", linestyle="--", linewidth=1.5)
plt.plot([x_last - dx + gap, x_last + dx + gap],
         [y_last - dy, y_last + dy],
         color="black", linestyle="--", linewidth=1.5)

# Define arrow start and end
idx = np.argmax(average_pmf[mask])        # x-position of the arrow (reaction coordinate)
x_pos=reaction_path[mask][idx]
y_start = min(average_pmf[mask])       # starting free energy
y_end =average_pmf[mask][idx]         # ending free energy

# Draw vertical arrow
plt.annotate(
    "", xy=(x_pos, y_end), xytext=(x_pos, y_start),
    arrowprops=dict(arrowstyle="->", color="#F73152", lw=2)
)

# Optional label
plt.text(x_pos + 0.025, (y_start + y_end) / 2,
         f"{y_end - y_start:.1f}",
         va="center", ha="left", color="red", fontsize=14)

# Formatting
plt.xlabel(r"$C_{LG}$", fontsize=12)
plt.ylabel(r"$\Delta$G (kcal · mol$^{-1}$)", fontsize=12)

ticks = np.arange(-2.0, 0.5, 0.2)
plt.xticks(ticks, fontsize=8)
plt.yticks(fontsize=8)


plt.ylim(min(average_pmf[mask]), max(average_pmf[mask])*1.2)
plt.xlim(min(reaction_path[mask]), max(reaction_path[mask]))
plt.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)

# Legend for the curve
plt.legend(fontsize=16, loc="upper right", frameon=False)

plt.tight_layout()
plt.savefig("average_pmf.png", dpi=600)  # High-res for paper
#plt.show()
