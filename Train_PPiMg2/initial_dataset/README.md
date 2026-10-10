=====================================
FOLDER: initial_dataset
SYSTEM: MareNostrum 5 — glogin2
CREATED: 01/10/2026
UPDATED: 01/10/2026
PURPOSE: Generation of the pre-iteration-0 DeePMD training set for the ppimg2
         (2Mg(2+)[P2O7](4-)) system: CP2K AIMD trajectories, frame extraction,
         CP2K labeling of the extracted frames, and conversion to DeePMD format.
=====================================

01/10/2026

o Added this file as a structural guide. The author's own notes are in
  'README.txt' and in 'new_rep/README' and I have deliberately left both
  untouched -- they carry the configuration counts and the hand-over notes to
  Adrian, and they remain the authority on how many frames each replica gave.
  What follows is the folder layout and the traps, not a restatement of those
  counts.

o Read the two generations in order, because the first one is discarded. The
  top-level 'rep1' ... 'rep13' are the FIRST extraction attempt. Per 'README.txt',
  rep3 through rep8 are corrupted: VMD was used to subsample the AIMD trajectory
  and it truncated decimal digits in the atomic coordinates, which displaced atoms
  enough that CP2K raised "atom closer than 0.5 A" and either failed to converge
  or returned an energy far from the undistorted reference. Those frames were
  excluded. 'new_rep/' is the SECOND extraction, done with a script instead of VMD,
  and it is the one that converged. Unless you are investigating the corruption
  itself, 'new_rep/' is the live data and the top-level 'repN' are history.

o Inside a 'repN' folder the layout follows ArcaNN's labeling convention:
  'PPiMg2-MD-repN.inp' is the CP2K AIMD input that generated the trajectory,
  'PPiMg2-opt-repN.xyz' is the full trajectory, 'repN.xyz' is the subsampled set of
  frames, and one numbered subfolder per extracted frame holds that frame's CP2K
  labeling calculation. The '.txt' files are byproducts of the energy-extraction
  script and are not inputs to anything.

o Helper scripts at this level: 'energy_grep.sh' collects labeled energies into
  'Energy_dist.txt'; 'selected_configurations.txt' and
  'discarded_configurations.txt' are the resulting keep/drop lists. The
  convergence checker referred to in 'README.txt' as 'check_convergence.sh' lives
  in the project-wide '../../script/' folder.

o 'new_rep/init_mg2ppi-initial/' is the end product of the whole folder: the
  training set in DeePMD-kit format. 'box.raw', 'coord.raw', 'energy.raw',
  'force.raw' and 'type.raw' are the flat text system, 'set.000/' holds the same
  data as the '.npy' arrays DeePMD actually reads, and 'raw_generator.py' plus
  'npy_generator.sh' are the two conversion steps. This is the directory that gets
  handed to the ArcaNN iteration-0 training.

o Two empty or dead directories, flagged so they are not mistaken for missing
  data. 'init_ppmg2_initial/' at this level is completely EMPTY -- it is the
  first-generation counterpart of 'new_rep/init_mg2ppi-initial/' and was never
  filled, consistent with the first generation having been abandoned.
  'new_rep/rep13_dynamic/' holds a CP2K input and a job log but every output file
  in it is zero bytes, so that run produced nothing; the usable rep13 data is in
  'new_rep/rep13/'.

o Also note 'new_rep/' has no 'rep10', while the top-level generation does. That is
  not a gap in the numbering to chase: 'README.txt' lists rep10 among the
  not-corrupted first-generation replicas, so it was simply not re-extracted.

o Replica folders are structurally identical to one another by construction (same
  inputs, different trajectory segment and seed), so they are described once here
  rather than carrying one README each.
