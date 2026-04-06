
# To run main.py
# uvicorn main:app --reload


import os
import joblib
from datetime import datetime, timedelta
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
import io
import requests
import numpy as np

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

# --- Configuration & Setup ---
load_dotenv()
app = FastAPI(title="SmartAgro API")
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configure Google AI (Gemini) ---
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
except Exception as e:
    print(f"Error configuring Google AI: {e}")

# --- Load Models on Startup ---
CROP_MODEL_PATH = os.path.join('models', 'crop_recommender.pkl')
try:
    crop_model = joblib.load(CROP_MODEL_PATH)
except FileNotFoundError:
    crop_model = None

YIELD_MODELS_DIR = 'models/yield_models'
yield_models = {}
if os.path.exists(YIELD_MODELS_DIR):
    for model_file in os.listdir(YIELD_MODELS_DIR):
        if model_file.endswith('.pkl'):
            crop_name = model_file.replace('yield_model_', '').replace('.pkl', '')
            yield_models[crop_name] = joblib.load(os.path.join(YIELD_MODELS_DIR, model_file))

# --- Pydantic Models ---
class FarmData(BaseModel):
    temperature_c: float
    soil_ph: float
    soil_moisture_percent: float
    rainfall_mm: float
    humidity_percent: float
    sunlight_hours: float
    irrigation_type: str
    fertilizer_type: str
    pesticide_usage_ml: float
    total_days: int

class ChatMessage(BaseModel):
    message: str
    language: str = 'en'

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the SmartAgro API"}

@app.post("/api/recommend_crop")
async def recommend_crop(data: FarmData):
    if crop_model is None:
        raise HTTPException(status_code=500, detail="Crop recommendation model is not loaded.")
    
    try:
        features = [[
            data.temperature_c, data.soil_ph, data.soil_moisture_percent,
            data.rainfall_mm, data.humidity_percent, data.sunlight_hours
        ]]
        recommended_crop = crop_model.predict(features)[0]
        confidence = crop_model.predict_proba(features).max()
        
        predicted_yield = 0
        if recommended_crop in yield_models:
            yield_model = yield_models[recommended_crop]
            predicted_yield = yield_model.predict(features)[0]
        
        sowing_date = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
        harvest_date = (datetime.now() + timedelta(days=100)).strftime('%Y-%m-%d')

        return {
            "recommended_crop": recommended_crop,
            "confidence": float(confidence),
            "predicted_yield_kg_per_hectare": round(predicted_yield, 2),
            "sowing_date": sowing_date,
            "harvest_date": harvest_date
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/detect_disease")
async def detect_disease(file: UploadFile = File(...)):
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="Gemini API key not configured.")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        image_bytes = await file.read()
        pil_image = Image.open(io.BytesIO(image_bytes))
        prompt = "Analyze this image of a plant leaf. Identify the specific disease if one is present, or state if the plant appears healthy. Provide only the name of the disease or 'Healthy'."
        response = model.generate_content([prompt, pil_image])
        prediction = response.text.strip()
        return {"prediction": prediction}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while analyzing the image.")

@app.post("/api/chat")
async def chat(message: ChatMessage):
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="Gemini API key not configured.")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        language_map = {'en': 'English', 'hi': 'Hindi'}
        lang_name = language_map.get(message.language, 'English')
        system_prompt = f"You are SmartAgro Assistant, an expert in agriculture. Provide a clear and helpful answer in the {lang_name} language."
        full_prompt = f"{system_prompt}\n\nUser Question: {message.message}"
        response = model.generate_content(full_prompt)
        reply = response.text
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred with the AI Assistant.")