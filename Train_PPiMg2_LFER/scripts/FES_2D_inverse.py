import numpy as np
import matplotlib.pyplot as plt

# Load data from file
data = np.genfromtxt('fes-rew.dat', comments='#')

# Extract columns
dC = data[:, 0]
dD = data[:, 1]
free_energy = data[:, 2]

# Define grid for contour plot
x_unique = np.sort(np.unique(dD))
y_unique = np.sort(np.unique(dC))
X, Y = np.meshgrid(x_unique, y_unique)

#print('X')
#print(X)
#print('Y')
#print(Y)

# Reshape free energy values to match grid
Z = free_energy.reshape(len(y_unique), len(x_unique)).T
#print('Z')
#print(Z)

# Plot contour plot
plt.figure(figsize=(8, 6))
contour = plt.contourf(X, Y, Z, cmap='rainbow', levels=np.linspace(0, 50, 25))
#contour = plt.contourf(X, Y, Z, cmap='rainbow', levels=np.linspace(-10, 10, 7))
cbar = plt.colorbar(contour)
cbar.set_ticks(np.arange(0, 51, 5))  # <-- Add this line
cbar.ax.tick_params(labelsize=16)   # tick font size
cbar.set_label(r'Free energy (kcal · mol$^{-1}$)', fontsize=20)
#plt.xlabel(r'$d_{\mathrm{O_{b}}\!-\!P} - d_{\mathrm{O_{w}}\!-\!P}$ (Å)', fontsize=14)
#plt.ylabel(r'$C_{\mathrm{O_{b}}\!-\!H} - C_{\mathrm{O_{w}}\!-\!H}$', fontsize=14)
plt.xlabel(r'$d_{p \mathscr{l}} - d_{pw}$ (Å)', fontsize=20)
plt.ylabel(r'$C_{\mathscr{l}} - C_{w}$', fontsize=20)
plt.tick_params(axis='both', labelsize=16)
#plt.title('Pyrophosphate(4-) hydrolysis')
#plt.title(r'$P_{2}O_{7}^{4-}$ hydrolysis')
#plt.title('Pyrophosphate(2-) hydrolysis')
plt.xlim(dD.min(), dD.max())
plt.ylim(dC.min(), dC.max())
plt.tight_layout()
plt.savefig('FES_2D.png', dpi=600, bbox_inches='tight')
#plt.show()
