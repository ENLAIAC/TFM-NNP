#!/bin/bash

cat << EOF > import.py
import numpy as np
c=np.loadtxt("coord.raw").astype(np.float32)
b=np.loadtxt("box.raw").astype(np.float32)
f=np.loadtxt("force.raw").astype(np.float32)
e=np.loadtxt("energy.raw").astype(np.float32)
np.save("energy",e)
np.save("box",b)
np.save("force",f)
np.save("coord",c)
EOF

python import.py
mkdir set.000
mv *npy set.000
rm import.py