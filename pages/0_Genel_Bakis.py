#!/usr/bin/env python3
"""
Johnny Genel Bakış Sayfası
Ana dashboard — Sadece rakamlar, temiz layout
"""
import streamlit as st
import time
from datetime import datetime

st.set_page_config(
    page_title="📊 Johnny — Genel Bakış",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# AUTO-REFRESH: 15 saniye
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

current_time = time.time()
if current_time - st.session_state.last_refresh > 15:
    st.session_state.last_refresh = current_time
    st.rerun()

# Tema
st.markdown("""
<style>
    .stApp { 
        background: linear-gradient(135deg, #0a0e1a 0%, #0d1226 50%, #0a0e1a 100%);
        color: #e8eaf0; 
    }
    
    h1 { color: #4a9eff; text-shadow: 0 0 20px rgba(74, 158, 255, 0.3); }
    h2 { color: #8ba7d0; }
    
    .metric-box {
        background: linear-gradient(135deg, rgba(13, 18, 38, 0.8), rgba(26, 42, 74, 0.6));
        border: 2px solid rgba(74, 158, 255, 0.3);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(74, 158, 255, 0.1);
    }
    
    .metric-box:hover {
        border: 2px solid rgba(74, 158, 255, 0.6);
        box-shadow: 0 12px 40px rgba(74, 158, 255, 0.2);
    }
    
    .pos-card {
        background: linear-gradient(135deg, rgba(13, 18, 38, 0.9), rgba(26, 42, 74, 0.7));
        border: 2px solid rgba(74, 158, 255, 0.3);
        border-radius: 12px;
        padding: 25px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(74, 158, 255, 0.1);
        min-height: 280px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .pos-card:hover {
        border: 2px solid rgba(74, 158, 255, 0.6);
        box-shadow: 0 12px 40px rgba(74, 158, 255, 0.2);
        transform: translateY(-5px);
    }
    
    .pos-gain { border-top: 4px solid #00c864; }
    .pos-loss { border-top: 4px solid #ff4444; }
    .pos-flat { border-top: 4px solid #ffcc00; }
    
    .pos-symbol { font-size: 2rem; font-weight: bold; color: #4a9eff; }
    .pos-name { font-size: 0.85rem; color: #8ba7d0; margin-top: 5px; }
    
    .pos-row { margin: 12px 0; font-size: 0.9rem; }
    .pos-label { color: #8ba7d0; font-size: 0.75rem; }
    .pos-value { color: #e8eaf0; font-weight: bold; font-size: 1rem; }
    
    .pos-amount { font-size: 1.2rem; color: #4a9eff; font-weight: bold; margin: 10px 0; }
    
    .pos-pnl { margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(74, 158, 255, 0.2); }
    .pos-pnl-pct { font-size: 1.3rem; font-weight: bold; }
    .pos-pnl-usd { font-size: 1rem; font-weight: bold; margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

# Başlık
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown("# 📊 JOHNNY")
with col2:
    now = datetime.now().strftime("%H:%M:%S")
    st.caption(f"🔄 {now}")

st.divider()

# PORTFÖY ÖZETİ
st.subheader("💰 Portföy Özeti")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown("""
    <div class="metric-box">
    <p style="color: #8ba7d0; font-size: 0.8rem;">💵 Başlangıç</p>
    <p style="color: #4a9eff; font-size: 1.5rem; font-weight: bold;">$20,000</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-box">
    <p style="color: #8ba7d0; font-size: 0.8rem;">🎯 Hedef</p>
    <p style="color: #00c864; font-size: 1.5rem; font-weight: bold;">+50%</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-box">
    <p style="color: #8ba7d0; font-size: 0.8rem;">📈 Mevcut</p>
    <p style="color: #00c864; font-size: 1.5rem; font-weight: bold;">+28%</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="metric-box">
    <p style="color: #8ba7d0; font-size: 0.8rem;">📊 Hisse</p>
    <p style="color: #4a9eff; font-size: 1.5rem; font-weight: bold;">59</p>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown("""
    <div class="metric-box">
    <p style="color: #8ba7d0; font-size: 0.8rem;">⏰ Gün</p>
    <p style="color: #4a9eff; font-size: 1.5rem; font-weight: bold;">~90</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# AÇIK POZİSYONLAR (MOC — Market on Close Fiyatları)
st.subheader("📈 Açık Pozisyonlar")

# Mock data — MOC (Kapanış) fiyatları
positions_data = [
    {"symbol": "HOOD", "name": "Robinhood", "entry": 32.47, "moc": 35.00, "amount": 2000},
    {"symbol": "MSTR", "name": "Strategy Inc", "entry": 140.00, "moc": 166.52, "amount": 2500},
    {"symbol": "NVDA", "name": "NVIDIA", "entry": 850.00, "moc": 912.45, "amount": 1800},
    {"symbol": "PLTR", "name": "Palantir", "entry": 18.50, "moc": 34.56, "amount": 1500},
    {"symbol": "HUT", "name": "Hut 8 Corp", "entry": 12.50, "moc": 74.90, "amount": 1200},
    {"symbol": "INTC", "name": "Intel", "entry": 20.00, "moc": 68.50, "amount": 1400},
    {"symbol": "AMD", "name": "AMD", "entry": 125.00, "moc": 278.39, "amount": 1600},
    {"symbol": "PLUG", "name": "Plug Power", "entry": 1.10, "moc": 2.78, "amount": 900},
    {"symbol": "SERV", "name": "Serve Robotics", "entry": 10.00, "moc": 9.57, "amount": 500},
    {"symbol": "SOUN", "name": "SoundHound AI", "entry": 8.50, "moc": 8.08, "amount": 600},
    {"symbol": "RXRX", "name": "Recursion", "entry": 4.20, "moc": 3.78, "amount": 700},
    {"symbol": "APLD", "name": "Applied Digital", "entry": 28.00, "moc": 31.53, "amount": 1100},
    {"symbol": "AAPL", "name": "Apple", "entry": 202.00, "moc": 218.65, "amount": 2200},
    {"symbol": "MSFT", "name": "Microsoft", "entry": 377.00, "moc": 445.32, "amount": 1900},
    {"symbol": "GOOGL", "name": "Alphabet", "entry": 160.00, "moc": 178.92, "amount": 1700},
    {"symbol": "AMZN", "name": "Amazon", "entry": 185.00, "moc": 212.45, "amount": 2100},
    {"symbol": "META", "name": "Meta", "entry": 320.00, "moc": 498.23, "amount": 1300},
    {"symbol": "TSLA", "name": "Tesla", "entry": 228.00, "moc": 285.67, "amount": 1400},
    {"symbol": "SEDG", "name": "SolarEdge", "entry": 12.50, "moc": 38.30, "amount": 800},
    {"symbol": "ENPH", "name": "Enphase", "entry": 150.00, "moc": 95.34, "amount": 950},
]

# Toplam P&L hesapla
total_investment = sum([p["amount"] for p in positions_data])
total_pnl_usd = sum([p["amount"] * ((p["moc"] - p["entry"]) / p["entry"]) for p in positions_data])
total_pnl_pct = (total_pnl_usd / total_investment * 100) if total_investment > 0 else 0
winning = sum(1 for p in positions_data if ((p["moc"] - p["entry"]) / p["entry"]) > 0.005)
losing = sum(1 for p in positions_data if ((p["moc"] - p["entry"]) / p["entry"]) < -0.005)
flat = len(positions_data) - winning - losing

# Top bar
col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

with col1:
    st.markdown(f"<div class='metric-box'><p style='color: #8ba7d0; font-size: 0.75rem;'>💰 Toplam</p><p style='color: #4a9eff; font-size: 1.3rem; font-weight: bold;'>${total_investment:,.0f}</p></div>", unsafe_allow_html=True)

with col2:
    color = "#00c864" if total_pnl_usd >= 0 else "#ff4444"
    st.markdown(f"<div class='metric-box'><p style='color: #8ba7d0; font-size: 0.75rem;'>📊 P&L</p><p style='color: {color}; font-size: 1.3rem; font-weight: bold;'>${total_pnl_usd:+,.0f}</p></div>", unsafe_allow_html=True)

with col3:
    color = "#00c864" if total_pnl_pct >= 0 else "#ff4444"
    st.markdown(f"<div class='metric-box'><p style='color: #8ba7d0; font-size: 0.75rem;'>📈 %</p><p style='color: {color}; font-size: 1.3rem; font-weight: bold;'>{total_pnl_pct:+.1f}%</p></div>", unsafe_allow_html=True)

with col4:
    st.markdown(f"<div class='metric-box'><p style='color: #8ba7d0; font-size: 0.75rem;'>✅</p><p style='color: #00c864; font-size: 1.3rem; font-weight: bold;'>{winning}</p></div>", unsafe_allow_html=True)

with col5:
    st.markdown(f"<div class='metric-box'><p style='color: #8ba7d0; font-size: 0.75rem;'>❌</p><p style='color: #ff4444; font-size: 1.3rem; font-weight: bold;'>{losing}</p></div>", unsafe_allow_html=True)

with col6:
    st.markdown(f"<div class='metric-box'><p style='color: #8ba7d0; font-size: 0.75rem;'>🟡</p><p style='color: #ffcc00; font-size: 1.3rem; font-weight: bold;'>{flat}</p></div>", unsafe_allow_html=True)

with col7:
    st.markdown(f"<div class='metric-box'><p style='color: #8ba7d0; font-size: 0.75rem;'>📍</p><p style='color: #4a9eff; font-size: 1.3rem; font-weight: bold;'>{len(positions_data)}</p></div>", unsafe_allow_html=True)

st.divider()

# KARTLAR (4 sütun)
cols = st.columns(4)

for idx, pos in enumerate(positions_data):
    with cols[idx % 4]:
        pnl_pct = ((pos["moc"] - pos["entry"]) / pos["entry"]) * 100
        pnl_usd = pos["amount"] * ((pos["moc"] - pos["entry"]) / pos["entry"])
        
        # Renk belirle
        if pnl_pct > 0.5:
            pos_class = "pos-gain"
            color = "#00c864"
            emoji = "🟢"
        elif pnl_pct < -0.5:
            pos_class = "pos-loss"
            color = "#ff4444"
            emoji = "🔴"
        else:
            pos_class = "pos-flat"
            color = "#ffcc00"
            emoji = "🟡"
        
        st.markdown(f"""
        <div class="pos-card {pos_class}">
            <div>
                <div class="pos-symbol">{pos['symbol']} {emoji}</div>
                <div class="pos-name">{pos['name']}</div>
            </div>
            
            <div class="pos-row">
                <span class="pos-label">Entry</span><br>
                <span class="pos-value">${pos['entry']:.2f}</span>
            </div>
            <div class="pos-row">
                <span class="pos-label">MOC</span><br>
                <span class="pos-value">${pos['moc']:.2f}</span>
            </div>
            
            <div class="pos-amount">${pos['amount']:,.0f}</div>
            
            <div class="pos-pnl">
                <div class="pos-pnl-pct" style="color: {color};">{pnl_pct:+.1f}%</div>
                <div class="pos-pnl-usd" style="color: {color};">{pnl_usd:+,.0f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.divider()
st.caption("🔄 15 saniyede otomatik yenileme | MOC: Market on Close (Kapanış fiyatı)")
