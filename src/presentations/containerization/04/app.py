from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier

print("loading data")
data = load_iris()
X = data.data
y = data.target

print("splitting data")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

knn = KNeighborsClassifier(n_neighbors=3)

print("training model")
knn.fit(X_train, y_train)

accuracy = knn.score(X_test, y_test)
print(f"Accuracy: {accuracy:.2f}")
