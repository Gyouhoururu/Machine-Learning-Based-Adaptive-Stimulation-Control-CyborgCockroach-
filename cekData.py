import os
import numpy as np
from matplotlib import pyplot as plt, patches
from scipy.signal import butter, lfilter
from scipy.signal import freqs
import scipy.signal

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def getData(pathData):
    # getData(pathData, start, end):# previously
    data = np.loadtxt(pathData, delimiter=",", dtype=float)
    # data[:,4] = [525 if x>550 else x for x in data[:,4]]
    # data[:,4] = [425 if x<425 else x for x in data[:,4]]
    # data[:,12] = [120 if x>800 else x for x in data[:,12]]
    # data[:,13] = [120 if x>800 else x for x in data[:,13]]
    # data[:,14] = [120 if x>800 else x for x in data[:,14]]
    # data = data[start:end, :]

    return data

# data = getData("data\StimulationNavigationOK2024_04_18-02_09_29_PMData.csv") # Stimulation
data = getData("data/VICONTRAB_DEL/2024_12_16-06_46_58_PMDataOK_VICONTRAB.csv") # Free motion 


def lowpass(data: np.ndarray, cutoff: float, sample_rate: float, poles: int = 5):
    sos = scipy.signal.butter(poles, cutoff, 'lowpass', fs=sample_rate, output='sos')
    filtered_data = scipy.signal.sosfiltfilt(sos, data)
    return filtered_data



time = data[:,0]
xpos= data[:,9]
ypos= data[:,10]

xfiltered = lowpass(xpos, 0.9, 25)
yfiltered = lowpass(ypos, 0.9, 25)
plt.subplot(2, 2, 1)
plt.plot(time, xpos)
plt.plot(time, xfiltered)
plt.subplot(2, 2, 2)
plt.plot(time, ypos)
plt.plot(time, yfiltered)
plt.subplot(2, 2, 3)
plt.plot(xpos, ypos)
plt.plot(xfiltered, yfiltered)
plt.subplot(2, 2, 4)

# plt.plot(time, xfiltered)

plt.show()