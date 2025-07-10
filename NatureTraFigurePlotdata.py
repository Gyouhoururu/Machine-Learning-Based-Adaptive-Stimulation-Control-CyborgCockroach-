import os
import numpy as np
from matplotlib import pyplot as plt, patches
from scipy.signal import butter, lfilter
from scipy.signal import freqs
import scipy.signal
from matplotlib import image 
import glob
from matplotlib.lines import Line2D

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def getData(pathData):
    data = np.loadtxt(pathData, delimiter=",", dtype=float)
    return data

def lowpass(data: np.ndarray, cutoff: float, sample_rate: float, poles: int = 5):
    sos = scipy.signal.butter(poles, cutoff, 'lowpass', fs=sample_rate, output='sos')
    filtered_data = scipy.signal.sosfiltfilt(sos, data)
    return filtered_data

cutFreq = 0.9

fig, ax = plt.subplots(1,figsize=(14, 14))
plt.rcParams.update({'font.size': 25})
im = plt.imread("WIN_20241113_18_24_38_Pro.jpg")
# im = plt.imread("Groundtruth_1.png")
plt.rcParams.update({'font.size': 40})

# im = im[:,1162:-1] # Left cut
# im = im[:,0:2050] # right cut
# im = im[140:-1,:] # top cut

print((im.shape))
ax.imshow(im, extent=[0, 64, 0, 82])

# pathFile = "Nature_Tra_data/Nature_Tra_Old/"
pathFile = "Nature_Tra_data/Nature_Tra_New/"
Files_F = sorted(glob.glob(pathFile+ "F/*.csv"))
Files_S = sorted(glob.glob(pathFile+ "S/*.csv"))


for i, file in enumerate(Files_F):
    if i <= 20:
        data1 = getData(file)
        
        time = data1[:,0]      
        xpos= data1[:,1]
        ypos= data1[:,2]
        theta = data1[:,3]
        xfiltered1 = lowpass(xpos, cutFreq, 25)
        yfiltered1 = lowpass(ypos, cutFreq, 25)
        ax.plot(xfiltered1, yfiltered1, linestyle='solid', color="red", linewidth=1.7)
        # ra = list(data[:,1])
        # la = list(data[:,2])
        # ce = list(data[:,3])
for i, file in enumerate(Files_S):
    if i <= 6:
        data2 = getData(file)
        
        time = data2[:,0]      
        xpos= data2[:,1]
        ypos= data2[:,2]
        theta = data2[:,3]
        xfiltered2 = lowpass(xpos, cutFreq, 25)
        yfiltered2 = lowpass(ypos, cutFreq, 25)
        # ax.plot(xpos, ypos, linestyle='solid', color="red", linewidth=1.7)
        ax.plot(xfiltered2, yfiltered2, linestyle='solid', color="blue", linewidth=1.7)
     

labels = ["Successful", "Failed"]
lines = [       Line2D([0], [0], color="blue", linewidth=2, linestyle='solid'), 
                Line2D([0], [0], color="red", linewidth=2, linestyle='solid')]

fig.legend(lines, labels, loc="upper center", fontsize = 16, bbox_to_anchor=(0.5, 0.93), ncol=4) 
ax.text(71, 60, "N = 25", fontsize = 20)
ax.text(71, 55, "F$_{N}$ = 19", fontsize = 20)
ax.text(71, 50, "R$_{F}$ = 76%", fontsize = 20)
ax.text(71, 45, "n = 5", fontsize = 20)
ax.set_xlim(0, 70)
ax.set_ylim(0, 85)
ax.set_xlabel(" X (cm)", fontsize = 15)
ax.set_ylabel(" Y (cm)", fontsize = 15)
ax.set_aspect('equal', adjustable='box')
ax.tick_params(axis='x', labelsize=15)
ax.tick_params(axis='y', labelsize=15)


fig.savefig('Natural_Tra')


plt.show()