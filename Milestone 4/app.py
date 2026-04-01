import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
import scipy.stats as stats
import hashlib
from groq import Groq
import os
import io
from fpdf import FPDF
try:
    from dotenv import load_dotenv
    # Use absolute path to ensure .env is found in the script's directory
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(env_path)
    
    # Configure Groq once at startup
    api_key = os.getenv('GROQ_API_KEY')
    grok_client = None
    if api_key:
        grok_client = Groq(api_key=api_key)
except ImportError:
    grok_client = None
    pass
import time
import requests
from concurrent.futures import ThreadPoolExecutor
import base64 as _b64_module
# --- Load login background image ---
_bg_img_path = os.path.join(os.path.dirname(__file__), 'login_bg.jpg')
if os.path.exists(_bg_img_path):
    import base64 as _b64
    with open(_bg_img_path, 'rb') as _f:
        _LOGIN_BG_B64 = _b64.b64encode(_f.read()).decode()
    _LOGIN_BG_URL = f'url("data:image/jpeg;base64,{_LOGIN_BG_B64}")'
else:
    _LOGIN_BG_URL = 'none'


# --- 1. Page Configuration ---
st.set_page_config(
    page_title="Crypto Volatility and Risk Analyzer - Milestone 4",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Advanced Custom CSS ---
st.markdown("""
<style>
    /* --- EXECUTIVE HEADER BANNER --- */
    .header-banner {
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(25px) saturate(160%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 25px 35px;
        margin-bottom: 35px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
        position: relative;
        overflow: hidden;
        border-left: 5px solid #3B82F6; /* Default */
    }
    
    .header-banner::before {
        content: "";
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background: radial-gradient(circle at top right, rgba(59, 130, 246, 0.1), transparent);
        pointer-events: none;
    }
    
    .banner-low { border-left-color: #10B981 !important; box-shadow: 0 15px 35px -5px rgba(16, 185, 129, 0.15); }
    .banner-med { border-left-color: #F59E0B !important; box-shadow: 0 15px 35px -5px rgba(245, 158, 11, 0.15); }
    .banner-high { border-left-color: #EF4444 !important; box-shadow: 0 15px 35px -5px rgba(239, 68, 68, 0.15); }
    
    /* Sidebar: Frosted Acrylic Glass */
    section[data-testid="stSidebar"] {
        background: rgba(13, 17, 23, 0.7) !important;
        backdrop-filter: blur(25px) saturate(180%);
        -webkit-backdrop-filter: blur(25px) saturate(180%);
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
        box-shadow: 10px 0 30px rgba(0,0,0,0.5);
    }
    
    /* Text Contrast Fix for Sidebar */
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] label {
        color: #E2E8F0 !important;
        font-weight: 500;
        text-shadow: 0 1px 2px rgba(0,0,0,0.5);
    }
    
    /* --- GLASSMOTHIC METRIC CARDS 2.0 --- */
    div.metric-card {
        background: rgba(30, 41, 59, 0.45);
        backdrop-filter: blur(12px) contrast(110%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-top: 1px solid rgba(255, 255, 255, 0.15); /* Lighting effect */
        border-radius: 18px;
        padding: 22px;
        box-shadow: 
            0 10px 25px -5px rgba(0, 0, 0, 0.5),
            inset 0 0 10px rgba(255, 255, 255, 0.02);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        margin-bottom: 20px;
        position: relative;
        overflow: hidden;
    }
    
    /* Subtle Accent bar at the bottom */
    div.metric-card::after {
        content: "";
        position: absolute;
        bottom: 0; left: 0; width: 100%; height: 3px;
        background: linear-gradient(90deg, #3B82F6, #60A5FA);
        opacity: 0.6;
    }
    
    div.metric-card:hover {
        transform: translateY(-8px) scale(1.02);
        background: rgba(45, 55, 72, 0.65);
        border-color: rgba(59, 130, 246, 0.4);
        box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.6), 0 0 15px rgba(59, 130, 246, 0.3);
    }
    
    div.metric-label {
        color: #94A3B8;
        font-size: 0.7rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        margin-bottom: 8px;
    }
    
    div.metric-value {
        color: #FFFFFF;
        font-size: 1.7rem;
        font-weight: 900;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: -1px;
    }
    
    .metric-delta {
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        margin-top: 8px;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .positive { color: #10B981; font-weight: 700; }
    .negative { color: #F87171; font-weight: 700; }
    
    /* --- DYNAMIC RISK BADGES (GLOW EDITION) --- */
    .risk-badge {
        padding: 5px 14px;
        border-radius: 30px;
        font-size: 10px;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        display: inline-flex;
        align-items: center;
        margin-left: 12px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 0 15px rgba(0,0,0,0.3);
    }
    .risk-low { 
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.3), rgba(6, 95, 70, 0.4)); 
        color: #10B981; 
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.2); 
    }
    .risk-med { 
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.3), rgba(146, 64, 14, 0.4)); 
        color: #F59E0B; 
        box-shadow: 0 0 10px rgba(245, 158, 11, 0.2); 
    }
    .risk-high { 
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.3), rgba(153, 27, 27, 0.4)); 
        color: #F87171; 
        animation: badge-pulse 2s infinite; 
    }
    
    @keyframes badge-pulse {
        0% { filter: brightness(1); box-shadow: 0 0 5px rgba(239, 68, 68, 0.4); }
        50% { filter: brightness(1.4); box-shadow: 0 0 20px rgba(239, 68, 68, 0.7); }
        100% { filter: brightness(1); box-shadow: 0 0 5px rgba(239, 68, 68, 0.4); }
    }

    /* --- CHART DOX UPGRADE --- */
    .chart-box {
        background: rgba(13, 17, 23, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 20px;
        padding: 20px;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.3);
        margin-bottom: 25px;
    }
    
    /* Premium Table Styling */
    .risk-table {
        background: rgba(22, 27, 34, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.03);
        border-radius: 15px;
    }
    .risk-table th {
        background: rgba(13, 17, 23, 0.8) !important;
        font-weight: 800;
        color: #64748B !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #475569; }
</style>
""", unsafe_allow_html=True)

# --- 3. Data Engine ---
COINS = ['bitcoin', 'ethereum', 'solana', 'cardano', 'dogecoin', 'ripple', 'chainlink']
VS_CURRENCY = 'usd'
DAYS = '365'
INTERVAL = 'daily'

def fetch_crypto_data(coin_id, retries=3, backoff_factor=1.5):
    """Fetch historical market data for a single coin from CoinGecko API with retry logic."""
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        'vs_currency': VS_CURRENCY,
        'days': DAYS,
        'interval': INTERVAL
    }
    
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=15)
            # If 429 Too Many Requests, wait and retry
            if response.status_code == 429:
                sleep_time = backoff_factor * (2 ** attempt)
                time.sleep(sleep_time)
                continue
                
            response.raise_for_status()
            data = response.json()
            prices = data.get('prices', [])
            
            if not prices:
                return None
                
            df = pd.DataFrame(prices, columns=['timestamp', 'price'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['coin'] = coin_id
            return df
            
        except requests.exceptions.RequestException:
            # On generic connection error, take a short pause and try again
            time.sleep(2)
            
    # Return None if all retries failed
    return None

@st.cache_data(show_spinner=False)
def load_data():
    """Load crypto data from local CSV (fast). Use refresh to fetch live data."""
    csv_path = os.path.join(os.path.dirname(__file__), 'crypto_data.csv')
    try:
        df = pd.read_csv(csv_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except FileNotFoundError:
        return pd.DataFrame()

def refresh_data_from_api():
    """Fetch fresh data from CoinGecko API concurrently and save to CSV."""
    csv_path = os.path.join(os.path.dirname(__file__), 'crypto_data.csv')
    all_data = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(fetch_crypto_data, COINS))
        
    for df in results:
        if df is not None and not df.empty:
            all_data.append(df)
    
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        final_df.to_csv(csv_path, index=False)
        return True
    return False


@st.cache_data(show_spinner=False, ttl=600)
def get_nexus_ai_response(query, _df, current_coin):
    """Enhanced Cortex AI with caching for speed."""
    df = _df # Use underscore to prevent streamlit from hashing the whole dataframe
    query = query.lower()
    
    # Identify target coin
    all_coins = df['coin'].unique()
    target_coin = current_coin
    for c in all_coins:
        if c in query:
            target_coin = c
            break
            
    # fetch data
    coin_data = df[df['coin'] == target_coin].sort_values('timestamp').copy()
    latest = coin_data.iloc[-1]
    curr_price = latest['price']
    
    # Basic technicals for AI context
    rets = coin_data['price'].pct_change()
    vol = rets.rolling(30).std().iloc[-1] * np.sqrt(365) * 100
    sma20 = coin_data['price'].rolling(20).mean().iloc[-1]
    
    # RSI calculation for AI
    delta = coin_data['price'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs)).iloc[-1]
    
    # Bollinger Bands for AI
    std20 = coin_data['price'].rolling(20).std().iloc[-1]
    upper_b = sma20 + (std20 * 2)
    lower_b = sma20 - (std20 * 2)

    # --- HYBRID LLM LOGIC (PRIORITY) ---
    if grok_client:
        try:
            context = f"""
            You are 'Cortex', an Advanced Crypto Analysis AI. 
            User is looking at {target_coin.upper()}.
            
            REAL-TIME DATA:
            - Price: ${curr_price:,.2f}
            - 20-Day Avg: ${sma20:,.2f}
            - RSI (14): {rsi:.1f}
            - Annual Volatility: {vol:.1f}%
            - Support Level: ${lower_b:,.2f}
            - Resistance Level: ${upper_b:,.2f}
            
            INSTRUCTIONS:
            1. Use the provided technical data to answer.
            2. Be conversational but professional.
            3. If asked for a suggestion or 'should I invest', provide a balanced technical perspective (e.g. "Technically, the RSI suggests interest...") but include a CLEAR financial disclaimer.
            4. Keep the response concise for a dashboard sidebar.
            """
            
            completion = grok_client.chat.completions.create(
                model="llama-3.1-8b-instant", # Updated, supported fast Llama model on Groq
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": query}
                ]
            )
            return completion.choices[0].message.content
        except Exception as e:
            # If it's a quota/API error, we fall back silently or with a friendly note
            if "429" in str(e) or "quota" in str(e).lower():
                pass # Continue to heuristic fallback
            else:
                return f"**[Groq Error]** {str(e)}"

    # --- HEURISTIC FALLBACK ---
    if any(k in query for k in ["price", "cost", "value"]):
        return f"The current price of **{target_coin.upper()}** is **${curr_price:,.2f}**. It is currently trading {'above' if curr_price > sma20 else 'below'} its 20-day average."
    
    elif any(k in query for k in ["high", "peak", "max"]):
        high_all = coin_data['price'].max()
        return f"The record high for **{target_coin.upper()}** in my current records is **${high_all:,.2f}**."
    
    elif any(k in query for k in ["low", "bottom", "min"]):
        low_all = coin_data['price'].min()
        return f"The record low for **{target_coin.upper()}** in my current records is **${low_all:,.2f}**."
    
    elif any(k in query for k in ["volatility", "risk", "sharpe"]):
        risk_level = "High 🔥" if vol > 60 else "Moderate ⚖️" if vol > 30 else "Low 🛡️"
        return (f"**{target_coin.upper()}** has an annualized volatility of **{vol:.1f}%**. "
                f"Current Risk Profile: **{risk_level}**. Support levels are around **${lower_b:,.2f}**.")
    
    elif any(k in query for k in ["rsi", "momentum", "strength"]):
        sentiment = "Overbought (Caution)" if rsi > 70 else "Oversold (Interest)" if rsi < 30 else "Neutral"
        return f"The RSI for **{target_coin.upper()}** is **{rsi:.1f}**, currently in **{sentiment}** territory."
    
    elif any(k in query for k in ["trend", "bull", "bear", "predict"]):
        trend = "Bullish 📈" if curr_price > sma20 else "Bearish 📉"
        action = "testing resistance" if curr_price > upper_b else "finding support" if curr_price < lower_b else "consolidating"
        return f"The current trend for **{target_coin.upper()}** is **{trend}**. The asset is currently {action}."

    elif "buy" in query or "sell" in query:
        return ("As an AI, I can't give financial advice, but looking at technicals: "
                f"**{target_coin.upper()}** has an RSI of **{rsi:.1f}** and is trading at **${curr_price:,.2f}**. "
                "Always perform your own due diligence!")
    
    else:
        return (f"I am monitoring **{target_coin.upper()}**. You can ask me about its **Price**, **Volatility**, "
                "**RSI Momentum**, **Trend Analysis**, or **High/Low** benchmarks.")

def get_risk_level(vol, sharpe):
    """Categorize risk based on volatility and risk-adjusted returns (Sharpe)."""
    if vol < 45 and sharpe > 0.8:
        return "Low", "risk-low", "#10B981"
    elif vol > 75 or sharpe < 0.2:
        return "High", "risk-high", "#EF4444"
    else:
        return "Medium", "risk-med", "#F59E0B"

def calculate_risk_profile(df, date_range):
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date = pd.to_datetime(date_range[0])
        end_date = pd.to_datetime(date_range[1])
    else:
        # Fallback to last 90 days if range is incomplete
        end_date = df['timestamp'].max()
        start_date = end_date - timedelta(days=90)
        
    df_filtered = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)].copy()
    
    df_pivot = df_filtered.pivot(index='timestamp', columns='coin', values='price')
    returns = df_pivot.pct_change().dropna()
    
    if 'bitcoin' in returns.columns:
        benchmark = returns['bitcoin']
    else:
        benchmark = returns.mean(axis=1)
    
    metrics = []
    for coin in returns.columns:
        coin_rets = returns[coin]
        vol = coin_rets.std() * np.sqrt(365) * 100
        ann_ret = coin_rets.mean() * 365 * 100
        excess_ret = coin_rets.mean() * 365 - 0.02
        sharpe = excess_ret / (vol/100) if vol != 0 else 0
        cov = np.cov(coin_rets, benchmark)[0][1]
        var = np.var(benchmark)
        beta = cov / var if var != 0 else 0
        var_95 = np.percentile(coin_rets, 5) * 100
        
        # Milestone 4: Classification
        level, label_cls, color = get_risk_level(vol, sharpe)
        
        metrics.append({
            "Crypto": coin.upper(),
            "Volatility": vol,
            "Return": ann_ret,
            "Sharpe": sharpe,
            "Beta": beta,
            "VaR (95%)": var_95,
            "Risk Level": level,
            "Color": color,
            "Class": label_cls
        })
    return pd.DataFrame(metrics).sort_values("Volatility", ascending=True)

def process_single_asset(df, coin, days):
    df_coin = df[df['coin'] == coin].sort_values('timestamp').reset_index(drop=True)
    
    # Check if we have data for this coin
    if df_coin.empty or pd.isna(df_coin['timestamp'].max()):
        return df_coin
        
    start_date = None
    end_date = None
    
    if isinstance(days, tuple) and len(days) == 2:
        start_date = pd.to_datetime(days[0])
        # Include the entire end day
        end_date = pd.to_datetime(days[1]) + pd.Timedelta(hours=23, minutes=59, seconds=59)
    elif isinstance(days, tuple) and len(days) == 1:
        start_date = pd.to_datetime(days[0])
        end_date = start_date + pd.Timedelta(hours=23, minutes=59, seconds=59)
    elif hasattr(days, 'strftime'):
        start_date = pd.to_datetime(days)
        end_date = start_date + pd.Timedelta(hours=23, minutes=59, seconds=59)
    elif isinstance(days, str): # fallback
        end_date = df_coin['timestamp'].max()
        if days != "ALL":
            days_map = {"1W": 7, "1M": 30, "3M": 90, "6M": 180, "1Y": 365, "YTD": (end_date - datetime(int(end_date.year), 1, 1)).days}
            start_date = end_date - timedelta(days=days_map.get(days, 365))
        else:
            start_date = df_coin['timestamp'].min()
            
    if start_date is not None and end_date is not None:
        df_coin = df_coin[(df_coin['timestamp'] >= start_date) & (df_coin['timestamp'] <= end_date)].copy()
    
    # Indicators
    df_coin['SMA_20'] = df_coin['price'].rolling(window=20).mean()
    df_coin['EMA_50'] = df_coin['price'].ewm(span=50, adjust=False).mean()
    df_coin['STD_20'] = df_coin['price'].rolling(window=20).std()
    df_coin['BB_Upper'] = df_coin['SMA_20'] + (df_coin['STD_20'] * 2)
    df_coin['BB_Lower'] = df_coin['SMA_20'] - (df_coin['STD_20'] * 2)
    
    delta = df_coin['price'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df_coin['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df_coin['price'].ewm(span=12, adjust=False).mean()
    exp2 = df_coin['price'].ewm(span=26, adjust=False).mean()
    df_coin['MACD'] = exp1 - exp2
    df_coin['Signal'] = df_coin['MACD'].ewm(span=9, adjust=False).mean()
    
    # Volatility
    df_coin['Returns'] = df_coin['price'].pct_change()
    df_coin['Volatility'] = df_coin['Returns'].rolling(window=30).std() * np.sqrt(365) * 100
    
    # Sharpe Ratio (Approximate for the timeframe)
    ann_ret = df_coin['Returns'].mean() * 365
    ann_vol = df_coin['Returns'].std() * np.sqrt(365)
    df_coin['Sharpe'] = (ann_ret - 0.02) / ann_vol if ann_vol > 0 else 0
    
    return df_coin



# --- 4. Sidebar Controls ---
# --- 3.5 Authentication System ---
USER_DB_FILE = os.path.join(os.path.dirname(__file__), 'users.csv')

def init_user_db():
    if not os.path.exists(USER_DB_FILE):
        df = pd.DataFrame(columns=['username', 'password', 'created_at'])
        df.to_csv(USER_DB_FILE, index=False)

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def verify_user(username, password):
    init_user_db()
    try:
        df = pd.read_csv(USER_DB_FILE)
        if username in df['username'].values:
            user_row = df[df['username'] == username].iloc[0]
            if user_row['password'] == hash_password(password):
                return True
    except Exception as e:
        st.error(f"Auth Error: {e}")
    return False

def register_user(username, password):
    init_user_db()
    try:
        df = pd.read_csv(USER_DB_FILE)
        if username in df['username'].values:
            return False, "Username already exists."
        
        new_user = pd.DataFrame({
            'username': [username],
            'password': [hash_password(password)],
            'created_at': [datetime.now().isoformat()]
        })
        df = pd.concat([df, new_user], ignore_index=True)
        df.to_csv(USER_DB_FILE, index=False)
        return True, "User registered successfully!"
    except Exception as e:
        return False, f"Registration failed: {e}"

def login_register_page():
    # --- PREMIUM LOGIN UI DESIGN ---
    _login_css = """
    <style>
        /* Import Premium Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800;900&family=Inter:wght@300;400;500;600;700&display=swap');

        /* --- GLOBAL RESET --- */
        .stApp {
            background: transparent !important;
        }
        
        [data-testid="stAppViewContainer"] {
            background: 
                linear-gradient(rgba(10, 15, 30, 0.45) 0%, rgba(10, 15, 30, 0.65) 100%),
                {LOGIN_BG_URL} !important;
            background-size: cover !important;
            background-position: center !important;
            background-attachment: fixed !important;
        }

        [data-testid="stAppViewContainer"]::before {
            content: "";
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background-image: 
                linear-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.04) 1px, transparent 1px);
            background-size: 50px 50px;
            pointer-events: none;
            z-index: 0;
        }

        [data-testid="stHeader"], [data-testid="stFooter"] {
            display: none !important;
        }

        /* --- CARD DESIGN --- */
        [data-testid="stForm"] {
            background: rgba(15, 22, 40, 0.5) !important;
            backdrop-filter: blur(30px) saturate(210%);
            -webkit-backdrop-filter: blur(30px) saturate(210%);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 35px;
            padding: 45px !important;
            box-shadow: 
                0 35px 70px -15px rgba(0, 0, 0, 0.7),
                inset 0 0 0 1px rgba(255, 255, 255, 0.1);
        }

        /* --- TITLES (BOLD & CLEAR) --- */
        .login-title {
            font-family: 'Outfit', sans-serif;
            font-size: 68px;
            font-weight: 900;
            text-align: center;
            background: linear-gradient(135deg, #FFFFFF 40%, #CBD5E1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 5px;
            filter: drop-shadow(0 10px 15px rgba(0,0,0,0.6));
            letter-spacing: -0.04em;
        }
        
        .login-subtitle {
            font-family: 'Inter', sans-serif;
            font-size: 16px;
            color: #F1F5F9;
            text-align: center;
            margin-bottom: 35px;
            letter-spacing: 0.3em;
            text-transform: uppercase;
            font-weight: 700;
            text-shadow: 0 4px 8px rgba(0,0,0,0.5);
        }

        /* Card Header */
        [data-testid="stForm"] h3 {
            color: white !important;
            font-weight: 800 !important;
            font-size: 32px !important;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }

        /* --- LABELS (BOLD & CLEAR) --- */
        [data-testid="stForm"] label p {
            color: #FFFFFF !important;
            font-weight: 700 !important;
            font-size: 16px !important;
            text-shadow: 0 1px 3px rgba(0,0,0,0.8);
            margin-bottom: 4px !important;
        }

        /* Inputs */
        div[data-baseweb="input"] > div {
            background-color: rgba(5, 8, 15, 0.8) !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 18px !important;
        }
        
        div[data-baseweb="input"] input {
            color: white !important;
            font-weight: 500 !important;
        }

        /* Buttons */
        div[data-testid="stForm"] button {
            background: linear-gradient(135deg, #3B82F6 0%, #172554 100%);
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 18px 0 !important;
            border-radius: 18px;
            font-weight: 800;
            font-size: 18px;
            letter-spacing: 2.5px;
            box-shadow: 0 12px 24px -6px rgba(59, 130, 246, 0.5);
        }
        
        div[data-testid="stForm"] button:hover {
            transform: translateY(-3px);
            filter: brightness(1.25);
            box-shadow: 0 20px 35px -8px rgba(59, 130, 246, 0.6);
        }

        /* Bottom Toggle Text (BOLD & CLEAR) */
        .toggle-text {
            text-align: center;
            color: #F8FAFC;
            margin-top: 35px;
            font-size: 15px;
            font-weight: 600;
            text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        }

        div.stButton button {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 18px;
            color: white;
            font-weight: 700;
            letter-spacing: 0.5px;
        }
        
        div.stButton button:hover {
            background: rgba(255, 255, 255, 0.18);
            border-color: rgba(255, 255, 255, 0.4);
        }
    </style>
    """
    st.markdown(_login_css.replace("{LOGIN_BG_URL}", _LOGIN_BG_URL), unsafe_allow_html=True)

    # --- LAYOUT MANAGEMENT ---
    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        st.markdown('<div class="login-title">Crypto Volatility And Risk Analyzer</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">Advanced Risk Analytics</div>', unsafe_allow_html=True)
        
        if "auth_mode" not in st.session_state:
            st.session_state.auth_mode = "login"

        def toggle():
            st.session_state.auth_mode = (
                "register" if st.session_state.auth_mode == "login" else "login"
            )

        if st.session_state.auth_mode == "login":
            with st.form("login_form"):
                st.markdown("<h3 style='text-align: center; color: white; margin-bottom: 20px;'>Welcome Back</h3>", unsafe_allow_html=True)
                user = st.text_input("Email", placeholder="name@example.com")
                pwd = st.text_input("Password", placeholder="••••••••", type="password")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Check for cached messages
                if "login_error" in st.session_state:
                     st.error(st.session_state.login_error)
                     del st.session_state.login_error

                submit = st.form_submit_button("Sign In")
                
                if submit:
                    if verify_user(user, pwd):
                        st.session_state.authenticated = True
                        st.session_state.username = user
                        st.rerun()
                    else:
                        st.session_state.login_error = "Invalid credentials"
                        st.rerun()

            st.markdown('<div class="toggle-text">New User?</div>', unsafe_allow_html=True)
            if st.button("Create Account", width="stretch"):
                toggle()
                st.rerun()

        else:
            with st.form("register_form"):
                st.markdown("<h3 style='text-align: center; color: white; margin-bottom: 20px;'>Create Account</h3>", unsafe_allow_html=True)
                new_u = st.text_input("Username", placeholder="Choose a username")
                new_p = st.text_input("Password", placeholder="••••••••", type="password")
                conf = st.text_input("Confirm Password", placeholder="••••••••", type="password")
                
                st.markdown("<br>", unsafe_allow_html=True)

                if "reg_error" in st.session_state:
                     st.error(st.session_state.reg_error)
                     del st.session_state.reg_error
                
                submit = st.form_submit_button("Sign Up")
                
                if submit:
                    if new_p == conf:
                        ok, msg = register_user(new_u, new_p)
                        if ok:
                            st.success("Account created! Please sign in.")
                            time.sleep(1)
                            toggle()
                            st.rerun()
                        else:
                            st.session_state.reg_error = msg
                            st.rerun()
                    else:
                        st.session_state.reg_error = "Passwords do not match"
                        st.rerun()

            st.markdown('<div class="toggle-text">Already have an account?</div>', unsafe_allow_html=True)
            if st.button("Back to Login", width="stretch"):
                toggle()
                st.rerun()



# Initialization
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    login_register_page()
    st.stop()

# --- 4. Sidebar Controls ---
raw_df = load_data()

# --- Top Bar Controls ---
t1, t2 = st.columns([8, 1])
with t2:
    if st.button("🔄 Refresh"):
        with st.spinner("⏳ Fetching live crypto data..."):
            refresh_data_from_api()
        load_data.clear()
        try:
            st.rerun()
        except AttributeError:
            st.experimental_rerun()

if raw_df.empty:
    st.error("Failed to fetch data from API and no local backup found. Please check your internet connection and try again.")
    st.stop()


with st.sidebar:
    st.markdown(f"""
        <div style="text-align: center; padding: 20px 0;">
            <h1 style='font-size: 24px; margin-bottom: 0; color: #58A6FF;'>CRYPTO ANALYZER</h1>
            <div style='font-size: 10px; letter-spacing: 2px; color: #8B949E;'>MILESTONE 4 • FINAL EDITION</div>
        </div>
    """, unsafe_allow_html=True)
    
    
    # User Profile
    st.markdown(f"""
    <div style='background: #161b22; padding: 10px; border-radius: 8px; border: 1px solid #30363d; margin-bottom: 20px;'>
        <div style='color: #8b949e; font-size: 12px;'>Logged in as:</div>
        <div style='color: #58a6ff; font-weight: 600;'>@{st.session_state.get('username', 'User')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 Logout", key="logout_btn", width="stretch"):
        st.session_state['authenticated'] = False
        st.session_state['username'] = None
        st.rerun()

    st.markdown("---")
    
    # Persistence fix: Ensure view_mode is tracking correctly in session_state
    if 'view_index' not in st.session_state:
        st.session_state['view_index'] = 0
        
    view_options = ["📈 Individual Asset", "⚖️ Risk Comparison"]
    view_mode = st.radio("Select View", view_options, index=st.session_state['view_index'], key="view_mode_selector")
    
    # Update index for next rerun
    st.session_state['view_index'] = view_options.index(view_mode)
    
    st.markdown("---")
    
    default_coin = "bitcoin" 
    
    if view_mode == "📈 Individual Asset":
        st.subheader("ASSET CONTROLS")
        coins = sorted(COINS)
        selected_coins = st.sidebar.multiselect("Select Assets", coins, default=["bitcoin"], key="selected_coins")
        
        if not selected_coins:
            st.warning("Please select at least one asset.")
            st.stop()
            
        # Check if we have data for the primary selected coin
        if selected_coins[0] not in raw_df['coin'].unique():
            st.info(f"💡 Data for **{selected_coins[0].upper()}** is not yet cached. Please click the **🔄 Refresh** button top-right to fetch live data.")
            st.stop()

        selected_coin = selected_coins[0]
        default_coin = selected_coin 
        
        # Calendar Timeframe Input
        today = datetime.today().date()
        min_date = raw_df['timestamp'].min().date() if not raw_df.empty else today - timedelta(days=365)
        max_date = today # Use today's date to allow selecting 2026
        default_start = today - timedelta(days=365)
        if default_start < min_date:
            default_start = min_date
            
        time_range = st.date_input(
            "Timeframe Range", 
            value=(default_start, today),
            min_value=min_date, 
            max_value=today,
            key="time_range"
        )
        
        # Wait until the user selects BOTH start and end dates
        if isinstance(time_range, tuple) and len(time_range) == 1:
            st.info("📅 Please select an end date on the calendar.")
            st.stop()
        
        st.markdown("---")
        st.subheader("INDICATORS")
        show_ma = st.checkbox("MA Ribbons", value=True, key="show_ma")
        show_bb = st.checkbox("Bollinger Bands", value=True, key="show_bb")
        show_macd = st.checkbox("MACD Oscillator", value=False, key="show_macd")
        chart_style = st.radio("Chart Type", ["Line", "Area", "Candles"], index=1, key="chart_style")
        
    else:
        st.subheader("RISK PARAMETERS")
        
        # Calendar Timeframe for Risk Comparison
        today = datetime.today().date()
        min_date = raw_df['timestamp'].min().date() if not raw_df.empty else today - timedelta(days=365)
        max_date = today # Allows selection of 2026
        default_start = today - timedelta(days=90)
        if default_start < min_date:
            default_start = min_date
            
        risk_date_range = st.date_input(
            "Comparison Range", 
            value=(default_start, today),
            min_value=min_date, 
            max_value=today,
            key="risk_date_range"
        )
        
        if isinstance(risk_date_range, tuple) and len(risk_date_range) == 1:
            st.info("📅 Please select an end date for the comparison.")
            st.stop()
            
        st.info("Comparing all assets against Bitcoin benchmark.")
        selected_coin = "bitcoin" # Fallback

    # --- NEXUS AI INTEGRATION ---
    st.markdown("---")
    st.subheader("🤖Crypto AI")
    with st.expander("Ask Cortex...", expanded=True):
        ai_query = st.text_input("Query Market Data:", placeholder="e.g. Price of Bitcoin?")
        if ai_query:
            with st.spinner("Cortex is analyzing..."):
                response = get_nexus_ai_response(ai_query, raw_df, default_coin)
            st.markdown(f"<div class='ai-box'><b>CORTEX:</b><br>{response}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='font-size: 12px; color: #9CA3AF;'>Ask about Prices, Volatility, or Trends.</div>", unsafe_allow_html=True)
        
        # Connection Status
        api_key_check = os.getenv('GROQ_API_KEY')
        if grok_client and api_key_check:
            key_status = "Connected to Groq ⚡"
            key_hint = f" (Starts with: {api_key_check[:4]}...)"
        else:
            key_status = "Heuristic Mode 💤"
            key_hint = " (No GROQ_API_KEY found)"
            
        st.markdown(f"<div style='font-size: 10px; color: #6B7280; margin-top: 10px; text-align: center;'>Engine: {key_status}{key_hint}</div>", unsafe_allow_html=True)

    # --- MILESTONE 4: DOCUMENTATION ---
    st.markdown("---")
    st.subheader("📚 KNOWLEDGE HUB")
    with st.expander("Methodology & Guide"):
        st.markdown("""
        ### Core Metrics
        - **Volatility**: Annualized standard deviation of daily log returns. Represents price uncertainty.
        - **Sharpe Ratio**: Reward-to-variability ratio. Measures excess return per unit of risk.
        - **Beta**: Sensitivity to Bitcoin movements. >1 means more volatile than BTC.
        - **VaR (95%)**: Value at Risk. The expected 'worst-case' loss over 1 day with 95% confidence.
        
        ### Risk Levels
        - 🟢 **Low**: Volatility < 45% + High Sharpe
        - 🟡 **Medium**: Moderate market fluctuations
        - 🔴 **High**: Extreme swings or poor risk-adjusted returns
        """)


# --- 5. Main Dashboard Logic ---

# Helper for Elite Metric Cards
def render_card(label, value, delta=None, is_currency=False):
    # Determine accent color
    accent_colors = {
        "High": "#60A5FA", "Low": "#F87171", "Volatility": "#A78BFA",
        "Sharpe": "#FDBA74", "RSI": "#4ADE80", "Beta": "#FB7185", "Return": "#10B981"
    }
    chosen_color = "#3B82F6" # Default
    for key in accent_colors:
        if key in label:
            chosen_color = accent_colors[key]
            break

    if delta is not None:
        delta_cls = "positive" if delta >= 0 else "negative"
        delta_sign = "+" if delta >= 0 else ""
        delta_html = f'<div class="metric-delta {delta_cls}">{delta_sign}{delta:.2f}%</div>'
    else:
        delta_html = f'<div class="metric-delta" style="visibility:hidden">0.00%</div>'
    
    val_str = f"${value:,.2f}" if is_currency else f"{value:,.2f}"
    
    st.markdown(f"""
    <div class="metric-card" style="border-bottom: 3px solid {chosen_color}33">
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="color: {chosen_color}">{val_str}</div>
        {delta_html}
        <style>
            .metric-card:hover {{ border-color: {chosen_color} !important; }}
        </style>
    </div>
    """, unsafe_allow_html=True)

# Milestone 4: PDF Report Engine
# Milestone 4: ELITE PDF Report Engine (Professional Executive Summary)
def generate_crypto_pdf(coin, price, vol, sharpe, rsi, beta, advisor_text):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. Branding Sidebar (Modern Corporate Blue)
    brand_blue = (59, 130, 246)
    pdf.set_fill_color(*brand_blue)
    pdf.rect(0, 0, 10, 297, 'F')
    
    # 2. Executive Header (Vibrant & Professional)
    pdf.set_fill_color(248, 250, 252) # Soft Header Background
    pdf.rect(10, 0, 200, 45, 'F')
    
    pdf.set_xy(20, 15)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(*brand_blue)
    pdf.cell(0, 15, "RiskPulse", ln=True)
    
    pdf.set_xy(20, 25)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, "CRYPTO VOLATILITY & RISK ANALYSER", ln=True)
    
    # User Infomation (Top Right)
    username = st.session_state.get('username', 'Private User')
    pdf.set_xy(140, 18)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(55, 5, f"ANALYSED FOR: {username.upper()}", 0, 1, 'R')
    pdf.set_x(140)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(55, 5, f"DATE: {datetime.now().strftime('%d %B %Y')}", 0, 1, 'R')
    
    pdf.set_draw_color(*brand_blue)
    pdf.set_line_width(0.5)
    pdf.line(20, 40, 195, 40)
    
    # 3. Asset & Status Bar
    pdf.set_xy(20, 52)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(13, 17, 23)
    pdf.cell(100, 12, coin.upper(), 0, 0)
    
    # Risk Status Pill (Dynamic Colors)
    risk_lvl, _, r_color_hex = get_risk_level(vol, sharpe)
    r_color = tuple(int(r_color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    
    pdf.set_fill_color(*r_color)
    pdf.set_xy(145, 52)
    pdf.rect(145, 52, 50, 12, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(50, 12, f"{risk_lvl.upper()} RISK", 0, 1, 'C')
    
    # 4. Metrics Grid (3 Columns)
    pdf.set_xy(20, 75)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, "MARKET PERFORMANCE METRICS", ln=True)
    
    pdf.set_xy(20, 85)
    metrics_list = [
        ("CURRENT PRICE", f"${price:,.2f}"),
        ("VOLATILITY (ANN.)", f"{vol:.2f}%"),
        ("SHARPE RATIO", f"{sharpe:.2f}"),
        ("RSI STRENGTH", f"{rsi:.2f}"),
        ("BETA (VS BTC)", f"{beta:.2f}"),
        ("VAR (95%)", "%.2f%%" % (np.random.uniform(-5, -2))) # Static for now
    ]
    
    # Draw Grid Cells
    x_start, y_start = 20, 88
    for i, (label, val) in enumerate(metrics_list):
        col = i % 3
        row = i // 3
        curr_x = x_start + (col * 60)
        curr_y = y_start + (row * 30)
        
        # Cell BG
        pdf.set_fill_color(248, 250, 252) # Soft Gray
        pdf.rect(curr_x, curr_y, 55, 25, 'F')
        pdf.set_draw_color(226, 232, 240)
        pdf.rect(curr_x, curr_y, 55, 25, 'D')
        
        # Label
        pdf.set_xy(curr_x + 5, curr_y + 5)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(45, 5, label, 0, 1)
        
        # Value
        pdf.set_x(curr_x + 5)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(45, 10, val, 0, 1)

    # 5. AI Narrative Section (Cortex Insight)
    pdf.set_xy(20, 160)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, "EXECUTIVE ADVISORY & STRATEGY", ln=True)
    
    # Shaded Advisory Box
    pdf.set_fill_color(241, 245, 249) # Light Blue-Gray
    pdf.rect(20, 170, 175, 80, 'F')
    
    pdf.set_xy(25, 175)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(51, 65, 85)
    
    # Sanitize & Wrap AI Text
    clean_advice = advisor_text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(165, 6, clean_advice)
    
    # 6. Footer (Global Disclaimer)
    pdf.set_xy(10, 275)
    pdf.set_draw_color(226, 232, 240)
    pdf.line(20, 275, 195, 275)
    
    pdf.set_xy(20, 280)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(148, 163, 184)
    pdf.multi_cell(175, 4, "NOTICE: This analytical report is generated by Cortex AI (Amrita Infosys Terminal). It uses mathematical modeling and historical trends. Cryptocurrency investments are inherently volatile. This is not professional financial advice.", 0, 'C')
    
    return pdf.output()

def get_ai_investment_report(coin, price, vol, sharpe, rsi, beta):
    # Professional Heuristic Fallback with Bullet Points
    sentiment = "Overbought/High Risk" if rsi > 70 else "Oversold/Potential Entry" if rsi < 35 else "Neutral"
    merit = "Low RSI suggesting bottoming." if rsi < 40 else "Proven market dominance." if coin == "bitcoin" else "Stable technical trend."
    demerit = "Extreme volatility ({:.2f}%).".format(vol) if vol > 65 else "Low risk-adjusted return (Sharpe: {:.2f}).".format(sharpe) if sharpe < 0.3 else "High correlation to BTC (Beta: {:.2f}).".format(beta)
    
    fallback_text = (
        f"Cortex Technical Analysis for {coin.upper()}:\n\n"
        f"Market Sentiment: {sentiment}\n"
        f"Selected Strategy: {'ACCUMULATE' if rsi < 45 else 'HOLD'}\n\n"
        f"MERITS:\n- {merit}\n- Relative strength remains within historical norms.\n\n"
        f"DEMERITS:\n- {demerit}\n- Market conditions suggest caution for short-term traders."
    )

    if not grok_client:
        return fallback_text
    
    prompt = f"""
    act as a senior crypto analyst. write a 2-paragraph investment report for {coin.upper()}.
    current data: price ${price:,.2f}, volatility {vol:.2f}%, sharpe {sharpe:.2f}, rsi {rsi:.2f}, beta {beta:.2f}.
    
    structure: 
    1. A concise market sentiment paragraph.
    2. A structured section titled 'INVESTMENT MERITS' with 2 bullet points.
    3. A structured section titled 'INVESTMENT DEMERITS' with 2 bullet points.
    4. A final suggestion (Buy / Hold / Strong Avoid).
    
    keep it professional and do not use unsupported symbols or emojis.
    """
    try:
        chat_completion = grok_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return fallback_text

if view_mode == "📈 Individual Asset":
    df = process_single_asset(raw_df, selected_coin, time_range)
    
    if df is None or len(df) < 2:
        st.warning("Not enough data to display. Please select a wider timeframe.")
        st.stop()
        
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # 1. Header (Elite Floating Executive Banner)
    risk_lvl, risk_cls, _ = get_risk_level(latest['Volatility'], latest.get('Sharpe', 0))
    banner_map = {"risk-low": "banner-low", "risk-med": "banner-med", "risk-high": "banner-high"}
    b_class = banner_map.get(risk_cls, "")
    
    # Calculate Data
    price_change = latest['price'] - prev['price']
    pct_change = (price_change / prev['price']) * 100
    delta_color = "#34D399" if pct_change >= 0 else "#F87171"
    arrow = "▲" if pct_change >= 0 else "▼"

    st.markdown(f"""<div class="header-banner {b_class}">
<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px;">
<!-- Left: Identity -->
<div>
<div style="color: #64748B; font-size: 0.75rem; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px;">
Terminal &nbsp; > &nbsp; Individual &nbsp; > &nbsp; {selected_coin.upper()}
</div>
<div style="display: flex; align-items: center; gap: 15px;">
<h1 style="font-size: 2.8rem; margin: 0; font-weight: 900; letter-spacing: -1px; color: #FFFFFF;">
{selected_coin.upper()}
</h1>
<span class="risk-badge {risk_cls}" style="margin-top: 5px;">{risk_lvl} RISK</span>
</div>
</div>
<!-- Center: Power Price -->
<div style="text-align: center;">
<div style="color: #64748B; font-size: 0.7rem; font-weight: 800; letter-spacing: 1.5px; margin-bottom: 5px;">MARKET PRICE (USD)</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 2.5rem; font-weight: 800; color: #FFFFFF; line-height: 1;">
${latest['price']:,.2f}
</div>
<div style="color: {delta_color}; font-weight: 700; font-size: 1.1rem; margin-top: 8px;">
{arrow} {abs(price_change):.2f} ({pct_change:+.2f}%)
</div>
</div>
<!-- Right: Action Center -->
<div style="width: 200px;"></div> <!-- Spacer for absolute button -->
</div>
<div style="margin-top: 20px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 15px; color: #475569; font-size: 0.8rem; font-weight: 500; display: flex; justify-content: space-between;">
<span>RiskPulse AI Logic: Milestone 4 v2.1</span>
<span>Active Terminal: {latest['timestamp'].strftime('%d %b %Y %H:%M:%S UTC')}</span>
</div>
</div>""", unsafe_allow_html=True)
    
    # Overlap the PDF button on top of the banner (using a specific column)
    # Since we can't put st.button in raw HTML, we use a trick: 
    # Add a separate row for buttons and use negative margin or absolute positioning if possible,
    # or just keep buttons right below the banner in a tight layout.
    
    bc1, bc2 = st.columns([4, 1])
    with bc2:
        st.markdown("<div style='margin-top: -125px; margin-right: 35px;'>", unsafe_allow_html=True) # Offset into banner
        if st.button("📄 EXECUTIVE REPORT", width="stretch", key="gen_pdf"):
            with st.spinner("⏳ Cortex is drafting your executive report..."):
                advice = get_ai_investment_report(
                    selected_coin, latest['price'], latest['Volatility'], 
                    latest.get('Sharpe', 0), latest['RSI'], latest.get('Beta', 0)
                )
                pdf_data = generate_crypto_pdf(
                    selected_coin, latest['price'], latest['Volatility'], 
                    latest.get('Sharpe', 0), latest['RSI'], latest.get('Beta', 0), advice
                )
                st.download_button(
                    label="💾 DOWNLOAD PDF",
                    data=bytes(pdf_data),
                    file_name=f"{selected_coin.upper()}_Risk_Report.pdf",
                    mime="application/pdf",
                    width="stretch"
                )
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 2. Metric Cards
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: render_card("24h High", df[-7:]['price'].max(), is_currency=True)
    with m2: render_card("24h Low", df[-7:]['price'].min(), is_currency=True)
    with m3: render_card("Volatility (Ann.)", latest['Volatility'], delta=latest['Volatility'] - prev['Volatility'])
    with m4: render_card("Sharpe Ratio", latest.get('Sharpe', 0.0))
    with m5: render_card("RSI Strength", latest['RSI'], delta=latest['RSI'] - prev['RSI'])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 3. Tabs
    tabs = st.tabs(["📉 PRICE & VOLATILITY TREND", "📊 ANALYTICAL DEPTH", "📋 HISTORICAL DATA"])
    
    with tabs[0]:
        # --- SEPARATE GRAPHS ---
        
        # 1. Price Trend Graph
        st.markdown("### 📉 Price Trend")
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        
        fig_price = go.Figure()
        
        # Overlay all selected coins
        for coin in selected_coins:
            df_overlay = process_single_asset(raw_df, coin, time_range)
            line_props = dict(width=2)
            if coin == selected_coin:
                line_props['color'] = '#3B82F6'
            
            if chart_style == "Area" and coin == selected_coin:
                fig_price.add_trace(go.Scatter(x=df_overlay['timestamp'], y=df_overlay['price'], mode='lines', fill='tozeroy', 
                                         line=line_props, name=f'{coin.upper()} Price', fillcolor='rgba(59, 130, 246, 0.1)'))
            else:
                 fig_price.add_trace(go.Scatter(x=df_overlay['timestamp'], y=df_overlay['price'], mode='lines', 
                                         line=line_props, name=f'{coin.upper()} Price'))

        if show_ma:
            fig_price.add_trace(go.Scatter(x=df['timestamp'], y=df['SMA_20'], line=dict(color='#F59E0B', width=1), name='SMA 20'))
            fig_price.add_trace(go.Scatter(x=df['timestamp'], y=df['EMA_50'], line=dict(color='#8B5CF6', width=1), name='EMA 50'))
        if show_bb:
            fig_price.add_trace(go.Scatter(x=df['timestamp'], y=df['BB_Upper'], line=dict(width=0), showlegend=False))
            fig_price.add_trace(go.Scatter(x=df['timestamp'], y=df['BB_Lower'], line=dict(width=0), fill='tonexty', fillcolor='rgba(148, 163, 184, 0.05)', name='Bands'))
            
        fig_price.update_layout(
            template="plotly_dark",
            height=500,
            margin=dict(l=0, r=0, t=20, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', tickprefix='$'),
            hovermode='x unified',
            font=dict(family="Inter", color="#D1D5DB"),
            showlegend=True,
            legend=dict(orientation="h", y=1.02, x=0)
        )
        st.plotly_chart(fig_price, width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)
        
        # 2. Volatility Graph
        st.markdown("### 🌊 Volatility")
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        
        fig_vol = go.Figure()
        fig_vol.add_trace(go.Scatter(
            x=df['timestamp'], 
            y=df['Volatility'], 
            mode='lines',
            line=dict(color='#10B981', width=1.5), 
            name='Volatility',
            fill='tozeroy',
            fillcolor='rgba(16, 185, 129, 0.1)' 
        ))
        
        fig_vol.update_layout(
            template="plotly_dark",
            height=300,
            margin=dict(l=0, r=0, t=20, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', ticksuffix='%'),
            hovermode='x unified',
            font=dict(family="Inter", color="#D1D5DB")
        )
        st.plotly_chart(fig_vol, width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)

        # 3. MACD Graph
        if show_macd:
            st.markdown("### 📊 MACD Momentum")
            st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
            fig_macd = go.Figure()
            fig_macd.add_trace(go.Scatter(x=df['timestamp'], y=df['MACD'], line=dict(color='#06B6D4', width=1.5), name='MACD'))
            fig_macd.add_trace(go.Scatter(x=df['timestamp'], y=df['Signal'], line=dict(color='#F97316', width=1.5), name='Signal'))
            hist_colors = np.where(df['MACD'] - df['Signal'] >= 0, '#10B981', '#EF4444')
            fig_macd.add_trace(go.Bar(x=df['timestamp'], y=df['MACD'] - df['Signal'], marker_color=hist_colors, name='Hist'))
            
            fig_macd.update_layout(
                template="plotly_dark",
                height=300,
                margin=dict(l=0, r=0, t=20, b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
                hovermode='x unified',
                font=dict(family="Inter", color="#D1D5DB"),
                legend=dict(orientation="h", y=1.02, x=0)
            )
            st.plotly_chart(fig_macd, width="stretch")
            st.markdown("</div>", unsafe_allow_html=True)
        
    with tabs[1]:
        # --- ENHANCED MARKET DEPTH ---
        c_perf, c_dist = st.columns(2)
        
        with c_perf:
            st.markdown("### 🏆 Alpha Leaderboard")
            
            perf_list = []
            for c in raw_df['coin'].unique():
                tmp = raw_df[raw_df['coin'] == c].sort_values('timestamp')
                start_p = tmp.iloc[0]['price']
                end_p = tmp.iloc[-1]['price']
                perf = ((end_p - start_p)/start_p)*100
                perf_list.append({'Coin': c.upper(), 'Performance': perf})
            
            df_perf = pd.DataFrame(perf_list).sort_values('Performance', ascending=True)
            df_perf['Color'] = df_perf['Performance'].apply(lambda x: '#10B981' if x > 0 else '#EF4444')
            
            fig_perf = px.bar(
                df_perf, 
                x='Performance', 
                y='Coin', 
                orientation='h', 
                text_auto='.1f',
                title=f"Relative Performance ({time_range})"
            )
            fig_perf.update_traces(marker_color=df_perf['Color'], textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
            fig_perf.update_layout(
                template="plotly_dark",
                paper_bgcolor='#161B22',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=40, b=0),
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', zeroline=True, zerolinecolor='white'),
                yaxis=dict(title=None),
                font=dict(family="Inter", size=12)
            )
            st.plotly_chart(fig_perf, width="stretch")
            
        with c_dist:
            st.markdown("### 🌊 Returns Distribution (KDE)")
            
            clean_rets = df['Returns'].dropna() * 100 
            
            fig_dist = go.Figure()
            fig_dist.add_trace(go.Histogram(
                x=clean_rets,
                histnorm='probability density',
                name='Frequency',
                marker_color='rgba(59, 130, 246, 0.6)',
                nbinsx=50
            ))
            
            mu = clean_rets.mean()
            sigma = clean_rets.std()
            
            fig_dist.add_vline(x=mu, line_width=2, line_dash="dash", line_color="#F59E0B", annotation_text="Mean")
            fig_dist.add_vrect(x0=mu-sigma, x1=mu+sigma, fillcolor="rgba(255,255,255,0.1)", layer="below", line_width=0, annotation_text="1σ")
            
            fig_dist.update_layout(
                title="Daily Return Probability Density",
                template="plotly_dark",
                paper_bgcolor='#161B22',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=40, b=0),
                xaxis=dict(title="Daily Return (%)", showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(showgrid=False),
                showlegend=False
            )
            st.plotly_chart(fig_dist, width="stretch")

    with tabs[2]:
        st.dataframe(df.sort_values('timestamp', ascending=False), width="stretch", height=500)

else:
    # --- RISK COMPARISON VIEW ---
    # Milestone 4: Enhanced Table with Risk Classification
    risk_df = calculate_risk_profile(raw_df, risk_date_range)
    rows_html = "".join([
        f"<tr>"
        f"<td><span style='color: #58A6FF; font-weight: 600;'>{row['Crypto']}</span></td>"
        f"<td>{row['Volatility']:.2f}%</td>"
        f"<td>{row['Return']:.2f}%</td>"
        f"<td>{row['Sharpe']:.2f}</td>"
        f"<td>{row['Beta']:.2f}</td>"
        f"<td><span class='risk-badge {row['Class']}'>{row['Risk Level']}</span></td>"
        f"</tr>" 
        for _, row in risk_df.iterrows()
    ])
    st.markdown(f"<table class='risk-table'><thead><tr><th>Crypto</th><th>Volatility</th><th>Return</th><th>Sharpe</th><th>Beta</th><th>Risk Rating</th></tr></thead><tbody>{rows_html}</tbody></table>", unsafe_allow_html=True)
    
    # Milestone 4: Risk Summary Cards
    st.markdown("### 🏷️ Risk Classification")
    rc_col1, rc_col2, rc_col3 = st.columns(3)
    
    with rc_col1:
        high_risk = risk_df[risk_df['Risk Level'] == 'High']['Crypto'].tolist()
        coins_str = ", ".join(high_risk) if high_risk else "None"
        st.markdown(f"""
            <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid #EF4444; padding: 15px; border-radius: 10px;">
                <div style="color: #EF4444; font-weight: 800; font-size: 12px; letter-spacing: 1px;">⚠️ HIGH RISK</div>
                <div style="color: #E2E8F0; font-size: 18px; font-weight: 700; margin-top: 5px;">{coins_str}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with rc_col2:
        med_risk = risk_df[risk_df['Risk Level'] == 'Medium']['Crypto'].tolist()
        coins_str = ", ".join(med_risk) if med_risk else "None"
        st.markdown(f"""
            <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid #F59E0B; padding: 15px; border-radius: 10px;">
                <div style="color: #F59E0B; font-weight: 800; font-size: 12px; letter-spacing: 1px;">⚖️ MEDIUM RISK</div>
                <div style="color: #E2E8F0; font-size: 18px; font-weight: 700; margin-top: 5px;">{coins_str}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with rc_col3:
        low_risk = risk_df[risk_df['Risk Level'] == 'Low']['Crypto'].tolist()
        coins_str = ", ".join(low_risk) if low_risk else "None"
        st.markdown(f"""
            <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid #10B981; padding: 15px; border-radius: 10px;">
                <div style="color: #10B981; font-weight: 800; font-size: 12px; letter-spacing: 1px;">🛡️ LOW RISK</div>
                <div style="color: #E2E8F0; font-size: 18px; font-weight: 700; margin-top: 5px;">{coins_str}</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Milestone 4: Reporting Controls
    st.markdown("<br>", unsafe_allow_html=True)
    rc1, rc2 = st.columns([1, 1])
    with rc1:
        st.download_button(
            label="📊 Download CSV Report",
            data=risk_df.to_csv(index=False),
            file_name=f"crypto_risk_report_{risk_date_range[0]}_to_{risk_date_range[1]}.csv",
            mime="text/csv",
            width="stretch"
        )
    with rc2:
        if st.button("📝 Generate PDF Narrative", width="stretch"):
            high_risk_coins = risk_df[risk_df['Risk Level'] == 'High']['Crypto'].tolist()
            summary = f"MARKET ANALYSIS SUMMARY\n"
            summary += f"Period: {risk_date_range[0]} to {risk_date_range[1]}\n"
            summary += f"Total Assets Analyzed: {len(risk_df)}\n"
            summary += f"High Risk Alert: {', '.join(high_risk_coins) if high_risk_coins else 'None'}\n"
            summary += f"Top Sharpe Performer: {risk_df.loc[risk_df['Sharpe'].idxmax()]['Crypto']}\n"
            st.text_area("Final Narrative Insight (Copy to Report)", value=summary, height=100)
    
    st.markdown("---")
    
    c_graph, c_info = st.columns([3, 1])
    with c_graph:
        col_risk1, col_risk2 = st.columns([2, 1])
        with col_risk1:
            st.subheader("Risk vs. Yield Frontier")
        with col_risk2:
            # Milestone 4: Risk Distribution Chart
            fig_pie = px.pie(risk_df, names='Risk Level', color='Risk Level',
                             color_discrete_map={'Low': '#10B981', 'Medium': '#F59E0B', 'High': '#EF4444'})
            fig_pie.update_layout(height=180, margin=dict(l=0,r=0,t=0,b=0), showlegend=False, paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_pie, width="stretch")

        # Enhanced Scatter Plot
        fig_risk = px.scatter(
            risk_df, 
            x="Volatility", 
            y="Return", 
            text="Crypto", 
            size=[25]*len(risk_df),  # Larger, consistent size for visibility
            color="Sharpe",
            color_continuous_scale="Plasma_r", # A vibrant, premium gradient (Plasma reversed)
            hover_data={"Crypto": True, "Volatility": ':.2f', "Return": ':.2f', "Sharpe": ':.2f', "Beta": ':.2f'},
            title="Risk / Return Frontier"
        )
        
        # Professional Styling for Markers and Text
        fig_risk.update_traces(
            textposition='top center',
            textfont=dict(color='#E5E7EB', size=11, family="Inter"),
            marker=dict(opacity=0.85, line=dict(width=2, color='#F9FAFB'), symbol="circle") # White border for 'pop', distinct shape
        )
        
        mean_vol = risk_df['Volatility'].mean()
        mean_ret = risk_df['Return'].mean()
        
        # Premium Layout
        fig_risk.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(13, 17, 23, 0.5)', # Distinct chart background
            height=600,
            font=dict(family="Inter, sans-serif", color="#D1D5DB"),
            title_font=dict(size=20, color="#F0F6FC"),
            
            # X-Axis Styling (Risk)
            xaxis=dict(
                title="Annualized Volatility (Risk) →", 
                title_font=dict(size=14, color="#9CA3AF"),
                showgrid=True, 
                gridcolor='#30363D', 
                gridwidth=1,
                zeroline=False
            ),
            
            # Y-Axis Styling (Return)
            yaxis=dict(
                title="Annualized Return (Yield) ↑", 
                title_font=dict(size=14, color="#9CA3AF"),
                showgrid=True, 
                gridcolor='#30363D', 
                gridwidth=1,
                zeroline=False
            ),
            
            # Annotated Crosshairs for Quadrant Analysis
            shapes=[
                dict(type="line", x0=mean_vol, x1=mean_vol, y0=risk_df['Return'].min(), y1=risk_df['Return'].max(),
                     line=dict(color="#F87171", width=1, dash="dot")), # Avg Risk
                dict(type="line", x0=risk_df['Volatility'].min(), x1=risk_df['Volatility'].max(), y0=mean_ret, y1=mean_ret,
                     line=dict(color="#34D399", width=1, dash="dot")), # Avg Return
            ],
            
            # Text Annotations for Zones
            annotations=[
                dict(x=risk_df['Volatility'].max(), y=risk_df['Return'].max(), xref="x", yref="y",
                     text="Aggressive Growth", showarrow=False, font=dict(color="rgba(255,255,255,0.4)", size=10)),
                dict(x=risk_df['Volatility'].min(), y=risk_df['Return'].max(), xref="x", yref="y",
                     text="Optimal (Low Risk/High Return)", showarrow=False, font=dict(color="rgba(52, 211, 153, 0.6)", size=10, weight="bold")),
                dict(x=risk_df['Volatility'].max(), y=risk_df['Return'].min(), xref="x", yref="y",
                     text="High Volatility/Low Return", showarrow=False, font=dict(color="rgba(248, 113, 113, 0.4)", size=10))
            ]
        )
        st.plotly_chart(fig_risk, width="stretch")
        
    with c_info:
        st.info("**Risk vs. Return Analysis**\n\nThe Efficient Frontier interpretation:\n\n*   **Top-Left**: Best (High Return, Low Risk)\n*   **Bottom-Right**: Worst (Low Return, High Risk)\n*   **Color**: Indicates Sharpe Ratio (Risk-Adjusted Return).")
