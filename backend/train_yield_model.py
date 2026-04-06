import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib
import os

print("--- Starting Yield Prediction Model Training ---")

# 1. Load the dataset
try:
    df = pd.read_csv('crop_data.csv')
    # Drop rows where essential data or yield is missing
    df.dropna(subset=['yield_kg_per_hectare', 'crop'], inplace=True)
    print("Dataset loaded successfully.")
except FileNotFoundError:
    print("Error: crop_data.csv not found! Please make sure it's in the backend directory.")
    exit()

# Define the features to be used for prediction
features = [
    'temperature_c',
    'soil_ph',
    'soil_moisture_percent',
    'rainfall_mm',
    'humidity_percent',
    'sunlight_hours'
]
target = 'yield_kg_per_hectare'

# Get a list of unique crops in the dataset
unique_crops = df['crop'].unique()
print(f"Found crop types: {unique_crops}")

# Create the models directory if it doesn't exist
os.makedirs('models/yield_models', exist_ok=True)

# 2. Train a separate model for each crop
for crop_name in unique_crops:
    print(f"\n--- Training model for: {crop_name} ---")
    
    # Filter the dataset for the current crop
    crop_df = df[df['crop'] == crop_name]
    
    if len(crop_df) < 10:
        print(f"Skipping {crop_name}: Not enough data samples ({len(crop_df)}).")
        continue

    X_crop = crop_df[features]
    y_crop = crop_df[target]
    
    # We use RandomForestRegressor because yield is a continuous number
    yield_model = RandomForestRegressor(n_estimators=100, random_state=42)
    
    # Train the model on all data available for that crop
    yield_model.fit(X_crop, y_crop)
    
    # Save the trained model
    model_path = os.path.join('models/yield_models', f'yield_model_{crop_name}.pkl')
    joblib.dump(yield_model, model_path)
    print(f"Model for {crop_name} saved successfully to: {model_path}")

print("\n--- All Yield Models Trained Successfully ---")