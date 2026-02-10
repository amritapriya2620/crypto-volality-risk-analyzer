from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
import requests
from typing import Optional, List, Dict, Any

app = FastAPI()

class MarketDataRequest(BaseModel):
    coin_id: str
    days: str

class MarketDataResponse(BaseModel):
    prices: List[float]
    current_price: float
    volatility: float
    max_drawdown: float
    risk_level: str
    risk_color: str
    daily_returns: List[float]
    timestamps: List[int]

def get_risk_level(vol):
    if vol > 100: return "#ff2b2b", "EXTREME ☢️"
    elif vol > 60: return "#ff9f1c", "HIGH 🔥"
    elif vol > 30: return "#fbd400", "MODERATE ⚖️"
    else: return "#2ec4b6", "LOW 🛡️"

def fetch_and_analyze_data(coin_id: str, days: str):
    """
    Core logic extracted for reusability.
    Returns a dictionary matching the MarketDataResponse structure.
    """
    try:
        # Fetch data
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": days}
        response = requests.get(url, params=params)
        data = response.json()
        
        if "prices" not in data:
            return None # Or raise specific error to be handled
            
        prices = data["prices"]
        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("date", inplace=True)
        
        # Calculate Metrics
        df['daily_return'] = df['price'].pct_change() * 100
        current_price = df['price'].iloc[-1]
        
        # Annualized volatility
        if len(df) < 2:
             vol = 0
             max_drawdown = 0
        else:
            vol = df['daily_return'].std() * np.sqrt(365)
            # Max Drawdown
            max_drawdown = ((df['price'] - df['price'].cummax()) / df['price'].cummax() * 100).min()

        if np.isnan(vol): vol = 0
        if np.isnan(max_drawdown): max_drawdown = 0
            
        risk_color, risk_level = get_risk_level(vol)
        
        return {
            "prices": df['price'].tolist(),
            "current_price": float(current_price),
            "volatility": float(vol),
            "max_drawdown": float(max_drawdown),
            "risk_level": risk_level,
            "risk_color": risk_color,
            "daily_returns": df['daily_return'].fillna(0).tolist(),
            "timestamps": df.index.astype('int64').tolist() # nanoseconds
        }
    except Exception as e:
        print(f"Error in calculation: {e}")
        raise e

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Crypto Risk Commander Backend is running"}

@app.post("/analyze", response_model=MarketDataResponse)
def analyze_market(request: MarketDataRequest):
    try:
        result = fetch_and_analyze_data(request.coin_id, request.days)
        if result is None:
             raise HTTPException(status_code=404, detail="Coin data not found")
        return result
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
