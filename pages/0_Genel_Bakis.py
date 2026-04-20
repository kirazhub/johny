#!/usr/bin/env python3
import streamlit as st
import time
from datetime import datetime

st.set_page_config(page_title="📊 Johnny", page_icon="📊", layout="wide")

# Auto-refresh
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > 15:
    st.session_state.last_refresh = time.time()
    st.rerun()

# BAŞLIK
st.title("📊 JOHNNY")
now = datetime.now().strftime("%H:%M:%S")
st.caption(f"🔄 {now}")

st.divider()

# PORTFÖY ÖZETİ
st.subheader("💰 Portföy Özeti")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("💵 Başlangıç", "$20,000")
with col2:
    st.metric("🎯 Hedef", "+50%")
with col3:
    st.metric("📈 Mevcut", "+28%")
with col4:
    st.metric("📊 Hisse", "59")
with col5:
    st.metric("⏰ Gün", "~90")

st.divider()

# AÇIK POZİSYONLAR
st.subheader("📈 Açık Pozisyonlar")

# Veri
positions = [
    {"sym": "HOOD", "name": "Robinhood", "entry": 32.47, "moc": 35.00, "amt": 2000},
    {"sym": "MSTR", "name": "Strategy Inc", "entry": 140.00, "moc": 166.52, "amt": 2500},
    {"sym": "NVDA", "name": "NVIDIA", "entry": 850.00, "moc": 912.45, "amt": 1800},
    {"sym": "PLTR", "name": "Palantir", "entry": 18.50, "moc": 34.56, "amt": 1500},
    {"sym": "HUT", "name": "Hut 8 Corp", "entry": 12.50, "moc": 74.90, "amt": 1200},
    {"sym": "INTC", "name": "Intel", "entry": 20.00, "moc": 68.50, "amt": 1400},
    {"sym": "AMD", "name": "AMD", "entry": 125.00, "moc": 278.39, "amt": 1600},
    {"sym": "PLUG", "name": "Plug Power", "entry": 1.10, "moc": 2.78, "amt": 900},
    {"sym": "SERV", "name": "Serve Robotics", "entry": 10.00, "moc": 9.57, "amt": 500},
    {"sym": "SOUN", "name": "SoundHound AI", "entry": 8.50, "moc": 8.08, "amt": 600},
    {"sym": "RXRX", "name": "Recursion", "entry": 4.20, "moc": 3.78, "amt": 700},
    {"sym": "APLD", "name": "Applied Digital", "entry": 28.00, "moc": 31.53, "amt": 1100},
    {"sym": "AAPL", "name": "Apple", "entry": 202.00, "moc": 218.65, "amt": 2200},
    {"sym": "MSFT", "name": "Microsoft", "entry": 377.00, "moc": 445.32, "amt": 1900},
    {"sym": "GOOGL", "name": "Alphabet", "entry": 160.00, "moc": 178.92, "amt": 1700},
    {"sym": "AMZN", "name": "Amazon", "entry": 185.00, "moc": 212.45, "amt": 2100},
    {"sym": "META", "name": "Meta", "entry": 320.00, "moc": 498.23, "amt": 1300},
    {"sym": "TSLA", "name": "Tesla", "entry": 228.00, "moc": 285.67, "amt": 1400},
    {"sym": "SEDG", "name": "SolarEdge", "entry": 12.50, "moc": 38.30, "amt": 800},
    {"sym": "ENPH", "name": "Enphase", "entry": 150.00, "moc": 95.34, "amt": 950},
]

# Hesapla
total_amt = sum(p["amt"] for p in positions)
total_pnl = sum(p["amt"] * ((p["moc"] - p["entry"]) / p["entry"]) for p in positions)
total_pct = (total_pnl / total_amt * 100) if total_amt > 0 else 0
win = sum(1 for p in positions if ((p["moc"] - p["entry"]) / p["entry"]) > 0.005)
lose = sum(1 for p in positions if ((p["moc"] - p["entry"]) / p["entry"]) < -0.005)
flat = len(positions) - win - lose

# Top bar
col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
with col1:
    st.metric("💰 Toplam", f"${total_amt:,.0f}")
with col2:
    if total_pnl >= 0:
        st.metric("📊 P&L", f"${total_pnl:+,.0f}", delta=f"+${abs(total_pnl):.0f}")
    else:
        st.metric("📊 P&L", f"${total_pnl:+,.0f}", delta=f"-${abs(total_pnl):.0f}")
with col3:
    if total_pct >= 0:
        st.metric("📈 %", f"{total_pct:+.1f}%", delta=f"+{total_pct:.1f}%")
    else:
        st.metric("📈 %", f"{total_pct:+.1f}%", delta=f"{total_pct:.1f}%")
with col4:
    st.metric("✅ Kazanan", win)
with col5:
    st.metric("❌ Kaybeden", lose)
with col6:
    st.metric("🟡 Flat", flat)
with col7:
    st.metric("📍 Açık", len(positions))

st.divider()

# KARTLAR
cols = st.columns(4)
for idx, p in enumerate(positions):
    pnl_pct = ((p["moc"] - p["entry"]) / p["entry"]) * 100
    pnl_usd = p["amt"] * ((p["moc"] - p["entry"]) / p["entry"])
    
    with cols[idx % 4]:
        # Renk belirle
        if pnl_pct > 0.5:
            emoji = "🟢"
            color = "green"
        elif pnl_pct < -0.5:
            emoji = "🔴"
            color = "red"
        else:
            emoji = "🟡"
            color = "gray"
        
        st.write(f"### {p['sym']} {emoji}")
        st.write(f"*{p['name']}*")
        st.write(f"Entry: ${p['entry']:.2f}")
        st.write(f"MOC: ${p['moc']:.2f}")
        st.write(f"Pos: ${p['amt']:,.0f}")
        
        # P&L - Renkli
        if pnl_pct >= 0:
            st.success(f"**+{pnl_pct:.1f}%** | **+${pnl_usd:,.0f}**")
        else:
            st.error(f"**{pnl_pct:.1f}%** | **-${abs(pnl_usd):,.0f}**")

st.divider()
st.caption("🔄 15 saniye refresh | MOC: Kapanış Fiyat | 🟢 Yeşil=Kar | 🔴 Kırmızı=Zarar")
