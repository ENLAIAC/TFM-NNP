#!/usr/bin/env python3
"""
lammps_to_dcd.py
----------------
Convert a LAMMPS dump file (id type xs ys zs - fractional/scaled coords)
to a DCD trajectory readable by VMD, NAMD, CHARMM, MDAnalysis, etc.

Requires:
    MDAnalysis >= 2.0   (pip install MDAnalysis)
    numpy               (pulled in automatically by MDAnalysis)

Usage:
    python lammps_to_dcd.py \\
        --dump     trajectory.lammpsdump \\
        --types    atom_types.dat \\
        --out      trajectory.dcd \\
        [--psf     topology.psf]   # optional, written if requested

Atom-type file format (whitespace-separated, one per line, no header):
    <type_id>  <element_or_name>  <mass>
Example:
    1   OW   15.9994
    2   HW    1.0080
    4   Na   22.9898

Dump format assumed:
    ITEM: ATOMS id type xs ys zs
    (fractional / scaled coordinates - values between 0 and 1)
If your dump uses real coordinates (x y z), pass --realcoords.
"""

import argparse
import sys
import re
import numpy as np

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_type_file(path):
    """Return {type_id(int): (name, mass)} from the property file."""
    mapping = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            tid = int(parts[0])
            name = parts[1]
            mass = float(parts[2]) if len(parts) >= 3 else 1.0
            mapping[tid] = (name, mass)
    return mapping


def parse_lammpsdump(path, type_map, scaled=True):
    """
    Generator - yields one dict per frame:
        {
          'timestep': int,
          'n_atoms':  int,
          'box':      np.array shape (3, 2)  [[xlo,xhi],[ylo,yhi],[zlo,zhi]],
          'ids':      np.array (N,) int,
          'types':    np.array (N,) int,
          'names':    list of str,
          'masses':   np.array (N,),
          'coords':   np.array (N, 3)   - always in Angström (real coords),
        }
    """
    col_id = col_type = col_x = col_y = col_z = None

    with open(path) as f:
        while True:
            # --- header ---
            line = f.readline()
            if not line:
                break  # EOF
            if "ITEM: TIMESTEP" not in line:
                continue

            timestep = int(f.readline().strip())

            assert "ITEM: NUMBER OF ATOMS" in f.readline()
            n_atoms = int(f.readline().strip())

            box_line = f.readline()  # ITEM: BOX BOUNDS ...
            box = np.zeros((3, 2))
            for i in range(3):
                lo, hi = map(float, f.readline().split()[:2])
                box[i] = [lo, hi]

            atoms_header = f.readline()  # ITEM: ATOMS ...
            cols = atoms_header.split()[2:]  # strip "ITEM:" and "ATOMS"
            col_id   = cols.index("id")
            col_type = cols.index("type")
            # Support xs/ys/zs (scaled) and x/y/z (real)
            if "xs" in cols:
                col_x, col_y, col_z = cols.index("xs"), cols.index("ys"), cols.index("zs")
                this_frame_scaled = True
            else:
                col_x, col_y, col_z = cols.index("x"), cols.index("y"), cols.index("z")
                this_frame_scaled = False

            ids    = np.empty(n_atoms, dtype=int)
            types  = np.empty(n_atoms, dtype=int)
            coords = np.empty((n_atoms, 3), dtype=float)

            for i in range(n_atoms):
                parts = f.readline().split()
                ids[i]       = int(parts[col_id])
                types[i]     = int(parts[col_type])
                coords[i, 0] = float(parts[col_x])
                coords[i, 1] = float(parts[col_y])
                coords[i, 2] = float(parts[col_z])

            # Sort by atom id so order is consistent across frames
            order  = np.argsort(ids)
            ids    = ids[order]
            types  = types[order]
            coords = coords[order]

            # Fractional -> real Angstrom
            if scaled or this_frame_scaled:
                lengths = box[:, 1] - box[:, 0]   # [Lx, Ly, Lz]
                coords = coords * lengths + box[:, 0]

            names  = [type_map.get(t, (f"X{t}", 1.0))[0] for t in types]
            masses = np.array([type_map.get(t, (f"X{t}", 1.0))[1] for t in types])

            yield {
                "timestep": timestep,
                "n_atoms":  n_atoms,
                "box":      box,
                "ids":      ids,
                "types":    types,
                "names":    names,
                "masses":   masses,
                "coords":   coords,
            }


def build_universe(first_frame, type_map):
    """
    Build a minimal MDAnalysis Universe from the first frame so we have
    the topology needed to write DCD.
    """
    import MDAnalysis as mda
    from MDAnalysis.core.topology import Topology
    from MDAnalysis.core.topologyattrs import (
        Atomids, Atomnames, Atomtypes, Masses, Resids, Resnames, Segids
    )

    n = first_frame["n_atoms"]
    names  = np.array(first_frame["names"])
    masses = first_frame["masses"]
    ids    = first_frame["ids"]

    # One residue per atom is the safest assumption when we have no topology
    resids   = np.arange(1, n + 1)
    resnames = np.array(["MOL"] * n)
    segids   = np.array(["SEG"] * n)

    top = Topology(
        n_atoms=n,
        n_res=n,
        n_seg=1,
        attrs=[
            Atomids(ids),
            Atomnames(names),
            Atomtypes(names),
            Masses(masses),
            Resids(resids),
            Resnames(resnames),
            Segids(np.array(["SEG"])),
        ],
        atom_resindex=np.arange(n),
        residue_segindex=np.zeros(n, dtype=int),
    )

    u = mda.Universe(top)
    return u


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Convert LAMMPS dump to DCD trajectory"
    )
    parser.add_argument("--dump",      required=True, help="Input LAMMPS dump file")
    parser.add_argument("--types",     required=True, help="Atom-type property file (id name mass)")
    parser.add_argument("--out",       required=True, help="Output DCD file")
    parser.add_argument("--realcoords", action="store_true",
                        help="Dump uses real coords (x y z) instead of scaled (xs ys zs)")
    parser.add_argument("--psf",       default=None,
                        help="Also write a minimal PSF topology file (optional, useful for VMD)")
    parser.add_argument("--dt",        type=float, default=1.0,
                        help="Timestep in ps stored in DCD header (default: 1.0)")
    args = parser.parse_args()

    # --- load type mapping ---
    print(f"[1/4] Reading atom-type file: {args.types}")
    type_map = parse_type_file(args.types)
    print(f"      Found {len(type_map)} atom types: "
          + ", ".join(f"{k}={v[0]}" for k, v in sorted(type_map.items())))

    # --- stream dump and collect frames ---
    print(f"[2/4] Parsing LAMMPS dump: {args.dump}")
    scaled = not args.realcoords
    frames = list(parse_lammpsdump(args.dump, type_map, scaled=scaled))
    print(f"      Read {len(frames)} frames, {frames[0]['n_atoms']} atoms each")

    # --- build MDAnalysis universe ---
    print("[3/4] Building MDAnalysis Universe...")
    try:
        import MDAnalysis as mda
        from MDAnalysis.coordinates.DCD import DCDWriter
    except ImportError:
        sys.exit(
            "\n[ERROR] MDAnalysis not found.\n"
            "Install it with:  pip install MDAnalysis\n"
            "See setup_env.sh for a full offline-friendly environment setup.\n"
        )

    u = build_universe(frames[0], type_map)

    # Attach a MemoryReader so u.trajectory exists and ts.dimensions is writable.
    # We load just the first frame's coords; we'll overwrite each frame in the loop.
    from MDAnalysis.coordinates.memory import MemoryReader
    dummy_coords = frames[0]["coords"].astype(np.float32)[np.newaxis, ...]  # (1, N, 3)
    u.load_new(dummy_coords, format=MemoryReader)

    def box_to_mda(box_arr):
        """Convert [[xlo,xhi],[ylo,yhi],[zlo,zhi]] -> [lx,ly,lz,90,90,90] in Angstrom."""
        lx = box_arr[0, 1] - box_arr[0, 0]
        ly = box_arr[1, 1] - box_arr[1, 0]
        lz = box_arr[2, 1] - box_arr[2, 0]
        return np.array([lx, ly, lz, 90.0, 90.0, 90.0], dtype=np.float32)

    # --- write DCD ---
    print(f"[4/4] Writing DCD: {args.out}")
    with DCDWriter(args.out, n_atoms=frames[0]["n_atoms"], dt=args.dt) as writer:
        for i, frame in enumerate(frames):
            # Set box on TimeStep, positions via AtomGroup, write AtomGroup
            u.trajectory.ts.dimensions = box_to_mda(frame["box"])
            u.atoms.positions = frame["coords"].astype(np.float32)
            writer.write(u.atoms)
            if (i + 1) % 100 == 0 or i == 0:
                print(f"      … written frame {i+1}/{len(frames)}", end="\r")

    print(f"\n      Done! -> {args.out}")

    # --- optional PSF ---
    if args.psf:
        print(f"      Writing PSF: {args.psf}")
        try:
            with mda.Writer(args.psf, n_atoms=frames[0]["n_atoms"]) as w:
                w.write(u.atoms)
        except Exception as e:
            # PSF writing can be finicky; fallback to manual minimal PSF
            print(f"      [warn] MDAnalysis PSF writer failed ({e}), writing minimal PSF manually.")
            _write_minimal_psf(args.psf, frames[0], type_map)
        print(f"      PSF written -> {args.psf}")


def _write_minimal_psf(path, frame, type_map):
    """Write a bare-bones CHARMM PSF so VMD can load DCD without bonds."""
    n = frame["n_atoms"]
    with open(path, "w") as f:
        f.write("PSF EXT\n\n")
        f.write(f"       1 !NTITLE\n")
        f.write(f" REMARKS Minimal PSF generated by lammps_to_dcd.py\n\n")
        f.write(f"{n:>10d} !NATOM\n")
        for i, (aid, atype, aname, mass) in enumerate(
            zip(frame["ids"], frame["types"], frame["names"], frame["masses"]), 1
        ):
            # columns: index segid resid resname name type charge mass  0
            f.write(
                f"{i:>10d} SEG  {i:<5d} MOL      "
                f"{aname:<5s} {aname:<5s}  0.000000   {mass:>10.4f}           0\n"
            )
        f.write(f"\n       0 !NBOND\n")
        f.write(f"\n       0 !NTHETA\n")
        f.write(f"\n       0 !NPHI\n")
        f.write(f"\n       0 !NIMPHI\n")


if __name__ == "__main__":
    main()
