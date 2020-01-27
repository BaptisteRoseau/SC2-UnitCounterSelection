import numpy as np
import os

pathBot1Input  = os.path.join("data", "Bot1", "INPUT")
pathBot2Input  = os.path.join("data", "Bot2", "INPUT")
pathBot1Output = os.path.join("data", "Bot1", "OUTPUT")
pathBot2Output = os.path.join("data", "Bot2", "OUTPUT")

def numberOfFiles(path):
    return len([f for f in os.listdir(path)if os.path.isfile(os.path.join(path, f))])

file_count = numberOfFiles(pathBot1Input)
assert file_count == numberOfFiles(pathBot2Input)
assert file_count == numberOfFiles(pathBot1Output)
assert file_count == numberOfFiles(pathBot2Output)
# If you pass this line, the data has the good format
print("Found", file_count, "files.")



# Cumputing first step to initialize inputArr and outputArr
waveInputArr = np.array([np.concatenate((np.loadtxt(os.path.join(pathBot1Input, "InputWave1.csv"), dtype=np.float32),
                          np.loadtxt(os.path.join(pathBot2Input, "InputWave1.csv"), dtype=np.float32)), axis=0)])
inputArr = waveInputArr.copy()

waveOutputArr = np.loadtxt(os.path.join(pathBot1Output, "OutputWave1.csv"), dtype=np.float32) - np.loadtxt(os.path.join(pathBot2Output, "OutputWave1.csv"), dtype=np.float32)
outputArr = np.array([waveOutputArr])


terranBotWaveInputArr = np.array([np.loadtxt(os.path.join(pathBot2Input, "InputWave1.csv"), dtype=np.float32)])
terranBotInputArr = terranBotWaveInputArr.copy()

# Concatenating each files
print("Concatenating files... (0%)", end='\r')
for i in range(2, file_count+1):
    waveInputArr = np.array([np.concatenate((np.loadtxt(os.path.join(pathBot1Input, "InputWave"+str(i)+".csv"), dtype=np.float32),
                          np.loadtxt(os.path.join(pathBot2Input, "InputWave"+str(i)+".csv"), dtype=np.float32)), axis=0)])
    inputArr = np.concatenate((inputArr, waveInputArr), axis=0)

    waveOutputArr = np.loadtxt(os.path.join(pathBot1Output, "OutputWave"+str(i)+".csv"), dtype=np.float32) - np.loadtxt(os.path.join(pathBot2Output, "OutputWave"+str(i)+".csv"), dtype=np.float32)
    outputArr = np.append(outputArr, [waveOutputArr], axis=0)

    terranBotWaveInputArr = np.array(np.loadtxt(os.path.join(pathBot2Input, "InputWave"+str(i)+".csv"), dtype=np.float32))
    terranBotInputArr = np.concatenate((terranBotInputArr, [terranBotWaveInputArr]), axis=0)

    print("Concatenating files... ("+str(100*i/file_count)+"%)", end='\r')
print()

# Saving data into numpy format
print("Input data shape", inputArr.shape)
print("Output data shape", outputArr.shape)
print("Terran Bot data shape", terranBotInputArr.shape)
np.save(os.path.join("data", "MergedData", "InputData.npy"), inputArr)
np.save(os.path.join("data", "MergedData", "OutputData.npy"), outputArr)
np.save(os.path.join("data", "MergedData", "terranBotInputData.npy"), terranBotInputArr)
print("Saved", os.path.join("data", "MergedData", "InputData.npy"))
print("Saved", os.path.join("data", "MergedData", "OutputData.npy"))
print("Saved", os.path.join("data", "MergedData", "terranBotInputData.npy"))