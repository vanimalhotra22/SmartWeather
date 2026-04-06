# 🌱 Smart Agro

**Smart Agro** is an all-in-one, AI-powered agricultural solution designed to empower farmers with data-driven insights. It provides intelligent crop recommendations, instant plant disease detection, and yield predictions to optimize farming practices and protect crops.

## ✨ Key Features

* **Intelligent Crop Recommendation:** Suggests the best crops to plant based on unique soil parameters, weather, and climate conditions using machine learning.
* **AI-Powered Disease Detection:** Users can upload a leaf image to instantly identify potential diseases and get actionable advice to protect their yield.
* **Crop Yield Prediction:** Estimates future crop yields based on historical data and environmental factors.
* **Multilingual Support:** Fully accessible in English and Hindi to ensure ease of use for regional farmers.
* **Agri-Chatbot:** An integrated virtual assistant to answer farming-related queries in real-time.

## 🛠️ Tech Stack

* **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
* **Backend:** Python
* **Machine Learning:** Custom-trained models for crop recommendation and image-based disease detection (`crop_data.csv`)
* **Localization:** JSON-based translation system (`en.json`, `hi.json`)

## 📂 Project Structure

```text
├── backend/
│   ├── models/                  # Saved ML models (.pkl, .h5, etc.)
│   ├── uploads/                 # Directory for user-uploaded leaf images
│   ├── main.py                  # Main backend application script
│   ├── train_model.py           # Script for training the crop recommendation model
│   ├── train_yield_model.py     # Script for training the yield prediction model
│   └── requirements.txt         # Python dependencies
├── frontend/
│   ├── assets/                  # CSS, JavaScript, and Localization files
│   ├── index.html               # Landing page
│   ├── input.html               # Form for crop recommendation parameters
│   ├── disease.html             # Disease detection image upload interface
│   ├── result.html              # Results display page
│   └── chatbot.html             # Integrated Agri-Chatbot interface
├── .env                         # Environment variables (API keys, config)
└── README.md