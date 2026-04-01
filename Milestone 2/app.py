import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
import scipy.stats as stats
import hashlib
import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="Crypto Volatility and Risk Analyzer",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Advanced Custom CSS ---
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0d1117; 
        border-right: 1px solid #30363D;
        padding-top: 20px;
    }
    
    /* --- SIDEBAR VISIBILITY FIXES (CRITICAL v2) --- */
    
    /* Force ALL basic text in sidebar to be white */
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4 {
        color: #E6EDF3 !important;
    }
    
    /* 1. SELECT BOX (Closed State - "Select Asset") */
    /* This targets the container of the closed dropdown */
    div[data-baseweb="select"] > div {
        background-color: #0D1117 !important; /* Dark Background */
        color: #E6EDF3 !important;            /* White Text */
        border-color: #30363D !important;     /* Grey Border */
    }
    /* This targets the text inside */
    div[data-baseweb="select"] span {
        color: #E6EDF3 !important;
    }
    /* The arrow icon */
    div[data-baseweb="select"] svg {
        fill: #E6EDF3 !important; 
    }
    
    /* 2. EXPANDER HEADER ("Ask Cortex...") */
    /* Targets the summary/header of the expander */
    div[data-testid="stExpander"] details > summary {
        background-color: #161B22 !important; /* Dark Background */
        color: #E6EDF3 !important;            /* White Text */
        border: 1px solid #30363D !important;
        border-radius: 6px;
    }
    div[data-testid="stExpander"] details > summary:hover {
        background-color: #1F2937 !important; /* Slightly lighter on hover */
        color: #58A6FF !important;            /* Blue Text on Hover */
    }
    /* The arrow icon in expander */
    div[data-testid="stExpander"] details > summary svg {
        fill: #E6EDF3 !important;
    }
    
    /* 3. RADIO BUTTONS & CHECKBOXES */
    .stRadio div[role='radiogroup'] > label > div:first-child + div {
        color: #E6EDF3 !important;
    }
    .stCheckbox label span {
        color: #E6EDF3 !important;
    }
    
    /* 4. TEXT INPUT ("Query Market Data") */
    div[data-baseweb="input"] > div {
        background-color: #0D1117 !important;
        color: #E6EDF3 !important;
        border-color: #30363D !important; 
    }
    input[data-baseweb="input"] {
        color: #E6EDF3 !important;
    }
    
    /* Top Label of widgets ("Select Asset", "Timeframe") */
    div[data-testid="stWidgetLabel"] p {
        color: #9CA3AF !important; 
        font-weight: 600;
    }
    
    /* Dropdown Menu Items (The list that pops up) */
    ul[data-testid="stSelectboxVirtualDropdown"] li {
        background-color: #1F2937 !important;
        color: #E6EDF3 !important;
    }
    ul[data-testid="stSelectboxVirtualDropdown"] li:hover {
        background-color: #58A6FF !important;
        color: #FFFFFF !important;
    }
    
    /* Tabs Styling */
    button[data-baseweb="tab"] {
        color: #8B949E;
        font-weight: 600;
        font-size: 14px;
        padding: 10px 20px;
        background-color: transparent;
        border: none;
    }
    button[data-baseweb="tab"]:hover {
        color: #58A6FF;
        background-color: rgba(88, 166, 255, 0.1);
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #58A6FF !important;
        background-color: #1F2937;
        border-radius: 8px 8px 0 0;
        border-bottom: 2px solid #58A6FF;
    }
    
    /* Custom Metric Cards */
    div.metric-card {
        background: linear-gradient(145deg, #1f2937, #111827);
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        padding: 16px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        margin-bottom: 16px;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    div.metric-label {
        color: #9CA3AF;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    div.metric-value {
        color: #F9FAFB;
        font-size: 1.5rem;
        font-weight: 800;
        font-family: 'Roboto Mono', monospace;
    }
    .positive { color: #34D399; font-weight: 600; font-size: 0.9rem;}
    .negative { color: #F87171; font-weight: 600; font-size: 0.9rem;}
    
    /* Risk Table Styling */
    .risk-table {
        font-family: 'Segoe UI', sans-serif;
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 20px;
        background-color: #161B22;
        border-radius: 8px;
        overflow: hidden;
    }
    .risk-table th {
        text-align: left;
        color: #8B949E;
        padding: 16px;
        border-bottom: 1px solid #30363D;
        font-size: 14px;
        text-transform: uppercase;
        background-color: #0d1117;
    }
    .risk-table td {
        padding: 16px;
        border-bottom: 1px solid #21262D;
        color: #E6EDF3;
        font-size: 15px;
    }
    .risk-table tr:last-child td {
        border-bottom: none;
    }
    
    /* Chart Container */
    .chart-box {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        margin-bottom: 20px;
    }
    
    /* AI Chat Box */
    .ai-box {
        background-color: #0D1117;
        border: 1px solid #30363D;
        border-radius: 8px;
        padding: 15px;
        font-size: 13px;
        color: #E6EDF3;
        margin-top: 10px;
        border-left: 3px solid #58A6FF;
    }
    
    /* Refresh Button Styling */
    div.stButton > button {
        background-color: #238636;
        color: white;
        border: 1px solid rgba(240, 246, 252, 0.1);
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:hover {
        background-color: #2ea043;
        border-color: #8b949e;
        transform: scale(1.02);
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. Data Engine ---
COINS = ['bitcoin', 'ethereum', 'solana', 'cardano', 'dogecoin']
VS_CURRENCY = 'usd'
DAYS = '365'
INTERVAL = 'daily'

def fetch_crypto_data(coin_id):
    """Fetch historical market data for a single coin from CoinGecko API."""
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        'vs_currency': VS_CURRENCY,
        'days': DAYS,
        'interval': INTERVAL
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        prices = data.get('prices', [])
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['coin'] = coin_id
        return df
    except Exception:
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
    """Fetch fresh data from CoinGecko API and save to CSV."""
    csv_path = os.path.join(os.path.dirname(__file__), 'crypto_data.csv')
    all_data = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(fetch_crypto_data, COINS))
    for df in results:
        if df is not None:
            all_data.append(df)
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        final_df.to_csv(csv_path, index=False)
        return True
    return False

def get_nexus_ai_response(query, df, current_coin):
    """Simple heuristic 'AI' to answer market data questions."""
    query = query.lower()
    
    # Identify target coin
    all_coins = df['coin'].unique()
    target_coin = current_coin
    for c in all_coins:
        if c in query:
            target_coin = c
            break
            
    # fetch data
    coin_data = df[df['coin'] == target_coin].sort_values('timestamp')
    latest = coin_data.iloc[-1]
    
    # Calculate key metrics on the fly
    curr_price = latest['price']
    
    # Volatility calc
    rets = coin_data['price'].pct_change()
    vol = rets.rolling(30).std().iloc[-1] * np.sqrt(365) * 100
    
    # High/Low
    high_all = coin_data['price'].max()
    low_all = coin_data['price'].min()
    
    if "price" in query:
        return f"The current price of **{target_coin.upper()}** is **${curr_price:,.2f}**."
    elif "high" in query:
        return f"The all-time high for **{target_coin.upper()}** in this dataset is **${high_all:,.2f}**."
    elif "low" in query:
        return f"The all-time low for **{target_coin.upper()}** in this dataset is **${low_all:,.2f}**."
    elif "volatility" in query or "risk" in query:
        risk_level = "High" if vol > 60 else "Moderate" if vol > 30 else "Low"
        return f"**{target_coin.upper()}** has an annualized volatility of **{vol:.1f}%**. Current Risk Level: **{risk_level}**."
    elif "trend" in query:
         sma20 = coin_data['price'].rolling(20).mean().iloc[-1]
         trend = "Bullish" if curr_price > sma20 else "Bearish"
         return f"**{target_coin.upper()}** is currently trading {'above' if curr_price > sma20 else 'below'} its 20-day SMA, interpreted as a **{trend}** trend."
    else:
        return f"I am analyzing **{target_coin.upper()}**. You can ask me about its **Price**, **Volatility**, **Highs/Lows**, or **Trend**."

def calculate_risk_profile(df, days_str):
    end_date = df['timestamp'].max()
    days_map = {"30D": 30, "90D": 90, "1Y": 365}
    start_date = end_date - timedelta(days=days_map.get(days_str, 90))
    df_filtered = df[df['timestamp'] >= start_date].copy()
    
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
        metrics.append({
            "Crypto": coin.upper(),
            "Volatility": vol,
            "Return": ann_ret,
            "Sharpe": sharpe,
            "Beta": beta,
            "VaR (95%)": var_95
        })
    return pd.DataFrame(metrics).sort_values("Volatility", ascending=True)

def process_single_asset(df, coin, days):
    df_coin = df[df['coin'] == coin].sort_values('timestamp').reset_index(drop=True)
    if days != "ALL":
        end_date = df_coin['timestamp'].max()
        days_map = {"1W": 7, "1M": 30, "3M": 90, "6M": 180, "1Y": 365, "YTD": (end_date - datetime(end_date.year, 1, 1)).days}
        start_date = end_date - timedelta(days=days_map.get(days, 365))
        df_coin = df_coin[df_coin['timestamp'] >= start_date].copy()
    
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
    st.markdown("""
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
                url("data:image/jpeg;base64,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") !important;
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
""", unsafe_allow_html=True)

    # --- LAYOUT MANAGEMENT ---
    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        st.markdown('<div class="login-title">Crypto Volatility and Risk Analyzer</div>', unsafe_allow_html=True)
        
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
            if st.button("Create Account", use_container_width=True):
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
            if st.button("Back to Login", use_container_width=True):
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
    st.title("Crypto Voltality And Risk Analyzer")
    
    
    # User Profile
    st.markdown(f"""
    <div style='background: #161b22; padding: 10px; border-radius: 8px; border: 1px solid #30363d; margin-bottom: 20px;'>
        <div style='color: #8b949e; font-size: 12px;'>Logged in as:</div>
        <div style='color: #58a6ff; font-weight: 600;'>@{st.session_state.get('username', 'User')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
        st.session_state['authenticated'] = False
        st.session_state['username'] = None
        st.rerun()

    st.markdown("---")
    
    st.subheader("🖥️ DASHBOARD MODE")
    view_mode = st.radio("Select View", ["📈 Individual Asset", "⚖️ Risk Comparison"], index=0)
    
    st.markdown("---")
    
    default_coin = "bitcoin" 
    
    if view_mode == "📈 Individual Asset":
        st.subheader("ASSET CONTROLS")
        coins = sorted(raw_df['coin'].unique())
        selected_coin = st.selectbox("Select Asset", coins, index=0)
        default_coin = selected_coin 
        time_range = st.select_slider("Timeframe", options=["1W", "1M", "3M", "6M", "YTD", "1Y", "ALL"], value="1Y")
        
        st.markdown("---")
        st.subheader("INDICATORS")
        show_ma = st.checkbox("MA Ribbons", value=True)
        show_bb = st.checkbox("Bollinger Bands", value=True)
        show_macd = st.checkbox("MACD Oscillator", value=False)
        chart_style = st.radio("Chart Type", ["Line", "Area", "Candles"], index=1)
        
    else:
        st.subheader("RISK PARAMETERS")
        risk_timeframe = st.radio("Calculation Period", ["30D", "90D", "1Y"], horizontal=True, index=1)
        st.info("Comparing all assets against Bitcoin benchmark.")
        selected_coin = "bitcoin" # Fallback

    # --- NEXUS AI INTEGRATION ---
    st.markdown("---")
    st.subheader("🤖Crypto AI")
    with st.expander("Ask Cortex...", expanded=True):
        ai_query = st.text_input("Query Market Data:", placeholder="e.g. Price of Bitcoin?")
        if ai_query:
            response = get_nexus_ai_response(ai_query, raw_df, default_coin)
            st.markdown(f"<div class='ai-box'><b>CORTEX:</b><br>{response}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='font-size: 12px; color: #9CA3AF;'>Ask about Prices, Volatility, or Trends.</div>", unsafe_allow_html=True)


# --- 5. Main Dashboard Logic ---

# Helper for Metric Cards
def render_card(label, value, delta=None, is_currency=False):
    if delta is not None:
        delta_cls = "positive" if delta >= 0 else "negative"
        delta_sign = "+" if delta >= 0 else ""
        delta_html = f'<div class="metric-delta {delta_cls}">{delta_sign}{delta:.2f}%</div>'
    else:
        delta_html = f'<div class="metric-delta" style="visibility:hidden">0.00%</div>'
    val_str = f"${value:,.2f}" if is_currency else f"{value:,.2f}"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{val_str}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

if view_mode == "📈 Individual Asset":
    df = process_single_asset(raw_df, selected_coin, time_range)
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # 1. Header
    c1, c2 = st.columns([2,1])
    with c1:
        st.markdown(f"<h1 style='font-size: 2.2rem; margin-bottom: 0;'>{selected_coin.upper()} <span style='color: #6B7280; font-size: 1.5rem; font-weight: 400;'>USD</span></h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #9CA3AF; margin-top: -5px; font-size: 0.9rem;'>High-Frequency Market Data • {latest['timestamp'].strftime('%d %b %Y %H:%M:%S UTC')}</p>", unsafe_allow_html=True)
    
    with c2:
        price_change = latest['price'] - prev['price']
        pct_change = (price_change / prev['price']) * 100
        color = "#34D399" if pct_change >= 0 else "#F87171"
        arrow = "▲" if pct_change >= 0 else "▼"
        st.markdown(f"""
        <div style="text-align: right; background: rgba(31, 41, 55, 0.6); padding: 15px; border-radius: 12px; border: 1px solid #374151;">
            <div style="font-size: 24px; font-weight: 800; color: #F9FAFB; letter-spacing: -1px;">${latest['price']:,.2f}</div>
            <div style="font-size: 14px; font-weight: 600; color: {color}; margin-top: 5px;">
                {arrow} {abs(price_change):.2f} ({pct_change:+.2f}%)
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 2. Metric Cards
    m1, m2, m3, m4 = st.columns(4)
    with m1: render_card("24h High", df[-7:]['price'].max(), is_currency=True)
    with m2: render_card("24h Low", df[-7:]['price'].min(), is_currency=True)
    with m3: render_card("Volatility (Ann.)", latest['Volatility'], delta=latest['Volatility'] - prev['Volatility'])
    with m4: render_card("RSI Strength", latest['RSI'], delta=latest['RSI'] - prev['RSI'])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 3. Tabs
    tabs = st.tabs(["📉 PRICE & VOLATILITY TREND", "📊 ANALYTICAL DEPTH", "📋 HISTORICAL DATA"])
    
    with tabs[0]:
        # --- SEPARATE GRAPHS ---
        
        # 1. Price Trend Graph
        st.markdown("### 📉 Price Trend")
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        
        fig_price = go.Figure()
        
        line_props = dict(color='#3B82F6', width=2)
        if chart_style == "Area":
            fig_price.add_trace(go.Scatter(x=df['timestamp'], y=df['price'], mode='lines', fill='tozeroy', 
                                     line=line_props, name='Price', fillcolor='rgba(59, 130, 246, 0.1)'))
        else:
             fig_price.add_trace(go.Scatter(x=df['timestamp'], y=df['price'], mode='lines', 
                                     line=line_props, name='Price'))

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
        st.plotly_chart(fig_price, use_container_width=True)
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
        st.plotly_chart(fig_vol, use_container_width=True)
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
            st.plotly_chart(fig_macd, use_container_width=True)
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
            st.plotly_chart(fig_perf, use_container_width=True)
            
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
            st.plotly_chart(fig_dist, use_container_width=True)

    with tabs[2]:
        st.dataframe(df.sort_values('timestamp', ascending=False), use_container_width=True, height=500)

else:
    # --- RISK COMPARISON VIEW ---
    st.title("⚖️ Risk Metrics Dashboard")
    st.caption(f"Live Analysis | Market Benchmark: Bitcoin | Period: {risk_timeframe}")
    
    risk_df = calculate_risk_profile(raw_df, risk_timeframe)
    rows_html = "".join([f"<tr><td><span style='color: #58A6FF; font-weight: 600;'>{row['Crypto']}</span></td><td>{row['Volatility']:.2f}%</td><td>{row['Return']:.2f}%</td><td>{row['Sharpe']:.2f}</td><td>{row['Beta']:.2f}</td><td style='color: #F87171;'>{row['VaR (95%)']:.2f}%</td></tr>" for _, row in risk_df.iterrows()])
    st.markdown(f"<table class='risk-table'><thead><tr><th>Crypto</th><th>Volatility (Ann.)</th><th>Return (Ann.)</th><th>Sharpe Ratio</th><th>Beta (vs BTC)</th><th>VaR (95%)</th></tr></thead><tbody>{rows_html}</tbody></table>", unsafe_allow_html=True)
    st.markdown("---")
    
    c_graph, c_info = st.columns([3, 1])
    with c_graph:
        st.subheader("Risk vs. Return Frontier")
        
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
        st.plotly_chart(fig_risk, use_container_width=True)
        
    with c_info:
        st.info("**Risk vs. Return Analysis**\n\nThe Efficient Frontier interpretation:\n\n*   **Top-Left**: Best (High Return, Low Risk)\n*   **Bottom-Right**: Worst (Low Return, High Risk)\n*   **Color**: Indicates Sharpe Ratio (Risk-Adjusted Return).")
