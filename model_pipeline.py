import pandas as pd
import requests
import joblib
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

CITIES = [
    {"name": "New York", "lat": 40.7128, "lon": -74.0060},
    {"name": "London", "lat": 51.5074, "lon": -0.1278},
    {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503},
    {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
    {"name": "Beijing", "lat": 39.9042, "lon": 116.4074},
    {"name": "Sydney", "lat": -33.8688, "lon": 151.2093}
]

def fetch_historical_data(city, past_days=90):
    url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={city['lat']}&longitude={city['lon']}&hourly=us_aqi&past_days={past_days}&forecast_days=0"
    response = requests.get(url)
    if response.status_code != 200:
        return pd.DataFrame()
    data = response.json()
    
    df = pd.DataFrame({
        "time": pd.to_datetime(data["hourly"]["time"]),
        "us_aqi": data["hourly"]["us_aqi"]
    })
    df["lat"] = city["lat"]
    df["lon"] = city["lon"]
    return df

def prepare_features(df):
    df = df.sort_values("time")
    df["hour"] = df["time"].dt.hour
    df["dayofweek"] = df["time"].dt.dayofweek
    df["aqi_lag_24"] = df["us_aqi"].shift(24)
    df["aqi_roll_24"] = df["us_aqi"].rolling(window=24).mean()
    df = df.dropna()
    return df

def train_and_save_model():
    print("Fetching historical data for training...")
    all_dfs = []
    for city in CITIES:
        print(f"Fetching {city['name']}...")
        df = fetch_historical_data(city)
        if not df.empty:
            df = prepare_features(df)
            all_dfs.append(df)
            
    if not all_dfs:
        print("No data fetched. Aborting.")
        return
        
    full_df = pd.concat(all_dfs, ignore_index=True)
    
    X = full_df[["lat", "lon", "hour", "dayofweek", "aqi_lag_24", "aqi_roll_24"]]
    y = full_df["us_aqi"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training RandomForestRegressor model...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    preds = model.predict(X_test)
    mse = mean_squared_error(y_test, preds)
    print(f"Model MSE on test set: {mse:.2f}")
    
    os.makedirs("models", exist_ok=True)
    joblib.dump(model, "models/aqi_model.pkl")
    print("Model saved to models/aqi_model.pkl")

if __name__ == "__main__":
    train_and_save_model()
