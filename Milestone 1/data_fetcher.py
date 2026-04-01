import requests
import pandas as pd
import time
from datetime import datetime
import os

# Constants
COINS = ['bitcoin', 'ethereum', 'solana', 'cardano', 'dogecoin', 'ripple', 'polkadot', 'chainlink', 'litecoin', 'stellar']
VS_CURRENCY = 'usd'
DAYS = '365'  # Fetch last year's data
INTERVAL = 'daily'

def fetch_crypto_data(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        'vs_currency': VS_CURRENCY,
        'days': DAYS,
        'interval': INTERVAL
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        prices = data.get('prices', [])
        
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['coin'] = coin_id
        return df
    except Exception as e:
        print(f"Error fetching data for {coin_id}: {e}")
        return None

def main():
    all_data = []
    print("Fetching data...")
    for coin in COINS:
        print(f"Fetching {coin}...")
        df = fetch_crypto_data(coin)
        if df is not None:
            all_data.append(df)
        time.sleep(10)  # Increase delay to avoid 429 errors
    
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        # Ensure the path is correct relative to where user runs dashboard
        final_df.to_csv('milestone 1/crypto_data.csv', index=False)
        print("\nData saved to milestone 1/crypto_data.csv")
        print("Unique coins fetched:", final_df['coin'].unique())
    else:
        print("No data fetched.")

if __name__ == "__main__":
    main()
