# TFM-NNP: Neural Network Potentials for Mg₂P₂O₇ Hydrolysis

Master's thesis project — development and application of machine-learned interatomic potentials (NNPs) for studying the hydrolysis mechanism of magnesium pyrophosphate (Mg₂P₂O₇) in aqueous solution.

---

## Scientific context

Pyrophosphate (P₂O₇⁴⁻, PPi) hydrolysis is a biologically fundamental reaction that drives many cellular processes. Despite its importance, the free-energy landscape of PPi hydrolysis in the presence of divalent cations such as Mg²⁺ is not well characterised at the atomic level. Classical force fields fail to capture bond-breaking and bond-forming events accurately, while full *ab initio* MD is prohibitively expensive for the sampling timescales required.

This project builds accurate NNPs via the **ArcaNN active-learning framework**, combining:

- **DeePMD-kit** — deep learning model for atomic energy and forces
- **LAMMPS** — fast NNP-driven molecular dynamics for exploration and production
- **CP2K** — DFT (PBE-D3 / BLYP-D3) single-point labeling of selected configurations
- **ORCA** — benchmark quantum chemistry for reference structures
- **PLUMED** — enhanced sampling (OPES, Steered MD) to drive reactive trajectories

The system contains the atoms H, O, Mg, P, represented by a descriptor network using the smooth end-to-end ansatz (se\_e2\_a), with a cutoff radius of 6.0 Å.

---

## ArcaNN workflow

ArcaNN automates the active-learning cycle:

```
Initial dataset (prior AIMD)
        |
        v
  [ NNP Training ]  <------------------------------------------+
        |                                                       |
        v                                                       |
  [ Exploration ]  — LAMMPS+DeePMD+PLUMED/OPES                 |
  (iterations 001-006)                                          |
        |                                                       |
        v                                                       |
  [ Candidate selection ]  — query-by-committee (model deviation)|
        |                                                       |
        v                                                       |
  [ CP2K Labeling ]  — DFT single points                       |
  (iterations 001-002)                                          |
        |                                                       |
        v                                                       |
  [ Augmented dataset ] ----------------------------------------+
        |
        v
  [ Production MD ]  — Mg₂P₂O₇ steered MD + OPES hydrolysis
```

Each iteration folder (`001-exploration`, `001-labeling`, …) in `arcann_workflow/` corresponds to one pass through this loop.

---

## Repository structure

```
TFM-NNP/
├── user_files/              Training and job configuration files
│   ├── dptrain_2.1.json     DeePMD-kit training hyperparameters
│   ├── training_3.0.json    DeePMD-kit v3 training config (MN5)
│   ├── machine.json         ArcaNN machine/scheduler config (MN5)
│   ├── properties.txt       Atom-type to index mapping + masses
│   ├── pyro-hydrolysis-2h.* Starting geometry (.in / .lmp / .pdb / .xyz)
│   ├── job_deepmd_*.sh      SLURM scripts: train, compress, freeze, dptest
│   ├── job_lammps-*.sh      SLURM scripts: LAMMPS exploration
│   ├── job_CP2K_*.sh        SLURM scripts: CP2K labeling
│   └── job-array_*.sh       Array-job variants for batch submission
│
├── scripts/
│   ├── python/
│   │   ├── energy_grep.py   Extract and plot energy distributions from CP2K runs
│   │   └── extract.py       Extract individual configurations from XYZ trajectories
│   └── bash/
│       ├── check_convergence.sh  Batch SCF convergence check for CP2K labeling jobs
│       ├── check_data.sh         Validate training dataset integrity
│       ├── check_distance.sh     Detect atomic overlaps in candidate configurations
│       ├── energy_chart.sh       Consolidate energy data from multiple CP2K replicas
│       ├── energy_grep.sh        Extract energies from LAMMPS/DeePMD runs
│       ├── generate_xyz.sh       Convert trajectory formats to XYZ
│       ├── job_lammps-deepmd.sh  LAMMPS+DeePMD job wrapper
│       └── python_submission.sh  Python script cluster submission wrapper
│
├── arcann_workflow/         ArcaNN iteration inputs and outputs
│   ├── 001-exploration/     Candidate XYZ files from iteration 001
│   ├── 002-exploration/     LAMMPS/OPES inputs and candidate structures
│   ├── 003-exploration/     Full exploration: LAMMPS inputs, PLUMED files,
│   │                        job scripts, QbC stats and indexes per replica
│   ├── 006-exploration/     LAMMPS inputs and PLUMED configs (pph4-TS system)
│   ├── 001-labeling/        Selected reference structures (.xyz) for DFT
│   └── 002-labeling/        Selected reference structures (.xyz) for DFT
│
├── Mg2P2O7/                 Mg₂P₂O₇ system calculations
│   ├── CP2K_dynamics/
│   │   ├── inputs/          CP2K AIMD input files (PPiMg2, PPiMg2_edges)
│   │   └── PPiMg2_sides_final/
│   │       ├── PPiMg2_sides*.inp   CP2K input files (different protocol variants)
│   │       ├── energy_grep*.py     Energy extraction scripts for this run
│   │       ├── PPiMg2_sides-Energy.en  Energy series output
│   │       └── energy_distribution_*.png  Plotted energy distributions
│   ├── LAMMPS_MD_PPiMg2/    Steered MD of PPiMg2 with NNP committee (iteration 006)
│   │   ├── PPiMg2-SMD.in    LAMMPS input file
│   │   ├── PPiMg2-SMD.lmp   LAMMPS topology file
│   │   ├── plumed_PPiMg2-SMD.dat  PLUMED collective variables and walls
│   │   ├── job_lammps_submission.sh
│   │   └── README           Cluster session log
│   ├── hydrolysis_OPES/     OPES-driven hydrolysis MD with NNP
│   │   ├── ppimg2-hydrolysis.in   LAMMPS input
│   │   ├── ppimg2-hydrolysis.lmp  Topology
│   │   └── plumed_ppimg2-hydrolysis.dat  PLUMED OPES setup
│   ├── orca/                ORCA benchmark calculations
│   │   ├── PPi2Mg_2b_bridged/     Bidentate bridged coordination
│   │   ├── PPi2Mg_2b_up_down/     Bidentate up-down coordination
│   │   ├── PPi2Mg_3b/             Tridentate coordination
│   │   └── configurations/        Reference structures (.xyz / .pdb)
│   ├── SMD/                 LAMMPS inputs for Mg-constrained SMD runs
│   ├── pyro-hydrolysis-mg.pdb     Top-level reference geometry
│   └── pyro-hydrolysis-mg2.mol2
│
└── SMD/                     Steered MD of pph3 (pyrophosphate — 3H protonation state)
    ├── input/               LAMMPS topology, PLUMED SMD setup
    └── output/              Reactant and product structures
```

---

## SLURM job scripts

The `user_files/` folder contains SLURM submission scripts for two clusters:

| Suffix | Cluster | Login node | Partition |
|--------|---------|------------|-----------|
| `_gpu_alogin2` | MareNostrum 5 | alogin2.bsc.es | `acc` (GPU) |
| `_cpu_alogin2` | MareNostrum 5 | alogin2.bsc.es | `acc` (CPU) |
| `_cpu_glogin2` | MareNostrum 5 | glogin2.bsc.es | `gpp` (CPU) |
| `_cpu_vives` | Vives (UV) | vives.uv.es | CPU |

The `machine.json` file configures ArcaNN's job dispatch for MareNostrum 5.

---

## Scripts

### `scripts/python/energy_grep.py`
Reads CP2K energy output files from multiple replica directories, converts kinetic and potential energies from atomic units to kcal/mol, and generates histogram plots of the total energy distribution.

**Usage:** `python3 energy_grep.py` (run from the parent directory containing the replica subdirectories)

### `scripts/python/extract.py`
Extracts individual configurations from a multi-frame XYZ trajectory file and writes them to separate output files or a subsampled trajectory. Validates frame count and atom number. Writes a debug log (`debug.txt`).

**Usage:** `python3 extract.py <trajectory.xyz> <natoms>`

### `scripts/bash/check_convergence.sh`
Iterates over labeling job directories, reads CP2K output files, and classifies each calculation as converged, not converged (SCF failure or Cholesky decomposition error), requires manual inspection, or missing output. Writes summary files and prints a convergence report.

**Usage:** Run from the labeling iteration directory (e.g., `002-labeling/`).

### `scripts/bash/check_data.sh`
Validates the presence and consistency of expected data files across the labeling dataset directories.

### `scripts/bash/check_distance.sh`
Scans candidate configurations to detect atomic overlaps (inter-atomic distances below a threshold), which would cause DFT single-point failures.

### `scripts/bash/energy_chart.sh`
Loops over CP2K replica directories (`PPiMg2*/`), extracts the total energy (kinetic + potential, column 3+5 of the `.en` file) for each frame, and consolidates them into a single `all_energies_long.dat` file suitable for plotting.

### `scripts/bash/energy_grep.sh`
Extracts energy data from LAMMPS/DeePMD run logs across multiple simulation directories.

### `scripts/bash/generate_xyz.sh`
Converts LAMMPS trajectory or other formats to XYZ files for visualization and further analysis.

### `scripts/bash/job_lammps-deepmd.sh`
SLURM submission wrapper for LAMMPS+DeePMD exploration runs; configures modules, environment, and launches the LAMMPS executable.

### `scripts/bash/python_submission.sh`
SLURM wrapper for submitting Python analysis scripts to the cluster queue.

---

## Requirements and setup

This repository contains **workflow files only**, not the ArcaNN package or DeePMD-kit itself. To reproduce the calculations, set up:

1. **ArcaNN** — installation guide: https://github.com/arcann-chem/arcann_training
2. **DeePMD-kit** (v2.1 or v3.0) — https://github.com/deepmodeling/deepmd-kit
3. **LAMMPS** with the DeePMD plugin — https://github.com/deepmodeling/lammps
4. **CP2K** (v9+) — https://www.cp2k.org
5. **PLUMED** (v2.8+) — https://www.plumed.org
6. **ORCA** (v6.0) — https://www.faccts.de/orca/

Configure `user_files/machine.json` and the SLURM scripts for your HPC environment before launching.

---

## License

MIT License — see [LICENSE](LICENSE).

---

## Author

Elia Cazzanti — Master's thesis, Universitat de València / Barcelona Supercomputing Center, 2025–2026.
