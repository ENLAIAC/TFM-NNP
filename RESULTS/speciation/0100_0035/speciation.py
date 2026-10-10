import numpy as np
from scipy.optimize import brentq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Dictionary of the speciation plot with their labels and colors for visualization
SPECIES = {
    "mg_free":  dict(label=r"$\mathrm{Mg^{2+}}$", color="brown"),
    "mg_solid": dict(label=r"$\mathrm{Mg(OH)_2(s)}$", color="gray"),
    "mgoh":     dict(label=r"$\mathrm{MgOH^{+}}$", color="olive"),
    "mgpp":     dict(label=r"$\mathrm{MgP_2O_7^{2-}}$", color="blue"),
    "mghpp":    dict(label=r"$\mathrm{MgHP_2O_7^{-}}$", color="green"),
    "mg2pp":    dict(label=r"$\mathrm{Mg_2P_2O_7}$", color="red"),
    "pp":       dict(label=r"$\mathrm{P_2O_7^{4-}}$", color="orange"),
    "hpp":      dict(label=r"$\mathrm{HP_2O_7^{3-}}$", color="purple"),
    "h2pp":     dict(label=r"$\mathrm{H_2P_2O_7^{2-}}$", color="magenta"),
    "h3pp":     dict(label=r"$\mathrm{H_3P_2O_7^{-}}$", color="teal"),
    "h4pp":     dict(label=r"$\mathrm{H_4P_2O_7}$", color="goldenrod"),
}

# Column layout of the .dat files (index 0 is pH).
# This list ONLY controls the order of the output columns.  solve_concentrations
# returns a name-keyed dict, so reordering this list can never desynchronise the
# data from the labels.
COLUMNS = ["pp", "hpp", "h2pp", "h3pp", "h4pp", "mgpp", "mghpp", "mg2pp",
           "mg_free", "mg_solid", "mgoh"]

MG_SPECIES = ["mg_free", "mg_solid", "mgoh", "mgpp", "mghpp", "mg2pp"]
PP_SPECIES = ["pp", "hpp", "h2pp", "h3pp", "h4pp", "mgpp", "mghpp", "mg2pp"]
MG_ONLY = ["mg_free", "mg_solid", "mgoh"]      # species with no PP -> chi on the Mg basis

# stoichiometric coefficients nu_X,i for the two mass balances
NU_MG = {"mg_free": 1, "mg_solid": 1, "mgoh": 1, "mgpp": 1, "mghpp": 1, "mg2pp": 2}
NU_PP = {s: 1 for s in PP_SPECIES}

# --- consistency of the declarations themselves, checked once at import ---
assert set(COLUMNS) == set(SPECIES), "COLUMNS and SPECIES declare different species"
assert set(MG_SPECIES) <= set(COLUMNS) and set(PP_SPECIES) <= set(COLUMNS)
assert set(NU_MG) == set(MG_SPECIES) and set(NU_PP) == set(PP_SPECIES)
assert len(COLUMNS) == len(set(COLUMNS)), "duplicate name in COLUMNS"

# Thermodynamic constants
pka4 = 9.41   # HPP(3-)  -> PP(4-)   + H+
pka3 = 6.60   # H2PP(2-) -> HPP(3-)  + H+
pka2 = 1.96   # H3PP(1-) -> H2PP(2-) + H+
pka1 = 0.85   # H4PP     -> H3PP(1-) + H+
pKw = 14.0

# Dissociation constants (Taken from 10.1021/ja01578a006)
kd_ppmg = 3.9e-6      # [Mg][PP]  / [MgPP]
kd_pphmg = 8.7e-4     # [Mg][HPP] / [MgHPP]      <- written against HPP(3-)
kd_ppmg2 = 1.78e-8    # [Mg]^2[PP]/ [Mg2PP]      <- cumulative

ksp_mgoh2 = 5.61e-12  # Solubility product at 25 C. CRC Handbook, 76th ed., 1996

# Optional Mg(II) hydroxo complex: Mg2+ + OH- <-> MgOH+.  Set 0.0 to disable
# (0.0 reproduces the original model exactly).  log beta ~ 2.6 at 25 C.
beta_mgoh = 0.0

# Initial conditions (Molar) (Taken from 10.1074/jbc.M110.214510)
c1=0.100   # total Mg
c2=0.035   # total PP

# Files
resume = f"speciation_resume_{c1}_{c2}.txt"
datafile = f"concentrations_vs_pH_{c1}_{c2}.dat"
ratio_datafile = f"molecular_ratios_vs_pH_{c1}_{c2}.dat"
pp_molecular_ratio = f"pp_molecular_ratio_{c1}_{c2}.png"
mg_molecular_ratio = f"mg_molecular_ratio_{c1}_{c2}.png"


def _dg(c_mg, h):
    """Return (D, G, ladder, complexes) with PP_T = c_pp*D and
    Mg-held-in-PP-complexes = c_pp*G.

    Every PP-bearing species is first order in [PP(4-)], so D and G depend
    only on free Mg and h.
    """
    b1 = h    * 10.0**(pka4)
    b2 = h**2 * 10.0**(pka4 + pka3)
    b3 = h**3 * 10.0**(pka4 + pka3 + pka2)
    b4 = h**4 * 10.0**(pka4 + pka3 + pka2 + pka1)

    mgl = c_mg / kd_ppmg                 # [MgPP]   / [PP]
    mghl = c_mg * b1 / kd_pphmg          # [MgHPP]  / [PP]   (b1 folded in)
    mg2l = c_mg**2 / kd_ppmg2            # [Mg2PP]  / [PP]

    D = 1.0 + b1 + b2 + b3 + b4 + mgl + mghl + mg2l
    G = mgl + mghl + 2.0 * mg2l
    return D, G, (b1, b2, b3, b4), (mgl, mghl, mg2l)


def _mg_residual(c_mg, h, OH):
    """Unsaturated branch: F(c_mg) = 0.  Negative at 0, positive at c1."""
    D, G, _, _ = _dg(c_mg, h)
    return c_mg * (1.0 + beta_mgoh * OH) + (c2 / D) * G - c1


def speciate(pH):
    """Return {species name: concentration} at the given pH."""
    h = 10.0**-pH
    OH = 10.0**(pH - pKw)

    # ---- Branch B: assume Mg(OH)2(s) present -> free Mg2+ pinned by Ksp ----
    c_mg = ksp_mgoh2 / OH**2
    D, G, b, mg = _dg(c_mg, h)
    c_pp = c2 / D
    c_mg_solid = c1 - c_mg * (1.0 + beta_mgoh * OH) - c_pp * G

    if c_mg_solid <= 0.0:
        # ---- Branch A: no solid -> one monotone scalar equation ----
        c_mg = brentq(_mg_residual, 1e-300, c1, args=(h, OH),
                      xtol=1e-300, rtol=8.9e-16, maxiter=200)
        D, G, b, mg = _dg(c_mg, h)
        c_pp = c2 / D
        c_mg_solid = 0.0

    b1, b2, b3, b4 = b
    mgl, mghl, mg2l = mg

    # names bound to values HERE and nowhere else
    return {
        "mg_free":  c_mg,
        "mg_solid": c_mg_solid,
        "mgoh":     beta_mgoh * c_mg * OH,
        "pp":       c_pp,
        "hpp":      c_pp * b1,
        "h2pp":     c_pp * b2,
        "h3pp":     c_pp * b3,
        "h4pp":     c_pp * b4,
        "mgpp":     c_pp * mgl,
        "mghpp":    c_pp * mghl,
        "mg2pp":    c_pp * mg2l,
    }, OH


def solve_concentrations(pH):
    """Concentrations at the given pH, ordered by COLUMNS."""
    conc, OH = speciate(pH)
    test_solve_concentrations(conc, pH, OH)          # raises on failure
    return [conc[s] for s in COLUMNS]                # order generated, not typed


def test_solve_concentrations(conc, pH, OH):
    """Check the three invariants of the model: conservation, admissibility,
    and the solid/solution complementarity condition."""
    missing = set(COLUMNS) - set(conc)
    assert not missing, f"speciate() did not return {sorted(missing)}"

    total_mg = sum(NU_MG[s] * conc[s] for s in MG_SPECIES)
    assert np.isclose(total_mg, c1, rtol=1e-10, atol=0.0), \
        f"pH {pH:.2f}: total Mg {total_mg:.8e} != {c1:.8e}"

    total_pp = sum(NU_PP[s] * conc[s] for s in PP_SPECIES)
    assert np.isclose(total_pp, c2, rtol=1e-10, atol=0.0), \
        f"pH {pH:.2f}: total PP {total_pp:.8e} != {c2:.8e}"

    neg = {s: v for s, v in conc.items() if v < 0.0}
    assert not neg, f"pH {pH:.2f}: negative concentrations {neg}"

    omega = conc["mg_free"] * OH**2 / ksp_mgoh2          # IAP / Ksp
    if conc["mg_solid"] > 0.0:
        assert np.isclose(omega, 1.0, rtol=1e-10), \
            f"pH {pH:.2f}: solid present but IAP/Ksp = {omega:.10f}"
    else:
        assert omega <= 1.0 + 1e-10, \
            f"pH {pH:.2f}: no solid but IAP/Ksp = {omega:.10f}"


def plot_ratio():
    with open(ratio_datafile) as f:
        header = f.readline().split()[1:]
    ratio_data = np.loadtxt(ratio_datafile)
    conc = np.loadtxt(datafile)
    col = {name: i for i, name in enumerate(header)}     # header[0] == "pH"

    # --- PP speciation: fractions of total PP (as stored) ---
    plt.figure(figsize=(10, 6))
    for s in PP_SPECIES:
        plt.plot(ratio_data[:, 0], ratio_data[:, col[s]],
                 label=SPECIES[s]["label"], color=SPECIES[s]["color"])
    plt.xlabel("pH")
    plt.ylabel(r"Molecular ratio $\chi$")
    plt.title(r"PP species molecular ratios $\chi$ vs pH")
    plt.xlim(ratio_data[0, 0], ratio_data[-1, 0])
    plt.ylim(-0.02, 1.02)
    plt.legend(ncol=2, fontsize=9)
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(pp_molecular_ratio, dpi=150)
    plt.close()

    # --- Mg speciation: fractions of total Mg (recomputed on the Mg basis) ---
    plt.figure(figsize=(10, 6))
    for s in MG_SPECIES:
        if s == "mgoh" and beta_mgoh == 0.0:
            continue
        plt.plot(conc[:, 0], NU_MG[s] * conc[:, col[s]] / c1,
                 label=SPECIES[s]["label"], color=SPECIES[s]["color"])
    plt.xlabel("pH")
    plt.ylabel(r"Molecular ratio $\chi$")
    plt.title(r"Mg species molecular ratios $\chi$ vs pH")
    plt.xlim(conc[0, 0], conc[-1, 0])
    plt.ylim(-0.02, 1.02)
    plt.legend(ncol=2, fontsize=9)
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(mg_molecular_ratio, dpi=150)
    plt.close()


def write_resume(data):
    pH = data[:, 0]
    solid = data[:, 1 + COLUMNS.index("mg_solid")]
    sat = solid > 0.0
    with open(resume, "w") as f:
        f.write("Mg / pyrophosphate speciation with Mg(OH)2(s)\n")
        f.write(f"  total Mg = {c1:.4e} M   total PP = {c2:.4e} M\n")
        f.write(f"  pKa ladder = {pka1}, {pka2}, {pka3}, {pka4}   pKw = {pKw}\n")
        f.write(f"  kd_ppmg = {kd_ppmg:.3e}  kd_pphmg = {kd_pphmg:.3e}  "
                f"kd_ppmg2 = {kd_ppmg2:.3e}\n")
        f.write(f"  Ksp(Mg(OH)2) = {ksp_mgoh2:.3e}   beta_MgOH = {beta_mgoh:.3e}\n")
        if sat.any():
            f.write(f"  precipitation onset between pH {pH[sat][0] - (pH[1]-pH[0]):.2f} "
                    f"and {pH[sat][0]:.2f}\n")
            f.write(f"  max solid = {solid.max():.4e} M "
                    f"({100*solid.max()/c1:.2f} % of total Mg) at pH {pH[solid.argmax()]:.2f}\n")
        else:
            f.write("  no precipitation over the scanned pH range\n")
        f.write("\nDominant species by pH\n")
        for i in range(0, len(pH), max(1, len(pH) // 28)):
            row = dict(zip(COLUMNS, data[i, 1:]))
            top_pp = max(PP_SPECIES, key=lambda s: row[s])
            top_mg = max(MG_SPECIES, key=lambda s: NU_MG[s] * row[s])
            f.write(f"  pH {pH[i]:5.2f}  PP: {top_pp:<6s} ({row[top_pp]/c2:5.3f})"
                    f"   Mg: {top_mg:<8s} ({NU_MG[top_mg]*row[top_mg]/c1:5.3f})"
                    f"   solid: {row['mg_solid']:.3e}\n")


def main():
    pH_values = np.arange(0, 14, 0.05)

    data = []
    ratio_data = []
    for pH in pH_values:
        concentrations = solve_concentrations(pH)
        # chi on the Mg basis for Mg-only species, on the PP basis otherwise
        ratios = [c / (c1 if s in MG_ONLY else c2)
                  for s, c in zip(COLUMNS, concentrations)]
        data.append([pH] + concentrations)
        ratio_data.append([pH] + ratios)

    data = np.array(data)
    ratio_data = np.array(ratio_data)

    header = "pH " + " ".join(COLUMNS)
    np.savetxt(datafile, data, header=header, fmt="%.6e")
    np.savetxt(ratio_datafile, ratio_data, header=header, fmt="%.6e")

    plot_ratio()
    write_resume(data)

    print(f"All {len(pH_values)} pH points passed the mass-balance, "
          f"non-negativity and saturation checks.")
    print(f"Data saved to {datafile} and {ratio_datafile}. "
          f"Plots saved to {pp_molecular_ratio} and {mg_molecular_ratio}. "
          f"Summary in {resume}.")


if __name__ == "__main__":
    main()
