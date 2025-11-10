import numpy as np
import pickle
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.ensemble import GradientBoostingClassifier, VotingClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

# Load and prepare data
iris = load_iris()
X, y = iris.data, iris.target

# Split data: 80% train, 20% test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Standardize features (important for SVM)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print("Training SVM with GridSearchCV...")
# SVM with hyperparameter tuning
svm_params = {
    'C': [ 0.1, 1, 10, 100],
    'gamma': ['scale', 'auto', 0.001, 0.01],
    'kernel': ['rbf', 'poly']
}
svm = SVC(probability=True, random_state=42)
svm_grid = GridSearchCV(svm, svm_params, cv=5, n_jobs=-1, verbose=1)
svm_grid.fit(X_train_scaled, y_train)
best_svm = svm_grid.best_estimator_
print(f"Best SVM params: {svm_grid.best_params_}")

print("Training Gradient Boosting...")
# Gradient Boosting for ensemble
gb = GradientBoostingClassifier(
    n_estimators=200,
    learning_rate=0.1,
    max_depth=10,
    random_state=44
)
gb.fit(X_train_scaled, y_train)

print("Creating Voting Classifier ensemble...")
# Ensemble model combining SVM + Gradient Boosting
ensemble_model = VotingClassifier(
    estimators=[('svm', best_svm), ('gb', gb)],
    voting='soft'
)
ensemble_model.fit(X_train_scaled, y_train)

# Evaluate
y_pred = ensemble_model.predict(X_test_scaled)
y_pred_proba = ensemble_model.predict_proba(X_test_scaled)

print("\n=== MODEL EVALUATION ===")
print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
print(f"\nConfusion Matrix:\n{confusion_matrix(y_test, y_pred)}")
print(f"\nClassification Report:\n{classification_report(y_test, y_pred, target_names=iris.target_names)}")

# Save model and scaler
print("\nSaving model and scaler...")
with open('model.pkl', 'wb') as f:
    pickle.dump(ensemble_model, f)

with open('scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)

print("✅ Model saved to model.pkl")
print("✅ Scaler saved to scaler.pkl")
