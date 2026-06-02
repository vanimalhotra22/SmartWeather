
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

# Import SQLite database helpers
from database import (
    db_init,
    db_save_user,
    db_save_crop_recommendation,
    db_get_crop_history,
    db_save_disease_detection,
    db_get_disease_history,
    db_save_chat,
    db_get_chat_history,
    db_get_stats
)

# --- Configuration & Setup ---
load_dotenv(override=True)
app = FastAPI(title="SmartAgro API")
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    try:
        db_init()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")

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
    google_id: str = None

class ChatMessage(BaseModel):
    message: str
    language: str = 'en'
    google_id: str = None

class AuthToken(BaseModel):
    token: str

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the SmartAgro API"}

@app.post("/api/auth/google")
async def auth_google(payload: AuthToken):
    token = payload.token
    try:
        # Verify token with Google's tokeninfo API
        res = requests.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={token}")
        if res.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid Google token")
        
        user_info = res.json()
        
        # Verify audience matches client ID
        aud = user_info.get("aud")
        expected_client_id = "822402579088-cr2ea0olrf87stpqe9r7dg6qonqsja6r.apps.googleusercontent.com"
        if aud != expected_client_id:
            raise HTTPException(status_code=400, detail="Token audience mismatch")
            
        google_id = user_info.get("sub")
        email = user_info.get("email")
        name = user_info.get("name")
        picture = user_info.get("picture")
        
        db_save_user(google_id, email, name, picture)
        
        return {
            "google_id": google_id,
            "email": email,
            "name": name,
            "picture": picture
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

        # Log history if user is authenticated
        if data.google_id:
            try:
                db_save_crop_recommendation(
                    data.google_id,
                    data.temperature_c, data.soil_ph, data.soil_moisture_percent,
                    data.rainfall_mm, data.humidity_percent, data.sunlight_hours,
                    data.irrigation_type, data.fertilizer_type, data.pesticide_usage_ml, data.total_days,
                    recommended_crop, float(confidence), float(predicted_yield), sowing_date, harvest_date
                )
            except Exception as db_err:
                print(f"Database save error: {db_err}")

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
async def detect_disease(google_id: str = None, language: str = 'en', file: UploadFile = File(...)):
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="Gemini API key not configured.")
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        image_bytes = await file.read()
        pil_image = Image.open(io.BytesIO(image_bytes))
        prompt = "Analyze this image of a plant leaf. Identify the specific disease if one is present, or state if the plant appears healthy. Provide only the name of the disease or 'Healthy'."
        response = model.generate_content([prompt, pil_image])
        prediction = response.text.strip()
        
        # Clean prediction text
        prediction = prediction.replace("**", "").replace("*", "").replace("`", "").strip()
        
        # Gather detailed description & prevention advice directly using Gemini
        description = ""
        prevention = ""
        if prediction.lower() == 'healthy':
            if language == 'hi':
                prediction = "स्वस्थ (Healthy)"
                description = "पत्ता स्वस्थ लग रहा है। सामान्य बीमारियों के कोई लक्षण नहीं मिले।"
                prevention = "पौधे के स्वास्थ्य को बनाए रखने के लिए, उचित सिंचाई, पर्याप्त धूप और पोषक तत्वों से भरपूर मिट्टी सुनिश्चित करें।"
            else:
                description = "The leaf appears to be healthy. No signs of common diseases were detected."
                prevention = "To maintain plant health, ensure proper watering, adequate sunlight, and nutrient-rich soil."
        else:
            if language == 'hi':
                detail_prompt = f"In 50 words, what is {prediction} disease in plants and what is one prevention tip? Structure the response EXACTLY as: 'Description: [description in Hindi] Prevention: [prevention in Hindi]'. Do not use English language words in the description or prevention unless necessary."
            else:
                detail_prompt = f"In 50 words, what is {prediction} disease in plants and what is one prevention tip? Structure the response EXACTLY as: 'Description: ... Prevention: ...'"
                
            detail_response = model.generate_content(detail_prompt)
            detail_text = detail_response.text.strip()
            
            import re
            desc_match = re.search(r"Description:(.*?)(Prevention:|$)", detail_text, re.DOTALL | re.IGNORECASE)
            prev_match = re.search(r"Prevention:(.*)", detail_text, re.DOTALL | re.IGNORECASE)
            
            if not desc_match:
                desc_match = re.search(r"विवरण:(.*?)(निवारण:|उपाय:|$)", detail_text, re.DOTALL)
            if not prev_match:
                prev_match = re.search(r"(निवारण:|उपाय:)(.*)", detail_text, re.DOTALL)
                
            description = desc_match.group(1).strip() if desc_match else detail_text
            prevention = prev_match.group(1).strip() if prev_match else ("कृषि विशेषज्ञों से बचाव के उपाय देखें।" if language == 'hi' else "Check trusted agricultural sources for prevention tips.")
        
        # Log history if user is authenticated
        if google_id:
            try:
                db_save_disease_detection(google_id, file.filename, prediction, description, prevention)
            except Exception as db_err:
                print(f"Database save error: {db_err}")

        return {
            "prediction": prediction,
            "description": description,
            "prevention": prevention
        }
    except Exception as e:
        print(f"Error in detect_disease: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while analyzing the image.")

@app.post("/api/chat")
async def chat(message: ChatMessage):
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="Gemini API key not configured.")
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        language_map = {'en': 'English', 'hi': 'Hindi'}
        lang_name = language_map.get(message.language, 'English')
        system_prompt = f"You are SmartAgro Assistant, an expert in agriculture. Provide a clear and helpful answer in the {lang_name} language."
        full_prompt = f"{system_prompt}\n\nUser Question: {message.message}"
        response = model.generate_content(full_prompt)
        reply = response.text
        
        # Log history if user is authenticated
        if message.google_id:
            try:
                db_save_chat(message.google_id, message.message, reply, message.language)
            except Exception as db_err:
                print(f"Database save error: {db_err}")

        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred with the AI Assistant.")

# --- History and Stats Endpoints ---

@app.get("/api/history/crop")
async def get_crop_history(google_id: str):
    return db_get_crop_history(google_id)

@app.get("/api/history/disease")
async def get_disease_history(google_id: str):
    return db_get_disease_history(google_id)

@app.get("/api/history/chat")
async def get_chat_history(google_id: str):
    return db_get_chat_history(google_id)

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(google_id: str):
    return db_get_stats(google_id)

@app.get("/api/market-prices")
async def get_market_prices():
    import random
    
    crops = {
        "Rice": {"base": 2200, "volatility": 15},
        "Wheat": {"base": 2300, "volatility": 12},
        "Cotton": {"base": 7100, "volatility": 40},
        "Soybean": {"base": 4600, "volatility": 25},
        "Maize": {"base": 2100, "volatility": 10}
    }
    
    # Generate prices using today's day of month as a stable seed
    stable_seed = datetime.now().day
    
    market_data = []
    for crop, cfg in crops.items():
        base = cfg["base"]
        vol = cfg["volatility"]
        
        # Seed generator based on crop name and day
        seed = sum(ord(c) for c in crop) + stable_seed
        random.seed(seed)
        
        prices_7d = []
        curr = base
        for _ in range(7):
            curr += random.randint(-vol, vol)
            prices_7d.append(curr)
        
        current_price = prices_7d[-1]
        previous_price = prices_7d[-2]
        change = round(((current_price - previous_price) / previous_price) * 100, 2)
        trend = "up" if change >= 0 else "down"
        
        market_data.append({
            "crop": crop,
            "current_price": current_price,
            "change_percent": change,
            "trend": trend,
            "weekly_prices": prices_7d
        })
        
    return market_data