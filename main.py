from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import joblib
import pandas as pd
import requests
from datetime import datetime, timedelta
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Model
MODEL_PATH = "models/aqi_model.pkl"
try:
    model = joblib.load(MODEL_PATH)
except:
    model = None

@app.get("/")
def read_index():
    return FileResponse("index.html")
    
@app.get("/styles.css")
def read_css():
    return FileResponse("styles.css")
    
@app.get("/script.js")
def read_js():
    return FileResponse("script.js")

@app.get("/api/forecast")
def get_forecast(lat: float, lon: float):
    if not model:
        return {"error": "Model not loaded. Please run model_pipeline.py first."}
        
    # Fetch recent past 2 days to get enough lag data
    url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&hourly=us_aqi,pm10,pm2_5,nitrogen_dioxide&past_days=2&forecast_days=2"
    response = requests.get(url)
    if response.status_code != 200:
        return {"error": "Could not fetch data"}
    data = response.json()
    
    now = datetime.utcnow()
    times = pd.to_datetime(data["hourly"]["time"])
    
    df = pd.DataFrame({
        "time": times,
        "us_aqi": data["hourly"]["us_aqi"],
        "pm10": data["hourly"]["pm10"],
        "pm2_5": data["hourly"]["pm2_5"],
        "no2": data["hourly"]["nitrogen_dioxide"],
    })
    
    df["us_aqi"] = df["us_aqi"].ffill().bfill()
    
    # Find current time index
    past_df = df[df["time"] <= now]
    if past_df.empty:
      current_idx = 0
    else:
      current_idx = past_df.index[-1]

    current_data = {
        "us_aqi": float(df.loc[current_idx, "us_aqi"]),
        "pm10": float(df.loc[current_idx, "pm10"]),
        "pm2_5": float(df.loc[current_idx, "pm2_5"]),
        "no2": float(df.loc[current_idx, "no2"]),
    }
    
    predictions = []
    
    for i in range(1, 25):
        target_idx = current_idx + i
        if target_idx >= len(df):
            break
            
        target_time = df.loc[target_idx, "time"]
        hour = target_time.hour
        dayofweek = target_time.dayofweek
        
        lag_24 = df.loc[target_idx - 24, "us_aqi"] if (target_idx - 24) >= 0 else df["us_aqi"].mean()
        
        start_roll = max(0, target_idx - 24)
        roll_24 = df.loc[start_roll:target_idx-1, "us_aqi"].mean()
        
        X_pred = pd.DataFrame([{
            "lat": lat,
            "lon": lon,
            "hour": hour,
            "dayofweek": dayofweek,
            "aqi_lag_24": lag_24,
            "aqi_roll_24": roll_24
        }])
        
        pred_val = float(model.predict(X_pred)[0])
        predictions.append({
            "time": target_time.isoformat(),
            "predicted_aqi": round(pred_val)
        })
        
    return {
        "current": current_data,
        "forecast": predictions
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8080, log_level="info")
