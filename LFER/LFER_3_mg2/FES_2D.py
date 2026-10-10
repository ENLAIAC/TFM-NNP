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
plt.colorbar(contour, label='Free Energy (kcal/mol)')
plt.xlabel('D_Ow-P - D_Ob-P (Å)', fontsize=20)
plt.ylabel('C_Ow-H - C_Ob-H', fontsize=20)
#plt.ylabel('C_Ow-H')
#plt.ylabel('C_Ob-H')
#plt.xlabel('D_Ow-P + D_Ob-P (Å)' )
#plt.ylabel('C_Ol-H')
#plt.title('Difference between pyrophosphate(4-) and pyrophosphate-mg(2-) surfaces')
plt.title('Pyrophosphate(4-) hydrolysis')
#plt.title('Pyrophosphate-mg(2-) hydrolysis')
plt.xlim(dD.min(), dD.max())
plt.ylim(dC.min(), dC.max())
plt.tight_layout()
plt.savefig('FES_2D.png', dpi=300, bbox_inches='tight')
#plt.show()
