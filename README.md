The goal of this project is to predict some of Starcraft II Zerg units able to counter some Terran units to defeat them in an A-clic battle with a minimum of losses.

It uses mostly battle simulation and DeepLearning

## Installation

In order to launch a simulation, you need to install the Python modules listed in requirement.txt by using:

`pip3 install -r requirement.txt`

Then on windows, you need to install the game StarCraft II the official website : https://starcraft2.com/en-us/

On Linux, you need to donwload the game through the following link : https://github.com/Blizzard/s2client-proto
Download and extract the game into ~/StarCraftII, and the maps into ~/StarCraftII/maps (password is iagreetotheeula)

## Simulation of a battle

You can now launch a simulation by using the playGame.py script:

`python3 src/playGame.py`

The Bot used to simulate a battle is mapBot.py. The simulation data is stored into the `data` folder.
It contains numpy float array as text for each waves, which can be merged and compressed using the `mergeData.py` script, into `data/MergedData`.
This data is used by the training scripts.

## Training of the model

### Description
Two jupyter-notebook are used for training. If you want to use a GPU for the training, make you you have CUDA 10.0, 10.1 and 10.2 installed, as they are used by Tensorflow.

[Training_Step_1.ipynb](Training_Step_1.ipynb) uses the results of a battle, taking the units composition, health and upgrades as input, and the result of the battle as output.
This result is between [-1, 1]. -1 if the Terran wins without any losses, 1 the Zerg wins without any losses, 0 if no unit is either dammaged or alive.

[Training_Step_2.ipynb](Training_Step_2.ipynb) takes the Terran units as input, and returns the Zerg units choice to counter them.
It uses reinforcment learning method, using the first predicting model as a reference to estimate the result of the battle.
It is not done yet.

### Commands

After making sure StarCraft II is installed, you can:

1. Run Simulation using `python3 playGame.py`
2. Merge output data using `python3 mergeData.py`
3. Train the model using either `Training_Step_1.ipynb` or `Training_Step_1.ipynb` jupyter notebook.
