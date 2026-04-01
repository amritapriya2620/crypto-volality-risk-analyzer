import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- Configuration ---
st.set_page_config(page_title="Crypto Insights Pro", layout="wide", page_icon="🪙")

# --- Custom Styling ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@300;400;600&display=swap');
    
    .main {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
    }
    
    .stMetric {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: transform 0.3s ease;
    }
    
    .stMetric:hover {
        transform: translateY(-5px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif;
        letter-spacing: 2px;
        color: #00d2ff;
    }
    
    .sidebar .sidebar-content {
        background: rgba(0, 0, 0, 0.5);
    }
    
    .stButton>button {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(0, 210, 255, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.title("🪙 Crypto Insights Pro")
    st.markdown("#### Real-time Market Intelligence & Trend Analysis")
with col_h2:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# --- Load Data ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('milestone 1/crypto_data.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception:
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.error("🚨 System Alert: Data feed is currently offline. Please run the acquisition module.")
else:
    # --- Sidebar ---
    st.sidebar.image("https://www.cryptocompare.com/media/37746251/bitcoin.png", width=100) # Optional: generic crypto icon
    st.sidebar.header("🛡️ Control Center")
    
    all_coins = sorted(df['coin'].unique())
    selected_coins = st.sidebar.multiselect(
        "Select Assets", 
        all_coins, 
        default=all_coins[:3] if len(all_coins) >= 3 else all_coins
    )
    
    range_options = ["24h", "7d", "30d", "90d", "1y", "All Time"]
    selected_range = st.sidebar.select_slider("Time Horizon", options=range_options, value="30d")
    
    if selected_coins:
        # Filter by coin
        filtered_df = df[df['coin'].isin(selected_coins)]
        
        # Filter by time range
        max_date = df['timestamp'].max()
        if selected_range == "24h": start_date = max_date - timedelta(days=1)
        elif selected_range == "7d": start_date = max_date - timedelta(days=7)
        elif selected_range == "30d": start_date = max_date - timedelta(days=30)
        elif selected_range == "90d": start_date = max_date - timedelta(days=90)
        elif selected_range == "1y": start_date = max_date - timedelta(days=365)
        else: start_date = df['timestamp'].min()
        
        filtered_df = filtered_df[filtered_df['timestamp'] >= start_date]

        # --- Metrics ---
        st.subheader("🧊 Market Snapshot")
        metric_cols = st.columns(len(selected_coins) if len(selected_coins) <= 4 else 4)
        
        for i, coin in enumerate(selected_coins):
            coin_hist = df[df['coin'] == coin].sort_values('timestamp')
            if not coin_hist.empty:
                latest = coin_hist.iloc[-1]
                prev = coin_hist.iloc[-2] if len(coin_hist) > 1 else latest
                
                change = ((latest['price'] - prev['price']) / prev['price']) * 100
                
                with metric_cols[i % 4]:
                    st.metric(
                        label=coin.upper(),
                        value=f"${latest['price']:,.2f}",
                        delta=f"{change:.2f}%"
                    )

        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- Charts ---
        col_c1, col_c2 = st.columns([2, 1])
        
        with col_c1:
            st.subheader("📈 Performance Trajectory")
            fig = px.line(
                filtered_df, 
                x='timestamp', 
                y='price', 
                color='coin',
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#e0e0e0"),
                hovermode="x unified",
                margin=dict(l=0, r=0, b=0, t=40)
            )
            fig.update_xaxes(showgrid=False, zeroline=False)
            fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
            st.plotly_chart(fig, use_container_width=True)
            
        with col_c2:
            st.subheader("📊 Market Dominance")
            latest_prices = filtered_df.sort_values('timestamp').groupby('coin').tail(1)
            fig_pie = px.pie(
                latest_prices, 
                values='price', 
                names='coin',
                hole=0.6,
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, b=0, t=40),
                showlegend=False
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        # --- Data Tabs ---
        st.markdown("<br>", unsafe_allow_html=True)
        tab_list, tab_stats = st.tabs(["📋 Detailed Feed", "📊 Statistics"])
        
        with tab_list:
            st.dataframe(
                filtered_df.sort_values('timestamp', ascending=False),
                use_container_width=True,
                column_config={
                    "price": st.column_config.NumberColumn(format="$%.4f"),
                    "timestamp": st.column_config.DatetimeColumn(format="D MMM YYYY, HH:mm")
                }
            )
            
        with tab_stats:
            stats_df = filtered_df.groupby('coin')['price'].agg(['mean', 'max', 'min', 'std']).reset_index()
            st.table(stats_df)
    else:
        st.info("💡 Pro Tip: Use the Sidebar to select assets for analysis.")
