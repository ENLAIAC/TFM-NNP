# deepmd-training — structure overview

**Absolute root:** `/gpfs/scratch/uv36/adrian/deepmd-training`
**System:** MareNostrum 5 — glogin2 (account `uv169161`, group `uv36`; reached with the `train` shell alias)
**Written:** 01/10/2026 · **Finalized:** 07/10/2026 (open items closed)
**Scope:** Elia's reserved working area for DeePMD-kit NNP training of pyrophosphate
hydrolysis with Mg(II) via ArcaNN active learning, and the downstream LFER free-energy study.

This file is the map. Each folder's own `README` is the detail; this document says
what is where, what is authoritative, and what will mislead you.

---

## 1. Chemical systems

| Label in tree | Species | Notes |
|---|---|---|
| `pph4` | H₄P₂O₇ | fully protonated; the first and best-developed system |
| `pph3` | H₃P₂O₇⁻ | tri-protonated, in two isomers: `alpha` and `beta` |
| `ppimg2` | 2Mg²⁺·[P₂O₇]⁴⁻ | the bimagnesium complex |
| — | P₂O₇⁴⁻, MgP₂O₇²⁻, H₂P₂O₇²⁻ | appear only in the LFER/speciation tabulations |

`TS1`…`TS5` throughout the tree are the stationary points along the hydrolysis path.

## 2. Scale

| Folder | Dirs | Files | Max depth |
|---|---:|---:|---:|
| `LFER/` | 8 167 | 127 015 | 9 |
| `Train_PPiMg2/` | 4 482 | 48 639 | 9 |
| `JOBS/` | 3 455 | 44 033 | 5 |
| `templates/` | 1 026 | 12 190 | 5 |
| `pph3/` | 890 | 11 000 | 3 |
| `RESULTS/` | 416 | 2 554 | 3 |
| `softwares/` | 135 | 688 | 6 |
| `cp2k_MD/` | 6 | 54 | 3 |
| `script/`, `user_files_MN5/` | 1 each | 11 / 13 | 1 |

`LFER/` is 1 005 GB, `Train_PPiMg2/` 285 GB. Counts measured 07/10/2026. Before the
merges the LFER study was duplicated across both at 884 GB each, and
`NNP_LFER_choice/` at 121 GB each; each now exists once.

## 3. Three things to know before touching anything

**3.1 — The LFER study used to exist twice. As of 02/10/2026 it does not.**

```
/gpfs/scratch/uv36/adrian/deepmd-training/LFER/LFER_3_mg2/          the only copy
/gpfs/scratch/uv36/adrian/deepmd-training/Train_PPiMg2/LFER_3_mg2   -> symlink to it
```

The former `Train_PPiMg2/LFER_3_mg2/` directory was merged into `LFER/LFER_3_mg2/`
and deleted. The merge was bidirectional: after the 28/08 sync each side had work the
other lacked — 74 files only in `LFER/`, 7 only in `Train_PPiMg2/`, and 23 present on
both with different content. All 23 were resolved by reading each diff, and at the
time the losing version was kept beside the winner as `<name>.from_lfer_<date>` or
`<name>.from_train_<date>`. **Those 23 safety copies were deleted on 07/10/2026**
once reviewed, so they are no longer on disk; before deleting them the original
level-diagram renderer was rescued out of them as `LFER_3_mg2/TS_barplot_v1.py`.
Only a `__pycache__` bytecode entry was dropped at merge time. Verified by checksum (job 46887868, `rsync -avhnc`, 1 h 17 m over
947.78 GB) before anything was deleted.

**The path `Train_PPiMg2/LFER_3_mg2` still resolves** — it is a symlink, kept because
159 scripts hardcode the old absolute path, nearly all to reach the NNP graphs
(83 `convert_restart_to_lmp.py`, 67 `generate_US_window.py`, 7
`job-array_lammps-deepmd_explore_gpu_alogin1.sh`). Both spellings reach one copy, so
editing through either edits the same file.

**`LFER/copy_LFER_3_mg2.sh` and `verify_LFER_3_mg2.sh` are retired**
(`.retired_20261002`). Because of the symlink their `SRC` and `DST` now resolve to
the same directory, so the copy script would rsync the tree onto itself. Do not run
them.

**`NNP_LFER_choice/` is now single too** (07/10). `LFER/NNP_LFER_choice/` is the only
copy and `Train_PPiMg2/NNP_LFER_choice` is a symlink to it — necessary because 1830
files in that tree hardcode the old absolute path, mostly to reach
`WHAM_files/wham1D.py`. Verified byte-identical by checksum (job 47028791, 129.52 GB,
10 min) before the duplicate was removed; 121 GB recovered.

**So both entries in `Train_PPiMg2/` are now symlinks into `LFER/`.** Only
`Simulations/` and `initial_dataset/` are real directories there.

**3.2 — `RESULTS/energies/` holds two incompatible generations of the same calculation,
and the folder names do not say which.** Details in its README; summary in §5.

**3.3 — Replica folders are consistent, but three replica sets are incomplete.**
See §4 and §5.

## 4. The recurring sub-structure

Repeated near-verbatim for pph4 / pph3-alpha / pph3-beta / ppimg2:

```
<system>/
  OPES_*/                 OPES exploration of the TS region
  SMD_* | */SMD/          steered MD, pulls A -> B, emits window seed structures
  US_*  | */US/
      USW_100_<A>_<B>/    100 umbrella windows between endpoints A and B
          rep_1 .. rep_3/ three independent replicas (different seeds)
              000 .. 099/ one directory per window
              COLVAR/     PLUMED collective-variable output
              WHAM/       per-replica WHAM input/output
              inputs/     LAMMPS + PLUMED decks; lmp_files/ = starting configs
  WHAM_files/             combined WHAM across replicas -> final PMF
```

**Replica consistency was checked, not assumed.** Across `pph4/US/USW_*`,
`pph3/US_inter_{alpha,beta}/USW_*`, `ppimg2/TS_inter/*/US` and `NNP_LFER_choice/NNP_*`,
every replica carries the full 100 windows and the same file set once the SLURM job id in
`LAMMPS_DeepMD.<jobid>_<window>` log names is normalized away. Remaining differences are
incidental working files (`look_for_conf.py`, `generate_US_window*.py`,
`Valid_configurations.txt`, `COLVAR_bis`, `plumed_USW_XX.dat`, `safe/`, `_orig_*` backups)
present in one replica and not another; none affect sampling. **Replicas are therefore
documented once in their parent, never one README per replica.**

Note `pph4/rep_N` and `pph4/rep_N_tot_constrained` are *not* replicas of each other — they
are two different restraint variants (unconstrained vs fully constrained).

## 5. Per-folder review

### `/gpfs/scratch/uv36/adrian/deepmd-training/JOBS/`
~2 000 machine-generated SLURM scratch dirs `JOB-<id>/` serving every pipeline in the tree.
Arbitrary job ids, no internal organisation, not a replica set. Audit trail only; nothing
downstream reads it. Not documented per-directory, by design.

### `/gpfs/scratch/uv36/adrian/deepmd-training/cp2k_MD/`
Reference CP2K DFT-MD on PPiMg2, predating the NNP work. Used to produce and validate
starting geometries and to sanity-check the reaction-coordinate definitions later reused by
the NNP+PLUMED LFER runs. `configuration/` holds three starting-geometry framings (full,
"edges", "sides"); `PPiMg2_sides/` is an NVT run from the "sides" geometry; `CP2K_opt_SMD/`
is a steered-MD run driving the reaction directly, with the detailed work log in
`CP2K_opt_SMD/initial/README`. All subfolders already documented.

### `/gpfs/scratch/uv36/adrian/deepmd-training/pph3/`
ArcaNN CP2K **labeling batch** for the pph3 training set. **Unrelated to the free-energy
study of the same name** under `LFER/LFER_3_mg2/pph3/` — the name collision is the single
most likely source of confusion in this tree. `002-labeling/` holds the labeling
calculations; `JOBS/` holds 86 per-job scratch dirs. *README added to `pph3/JOBS/` this pass.*

### `/gpfs/scratch/uv36/adrian/deepmd-training/LFER/`
The single home of the LFER study since 02/10/2026. Contains `LFER_3_mg2/` (the production study: `pph4/`, `pph3/`, `ppimg2/`),
`NNP_LFER_choice/`, the sync/verify scripts and their logs. It carries the detailed per-folder documentation (82 READMEs).
`LFER_3_mg2/README` is now the fuller 20 449-byte version. The 8 662-byte copy it
previously held was parked at merge time and then deleted on 07/10 with the rest of
the parked set; the nearest surviving snapshot is the earlier, different
`LFER_3_mg2/README.bak_20260828` (7 220 bytes). Still outstanding: the four per-system
`ts_levels_<system>.png` figures were generated from a superseded `ts_energies.txt`,
and regenerating them is currently blocked — see §7 item 3.

### `/gpfs/scratch/uv36/adrian/deepmd-training/LFER/NNP_LFER_choice/`
Committee-consistency check: the same reactant→TS1 PMF rebuilt three times, each driven by a
different member of the iteration-004 NNP triplet (DeePMD-kit's LAMMPS plugin drives with the
first-listed graph; the other two only report model deviation). Compare
`NNP_N/average_pmf.png` across arms. *README updated this pass* with three verified
anomalies: `NNP_1/rep_2` is under-populated (1 317 files vs 1 512–1 521); `NNP_3/rep_1`
contains three 4 993-byte **files** literally named `rep_1`/`rep_2`/`rep_3`; `NNP_1/rep_3`
contains a nested `rep_3/` directory holding seven stray logs. All three exist in both the
source and the mirror, so they predate the sync. A glob one level too deep will pick them up.

### `/gpfs/scratch/uv36/adrian/deepmd-training/Train_PPiMg2/`
The live area. Four children:
- `LFER_3_mg2/` — now a **symlink** to `../LFER/LFER_3_mg2` (see §3.1), not a directory.
- `NNP_LFER_choice/` — now a **symlink** to `../LFER/NNP_LFER_choice` (07/10).
- `Simulations/` — general NNP-driven MD of ppimg2 on the iteration-006 committee, separate
  from the PMF machinery. `prod_MD/` is a single reference production run. `TS_OPES/` is OPES
  exploration of the TS region — *README corrected this pass*: it claimed five replicas, but
  `rep1`/`rep2` are complete, `rep3` is partial (missing the three NNP graphs and the LAMMPS
  input/log) and `rep4`/`rep5` are **empty**. Usable statistics: two replicas.
- `initial_dataset/` — generation of the pre-iteration-0 training set. *README.md added this
  pass*; the author's `README.txt` and `new_rep/README` were deliberately left untouched.
  Two generations: the top-level `rep1`…`rep13` were extracted with VMD, which truncated
  coordinate decimals and distorted structures (CP2K "atom closer than 0.5 Å"), so rep3–rep8
  were discarded; `new_rep/` is the script-based re-extraction and is the live data. The
  deliverable is `new_rep/init_mg2ppi-initial/` in DeePMD `.raw`/`set.000/*.npy` format.
  Dead ends flagged: `init_ppmg2_initial/` is **empty**; `new_rep/rep13_dynamic/` has
  zero-byte outputs; `new_rep/` has no `rep10`.

### `/gpfs/scratch/uv36/adrian/deepmd-training/RESULTS/`
Pure post-processing, no MD or DFT. *README expanded this pass.* `bulk.sh` drives the grid.
- `speciation/` — 400-run 20×20 grid (total Mg × total PP, 5–100 mM) of eleven-species
  equilibrium speciation vs pH. Thoroughly documented already, including the key negative
  result: Mg:PP ratio alone does **not** fix speciation, because Mg₂P₂O₇ is second order in
  free Mg. Also flags that `beta_mgoh = 0.0`, i.e. MgOH⁺ is declared but switched off.
- `energies/` — *README added this pass.* Converts a speciation curve plus a hand-entered
  table of per-species barriers into a Boltzmann-weighted effective ΔG‡ and Eyring rate
  constant vs pH. **Two incompatible generations:** the older folders (`0001_0120`,
  `0020_0050`, `01_002`, `03_03`, `1_0002`) use hpp = 29.0 / h3pp = 23.5 and define
  "catalyzed" as the three Mg complexes only; the newer ones (`0010_0010`, `0010_0020`,
  `0010_0050`, `0050_0100`) use hpp = 31.18 / h3pp = 23.75 and define "catalyzed" as **all
  eight** species. `wolfenden_case` uses the new grouping with its own barrier table and
  overlays experimental data. Consequences: in the new generation the two output columns
  coincide at low pH — that is correct, not a bug, because both averages are then dominated
  by the same protonated species; and the top-level `delta_G.py` is the **old** generation,
  so re-running it will not reproduce the new folders. Always use the frozen copy inside each
  subfolder. Unresolved: nothing records where the barriers in `energies.txt` came from.

### `/gpfs/scratch/uv36/adrian/deepmd-training/templates/`
ArcaNN scaffolding, currently one stage: `01_initial_trainingset/`, the pre-iteration-0
training-set generation for the 518-atom PPiMg2 system. Two parallel systems `Sys_1/` and
`Sys_2/`, each with five CP2K NVT-MD stages (revPBE-D3, 298 K) plus matching `-restart/`
reruns, a radial-distribution check, and ~500 numbered CP2K single-point labeling folders.
The README notes the five stages look like independent equilibration attempts rather than a
chained protocol — unconfirmed, and worth resolving before anyone reuses the protocol.

### `/gpfs/scratch/uv36/adrian/deepmd-training/user_files_MN5/`
ArcaNN machine configuration for MN5: `machine.json` (per-login-node SLURM partition, QOS,
account, job/array limits for glogin2 CPU and alogin2 GPU), `training_3.0.json` (DeePMD
hyperparameters), and one job-script template per ArcaNN step and queue. These are what the
chain dispatcher copies and fills per iteration.

### `/gpfs/scratch/uv36/adrian/deepmd-training/script/`
Eleven standalone helpers not tied to one pipeline: energy extraction and plotting
(`extract.py`, `energy_grep.py/.sh`, `energy_chart.sh`), `generate_xyz.sh`, post-hoc checks
(`check_distance.sh`, `check_convergence.sh`), two generic SLURM templates, and a loose
working copy of `speciation.py`.

### `/gpfs/scratch/uv36/adrian/deepmd-training/softwares/`
Live git checkout of `github.com/arcann-chem/arcann_training` plus its offline conda bundle.
Has its own upstream `README.md`. **No README was added here**, deliberately — it is a git
working tree that is not this project's own data, and untracked files do not belong in it.

## 6. What the 01/10 documentation pass changed

Eight files written, all under
`/gpfs/scratch/uv36/adrian/deepmd-training/`. Every replaced file was first copied to
`<name>.bak_20261001`; no file was deleted and no data was modified.

| Action | Path |
|---|---|
| added | `RESULTS/energies/README` |
| added | `pph3/JOBS/README` |
| added | `Train_PPiMg2/initial_dataset/README.md` |
| updated | `README` (root) |
| updated | `RESULTS/README` |
| updated | `Train_PPiMg2/Simulations/TS_OPES/README` |
| updated | `LFER/NNP_LFER_choice/README` |
| updated | `Train_PPiMg2/NNP_LFER_choice/README` |
| added | `STRUCTURE_OVERVIEW.md` (this file) |

Folders deliberately left without a README: `softwares/` (foreign git tree), the empty
`Train_PPiMg2/initial_dataset/init_ppmg2_initial/` and
`LFER/LFER_3_mg2/ppimg2/PMF_react_prod/SMD/TS3/TS2/` (documented in their parents instead),
and all replica and per-window directories (covered by their parents, per §4).

## 6b. What the 02/10 merge changed

| Action | Path |
|---|---|
| merged into | `LFER/LFER_3_mg2/` (+23 parked variants, +6 files from the old copy) |
| deleted | `Train_PPiMg2/LFER_3_mg2/` (884 GB, 114 136 files) |
| created | `Train_PPiMg2/LFER_3_mg2` → `../LFER/LFER_3_mg2` (symlink) |
| retired | `LFER/copy_LFER_3_mg2.sh`, `LFER/verify_LFER_3_mg2.sh` → `.retired_20261002` |
| updated | root `README`, `LFER/README`, `Train_PPiMg2/README`, this file |
| audit trail | `.merge_audit/` — manifests, action log, `verify_merge.log` |

Group `uv36` scratch went from 28.36 TB to 27.56 TB of its 31.25 TB quota.

## 6c. What the 07/10 pass changed

| Action | Path |
|---|---|
| preserved | `LFER/LFER_3_mg2/TS_barplot_v1.py` — the original level-diagram renderer, rescued from the parked variants before they were deleted |
| deleted | the 23 parked `.from_lfer_*` / `.from_train_*` variants under `LFER/LFER_3_mg2/` |
| deleted | 3 misnamed script copies in `LFER/NNP_LFER_choice/NNP_3/rep_1/` and the nested `NNP_1/rep_3/rep_3/` |
| preserved | `LFER/NNP_LFER_choice/NNP_1/rep_3/inputs/plumed_USW_XX.dat.from_nested_20260729` |
| deleted | `Train_PPiMg2/NNP_LFER_choice/` (121 GB) after checksum verification |
| created | `Train_PPiMg2/NNP_LFER_choice` → `../LFER/NNP_LFER_choice` (symlink) |
| updated | root `README`, `LFER/README`, `Train_PPiMg2/README`, `RESULTS/energies/README`, `TS_OPES/README`, `LFER/NNP_LFER_choice/README`, this file |
| audit trail | `.merge_audit/verify_nnp.log` |

Group `uv36` scratch went from 27.69 TB to 27.53 TB.

## 7. Open items

1. ~~Consolidate the LFER documentation~~ — done 02/10; the tree is now single.
2. ~~Merge the two `LFER_3_mg2/README` versions~~ — done 02/10; the fuller one is live.
3. `ts_levels.png` ~~regenerate~~ — **not needed**; verified 07/10 that the current file
   is already reproduced byte-identically by `TS_barplot_v1.py` from the present
   `ts_energies.txt`. **Still open:** the four per-system `ts_levels_<system>.png` cannot
   be regenerated until `TS_levels_per_system.py` gains `bHP2O7`, `aHP2O7` and `MgHP2O7`
   in its `SYSTEMS` dict — it currently raises `ValueError` on the 25/08 data file.
   Titles and colours can be copied verbatim from `TS_barplot.py`.
4. ~~Record the provenance of the barriers~~ — done 07/10: hand-written by Elia and
   placed manually; no generating script exists.
5. ~~Decide on `TS_OPES/rep3`–`rep5`~~ — decided 07/10: **leave as they are**, Elia will
   review them. Not clutter to tidy.
6. ~~Clean the stray `rep_*` artifacts~~ — done 07/10.
7. ~~Collapse the `NNP_LFER_choice/` duplicate~~ — done 07/10, with symlink.
8. ~~Delete the parked merge variants~~ — done 07/10, after rescuing `TS_barplot_v1.py`.
9. Rewrite the 159 hardcoded `Train_PPiMg2/LFER_3_mg2` paths — **declined 07/10**; the
   symlink stays. Same now applies to the 1830 `Train_PPiMg2/NNP_LFER_choice` paths.
10. `NNP_LFER_choice/NNP_1/rep_2` is under-sampled (1317 files vs 1521 / 1512). Left
    alone deliberately — treat the NNP_1 arm as weaker when comparing the three PMFs.
11. Pending: sync the October work to `ENLAIAC/TFM-NNP`, including `Training_2Mgcomplex`
    from Elia's own account `upg826249`.
