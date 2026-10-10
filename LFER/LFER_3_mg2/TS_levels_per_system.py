import os
import re
import sys
import matplotlib
matplotlib.use("Agg")            # safe on headless nodes / HPC
import matplotlib.pyplot as plt
import numpy as np

# ----------------------------------------------------------------------
# Per-system TS level diagrams.
#
# Companion of TS_barplot.py: instead of putting every system on a shared
# energy axis, this script writes ONE figure per system. Each figure shows
# only the TS ensemble of that system, ordered by its own relative energy
# ordering, with the y axis calibrated to the interval spanned by that
# ensemble alone. Nothing from the other systems enters the figure.
#
# usage:
#   python3 TS_levels_per_system.py [datafile] [system ...]
#   python3 TS_levels_per_system.py ts_energies.txt            # SELECTED
#   python3 TS_levels_per_system.py ts_energies.txt H4P2O7     # one system
#   python3 TS_levels_per_system.py ts_energies.txt all        # every system
# ----------------------------------------------------------------------

SYSTEMS = {
    "P2O7":    dict(title=r"P$_2$O$_7^{4-}$",              color="#56B4E9"),
    "MgP2O7":  dict(title=r"MgP$_2$O$_7^{2-}$",            color="#D55E00"),
    "Mg2P2O7": dict(title=r"Mg$_2$P$_2$O$_7$",             color="#E69F00"),
    "H2P2O7":  dict(title=r"H$_2$P$_2$O$_7^{2-}$",         color="#CC79A7"),
    "bH3P2O7": dict(title=r"$\beta$-H$_3$P$_2$O$_7^{-}$",  color="#009E73"),
    "aH3P2O7": dict(title=r"$\alpha$-H$_3$P$_2$O$_7^{-}$", color="#0072B2"),
    "H4P2O7":  dict(title=r"H$_4$P$_2$O$_7$",              color="#9467BD"),
}

# systems plotted when none is given on the command line
SELECTED = ["H4P2O7", "aH3P2O7", "bH3P2O7", "Mg2P2O7"]

# ----------------------------------------------------------------------
# Labels. The tags in the data file are rewritten as TS<n> plus a
# superscript identifying the system, so that a level keeps its meaning
# when the figure is looked at on its own. <n> is read from the data
# label ("TS3$_\alpha^+$" -> 3); a system listed in TS_INDEX_OVERRIDE
# takes its indices from that list instead, in file order.
# A system absent from TS_SUPERSCRIPT keeps its data-file label as is.
# ----------------------------------------------------------------------
TS_SUPERSCRIPT = {
    "H4P2O7":  r"$^{4}$",
    "aH3P2O7": r"$^{\alpha 3}$",
    "bH3P2O7": r"$^{\beta 3}$",
    "Mg2P2O7": r"$^{\mathrm{Mg}_{2}}$",
}

# 'ts_energies.txt' labels the four upper Mg2P2O7 levels all as TS2;
# they are taken to be TS2-TS5 in file order.
TS_INDEX_OVERRIDE = {
    "Mg2P2O7": [1, 2, 3, 4, 5],
}

FIGSIZE       = (6.4, 5.2)
BAR_HALFWIDTH = 0.30     # half-length of each level bar (x units)
ERR_ALPHA     = 0.25     # opacity of the +/- error band
VALUE_DY      = 0.030    # gap (axis fraction) between bar and value text
TOP_HEADROOM  = 0.16     # fraction of the y range kept free above the top level
BOT_HEADROOM  = 0.10     # idem below the bottom level
FS_VALUE      = 10       # font size of the energy values
FS_TICK       = 12       # font size of the TS labels on the x axis
ORDER         = "energy" # "energy": ascending barrier;  "file": file order
SHOW_RELATIVE_AXIS = True   # right axis with dDG relative to the lowest TS
CONNECT_LEVELS     = False  # faint guide line joining consecutive levels
# The data file may repeat a label inside one system (distinct energies but
# the same tag). Setting this to True keeps the figure readable by appending
# an occurrence index; a warning is printed either way.
DISAMBIGUATE_DUPLICATE_LABELS = True

YLABEL     = r"$\Delta G^{\ddagger}$ (kcal mol$^{-1}$)"
YLABEL_REL = r"$\Delta\Delta G^{\ddagger}$ (kcal mol$^{-1}$)"

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


def relabel(system, levels):
    """Rewrite the data-file tags as TS<n> + the system superscript."""
    suffix = TS_SUPERSCRIPT.get(system)
    if suffix is None:
        return levels

    indices = TS_INDEX_OVERRIDE.get(system)
    if indices is not None and len(indices) != len(levels):
        raise ValueError(f"TS_INDEX_OVERRIDE['{system}'] has {len(indices)} "
                         f"entries but the data file has {len(levels)} levels")

    out = []
    for k, (label, e, err) in enumerate(levels):
        if indices is not None:
            n = indices[k]
        else:
            match = re.search(r"TS\s*(\d+)", label)
            if match is None:
                raise ValueError(f"cannot read a TS index from '{label}' "
                                 f"in system {system}")
            n = int(match.group(1))
        out.append((f"TS{n}{suffix}", e, err))
    return out


def fix_duplicate_labels(system, levels):
    """Warn about repeated labels inside one system, optionally disambiguate."""
    seen = {}
    for label, _, _ in levels:
        seen[label] = seen.get(label, 0) + 1
    dups = sorted(lab for lab, n in seen.items() if n > 1)
    if not dups:
        return levels

    print(f"warning: {system} repeats the label(s) {', '.join(dups)} "
          f"on levels of different energy - check the data file",
          file=sys.stderr)
    if not DISAMBIGUATE_DUPLICATE_LABELS:
        return levels

    count, out = {}, []
    for label, e, err in levels:
        if seen[label] > 1:
            count[label] = count.get(label, 0) + 1
            label = f"{label}$^{{({count[label]})}}$"
        out.append((label, e, err))
    return out


def build_figure(system, levels):
    """One figure holding only the TS ensemble of `system`."""
    cfg = SYSTEMS[system]
    levels = fix_duplicate_labels(system, relabel(system, levels))
    if ORDER == "energy":
        levels = sorted(levels, key=lambda item: item[1])

    labels = [lab for lab, _, _ in levels]
    energies = np.array([e for _, e, _ in levels])
    errors = np.array([err for _, _, err in levels])
    x = np.arange(len(levels), dtype=float)

    # y window calibrated on this ensemble only, error bars included
    lo = float(np.min(energies - errors))
    hi = float(np.max(energies + errors))
    span = hi - lo
    if span < 1e-6:                      # degenerate ensemble: keep it visible
        span = 1.0
    ymin = lo - BOT_HEADROOM * span
    ymax = hi + TOP_HEADROOM * span
    yrange = ymax - ymin

    fig, ax = plt.subplots(figsize=FIGSIZE)

    if CONNECT_LEVELS:
        ax.plot(x, energies, color=cfg["color"], ls=":", lw=1.0,
                alpha=0.6, zorder=2)

    for xc, e, err in zip(x, energies, errors):
        ax.fill_between([xc - BAR_HALFWIDTH, xc + BAR_HALFWIDTH],
                        e - err, e + err,
                        color=cfg["color"], alpha=ERR_ALPHA,
                        linewidth=0, zorder=2)
        ax.hlines(e, xc - BAR_HALFWIDTH, xc + BAR_HALFWIDTH,
                  color=cfg["color"], lw=3, zorder=3)
        ax.text(xc, e + err + VALUE_DY * yrange,
                f"{e:.1f} $\\pm$ {err:.1f}",
                ha="center", va="bottom", fontsize=FS_VALUE,
                zorder=5, bbox=TEXT_BBOX)

    ax.set_xlim(-0.5, len(levels) - 0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=FS_TICK)
    ax.tick_params(axis="x", length=0)
    ax.set_ylim(ymin, ymax)
    ax.set_ylabel(YLABEL, fontsize=12)
    ax.set_title(cfg["title"], fontsize=15, pad=10)

    if SHOW_RELATIVE_AXIS:
        ref = float(np.min(energies))
        axr = ax.secondary_yaxis(
            "right", functions=(lambda v, r=ref: v - r,
                                lambda v, r=ref: v + r))
        axr.set_ylabel(YLABEL_REL + f"  (ref. {ref:.1f})", fontsize=11)

    for spine in ax.spines.values():
        spine.set_visible(True)

    fig.tight_layout()
    return fig


def main(datafile, systems, outdir="."):
    data = read_levels(datafile)
    for system in systems:
        levels = data[system]
        if not levels:
            print(f"warning: no levels for {system}, skipped", file=sys.stderr)
            continue
        fig = build_figure(system, levels)
        outfile = os.path.join(outdir, f"ts_levels_{system}.png")
        fig.savefig(outfile, dpi=300)
        plt.close(fig)
        print(f"saved {outfile}")


if __name__ == "__main__":
    datafile = sys.argv[1] if len(sys.argv) > 1 else "ts_energies.txt"
    requested = sys.argv[2:]
    if not requested:
        systems = list(SELECTED)
    elif len(requested) == 1 and requested[0].lower() == "all":
        systems = list(SYSTEMS)
    else:
        unknown = [s for s in requested if s not in SYSTEMS]
        if unknown:
            raise SystemExit(f"unknown system tag(s): {', '.join(unknown)}\n"
                             f"available: {', '.join(SYSTEMS)}")
        systems = requested
    main(datafile, systems)
