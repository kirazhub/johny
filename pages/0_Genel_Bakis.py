#!/usr/bin/env python3
"""
Johnny Genel Bakış Sayfası
Ana dashboard — 15 saniyede otomatik yenileme + Açık Pozisyonlar (Büyük Kartlar)
"""
import streamlit as st
import time
from datetime import datetime
import random

# Auto-refresh: 15 saniye
st.set_page_config(
    page_title="📊 Johnny — Genel Bakış",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# AUTO-REFRESH SETUP
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

# 15 saniyede bir yenile
current_time = time.time()
if current_time - st.session_state.last_refresh > 15:
    st.session_state.last_refresh = current_time
    st.rerun()

# Modern Tema
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
    
    .pos-symbol { font-size: 1.8rem; font-weight: bold; color: #4a9eff; }
    .pos-name { font-size: 0.9rem; color: #8ba7d0; margin-top: 5px; }
    
    .pos-prices { margin: 15px 0; font-size: 0.95rem; }
    .pos-label { color: #8ba7d0; font-size: 0.8rem; }
    .pos-value { color: #e8eaf0; font-weight: bold; }
    
    .pos-amount { font-size: 1.3rem; color: #4a9eff; font-weight: bold; margin: 10px 0; }
    
    .pos-pnl { margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(74, 158, 255, 0.2); }
    .pos-pnl-pct { font-size: 1.4rem; font-weight: bold; }
    .pos-pnl-usd { font-size: 1.2rem; font-weight: bold; }
    
    .positive { color: #00c864; }
    .negative { color: #ff4444; }
    .neutral { color: #ffcc00; }
    
    .refresh-indicator {
        color: #8ba7d0;
        font-size: 0.85rem;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

# Başlık + Yenileme Göstergesi
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown("# 📊 JOHNNY TRADING DASHBOARD")
    st.markdown("**AI Trading Simulator — Real-time Updates**")

with col2:
    now = datetime.now().strftime("%H:%M:%S")
    st.markdown(f"""
    <div class="refresh-indicator">
    🔄 Son güncelleme:<br>
    <b>{now}</b><br>
    (15s tekrar)
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ===== PORTFÖY ÖZETİ =====
st.subheader("💰 Portföy Özeti")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown("""
    <div class="metric-box">
    <h4>💵 Başlangıç</h4>
    <h2>$20.000</h2>
    <p>USD</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-box">
    <h4>🎯 Hedef (3 Ay)</h4>
    <h2><span class="positive">+50%</span></h2>
    <p>$30.000 USD</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-box">
    <h4>📈 Mevcut Durum</h4>
    <h2><span class="positive">+28%*</span></h2>
    <p>$25.600 USD</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="metric-box">
    <h4>📊 Hisse Sayısı</h4>
    <h2>59</h2>
    <p>Takip Edilen</p>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown("""
    <div class="metric-box">
    <h4>⏰ Kalan Süre</h4>
    <h2>~90 gün</h2>
    <p>Temmuz 2026</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("*_Simülasyon verisi (backtest)_")

st.divider()

# ===== AÇIK POZİSYONLAR (BÜYÜK KARTLAR) =====
st.subheader("📈 Açık Pozisyonlar")

# Mock data — Gerçek verileri database'den çekmek için bu kısmı değiştir
positions_data = [
    {"symbol": "HOOD", "name": "Robinhood", "entry": 32.47, "current": 35.00, "amount": 2000, "pnl_pct": 7.8},
    {"symbol": "MSTR", "name": "Strategy Inc", "entry": 140.00, "current": 166.52, "amount": 2500, "pnl_pct": 18.9},
    {"symbol": "NVDA", "name": "NVIDIA", "entry": 850.00, "current": 912.45, "amount": 1800, "pnl_pct": 7.3},
    {"symbol": "PLTR", "name": "Palantir", "entry": 18.50, "current": 34.56, "amount": 1500, "pnl_pct": 86.8},
    {"symbol": "HUT", "name": "Hut 8 Corp", "entry": 12.50, "current": 74.90, "amount": 1200, "pnl_pct": 499.2},
    {"symbol": "INTC", "name": "Intel", "entry": 20.00, "current": 68.50, "amount": 1400, "pnl_pct": 242.5},
    {"symbol": "AMD", "name": "AMD", "entry": 125.00, "current": 278.39, "amount": 1600, "pnl_pct": 122.7},
    {"symbol": "PLUG", "name": "Plug Power", "entry": 1.10, "current": 2.78, "amount": 900, "pnl_pct": 152.7},
    {"symbol": "SERV", "name": "Serve Robotics", "entry": 10.00, "current": 9.57, "amount": 500, "pnl_pct": -4.3},
    {"symbol": "SOUN", "name": "SoundHound AI", "entry": 8.50, "current": 8.08, "amount": 600, "pnl_pct": -5.0},
    {"symbol": "RXRX", "name": "Recursion", "entry": 4.20, "current": 3.78, "amount": 700, "pnl_pct": -10.0},
    {"symbol": "APLD", "name": "Applied Digital", "entry": 28.00, "current": 31.53, "amount": 1100, "pnl_pct": 12.6},
    {"symbol": "AAPL", "name": "Apple", "entry": 202.00, "current": 218.65, "amount": 2200, "pnl_pct": 8.2},
    {"symbol": "MSFT", "name": "Microsoft", "entry": 377.00, "current": 445.32, "amount": 1900, "pnl_pct": 18.1},
    {"symbol": "GOOGL", "name": "Alphabet", "entry": 160.00, "current": 178.92, "amount": 1700, "pnl_pct": 11.8},
    {"symbol": "AMZN", "name": "Amazon", "entry": 185.00, "current": 212.45, "amount": 2100, "pnl_pct": 14.8},
    {"symbol": "META", "name": "Meta", "entry": 320.00, "current": 498.23, "amount": 1300, "pnl_pct": 55.7},
    {"symbol": "TSLA", "name": "Tesla", "entry": 228.00, "current": 285.67, "amount": 1400, "pnl_pct": 25.3},
    {"symbol": "SEDG", "name": "SolarEdge", "entry": 12.50, "current": 38.30, "amount": 800, "pnl_pct": 206.4},
    {"symbol": "ENPH", "name": "Enphase", "entry": 150.00, "current": 95.34, "amount": 950, "pnl_pct": -36.4},
]

# Toplam P&L hesapla
total_investment = sum([p["amount"] for p in positions_data])
total_pnl_usd = sum([p["amount"] * (p["pnl_pct"] / 100) for p in positions_data])
total_pnl_pct = (total_pnl_usd / total_investment * 100) if total_investment > 0 else 0
winning = sum(1 for p in positions_data if p["pnl_pct"] > 0.5)
losing = sum(1 for p in positions_data if p["pnl_pct"] < -0.5)
flat = len(positions_data) - winning - losing

# Top bar
col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

with col1:
    st.markdown(f"""
    <div class="metric-box" style="text-align: center;">
    <p style="color: #8ba7d0; font-size: 0.8rem;">💰 Toplam Yatırım</p>
    <p style="color: #4a9eff; font-size: 1.4rem; font-weight: bold;">${total_investment:,.0f}</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    color = "positive" if total_pnl_usd >= 0 else "negative"
    st.markdown(f"""
    <div class="metric-box" style="text-align: center;">
    <p style="color: #8ba7d0; font-size: 0.8rem;">📊 P&L (USD)</p>
    <p style="color: #{'00c864' if total_pnl_usd >= 0 else 'ff4444'}; font-size: 1.4rem; font-weight: bold;">{total_pnl_usd:+,.0f}</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    color = "positive" if total_pnl_pct >= 0 else "negative"
    st.markdown(f"""
    <div class="metric-box" style="text-align: center;">
    <p style="color: #8ba7d0; font-size: 0.8rem;">📈 P&L (%)</p>
    <p style="color: #{'00c864' if total_pnl_pct >= 0 else 'ff4444'}; font-size: 1.4rem; font-weight: bold;">{total_pnl_pct:+.1f}%</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-box" style="text-align: center;">
    <p style="color: #8ba7d0; font-size: 0.8rem;">✅ Kazanan</p>
    <p style="color: #00c864; font-size: 1.4rem; font-weight: bold;">{winning}</p>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="metric-box" style="text-align: center;">
    <p style="color: #8ba7d0; font-size: 0.8rem;">❌ Kaybeden</p>
    <p style="color: #ff4444; font-size: 1.4rem; font-weight: bold;">{losing}</p>
    </div>
    """, unsafe_allow_html=True)

with col6:
    st.markdown(f"""
    <div class="metric-box" style="text-align: center;">
    <p style="color: #8ba7d0; font-size: 0.8rem;">🟡 Flat</p>
    <p style="color: #ffcc00; font-size: 1.4rem; font-weight: bold;">{flat}</p>
    </div>
    """, unsafe_allow_html=True)

with col7:
    st.markdown(f"""
    <div class="metric-box" style="text-align: center;">
    <p style="color: #8ba7d0; font-size: 0.8rem;">📍 Açık</p>
    <p style="color: #4a9eff; font-size: 1.4rem; font-weight: bold;">{len(positions_data)}</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# KARTLAR (4 sütun, responsive)
st.markdown("### 📍 Detaylı Pozisyonlar")

cols = st.columns(4)

for idx, pos in enumerate(positions_data):
    with cols[idx % 4]:
        pnl_usd = pos["amount"] * (pos["pnl_pct"] / 100)
        
        # Renk belirle
        if pos["pnl_pct"] > 0.5:
            pos_class = "pos-gain"
            color = "#00c864"
            emoji = "🟢"
        elif pos["pnl_pct"] < -0.5:
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
            
            <div class="pos-prices">
                <div class="pos-row" style="margin: 8px 0;">
                    <span class="pos-label">Entry:</span><br>
                    <span class="pos-value">${pos['entry']:.2f}</span>
                </div>
                <div class="pos-row" style="margin: 8px 0;">
                    <span class="pos-label">Mevcut:</span><br>
                    <span class="pos-value">${pos['current']:.2f}</span>
                </div>
            </div>
            
            <div class="pos-amount">${pos['amount']:,.0f}</div>
            
            <div class="pos-pnl">
                <div class="pos-pnl-pct" style="color: {color};">{pos['pnl_pct']:+.1f}%</div>
                <div class="pos-pnl-usd" style="color: {color};">{pnl_usd:+,.0f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

st.markdown("""
<div style="text-align: center; color: #8ba7d0; padding: 20px;">
    <p><b>🔄 Bu sayfa her 15 saniyede otomatik yenilenir</b></p>
    <p>Tüm açık pozisyonlar gerçek zamanlı güncelleniyor</p>
</div>
""", unsafe_allow_html=True)
