import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json
import os

# --- DEPLOYMENT MODE ---
# Set this to False if you want to deploy on Streamlit Cloud (Direct Import Mode)
# Set to True if you are running locally with separate `uvicorn backend:app` (API Mode)
USE_SEPARATE_BACKEND = False 

if not USE_SEPARATE_BACKEND:
    # Direct import for deployment
    try:
        from backend import fetch_and_analyze_data
    except ImportError:
        st.error("Error importing backend module. Ensure 'backend.py' is in the same directory.")

# --- CONFIGURATION (Must be the first Streamlit command) ---
st.set_page_config(
    page_title="Crypto Risk Commander",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Base URL - update if backend is running elsewhere
BACKEND_URL = "http://127.0.0.1:8000"

# --- SESSION STATE INITIALIZATION ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
# A simple mock database for users.
if "users" not in st.session_state:
    st.session_state["users"] = {"admin": "1234"}
if "page" not in st.session_state:
    st.session_state["page"] = "login"

# --- CUSTOM CSS FOR MODERN LOOK ---
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .metric-card {
        background-color: #262730;
        border: 1px solid #41424b;
        padding: 15px;
        border-radius: 10px;
        color: white;
    }
    h1, h2, h3 {
        color: #fafafa;
    }
    div.stButton > button {
        width: 100%;
        background-color: #ff4b4b;
        color: white;
        font-weight: bold;
    }
    /* Style the login container */
    .login-container {
        padding: 2rem;
        background-color: #262730;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# --- AUTHENTICATION FUNCTIONS ---
def show_login():
    st.title("🔐 Login to Crypto Risk Commander")
    st.markdown("Please sign in to access professional risk analysis tools.")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="admin")
            password = st.text_input("Password", type="password", placeholder="1234")

            submit = st.form_submit_button("Sign In")

            if submit:
                # Direct check against session state users
                if username in st.session_state["users"] and st.session_state["users"][username] == password:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.success("Login Successful!")
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")

        st.markdown("---")
        if st.button("Create New Account"):
            st.session_state["page"] = "register"
            st.rerun()

        st.info("💡 **Demo Creds:** Username: `admin`, Password: `1234`")

def show_register():
    st.title("📝 Create Account")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("register_form"):
            new_user = st.text_input("Choose Username")
            new_pass = st.text_input("Choose Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")

            submit = st.form_submit_button("Register")

            if submit:
                if new_user in st.session_state["users"]:
                    st.error("Username already exists!")
                elif new_pass != confirm_pass:
                    st.error("Passwords do not match!")
                elif not new_user or not new_pass:
                    st.error("Please fill out all fields.")
                else:
                    st.session_state["users"][new_user] = new_pass
                    st.success("Account Created! Please Login.")
                    st.session_state["page"] = "login"
                    st.rerun()

        if st.button("Back to Login"):
            st.session_state["page"] = "login"
            st.rerun()

def get_manual_risk_level(price_change):
    if price_change > 15:
        return "EXTREME RISK ☢️", "#ff2b2b", "Catastrophic! Indicates a crash or major manipulation."
    elif price_change > 7:
        return "HIGH RISK 🔥", "#ff9f1c", "Significant movement. Typical for altcoins or news events."
    elif price_change > 3:
        return "MODERATE RISK ⚖️", "#fbd400", "Standard daily volatility for crypto."
    else:
        return "LOW RISK 🛡️", "#2ec4b6", "Very stable market conditions."

# --- DATA & ANALYSIS FUNCTIONS (Hybrid) ---
@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_market_analysis(coin_id, days):
    if USE_SEPARATE_BACKEND:
        # API Mode (Local development with separate Uvicorn server)
        try:
            response = requests.post(
                f"{BACKEND_URL}/analyze",
                json={"coin_id": coin_id, "days": days}
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 422:
                 st.error(f"Validation Error from Backend: {response.json()}")
                 return None
            else:
                st.error(f"Error from backend: {response.text}")
                return None
        except requests.exceptions.ConnectionError:
            st.error(f"Cannot connect to backend at {BACKEND_URL}. Is it running?")
            return None
        except Exception as e:
            st.error(f"An error occurred: {e}")
            return None
    else:
        # Direct Mode (Streamlit Cloud Deployment)
        try:
            return fetch_and_analyze_data(coin_id, days)
        except Exception as e:
            st.error(f"Error processing data locally: {e}")
            return None

# --- DASHBOARD LOGIC ---
def show_dashboard():
    # Sidebar - User Info & Logout
    st.sidebar.title(f"👤 {st.session_state['username']}")
    if st.sidebar.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        st.rerun()

    # Sidebar - Settings
    st.sidebar.header("🔍 Analysis Settings")
    available_coins = {
        "Bitcoin": "bitcoin",
        "Ethereum": "ethereum",
        "Solana": "solana",
        "Dogecoin": "dogecoin",
        "Cardano": "cardano",
        "Ripple": "ripple",
    }
    selected_coin_name = st.sidebar.selectbox("Select Cryptocurrency", list(available_coins.keys()))
    selected_coin_id = available_coins[selected_coin_name]

    timeframe_map = {"Last 30 Days": "30", "Last 90 Days": "90", "Last Year": "365"}
    selected_timeframe = st.sidebar.selectbox("Select Time Horizon", list(timeframe_map.keys()))
    days = timeframe_map[selected_timeframe]

    # Sidebar - Manual Simulator
    st.sidebar.markdown("---")
    st.sidebar.subheader("🛠️ Manual Scenario Simulator")
    manual_price_change = st.sidebar.number_input(
        "Enter Daily Price Change (%)", min_value=0.0, max_value=100.0, value=5.0, step=0.5
    )
    analyze_button = st.sidebar.button("💥 Analyze Risk Scenario")

    # --- MAIN CONTENT ---
    st.title(f"⚡ {selected_coin_name} Risk Analysis Dashboard")

    # 1. Manual Analysis Result
    if analyze_button:
        st.markdown("### 🧪 Manual Scenario Results")
        m_risk, m_color, m_msg = get_manual_risk_level(manual_price_change)

        st.markdown(f"""
        <div style="padding: 20px; border-radius: 10px; background-color: {m_color}22; border-left: 5px solid {m_color};">
            <h3 style="margin:0; color: {m_color};">{m_risk}</h3>
            <p style="margin-top: 10px; font-size: 1.1em;">{m_msg}</p>
        </div>
        """, unsafe_allow_html=True)
        st.divider()

    # 2. Real-time Analysis
    st.markdown(f"### 📊 Live Market Data: {selected_coin_name}")
    with st.spinner(f"Connecting to data source for {selected_coin_name}..."):
        data = get_market_analysis(selected_coin_id, days)

    if data:
        # Reconstruct DataFrame locally for plotting
        timestamps = pd.to_datetime(data["timestamps"]) # nanoseconds -> datetime
        
        # Create DataFrame directly from lists
        processed_df = pd.DataFrame({
            'date': timestamps,
            'price': data['prices'],
            'daily_return': data['daily_returns']
        })
        processed_df.set_index('date', inplace=True)
        # Ensure it is sorted by date
        processed_df.sort_index(inplace=True)
        
        current_price = data['current_price']
        vol = data['volatility']
        max_drawdown = data['max_drawdown']
        r_level = data['risk_level']
        r_color = data['risk_color']

        # KPIs
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Current Price", f"${current_price:,.2f}")
        c2.metric("Annualized Volatility", f"{vol:.1f}%")
        c3.metric("Max Drawdown", f"{max_drawdown:.1f}%")
        c4.markdown(f"""
            <div style="text-align: center; padding: 5px; border-radius: 5px; background-color: {r_color}33; border: 1px solid {r_color};">
                <h4 style="margin:0; color: {r_color};">{r_level}</h4>
            </div>
            """, unsafe_allow_html=True)

        # Charts
        processed_df['7D_MA'] = processed_df['price'].rolling(window=7).mean()

        st.subheader("Price Trend")
        fig_price = go.Figure()
        fig_price.add_trace(go.Scatter(x=processed_df.index, y=processed_df['price'], mode='lines', name='Price', line=dict(color='#00d4ff')))
        fig_price.add_trace(go.Scatter(x=processed_df.index, y=processed_df['7D_MA'], mode='lines', name='7-Day MA', line=dict(color='#ffab00', dash='dash')))
        fig_price.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=400)
        st.plotly_chart(fig_price, use_container_width=True)

        c_chart1, c_chart2 = st.columns(2)
        with c_chart1:
            st.caption("Daily Returns Distribution")
            fig_hist = px.histogram(processed_df, x="daily_return", nbins=40, color_discrete_sequence=['#7b2cbf'])
            fig_hist.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_hist, use_container_width=True)
        with c_chart2:
            st.caption("Rolling Volatility (Risk Intensity)")
            processed_df['rolling_vol'] = processed_df['daily_return'].rolling(window=14).std()
            fig_vol = px.area(processed_df, x=processed_df.index, y='rolling_vol', color_discrete_sequence=['#ff0054'])
            fig_vol.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_vol, use_container_width=True)

    else:
        st.error("⚠️ No data available or backend is unreachable.")

# --- APP FLOW CONTROLLER ---
if st.session_state["logged_in"]:
    show_dashboard()
else:
    if st.session_state["page"] == "register":
        show_register()
    else:
        show_login()
