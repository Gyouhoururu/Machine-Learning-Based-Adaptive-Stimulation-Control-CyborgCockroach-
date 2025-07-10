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


os.chdir(os.path.dirname(os.path.abspath(__file__)))



def getAlldata(files):
    li = []
    for filename in files:
        df = pd.read_csv(filename, index_col=None, header=0)
        li.append(df)
    data = pd.concat(li, axis=0, ignore_index=True)
    data = data.to_numpy()
    return data[:,1:6]


# Get feature and target data
stop = glob.glob("MotionRecognition\Stop" + "/*.csv")
stopdata = getAlldata(stop)

print(stopdata)
stoptarget = np.zeros((stopdata.shape[0],1))

move = glob.glob("MotionRecognition\Move" + "/*.csv")
movedata = getAlldata(move)
movetarget = np.ones((movedata.shape[0],1))*1


# Get features and target set
features = np.concatenate((stopdata, movedata), axis=0)
target = np.concatenate((stoptarget, movetarget), axis=0)

data = np.concatenate((features, target), axis=1)
print(data)

np.savetxt("data.csv", data,delimiter = ",", fmt="%.2f")


X, X_test, y, y_test = train_test_split(features, target, test_size=1./3, random_state=1)

clf = SVC(kernel="linear", C=10).fit(X, y)

# print(y_test)
test_pred = clf.predict(X_test)
target_names = ["Stop", "Move"]

print("-------------------------------------------------")
print(classification_report(y_test, test_pred, target_names=target_names, digits=4))
print("-------------------------------------------------")
print("accuracy score  ", accuracy_score(y_test, test_pred))
print("-------------------------------------------------")

pp_matrix_from_data(y_test, test_pred, cmap="winter", title ="SVM")

# save the model 
filename = 'SVM_motion.sav'
pickle.dump(clf, open(filename, 'wb')) 

# load the model 
# clf_SVM = pickle.load(open(filename, 'rb')) 

