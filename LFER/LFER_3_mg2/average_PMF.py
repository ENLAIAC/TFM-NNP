import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import matplotlib.ticker as ticker
from scipy.signal import argrelextrema
import sys

# Folders containing replicas
base_folders = ["rep1/WHAM", "rep2/WHAM", "rep3/WHAM"]
all_pmfs = []

# Load PMF data from all files.
# Each replica is kept with its OWN WHAM reference (its own minimum = 0);
# no common/global reference is imposed.
for folder in base_folders:
    feps = sorted(Path(folder).glob("fep*.out"))
    if len(feps) != 1:
        # Fail loudly instead of silently averaging in a stale/mislabeled fep.
        raise SystemExit(
            f"{folder}: expected exactly one fep*.out, found {len(feps)}: "
            f"{[f.name for f in feps]}"
        )
    data = np.loadtxt(feps[0], skiprows=1)   # Skip header
    all_pmfs.append(data[:, 1])              # Free energy column (kcal/mol)

all_pmfs = np.array(all_pmfs)                # shape: (n_replicas, n_points)
all_pmfs[np.isinf(all_pmfs)] = np.nan        # unsampled bins -> nan

# --- Mean PMF and the STANDARD ERROR OF THE MEAN at every point --------------
# We want the *error* on the mean (its uncertainty), not the spread/deviation
# of the replicas. Per point:
#   SEM = sample_std(ddof=1) / sqrt(N_point)
# N_point is the number of replicas actually contributing at that point, so
# the error is honest where a replica is unsampled (nan). With fewer than two
# replicas the error is undefined -> nan (no bar drawn there).
n_valid = np.sum(np.isfinite(all_pmfs), axis=0)       # replicas per point
average_pmf = np.nanmean(all_pmfs, axis=0)            # mean PMF

with np.errstate(invalid="ignore", divide="ignore"):
    sample_std = np.nanstd(all_pmfs, axis=0, ddof=1)  # sample std (ddof=1)
    sem_pmf = sample_std / np.sqrt(n_valid)           # standard error of the mean
sem_pmf[n_valid < 2] = np.nan                         # error not estimable with <2 reps

# Assume reaction coordinate is same in all files
reaction_path = data[:, 0]

# Save averaged data (now carrying the standard error, not the deviation)
output_file = Path("average_pmf_error.dat")
np.savetxt(output_file,
           np.column_stack([reaction_path, average_pmf, sem_pmf, n_valid]),
           header="ReactionPath AveragePMF(kcal/mol) SEM(kcal/mol) N_replicas",
           fmt="%.6f")

# --- Plot ---
plt.figure(figsize=(8, 6), dpi=600)

valid = np.isfinite(average_pmf)
average_pmf = average_pmf[valid]
sem_pmf = sem_pmf[valid]
reaction_path = reaction_path[valid]

err_step = 25
x_max = 1.0 
x_min = -2.0
mask = (reaction_path >= x_min) & (reaction_path <= x_max)

plt.plot(reaction_path[mask], average_pmf[mask],
         color='#3399CC', lw=2, label=r"React $\rightarrow$ TS1")

# Standard-error bars, only every err_step points, cropped at x_max/x_min
mask_err = (reaction_path[::err_step] <= x_max) & (reaction_path[::err_step] >= x_min)
plt.errorbar(reaction_path[::err_step][mask_err],
             average_pmf[::err_step][mask_err],
             yerr=sem_pmf[::err_step][mask_err],
             fmt='none', ecolor='black', elinewidth=0.5, capsize=4)

# Last point of the curve
x_last = reaction_path[mask][-1]
y_last = average_pmf[mask][-1]

# --- Data restricted to plotting window (used for arrow placement) ---
y = average_pmf[mask]
x = reaction_path[mask]
err_filtered=sem_pmf[mask]

# Absolute (global) minimum
abs_max_idx = np.argmax(y)
y_abs_max = y[abs_max_idx]
abs_min_idx= np.argmin(y)
y_abs_min = y[abs_min_idx]


x_pos = x[abs_max_idx]      # arrow centered on absolute maxima x
y_end = y[abs_max_idx]      # arrow tip: absolute maxima y
y_start = y_abs_min         # arrow base: absolute minima y
y_err = err_filtered[abs_max_idx]

# Draw vertical arrow
plt.annotate(
    "", xy=(x_pos, y_end), xytext=(x_pos, y_start),
    arrowprops=dict(arrowstyle="->", color="#F73152", lw=2)
)

# Optional label
plt.text(x_pos + 0.1, (y_start + y_end) / 2,
        rf"{y_end - y_start:.1f} $\pm$ {y_err:.1f}",
         va="center", ha="left", color="red", fontsize=14)

# Formatting
plt.xlabel(r"$\Delta d$", fontsize=12)
plt.ylabel(r"$\Delta$G (kcal · mol$^{-1}$)", fontsize=12)
ticks = np.arange(-2.0, 2.01, 0.25)
plt.xticks(ticks, fontsize=8)
plt.yticks(fontsize=8)
plt.ylim(min(average_pmf[mask]), max(average_pmf[mask]) * 1.2)
plt.xlim(-2.0, 2.0)
plt.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)

# Legend for the curve
plt.legend(fontsize=16, loc="upper right", frameon=False)
plt.tight_layout()
plt.savefig("average_pmf.png", dpi=1200)  # High-res for paper
# plt.show()
