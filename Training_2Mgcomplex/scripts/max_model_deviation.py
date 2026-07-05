#Script to plot the max model deviation after an exploration phase of ArcaNN. Needs to be executed inside
#the XXX-exploration folder. 
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import os

#Gets the iteration from the working directory name
working_directory = os.path.basename(os.getcwd())
iteration = working_directory.split('-')[0]

#The json files are loaded to save the data of the exploration step
exploration_json_file = 'used_input.json'
input_json_file = '../used_input.json'

with open(exploration_json_file, 'r') as json_file:
    data_exploration = json.load(json_file)
with open(input_json_file, 'r') as json_file:
    data_systems = json.load(json_file)

systems_names = data_systems["systems_auto"]
nnp_count = data_systems["nnp_count"]
sigma_low = data_exploration["sigma_low"]
sigma_high = data_exploration["sigma_high"]
traj_count = data_exploration["traj_count"]

#Loop over every system, every NNP and every replica.
i=0
for system in systems_names:
    plt.figure(figsize=(8, 5))
    for j in range(1, nnp_count + 1):
        for k in range(1, traj_count[i] + 1):
            data = np.loadtxt(f'{system}/{j}/{k:05d}/model_devi_{system}_{j}_{iteration}.out', skiprows=1)
            x_values = data[:, 0]  # Assuming column 1 is at index 0
            y_values = data[:, 4]  # Assuming column 5 is at index 4
            # Plot the data
            plt.plot(x_values, y_values, label=f'{j} - {k:05d}')
    plt.axhline(y=sigma_low[i], color='lightblue', linestyle='--')
    plt.axhline(y=sigma_high[i], color='lightblue', linestyle='--')
    plt.ylim(0,1.1)
    plt.xlabel('Step')  # Replace with an appropriate label
    plt.ylabel('Max. Model Deviation (eV)')  # Replace with an appropriate label
    plt.title(f'Max. Model Deviation of {system} in iteration {iteration}')  # Replace with an appropriate title
    plt.legend()
    plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(5))
    plt.savefig(f'max_model_deviation_{system}_{iteration}.png', dpi=300)
    i = i + 1
    print(f'Subsystem {system} data plotted in max_model_deviation_{system}_{iteration}.png')

print('All subsystems are processed!')

