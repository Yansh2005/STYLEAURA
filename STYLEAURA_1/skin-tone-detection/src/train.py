import pickle
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import cv2
import numpy as np

data = pd.read_csv(
    "dataset/Skin_NonSkin.txt",
    sep="\t",
    header=None,
    names=["R", "G", "B", "Label"]
)

def rgb_to_hsv(row):
    rgb = np.uint8([[[row['R'], row['G'], row['B']]]])
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    return hsv[0][0]

data[['H','S','V']] = data.apply(
    lambda row: pd.Series(rgb_to_hsv(row)),
    axis=1
)

X = data[['H','S','V']]
y = data['Label']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

with open("models/skin_classifier.pkl", "wb") as f:
    pickle.dump(model, f)

print("Model trained and saved!")
