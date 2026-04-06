import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
import os

print("--- Starting Model Training ---")

# 1. Load the dataset
try:
    df = pd.read_csv('crop_data.csv')
    print("Dataset loaded successfully.")
    print(f"Dataset shape: {df.shape}")
except FileNotFoundError:
    print("Error: crop_data.csv not found! Please make sure it's in the backend directory.")
    exit()

# 2. Define features (X) and the target (y)
# These are the input columns the model will use to make a prediction.
features = [
    'temperature_c',
    'soil_ph',
    'soil_moisture_percent',
    'rainfall_mm',
    'humidity_percent',
    'sunlight_hours'
]
target = 'crop'

X = df[features]
y = df[target]
print("Features and target variable defined.")

# 3. Split the data into training and testing sets
# 80% for training, 20% for testing. This helps us see how well the model performs on new, unseen data.
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print("Data split into training and testing sets.")

# 4. Initialize and train the model
# We're using a RandomForestClassifier, which is excellent for this type of problem.
model = RandomForestClassifier(n_estimators=100, random_state=42)
print("Training the RandomForestClassifier model...")
model.fit(X_train, y_train)
print("Model training complete.")

# 5. Evaluate the model's performance
print("Evaluating model performance...")
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)
print(f"Model Accuracy on Test Data: {accuracy * 100:.2f}%")

# 6. Save the trained model
# The model will be saved to the 'models' folder, overwriting the old mock model.
model_path = os.path.join('models', 'crop_recommender.pkl')
joblib.dump(model, model_path)
print(f"Model saved successfully to: {model_path}")
print("--- Model Training Finished ---")