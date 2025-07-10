import os
import glob
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split 
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from scipy.stats import skew 
from sklearn import svm
from sklearn.metrics import accuracy_score
from sklearn.metrics import classification_report
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from pretty_confusion_matrix import pp_matrix_from_data
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier


os.chdir(os.path.dirname(os.path.abspath(__file__)))


def getAlldata(files):
    li = []
    for filename in files:
        df = pd.read_csv(filename, index_col=None, header=0)
        li.append(df)
    data = pd.concat(li, axis=0, ignore_index=True)
    data = data.to_numpy()
    return data[:,1:10]


# Get feature and target data
NoStim= glob.glob("StimulationRecognition\_Nostim" + "/*.csv")
NoStimdata = getAlldata(NoStim)
NoStimtarget = np.zeros((NoStimdata.shape[0],1))

Cerci = glob.glob("StimulationRecognition\Cerci" + "/*.csv")
Cercidata = getAlldata(Cerci)
Cercitarget = np.ones((Cercidata.shape[0],1))*1

RightAntenna = glob.glob("StimulationRecognition\RightAntenna" + "/*.csv")
RightAntennadata = getAlldata(RightAntenna)
RightAntennatarget = np.ones((RightAntennadata.shape[0],1))*2

LeftAntenna = glob.glob("StimulationRecognition\LeftAntenna" + "/*.csv")
LeftAntennadata = getAlldata(LeftAntenna)
LeftAntennatarget = np.ones((LeftAntennadata.shape[0],1))*3

# Get features and target set
features = np.concatenate((NoStimdata, Cercidata, RightAntennadata, LeftAntennadata), axis=0)
target = np.concatenate((NoStimtarget, Cercitarget, RightAntennatarget, LeftAntennatarget), axis=0)

data = np.concatenate((features, target), axis=1)
print(features.shape)

np.savetxt("dataStim.csv", data,delimiter = ",", fmt="%.2f")


X, X_test, y, y_test = train_test_split(features, target, test_size=1./3, random_state=1)

# clf = SVC(kernel="linear", C=10).fit(X, y)
# clf = RandomForestClassifier(n_estimators = 100).fit(X, y)
clf = MLPClassifier(hidden_layer_sizes=(150,100), max_iter=1000,activation = 'relu',solver='adam',random_state=1, verbose=True).fit(X, y)


# print(y_test)
test_pred = clf.predict(X_test)
target_names = ["NoStim", "Cerci Stim", "RightAntenna Stim", "LeftAntenna"]

print("-------------------------------------------------")
print(classification_report(y_test, test_pred, labels = np.arange(len(target_names)), target_names=target_names, digits=4))
print("-------------------------------------------------")
print("accuracy score  ", accuracy_score(y_test, test_pred))
print("-------------------------------------------------")

pp_matrix_from_data(y_test, test_pred, cmap="winter", title ="MLP")

#save the model 
filename = 'MLP_Stim.sav'
pickle.dump(clf, open(filename, 'wb')) 



