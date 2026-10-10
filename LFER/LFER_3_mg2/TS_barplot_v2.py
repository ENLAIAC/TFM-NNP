#!/usr/bin/env python3
"""
TS_barplot_v2.py -- transition-state level diagram for the PPi protonation
                    / Mg-complexation spectrum.

Rewrite of TS_barplot.py (which is left untouched).  Reads the same
'ts_energies.txt' format:

    <system>  <label>  <energy>  <error>

What changed with respect to v1
-------------------------------
1. Palette is chemistry-encoded instead of arbitrary: the protonation ramp
   (0H -> 4H) is a perceptual sequential map, the alpha isomer of a given
   protonation state is the lighter tint of its beta partner, and the three
   Mg-bearing species carry their own warm ramp.
2. v1 used spread_labels(), which nudged the *text* vertically while leaving
   the *bar* at its true energy -- so in P2O7 the "41.9 +/- 0.6" label did not
   sit at 41.9.  That is gone.  Text now always stays at the energy of its own
   bar; crowding is resolved by moving *bars* horizontally instead.
3. The figure is no longer a fixed 24x8 canvas.  Column widths are measured
   from the real rendered text extents, so the canvas is exactly as wide as it
   needs to be and the aspect ratio is balanced (~1.6:1).
4. A verification pass measures every drawn artist and refuses to save a
   figure that still contains an overlap.

Layout rules (as specified)
---------------------------
* Every species gets its own box delimited by light-grey dashed lines.
* isolated level        : bar centred, TS name to the left, energy to the right.
* near-degenerate pair  : higher level shifted right  -> TS name on top of the
                          bar, energy text to its left;
                          lower level shifted left    -> TS name under the bar,
                          energy text to its right.
* exact tie (equal E)   : bars side by side, each with its own TS name on top,
                          and ONE shared energy label on the left carrying both
                          uncertainties slash-separated ("25.0 +/- 0.1/0.7").
* tie + near neighbour  : the tie stays centred as above; the neighbour is drawn
                          centred at its own energy, TS name on top, energy on
                          the right.
* three or more crowded : bars occupy one slot each at their true energies
                          (highest leftmost) and are joined by leader lines to a
                          de-crowded "TSname  E +/- err" list at the right of the
                          species box.

Usage:  python3 TS_barplot_v2.py [ts_energies.txt] [ts_levels_v2.png]
"""

import sys

import matplotlib
matplotlib.use("Agg")                 # safe on headless nodes / HPC
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle


# ----------------------------------------------------------------------
# Palette: chemistry-encoded.
#   H_RAMP[k]   -> k protons on a purely protonated pyrophosphate
#   lighten(c)  -> alpha isomer of the beta species sharing that ramp stop
#   MG_RAMP[k]  -> the three Mg-bearing species
# ----------------------------------------------------------------------
H_RAMP = matplotlib.colormaps["viridis"](np.linspace(0.05, 0.66, 5))
MG_RAMP = matplotlib.colormaps["YlOrRd"](np.linspace(0.45, 0.88, 3))


def lighten(rgba, f=0.30):
    """Blend a colour f of the way towards white (alpha isomer tint)."""
    r, g, b, a = rgba
    return (r + (1.0 - r) * f, g + (1.0 - g) * f, b + (1.0 - b) * f, a)


# Column order left-to-right is kept exactly as in v1.
SYSTEMS = {
    "P2O7":    dict(title=r"P$_2$O$_7^{4-}$",              color=H_RAMP[0]),
    "MgP2O7":  dict(title=r"MgP$_2$O$_7^{2-}$",            color=MG_RAMP[0]),
    "bHP2O7":  dict(title=r"$\beta$-HP$_2$O$_7$",          color=H_RAMP[1]),
    "aHP2O7":  dict(title=r"$\alpha$-HP$_2$O$_7$",         color=lighten(H_RAMP[1])),
    "Mg2P2O7": dict(title=r"Mg$_2$P$_2$O$_7$",             color=MG_RAMP[1]),
    "MgHP2O7": dict(title=r"MgHP$_2$O$_7$",                color=MG_RAMP[2]),
    "H2P2O7":  dict(title=r"H$_2$P$_2$O$_7^{2-}$",         color=H_RAMP[2]),
    "bH3P2O7": dict(title=r"$\beta$-H$_3$P$_2$O$_7^{-}$",  color=H_RAMP[3]),
    "aH3P2O7": dict(title=r"$\alpha$-H$_3$P$_2$O$_7^{-}$", color=lighten(H_RAMP[3])),
    "H4P2O7":  dict(title=r"H$_4$P$_2$O$_7$",              color=H_RAMP[4]),
}

# ----------------------------------------------------------------------
# Geometry.  The x data coordinate of the axes IS inches (see build_figure),
# so every horizontal constant below is in inches and text extents measured
# from the renderer can be used directly.
# ----------------------------------------------------------------------
ASPECT       = 1.60    # figure width / height before the anti-collision growth
FS_ANNOT     = 8.5     # TS names and energy values
FS_TICK      = 12.0    # species titles under each column
FS_YLABEL    = 12.5

BAR_HW       = 0.110   # half length of a level bar, inches
BAR_LW       = 3.2     # line width of a level bar, points
GAP_X        = 0.078   # bar end  -> side text, inches (must exceed the label bbox pad)
GAP_Y        = 0.055   # bar      -> text above/below, in inches (converted)
COL_PAD      = 0.075   # inner margin between content and the dashed box edge

TIE_GAP      = 0.090   # clear space between the bars/names of a tie group
LEADER_GAP   = 0.090   # spacing between the bars of a leader cluster
HUB_RUN      = 0.105   # bars -> leader hub, inches
HUB_TO_TEXT  = 0.095   # leader hub -> text, inches

# Crowding thresholds, expressed in multiples of one rendered text line.
CLUSTER_MULT = 2.00    # gap below this  -> the default layout is too cramped
HARD_MULT    = 1.05    # gap below this  -> texts would literally overlap

MARGIN_L     = 1.00    # inches reserved for the y axis + label
MARGIN_R     = 0.18
MARGIN_B     = 0.72    # inches reserved for the species titles
MARGIN_T     = 0.22

DPI          = 200
Y_PAD        = 1.8     # kcal/mol of headroom below the lowest / above the highest bar

YLABEL       = r"$\Delta G^{\ddagger}$ (kcal mol$^{-1}$)"
BOX_COLOR    = "0.72"
TEXT_BBOX    = dict(facecolor="white", edgecolor="none", pad=0.9, alpha=0.85)


# ----------------------------------------------------------------------
# Text measurement
# ----------------------------------------------------------------------
_scratch_fig = plt.figure(figsize=(4.0, 4.0), dpi=100)
_scratch_ax = _scratch_fig.add_axes([0.0, 0.0, 1.0, 1.0])
_scratch_ax.set_axis_off()
_scratch_fig.canvas.draw()
_extent_cache = {}


def text_size(s, fs=FS_ANNOT):
    """(width, height) of a rendered string, in inches."""
    key = (s, fs)
    if key not in _extent_cache:
        t = _scratch_ax.text(0.5, 0.5, s, fontsize=fs)
        bb = t.get_window_extent(renderer=_scratch_fig.canvas.get_renderer())
        t.remove()
        _extent_cache[key] = (bb.width / _scratch_fig.dpi + 2 * 0.012,
                              bb.height / _scratch_fig.dpi + 2 * 0.012)
    return _extent_cache[key]


# ----------------------------------------------------------------------
# Input
# ----------------------------------------------------------------------
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
                raise ValueError("Unknown system tag '%s' (expected one of %s)"
                                 % (system, list(SYSTEMS)))
            data[system].append((label, float(energy), float(error)))
    return data


def make_items(levels):
    """
    Collapse a species' levels into 'items', highest energy first.
    An item is either a single level or a tie group (>1 level, identical E).
    """
    by_energy = {}
    order = []
    for label, e, err in levels:
        key = round(e, 6)
        if key not in by_energy:
            by_energy[key] = []
            order.append(key)
        by_energy[key].append((label, e, err))
    items = [dict(energy=key, members=by_energy[key]) for key in order]
    items.sort(key=lambda it: -it["energy"])
    return items


def energy_text(e, errs):
    """Energy label; a tie carries every distinct uncertainty, slash-separated."""
    uniq = sorted(set(round(u, 6) for u in errs))
    err_s = "/".join("%.1f" % u for u in uniq)
    return "%.1f $\\pm$ %s" % (e, err_s)


# ----------------------------------------------------------------------
# Layout: turn one species' items into positioned elements.
#
# Elements are dicts in LOCAL inches (x) / kcal (y); the whole column is
# recentred afterwards, so the local origin is arbitrary.
#   bar  : x, hw, y
#   text : x, y, s, ha, va
#   lead : pts = [(x, y), ...]
# ----------------------------------------------------------------------
def cluster_items(items, line_h):
    """Split the (descending) item list into vertically crowded clusters."""
    sep = CLUSTER_MULT * line_h
    clusters, cur = [], [items[0]]
    for prev, it in zip(items, items[1:]):
        if prev["energy"] - it["energy"] < sep:
            cur.append(it)
        else:
            clusters.append(cur)
            cur = [it]
    clusters.append(cur)
    return clusters


def spread(y_true, min_sep):
    """Push a set of text ordinates apart, keeping their centre of mass."""
    y = np.asarray(y_true, dtype=float)
    if len(y) < 2:
        return y.copy()
    order = np.argsort(y)
    adj = y[order].copy()
    for i in range(1, len(adj)):
        if adj[i] - adj[i - 1] < min_sep:
            adj[i] = adj[i - 1] + min_sep
    adj -= adj.mean() - y[order].mean()
    out = np.empty_like(adj)
    out[order] = adj
    return out


def emit_default(item, out):
    label, e, err = item["members"][0]
    out.append(dict(k="bar", x=0.0, hw=BAR_HW, y=e))
    out.append(dict(k="text", x=-(BAR_HW + GAP_X), y=e, s=label,
                    ha="right", va="center"))
    out.append(dict(k="text", x=BAR_HW + GAP_X, y=e,
                    s=energy_text(e, [err]), ha="left", va="center"))


def emit_tie(item, gy, out, x0=0.0, channel=0.0):
    """Side-by-side bars, TS name on top of each, one shared energy on the left.

    'channel' forces a minimum clear horizontal corridor between the bars, used
    when a near neighbour is drawn centred underneath and its own TS name has to
    pass between them without ever touching a bar."""
    members = item["members"]
    e = item["energy"]
    n = len(members)
    w_names = [text_size(m[0])[0] for m in members]
    pitch = max(2 * BAR_HW + TIE_GAP, max(w_names) + TIE_GAP,
                2 * BAR_HW + channel)
    left = None
    for k, (label, _, _) in enumerate(members):
        xc = x0 + (k - (n - 1) / 2.0) * pitch
        out.append(dict(k="bar", x=xc, hw=BAR_HW, y=e))
        out.append(dict(k="text", x=xc, y=e + gy, s=label,
                        ha="center", va="bottom"))
        edge = min(xc - BAR_HW, xc - w_names[k] / 2.0)
        left = edge if left is None else min(left, edge)
    errs = [m[2] for m in members]
    out.append(dict(k="text", x=left - GAP_X, y=e,
                    s=energy_text(e, errs), ha="right", va="center"))


def side_reach(label):
    """How far a side text must clear the bar centre: a TS name sitting on top
    of the bar is wider than the bar itself and would otherwise overhang into
    the energy text drawn beside it."""
    return max(BAR_HW, text_size(label)[0] / 2.0) + GAP_X


def emit_pair(hi, lo, gy, out):
    """Higher level shifted right (name on top, energy left);
       lower level shifted left (name below, energy right)."""
    lab_h, e_h, err_h = hi["members"][0]
    lab_l, e_l, err_l = lo["members"][0]
    # As wide a shift as possible while the two energy texts stay x-disjoint,
    # so the pair visibly reads as two offset bars.
    shift = (side_reach(lab_h) + side_reach(lab_l)) / 2.0 - 0.014

    out.append(dict(k="bar", x=shift, hw=BAR_HW, y=e_h))
    out.append(dict(k="text", x=shift, y=e_h + gy, s=lab_h,
                    ha="center", va="bottom"))
    out.append(dict(k="text", x=shift - side_reach(lab_h), y=e_h,
                    s=energy_text(e_h, [err_h]), ha="right", va="center"))

    out.append(dict(k="bar", x=-shift, hw=BAR_HW, y=e_l))
    out.append(dict(k="text", x=-shift, y=e_l - gy, s=lab_l,
                    ha="center", va="top"))
    out.append(dict(k="text", x=-shift + side_reach(lab_l), y=e_l,
                    s=energy_text(e_l, [err_l]), ha="left", va="center"))


def emit_tie_with_neighbour(cluster, gy, out):
    """A tie group plus one nearby single level: both stay centred, the
    neighbour's TS name goes on the side facing away from the tie."""
    tie = [it for it in cluster if len(it["members"]) > 1][0]
    others = [it for it in cluster if it is not tie]
    channel = 0.0
    if len(tie["members"]) > 1:
        widest = max(text_size(it["members"][0][0])[0] for it in others)
        channel = widest + 2 * TIE_GAP
    emit_tie(tie, gy, out, channel=channel)
    for it in others:
        label, e, err = it["members"][0]
        below = e < tie["energy"]
        out.append(dict(k="bar", x=0.0, hw=BAR_HW, y=e))
        out.append(dict(k="text", x=0.0, y=e + (gy if below else -gy), s=label,
                        ha="center", va="bottom" if below else "top"))
        out.append(dict(k="text", x=side_reach(label), y=e,
                        s=energy_text(e, [err]), ha="left", va="center"))


def emit_leader(cluster, gy, line_h, out):
    """Crowded levels: the bars stay aligned on the column axis at their true
    energies, and leader lines carry the eye out to a de-crowded label list at
    the right of the species box."""
    entries = []
    right = -1e9
    for it in cluster:
        e = it["energy"]
        members = it["members"]
        n = len(members)
        for k in range(n):                       # a tie inside a cluster keeps
            xc = (k - (n - 1) / 2.0) * (2 * BAR_HW + TIE_GAP)   # its two bars
            out.append(dict(k="bar", x=xc, hw=BAR_HW, y=e))
            right = max(right, xc + BAR_HW)
        entries.append((e, "%s   %s"
                        % (" / ".join(m[0] for m in members),
                           energy_text(e, [m[2] for m in members]))))

    hub = right + HUB_RUN
    tx = hub + HUB_TO_TEXT
    y_adj = spread([en[0] for en in entries], CLUSTER_MULT * line_h)
    for (e, label), ya in zip(entries, y_adj):
        out.append(dict(k="text", x=tx, y=ya, s=label, ha="left", va="center"))
        out.append(dict(k="lead", pts=[(right + 0.022, e), (hub, e),
                                       (hub, ya), (tx - 0.028, ya)]))


def layout_species(items, line_h, gy):
    """Positioned elements for one species, recentred on its column."""
    out = []
    if not items:
        return out, 0.0
    for cluster in cluster_items(items, line_h):
        n = len(cluster)
        has_tie = any(len(it["members"]) > 1 for it in cluster)
        if n == 1:
            if has_tie:
                emit_tie(cluster[0], gy, out)
            else:
                emit_default(cluster[0], out)
        elif has_tie:
            emit_tie_with_neighbour(cluster, gy, out)
        else:
            # Crowded is only a suspicion: try the plain centred layout first and
            # keep it whenever the labels genuinely clear one another, so bars are
            # only displaced when there is something real to fix.
            trial = []
            for it in cluster:
                emit_default(it, trial)
            if not overlapping_pairs(trial, line_h):
                out.extend(trial)
            elif n == 2 and (cluster[0]["energy"] - cluster[1]["energy"]
                             >= HARD_MULT * line_h):
                emit_pair(cluster[0], cluster[1], gy, out)
            else:
                emit_leader(cluster, gy, line_h, out)

    lo, hi = element_x_span(out)
    dx = -(lo + hi) / 2.0
    for el in out:
        if el["k"] == "lead":
            el["pts"] = [(x + dx, y) for x, y in el["pts"]]
        else:
            el["x"] += dx
    return out, (hi - lo) + 2 * COL_PAD


def text_x_span(el):
    w = text_size(el["s"])[0]
    if el["ha"] == "left":
        return el["x"], el["x"] + w
    if el["ha"] == "right":
        return el["x"] - w, el["x"]
    return el["x"] - w / 2.0, el["x"] + w / 2.0


def text_y_span(el, line_h):
    h = line_h
    if el["va"] == "bottom":
        return el["y"], el["y"] + h
    if el["va"] == "top":
        return el["y"] - h, el["y"]
    return el["y"] - h / 2.0, el["y"] + h / 2.0


def element_x_span(elements):
    lo, hi = None, None
    for el in elements:
        if el["k"] == "bar":
            a, b = el["x"] - el["hw"], el["x"] + el["hw"]
        elif el["k"] == "text":
            a, b = text_x_span(el)
        else:
            xs = [p[0] for p in el["pts"]]
            a, b = min(xs), max(xs)
        lo = a if lo is None else min(lo, a)
        hi = b if hi is None else max(hi, b)
    return lo, hi


# ----------------------------------------------------------------------
# Collision check
# ----------------------------------------------------------------------
def boxes(elements, line_h):
    """Bounding boxes used for the overlap test.  Text boxes are inflated by
    the white bbox padding actually painted by matplotlib plus a safety
    margin, and bars by half their stroke weight -- without this the check
    passes while the rendered label still clips a bar end."""
    kcal_per_in = line_h / (FS_ANNOT * 1.32 / 72.0)
    pad_in = TEXT_BBOX["pad"] / 72.0 + 0.014
    pad_y = pad_in * kcal_per_in
    bar_half = (BAR_LW / 2.0 / 72.0) * kcal_per_in
    out = []
    for el in elements:
        if el["k"] == "text":
            x0, x1 = text_x_span(el)
            y0, y1 = text_y_span(el, line_h)
            out.append((x0 - pad_in, x1 + pad_in, y0 - pad_y, y1 + pad_y,
                        "text %r" % el["s"]))
        elif el["k"] == "bar":
            out.append((el["x"] - el["hw"], el["x"] + el["hw"],
                        el["y"] - bar_half, el["y"] + bar_half,
                        "bar @%.1f" % el["y"]))
    return out


def overlapping_pairs(elements, line_h):
    bad = []
    bx = boxes(elements, line_h)
    for i in range(len(bx)):
        for j in range(i + 1, len(bx)):
            a, b = bx[i], bx[j]
            if a[0] < b[1] and b[0] < a[1] and a[2] < b[3] and b[2] < a[3]:
                bad.append("%s vs %s" % (a[4], b[4]))
    return bad


def collisions(elements, line_h, col_w):
    bad = overlapping_pairs(elements, line_h)
    bx = boxes(elements, line_h)
    half = col_w / 2.0 - COL_PAD * 0.35
    for a in bx:
        if a[0] < -half or a[1] > half:
            bad.append("%s crosses the species box edge" % a[4])
    return bad


# ----------------------------------------------------------------------
# Figure
# ----------------------------------------------------------------------
def build_figure(data, verbose=True):
    items = {k: make_items(v) for k, v in data.items()}
    all_e = [e for lv in data.values() for _, e, _ in lv]
    y0, y1 = min(all_e) - Y_PAD, max(all_e) + Y_PAD
    y_range = y1 - y0

    line_h = 0.55          # kcal/mol; refined by the loop below
    grow = 1.0
    layouts = col_w = None

    for _ in range(60):
        # Inner loop: column widths depend on the crowding thresholds, which
        # depend on kcal-per-inch, which depends on the column widths.  Iterate
        # to the fixed point.
        for _inner in range(12):
            gy = GAP_Y * line_h / (FS_ANNOT * 1.32 / 72.0)
            layouts, col_w = {}, {}
            for key in SYSTEMS:
                layouts[key], col_w[key] = layout_species(items[key], line_h, gy)
            axes_w = sum(col_w.values())
            fig_w = axes_w + MARGIN_L + MARGIN_R
            fig_h = fig_w / ASPECT * grow
            axes_h = fig_h - MARGIN_B - MARGIN_T
            new_line_h = (FS_ANNOT * 1.32 / 72.0) * y_range / axes_h
            if abs(new_line_h - line_h) < 0.002:
                line_h = new_line_h
                break
            line_h = new_line_h
        bad = []
        for key in SYSTEMS:
            for msg in collisions(layouts[key], line_h, col_w[key]):
                bad.append("%s: %s" % (key, msg))
        if not bad:
            break
        grow *= 1.035      # taller canvas -> more kcal head-room per text line
    else:
        raise RuntimeError("could not find a collision-free layout:\n  "
                           + "\n  ".join(bad))

    axes_w = sum(col_w.values())
    fig_w = axes_w + MARGIN_L + MARGIN_R
    fig_h = fig_w / ASPECT * grow
    axes_h = fig_h - MARGIN_B - MARGIN_T

    fig = plt.figure(figsize=(fig_w, fig_h))
    ax = fig.add_axes([MARGIN_L / fig_w, MARGIN_B / fig_h,
                       axes_w / fig_w, axes_h / fig_h])
    ax.set_xlim(0.0, axes_w)                 # 1 x unit == 1 inch
    ax.set_ylim(y0, y1)

    centres, edges, x = [], [0.0], 0.0
    for key in SYSTEMS:
        centres.append(x + col_w[key] / 2.0)
        x += col_w[key]
        edges.append(x)

    # species boxes: light-grey dashed dividers inside a solid black frame
    for xe in edges[1:-1]:
        ax.axvline(xe, color=BOX_COLOR, ls=(0, (5, 4)), lw=1.0, zorder=1)

    for key, xc in zip(SYSTEMS, centres):
        colour = SYSTEMS[key]["color"]
        for el in layouts[key]:
            if el["k"] == "bar":
                ax.plot([xc + el["x"] - el["hw"], xc + el["x"] + el["hw"]],
                        [el["y"], el["y"]], color=colour, lw=BAR_LW,
                        zorder=4, solid_capstyle="butt")
            elif el["k"] == "lead":
                pts = [(xc + px, py) for px, py in el["pts"]]
                ax.plot([p[0] for p in pts], [p[1] for p in pts],
                        color=colour, lw=0.8, alpha=0.75, zorder=2,
                        solid_capstyle="round")
            else:
                ax.text(xc + el["x"], el["y"], el["s"], ha=el["ha"], va=el["va"],
                        fontsize=FS_ANNOT, zorder=6, bbox=TEXT_BBOX)

    ax.set_xticks(centres)
    ax.set_xticklabels([SYSTEMS[k]["title"] for k in SYSTEMS], fontsize=FS_TICK)
    ax.tick_params(axis="x", length=0, pad=9)
    ax.tick_params(axis="y", labelsize=11)
    ax.set_ylabel(YLABEL, fontsize=FS_YLABEL, labelpad=8)
    for side in ("top", "right", "bottom", "left"):
        ax.spines[side].set_visible(True)
        ax.spines[side].set_color("black")
        ax.spines[side].set_linewidth(1.3)
    ax.set_axisbelow(False)

    if verbose:
        print("canvas      : %.2f x %.2f in  (aspect %.2f:1)"
              % (fig_w, fig_h, fig_w / fig_h))
        print("text line   : %.2f kcal/mol -> crowded below %.2f, "
              "overlapping below %.2f"
              % (line_h, CLUSTER_MULT * line_h, HARD_MULT * line_h))
        print("column width: %.2f - %.2f in" % (min(col_w.values()),
                                                max(col_w.values())))
        print("no text/bar overlap and nothing crosses a box edge (verified)")
    return fig, ax


def main(datafile, outfile):
    fig, _ = build_figure(read_levels(datafile))
    fig.savefig(outfile, dpi=DPI)
    print("saved %s" % outfile)


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "ts_energies.txt"
    dst = sys.argv[2] if len(sys.argv) > 2 else "ts_levels_v2.png"
    main(src, dst)
