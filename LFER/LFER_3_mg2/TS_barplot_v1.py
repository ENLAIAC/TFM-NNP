import sys
import matplotlib
matplotlib.use("Agg")            # safe on headless nodes / HPC
import matplotlib.pyplot as plt
import numpy as np
 
# ----------------------------------------------------------------------
# Configuration: column order, axis title shown under each column, color
# The keys must match the "system" tags in the data file.
# ----------------------------------------------------------------------
SYSTEMS = {
    "P2O7":    dict(title=r"P$_2$O$_7^{4-}$",              color="#56B4E9"),
    "MgP2O7":  dict(title=r"MgP$_2$O$_7^{2-}$",            color="#D55E00"),
    "bHP2O7":  dict(title=r"$\beta$-HP$_2$O$_7$",         color='mediumturquoise'),
    "aHP2O7":  dict(title=r"$\alpha$-HP$_2$O$_7$",         color='lawngreen'),
    "Mg2P2O7": dict(title=r"Mg$_2$P$_2$O$_7$",             color="#E69F00"),
    "MgHP2O7": dict(title=r"MgHP$_2$O$_7$",               color='blueviolet'),
    "H2P2O7":  dict(title=r"H$_2$P$_2$O$_7^{2-}$",         color="#CC79A7"),
    "bH3P2O7": dict(title=r"$\beta$-H$_3$P$_2$O$_7^{-}$",  color="#009E73"),
    "aH3P2O7": dict(title=r"$\alpha$-H$_3$P$_2$O$_7^{-}$", color="#0072B2"),
    "H4P2O7":  dict(title=r"H$_4$P$_2$O$_7$",              color="#9467BD"),
}
 
FIGSIZE        = (16.0, 9.0)
BAR_HALFWIDTH  = 0.08    # half-length of each level bar (x units)
SLOT_DX        = 0.26    # center-to-center spacing of degenerate bars
TEXT_GAP       = 0.05    # gap between bar end and side texts
LABEL_DY       = 0.22    # gap between a degenerate bar and its top label
MIN_LABEL_SEP  = 1.0     # min vertical separation between side texts
FS_TEXT        = 9       # font size of labels and values
TIE_ERROR_MODE = "max"   # "max": largest error of the degenerate group
                         # "all": every distinct error, slash-separated
YLABEL         = r"$\Delta G^{\ddagger}$ (kcal mol$^{-1}$)"
 
TEXT_BBOX = dict(facecolor="white", edgecolor="none", pad=0.8)
 
 
def read_levels(path):
    """Return {system: [(label, energy, error), ...]} in file order."""
    data = {key: [] for key in SYSTEMS}
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            system, label, energy, error = line.split()
            if system not in data:
                raise ValueError(f"Unknown system tag '{system}' "
                                 f"(expected one of {list(SYSTEMS)})")
            data[system].append((label, float(energy), float(error)))
    return data
 
 
def spread_labels(y, min_sep):
    """Nudge overlapping text positions apart (keeps original order)."""
    y = np.asarray(y, dtype=float)
    if len(y) < 2:
        return y
    order = np.argsort(y)
    adj = y[order].copy()
    for i in range(1, len(adj)):
        if adj[i] - adj[i - 1] < min_sep:
            adj[i] = adj[i - 1] + min_sep
    adj -= (adj.mean() - y[order].mean())
    out = np.empty_like(adj)
    out[order] = adj
    return out
 
 
def group_degenerates(levels):
    """
    Group levels of one system by exact energy, preserving file order.
    Returns a list of groups; each group is a list of (label, e, err).
    A group with more than one member is a degenerate set.
    """
    groups, index = [], {}
    for label, e, err in levels:
        key = round(e, 6)
        if key in index:
            groups[index[key]].append((label, e, err))
        else:
            index[key] = len(groups)
            groups.append([(label, e, err)])
    return groups
 
 
def tie_error_text(errs):
    """Format the error part of a degenerate group's shared value."""
    if TIE_ERROR_MODE == "max":
        return f"{max(errs):.1f}"
    return "/".join(f"{u:.1f}" for u in sorted(set(errs)))
 
 
def build_figure(data):
    fig, ax = plt.subplots(figsize=FIGSIZE)
 
    for i, (system, cfg) in enumerate(SYSTEMS.items()):
        levels = data[system]
        if not levels:
            continue
 
        groups = group_degenerates(levels)
 
        # one side-text slot per group, vertically de-overlapped
        y_true = [g[0][1] for g in groups]
        y_adj = spread_labels(y_true, MIN_LABEL_SEP)
 
        for group, ly in zip(groups, y_adj):
            if len(group) == 1:
                # ---- normal level: bar centered, label left, value right
                label, e, err = group[0]
                ax.hlines(e, i - BAR_HALFWIDTH, i + BAR_HALFWIDTH,
                          color=cfg["color"], lw=3, zorder=3)
                ax.text(i - BAR_HALFWIDTH - TEXT_GAP, ly, label,
                        ha="right", va="center", fontsize=FS_TEXT,
                        zorder=5, bbox=TEXT_BBOX)
                ax.text(i + BAR_HALFWIDTH + TEXT_GAP, ly,
                        f"{e:.1f} $\\pm$ {err:.1f}",
                        ha="left", va="center", fontsize=FS_TEXT,
                        zorder=5, bbox=TEXT_BBOX)
            else:
                # ---- degenerate levels: side-by-side bars, labels on
                # top, one shared value on the right of the group. The
                # rightmost bar is aligned with the normal bar position
                # so all value texts of the column line up.
                e = group[0][1]
                n = len(group)
                for k, (label, _, _) in enumerate(group):
                    xc = i - (n - 1 - k) * SLOT_DX
                    ax.hlines(e, xc - BAR_HALFWIDTH, xc + BAR_HALFWIDTH,
                              color=cfg["color"], lw=3, zorder=3)
                    ax.text(xc, e + LABEL_DY, label,
                            ha="center", va="bottom", fontsize=FS_TEXT,
                            zorder=5, bbox=TEXT_BBOX)
                errs = [err for _, _, err in group]
                ax.text(i + BAR_HALFWIDTH + TEXT_GAP, ly,
                        f"{e:.1f} $\\pm$ {tie_error_text(errs)}",
                        ha="left", va="center", fontsize=FS_TEXT,
                        zorder=5, bbox=TEXT_BBOX)
 
    # dashed separators between columns
    for x in np.arange(0.5, len(SYSTEMS) - 0.5, 1.0):
        ax.axvline(x, color="lightgray", ls="--", lw=1.2, zorder=1)
 
    ax.set_xlim(-0.5, len(SYSTEMS) - 0.5)
    ax.set_xticks(range(len(SYSTEMS)))
    ax.set_xticklabels([cfg["title"] for cfg in SYSTEMS.values()], fontsize=13)
    ax.tick_params(axis="x", length=0)
 
    all_e = [e for lv in data.values() for _, e, _ in lv]
    ax.set_ylim(min(all_e) - 2, max(all_e) + 2)
    ax.set_ylabel(YLABEL, fontsize=12)
 
    # full box around the plot
    for spine in ax.spines.values():
        spine.set_visible(True)
 
    fig.tight_layout()
    return fig, ax
 
 
def main(datafile, outfile="ts_levels.png"):
    data = read_levels(datafile)
    fig, _ = build_figure(data)
    fig.savefig(outfile, dpi=300)
    print(f"saved {outfile}")
 
 
if __name__ == "__main__":
    datafile = sys.argv[1] if len(sys.argv) > 1 else "ts_energies.txt"
    main(datafile)
