import re
import sys
import itertools
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
    "bHP2O7":  dict(title=r"$\beta$-HP$_2$O$_7^{3-}$",          color='mediumturquoise'),
    "aHP2O7":  dict(title=r"$\alpha$-HP$_2$O$_7^{3-}$",         color='lawngreen'),
    "Mg2P2O7": dict(title=r"Mg$_2$P$_2$O$_7$",             color="#E69F00"),
    "MgHP2O7": dict(title=r"MgHP$_2$O$_7^{-}$",                color='blueviolet'),
    "H2P2O7":  dict(title=r"H$_2$P$_2$O$_7^{2-}$",         color="#CC79A7"),
    "bH3P2O7": dict(title=r"$\beta$-H$_3$P$_2$O$_7^{-}$",  color="#009E73"),
    "aH3P2O7": dict(title=r"$\alpha$-H$_3$P$_2$O$_7^{-}$", color="#0072B2"),
    "H4P2O7":  dict(title=r"H$_4$P$_2$O$_7$",              color="#9467BD"),
}

# ----------------------------------------------------------------------
# Presentation framing.
#
# With all ten species on one 16:9 canvas each column is a tenth of the
# width, so what a level carries is what sets the size of the whole
# figure. Two redundancies are therefore dropped: the species
# superscript of a label, which the column title already gives, and the
# uncertainty, which stays in the data file. Each level is written as
#
#                          TS1   28.8
#                   ========================
#
# on a single line stacked over its own bar.
#
# Nothing is hard-coded: every string is measured with the real renderer
# and the font size is bisected up to the largest value at which every
# column still fits inside its own slot, never touching the dashed
# separators.
#
# Levels too close to be told apart vertically -- three of the P2O7
# levels lie within 0.8 kcal/mol, which at this scale is thinner than
# the bars themselves -- are drawn side by side at their true energies,
# the column being split into one slot per level. The script searches,
# for every column, the cheapest such partition that can actually be
# placed, so a level keeps its own full width bar unless it has to share.
# ----------------------------------------------------------------------
FIGSIZE        = (13.333, 7.5)   # 16:9 slide canvas (inches)
DPI_OUT        = 300
MARGINS        = dict(left=0.085, right=0.985, bottom=0.090, top=0.975)

STRIP_SUPERSCRIPT = True  # drop the '$^{...}$' species tag from labels
SHOW_ERROR        = False # write the uncertainty next to the energy

COL_MARGIN     = 0.030   # dead band kept clear next to each dashed line
BAR_WIDTH      = 0.80    # bar length (column units)
LABEL_VALUE_SEP = "   "  # spacing between the TS name and its energy
DEG_GAP        = 0.030   # gap between the bars of a cluster
CLUSTER_STYLE  = "stacked"
                         # how a cluster writes its levels. "stacked":
                         # each slot carries its own name with its own
                         # energy underneath, on two short rows. A full
                         # 'name   energy' line does not fit a slot,
                         # whereas either half of it does, so this is
                         # what lets the rest of the figure keep its
                         # size. "shared": a name over each bar and the
                         # energies listed once on a common row, which
                         # is wider and so limits clusters to two bars.
INNER_GAP      = 0.15    # gap between the two rows of a cluster, in
                         # units of text height

TEXT_BAR_GAP   = 0.22    # bar -> text gap, in units of text height
CLEARANCE      = 0.16    # min free space around a text block, in units
                         # of text height
YPAD           = 2.5     # extra y-range below/above the extreme levels.
                         # The crowded low end of H$_4$P$_2$O$_7$ needs
                         # room under its lowest bar; 2.5 is the best
                         # compromise, beyond it the wider range costs
                         # more than the room gains.

FS_BOUNDS      = (4.0, 44.0)   # search window for the auto-fitted size
BAR_LW_FAC     = 0.45    # bar linewidth (points), relative to font size

# The chrome -- column titles, axis label, tick numbers -- is NOT tied to
# the level font. The level font is capped by the crowding of the levels,
# while the chrome is only limited by the column width and by the
# margins, which are grown to fit it.
CHROME_MAX     = 26.0    # cap on the chrome size (pt)
TITLE_SCALE    = 0.75    # column titles, relative to the size the column
                         # width would allow. The axis label and the tick
                         # numbers are not affected by it.
TICK_REL       = 0.80    # y tick labels, relative to the column titles
YLABEL_REL     = 0.85    # y axis label, relative to the column titles
TITLE_PAD      = 8.0     # pt, frame -> column titles
TICK_PAD       = 6.0     # pt, frame -> tick numbers
LABEL_PAD      = 8.0     # pt, tick numbers -> axis label

YLABEL         = r"$\Delta G^{\ddagger}$ (kcal mol$^{-1}$)"
TEXT_BBOX = dict(facecolor="white", edgecolor="none", pad=1.0)

_MEASURED = {}


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


# ---- layout core, spliced into TS_barplot.py ----
def strip_tag(label):
    """Drop the species superscript; the column title already gives it."""
    return re.sub(r"\$\^.*\$\s*$", "", label) if STRIP_SUPERSCRIPT else label


def level_string(label, energy, error):
    """The one line written next to a level."""
    text = f"{strip_tag(label)}{LABEL_VALUE_SEP}{energy:.1f}"
    return f"{text} $\\pm$ {error:.1f}" if SHOW_ERROR else text


def measure(ax, renderer, string, fontsize):
    """
    Rendered (width, height) of a string, in pixels, at the size it will
    actually be drawn. Font metrics are not exactly proportional to the
    point size, so every candidate size is measured rather than scaled
    from a reference one; results are cached because the bisection asks
    for the same string many times.
    """
    key = (string, round(fontsize, 3))
    if key not in _MEASURED:
        art = ax.text(0, 0, string, fontsize=fontsize)
        bb = art.get_window_extent(renderer=renderer)
        art.remove()
        _MEASURED[key] = (bb.width, bb.height)
    return _MEASURED[key]


def value_only(energy, error):
    """The energy of one level, written on its own row inside a cluster."""
    return (f"{energy:.1f} $\\pm$ {error:.1f}" if SHOW_ERROR
            else f"{energy:.1f}")


def cluster_value(energies):
    """The shared energy row of a cluster: every distinct energy."""
    return " / ".join(f"{e:.1f}" for e in sorted(set(energies)))


def column_metrics(data):
    """Levels of each column, sorted by energy, with the lines to draw."""
    cols = []
    for system in SYSTEMS:
        levels = sorted(data[system], key=lambda t: t[1])
        cols.append(dict(
            system=system,
            e=[e for _, e, _ in levels],
            text=[level_string(lab, e, err) for lab, e, err in levels],
            name=[strip_tag(lab) for lab, _, _ in levels],
            value=[value_only(e, err) for _, e, err in levels]))
    return cols


def partitions(energies):
    """
    Every way of cutting a column's levels into consecutive clusters,
    cheapest first. A cut is not allowed between two exactly degenerate
    levels, which must always share a cluster. Ordering puts the
    partitions that cluster the fewest levels first, so a column is only
    split side-by-side where it has to be.
    """
    n = len(energies)
    out = []
    for mask in range(1 << max(n - 1, 0)):
        groups, start = [], 0
        for i in range(n - 1):
            if mask >> i & 1:
                if energies[i] == energies[i + 1]:
                    break
                groups.append(list(range(start, i + 1)))
                start = i + 1
        else:
            groups.append(list(range(start, n)))
            clustered = sum(len(g) for g in groups if len(g) > 1)
            out.append((clustered, len(groups), groups))
    out.sort(key=lambda t: (t[0], t[1]))
    return [g for _, _, g in out]


def slot_pitch(m):
    """Centre-to-centre spacing of the m bars of a cluster."""
    return BAR_WIDTH / m if m > 1 else BAR_WIDTH


def sub_bar_width(m):
    """Width of one bar of a cluster of m levels."""
    return (BAR_WIDTH - (m - 1) * DEG_GAP) / m if m > 1 else BAR_WIDTH


def place_blocks(bands, bars, clear, half_th, ylim):
    """
    Put each cluster's text block above or below its bars.

    `bands[i]` is the (above, below) pair of vertical spans of block i
    and `bars[i]` the energies it owns. A block is checked against the
    other blocks and against every bar it does not own; the bars of its
    own cluster are exempt, being side by side with it in x. Returns the
    above/below flags, or None if no assignment is clear everywhere.
    """
    n = len(bands)
    ylo, yhi = ylim

    def overlap(a, b):
        return min(a[1], b[1]) - max(a[0], b[0]) > -clear

    for combo in sorted(itertools.product([False, True], repeat=n),
                        key=lambda c: (sum(c), c)):
        spans = [bands[i][1] if combo[i] else bands[i][0] for i in range(n)]
        if any(s[0] < ylo + clear or s[1] > yhi - clear for s in spans):
            continue
        if any(overlap(spans[i], spans[j])
               for i in range(n) for j in range(i + 1, n)):
            continue
        if any(overlap(spans[i], (e - half_th, e + half_th))
               for i in range(n) for j in range(n) if i != j
               for e in bars[j]):
            continue
        return list(combo)
    return None


def layout_at(fs, cols, ax, renderer, px_col, px_y, ylim):
    """
    Try to lay the plot out with level font size `fs`; None if it does
    not fit. For every column the cheapest partition into clusters that
    can actually be placed is kept, so levels stay on their own full
    width bar unless they are too close to be told apart vertically.
    """
    usable = 1.0 - 2.0 * COL_MARGIN
    h_ref = measure(ax, renderer, "TS1", fs)[1] / px_y
    half_th = 0.5 * max(3.0, BAR_LW_FAC * fs) * (100.0 / 72.0) / px_y
    gap = half_th + TEXT_BAR_GAP * h_ref
    clear = CLEARANCE * h_ref

    chosen = []
    for col in cols:
        sizes = [measure(ax, renderer, t, fs) for t in col["text"]]
        widths = [w / px_col for w, _ in sizes]
        heights = [h / px_y for _, h in sizes]
        n_sizes = [measure(ax, renderer, t, fs) for t in col["name"]]
        n_widths = [w / px_col for w, _ in n_sizes]
        n_heights = [h / px_y for _, h in n_sizes]
        v_sizes = [measure(ax, renderer, t, fs) for t in col["value"]]
        v_widths = [w / px_col for w, _ in v_sizes]
        v_heights = [h / px_y for _, h in v_sizes]
        energies = col["e"]

        found = None
        for groups in partitions(energies):
            ok = True
            depths = []
            for g in groups:
                m = len(g)
                if m == 1:
                    if widths[g[0]] > usable:
                        ok = False
                        break
                    depths.append(heights[g[0]])
                elif CLUSTER_STYLE == "stacked":
                    # each slot: its own name with its own energy under it
                    h_name = max(n_heights[i] for i in g)
                    need = max(max(n_widths[i], v_widths[i]) for i in g)
                    if need > slot_pitch(m):
                        ok = False
                        break
                    depths.append(h_name + INNER_GAP * h_name
                                  + max(v_heights[i] for i in g))
                else:
                    # a name over each bar, energies on one shared row
                    v_w, v_h = measure(ax, renderer,
                                       cluster_value([energies[i] for i in g]),
                                       fs)
                    h_name = max(n_heights[i] for i in g)
                    if (max(n_widths[i] for i in g) > slot_pitch(m)
                            or v_w / px_col > usable):
                        ok = False
                        break
                    depths.append(h_name + INNER_GAP * h_name + v_h / px_y)
            if not ok:
                continue
            bands, bars = [], []
            for g, h in zip(groups, depths):
                lo, hi = energies[g[0]], energies[g[-1]]
                bands.append(((lo + gap, hi + gap + h),
                              (lo - gap - h, hi - gap)))
                bars.append([energies[i] for i in g])
            flags = place_blocks(bands, bars, clear, half_th, ylim)
            if flags is not None:
                found = (groups, flags)
                break
        if found is None:
            return None
        chosen.append(found)

    return dict(chosen=chosen, gap=gap, half_th=half_th)


def fit_font_size(cols, ax, renderer, px_col, px_y, ylim):
    """Largest font size (bisection) for which layout_at still fits."""
    lo, hi = FS_BOUNDS
    if layout_at(lo, cols, ax, renderer, px_col, px_y, ylim) is None:
        raise RuntimeError("even the smallest font does not fit; reduce "
                           "BAR_WIDTH, shorten the labels or enlarge FIGSIZE")
    if layout_at(hi, cols, ax, renderer, px_col, px_y, ylim) is not None:
        return hi
    for _ in range(24):
        mid = 0.5 * (lo + hi)
        if layout_at(mid, cols, ax, renderer, px_col, px_y, ylim) is None:
            hi = mid
        else:
            lo = mid
    return lo


def chrome_sizes(ax, renderer, px_col, box_h):
    """
    Largest column-title size that the column width allows, plus the
    axis sizes derived from it. The rotated y-axis label must also stay
    shorter than the axes box.
    """
    usable = 1.0 - 2.0 * COL_MARGIN
    fs = CHROME_MAX
    for _ in range(8):
        w = max(measure(ax, renderer, cfg["title"], fs)[0]
                for cfg in SYSTEMS.values())
        w_ylabel = measure(ax, renderer, YLABEL, fs * YLABEL_REL)[0]
        over = max(w / (usable * px_col), w_ylabel / (0.95 * box_h))
        if over <= 1.0:
            break
        fs /= over
    return fs * TITLE_SCALE, fs * TICK_REL, fs * YLABEL_REL


def fit_margins(fig, ax, ncol, ylim):
    """
    Grow the left and bottom margins until they hold the chrome at its
    own size. The axes box changes as they grow, so this is iterated.
    """
    margins = dict(MARGINS)
    pt = fig.dpi / 72.0
    fig_w, fig_h = FIGSIZE[0] * fig.dpi, FIGSIZE[1] * fig.dpi
    for _ in range(6):
        fig.subplots_adjust(**margins)
        ax.set_xlim(-0.5, ncol - 0.5)
        ax.set_ylim(*ylim)
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        box = ax.get_window_extent(renderer=renderer)
        fs_title, fs_tick, fs_ylabel = chrome_sizes(
            ax, renderer, box.width / ncol, box.height)
        h_title = max(measure(ax, renderer, cfg["title"], fs_title)[1]
                      for cfg in SYSTEMS.values())
        w_tick = max(measure(ax, renderer, f"{t:.0f}", fs_tick)[0]
                     for t in ax.get_yticks())
        h_ylabel = measure(ax, renderer, YLABEL, fs_ylabel)[1]
        new = dict(margins,
                   bottom=(h_title + TITLE_PAD * pt) / fig_h,
                   left=(w_tick + h_ylabel
                         + (TICK_PAD + LABEL_PAD) * pt) / fig_w)
        settled = (abs(new["bottom"] - margins["bottom"]) < 0.002
                   and abs(new["left"] - margins["left"]) < 0.002)
        margins = new
        if settled:
            break
    fig.subplots_adjust(**margins)
    fig.canvas.draw()
    return fs_title, fs_tick, fs_ylabel


def verify(fig, ax, ncol):
    """
    Safety net: re-measure every bar and every text actually drawn and
    check that nothing crosses a dashed separator and that no two of
    them overlap. Prints the smallest clearance found.
    """
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = [(t.get_text(), t.get_window_extent(renderer=renderer))
             for t in ax.texts]
    for coll in ax.collections:
        lw_px = coll.get_linewidth()[0] * fig.dpi / 72.0
        for seg in coll.get_segments():
            (x0, y0), (x1, y1) = ax.transData.transform(seg)
            boxes.append(("bar", matplotlib.transforms.Bbox.from_extents(
                min(x0, x1), min(y0, y1) - 0.5 * lw_px,
                max(x0, x1), max(y0, y1) + 0.5 * lw_px)))

    bad, worst = [], 1.0
    inv = ax.transData.inverted()
    for name, bb in boxes:
        (x0, _), (x1, _) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
        i = min(max(int(round(0.5 * (x0 + x1))), 0), ncol - 1)
        clear = min(x0 - (i - 0.5), (i + 0.5) - x1)
        worst = min(worst, clear)
        if clear < 0:
            bad.append(f"'{name}' crosses its separator by {-clear:.3f}")
    for k, (na, ba) in enumerate(boxes):
        for nb, bb in boxes[k + 1:]:
            if ba.overlaps(bb):
                bad.append(f"'{na}' overlaps '{nb}'")

    if bad:
        for msg in bad:
            print(f"  !! {msg}")
        print("layout check           : FAILED")
        return False
    print(f"layout check           : OK (no overlap, min clearance "
          f"{worst:.3f} column widths)")
    return True


def build_figure(data):
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ncol = len(SYSTEMS)
    all_e = [e for lv in data.values() for _, e, _ in lv]
    ylim = (min(all_e) - YPAD, max(all_e) + YPAD)

    fs_title, fs_tick, fs_ylabel = fit_margins(fig, ax, ncol, ylim)

    renderer = fig.canvas.get_renderer()
    box = ax.get_window_extent(renderer=renderer)
    px_col = box.width / ncol                # pixels per column (= x unit)
    px_y = box.height / (ylim[1] - ylim[0])  # pixels per kcal/mol

    cols = column_metrics(data)
    fs = fit_font_size(cols, ax, renderer, px_col, px_y, ylim)
    geo = layout_at(fs, cols, ax, renderer, px_col, px_y, ylim)
    gap = geo["gap"]
    bar_lw = max(3.0, BAR_LW_FAC * fs)
    clustered = 0

    for i, (col, (groups, flags)) in enumerate(zip(cols, geo["chosen"])):
        color = SYSTEMS[col["system"]]["color"]
        for group, below in zip(groups, flags):
            m = len(group)
            sub = sub_bar_width(m)
            pitch = slot_pitch(m)
            x0 = i - 0.5 * BAR_WIDTH + 0.5 * sub
            if m > 1:
                clustered += m
            shared = m > 1 and CLUSTER_STYLE == "shared"
            stacked = m > 1 and CLUSTER_STYLE == "stacked"
            va = "top" if below else "bottom"
            sign = -1.0 if below else 1.0
            for k, idx in enumerate(group):
                xc = x0 + k * pitch if m > 1 else i
                e = col["e"][idx]
                ax.hlines(e, xc - 0.5 * sub, xc + 0.5 * sub, color=color,
                          lw=bar_lw, zorder=3)
                ax.text(xc, e + sign * gap,
                        col["text"][idx] if m == 1 else col["name"][idx],
                        ha="center", va=va, fontsize=fs, zorder=5,
                        bbox=TEXT_BBOX)
                if stacked:
                    h_name = measure(ax, renderer, col["name"][idx],
                                     fs)[1] / px_y
                    ax.text(xc, e + sign * (gap + h_name
                                            + INNER_GAP * h_name),
                            col["value"][idx], ha="center", va=va,
                            fontsize=fs, zorder=5, bbox=TEXT_BBOX)
            if shared:
                es = [col["e"][idx] for idx in group]
                h_name = max(measure(ax, renderer, col["name"][idx], fs)[1]
                             for idx in group) / px_y
                y = (min(es) if below else max(es)) + sign * (
                    gap + h_name + INNER_GAP * h_name)
                ax.text(i, y, cluster_value(es), ha="center", va=va,
                        fontsize=fs, zorder=5, bbox=TEXT_BBOX)

    # dashed separators between columns
    for x in np.arange(0.5, ncol - 0.5, 1.0):
        ax.axvline(x, color="lightgray", ls="--", lw=1.4, zorder=1)

    ax.set_xticks(range(ncol))
    ax.set_xticklabels([cfg["title"] for cfg in SYSTEMS.values()],
                       fontsize=fs_title)
    ax.tick_params(axis="x", length=0, pad=TITLE_PAD)
    ax.tick_params(axis="y", labelsize=fs_tick, width=1.6, length=7,
                   pad=TICK_PAD)
    ax.set_ylabel(YLABEL, fontsize=fs_ylabel, labelpad=LABEL_PAD)

    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(1.6)

    n_levels = sum(len(c["e"]) for c in cols)
    print(f"canvas                 : {FIGSIZE[0]:.2f} x {FIGSIZE[1]:.2f} in")
    print(f"columns / levels       : {ncol} / {n_levels}"
          f" ({clustered} drawn side by side)")
    print(f"level font size        : {fs:.1f} pt")
    print(f"column title font size : {fs_title:.1f} pt")
    print(f"axis label / ticks     : {fs_ylabel:.1f} / {fs_tick:.1f} pt")
    print(f"bar length / linewidth : {BAR_WIDTH:.2f} column widths / "
          f"{bar_lw:.1f} pt")
    verify(fig, ax, ncol)
    return fig, ax


def main(datafile, outfile="ts_levels_v3.png"):
    data = read_levels(datafile)
    fig, _ = build_figure(data)
    fig.savefig(outfile, dpi=DPI_OUT)
    print(f"saved {outfile}")


if __name__ == "__main__":
    datafile = sys.argv[1] if len(sys.argv) > 1 else "ts_energies.txt"
    outfile = sys.argv[2] if len(sys.argv) > 2 else "ts_levels_v3.png"
    main(datafile, outfile)
