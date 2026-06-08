```tcl
# ===============================
# VMD template for LAMMPS traj
# Usage:
# vmd -e template.tcl traj.lammpstrj
# ===============================

# Get trajectory filename from command line
set trajfile [lindex $argv 0]

# Load LAMMPS trajectory
mol new $trajfile type lammpstrj waitfor all

# Turn off axes
axes location Off

# ===============================
# Set colors for atom types
# ===============================

# Type 1 -> white
color Type 1 white

# Type 2 -> red
color Type 2 red

# Type 3 -> green
color Type 3 pink

# Type 4 -> orange
color Type 4 orange


mol delrep 0 top
mol representation VDW 0.2 12
mol selection {serial 1 to 11 309}
mol color Type
mol addrep top

mol representation DynamicBonds 2.0 0.1
mol selection {serial 1 to 11 309}
mol color Type
mol addrep top

mol representation DynamicBonds 1.4 0.1
mol selection {within 1.4 of serial 1 to 309}
mol color Type
mol addrep top

mol representation VDW 0.2 20
mol selection {within 1.4 of serial 1 to 11 309}
mol color type
mol addrep top

mol representation VDW 0.2 20
mol selection type 1 2
mol color type
mol addrep top

mol representation VDW 0.2 20
mol selection {serial 309}
mol color ColorID 4
mol addrep top

# ===== PBC wrapping =====
pbc wrap -center com -centersel "serial 6" -all

# ===== Alignment =====

# Reference selection from first frame
set ref [atomselect top "serial 2 to 10" frame 0]

# Number of frames
set nframes [molinfo top get numframes]

# Loop over all frames
for {set i 0} {$i < $nframes} {incr i} {

    # Selection for current frame
    set sel [atomselect top "serial 2 to 10" frame $i]

    # Compute transformation matrix
    set M [measure fit $sel $ref]

    # Apply alignment to whole system
    set all [atomselect top "all" frame $i]
    $all move $M

    # Clean up
    $sel delete
    $all delete
}

# Delete reference selection
$ref delete
```

