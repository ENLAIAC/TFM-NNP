import numpy as np
import matplotlib.pyplot as plt

# Files in the working directory
files = [
    "pp.txt",
    "ppmg.txt",
    "pph.txt",
    "pph_lp.txt",
    "pphh.txt",
    "pph3.txt",
    "pph4.txt",
    "ppimg2.txt"
]

# Corresponding labels
labels = [
    r"P$_2$O$_7^{4-}$",
    r"MgP$_2$O$_7^{2-}$",
    r"HP$_2$O$_7^{3-}$ (P$\alpha$)",
    r"HP$_2$O$_7^{3-}$ (P$\beta$)",
    r"H$_2$P$_2$O$_7^{2-}$",
    r"H$_3$P$_2$O$_7^{-}$",
    r"H$_4$P$_2$O$_7$",
    r"Mg$_2$P$_2$O$_7$"
]

# Marker/color styles
styles = [
    {"color": "black", "marker": "o"},
    {"color": "red", "marker": "s"},
    {"color": "blue", "marker": "^"},
    {"color": "green", "marker": "v"},
    {"color": "purple", "marker": "D"},
    {"color": "pink", "marker": "P"},
    {"color": "orange", "marker": "X"},
    {"color": "olive", "marker": "8"}
]

plt.figure(figsize=(6, 4), dpi=300)

# Plot datasets
for file, label, style in zip(files, labels, styles):
    data = np.loadtxt(file)
    x = data[:, 0]
    y = data[:, 1]
    plt.plot(x, y,
             label=label,
             color=style["color"],
             marker=style["marker"],
             markersize=5,
             linewidth=1.5)

# Add dashed horizontal line at y = 0.05
plt.axhline(y=0.05, color="gray", linestyle="--", linewidth=1)

# Axis limits
plt.xlim(-2, 2)
plt.ylim(0.01, 0.12)

# Labels
plt.xlabel(r"$\Delta d$ ($\mathrm{\AA}$)", fontsize=12)
plt.ylabel(r"RMSE Forces (eV$\cdot\mathrm{\AA}^{-1}$)", fontsize=12)

# Grid
plt.grid(True, linestyle=":", linewidth=0.8, alpha=0.7)

# Legend
plt.legend(fontsize=9)

# Layout and save
plt.tight_layout()
plt.savefig("rmse_forces.png", dpi=600, bbox_inches="tight")
plt.close()


