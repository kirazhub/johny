#!/usr/bin/env python3
"""
Johnny Genel Bakış Sayfası
Ana dashboard — 15 saniyede otomatik yenileme
"""
import streamlit as st
import time
import sqlite3
import os
from datetime import datetime

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

# ===== AÇIK POZİSYONLAR =====
st.subheader("📈 Açık Pozisyonlar")

# CSS for position cards
st.markdown("""
<style>
    .positions-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 12px;
        margin: 16px 0;
    }
    @media (max-width: 1200px) { .positions-grid { grid-template-columns: repeat(4, 1fr); } }
    @media (max-width: 900px)  { .positions-grid { grid-template-columns: repeat(3, 1fr); } }
    @media (max-width: 600px)  { .positions-grid { grid-template-columns: repeat(2, 1fr); } }
    @media (max-width: 380px)  { .positions-grid { grid-template-columns: 1fr; } }

    .pos-card {
        background: linear-gradient(145deg, rgba(13,18,38,0.9), rgba(20,32,64,0.7));
        border-radius: 14px;
        padding: 14px 12px;
        min-height: 250px;
        max-width: 200px;
        width: 100%;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: transform 0.2s, box-shadow 0.2s;
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }
    .pos-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 32px rgba(74,158,255,0.25);
    }
    .pos-card.gain  { border: 2px solid rgba(0,200,100,0.5); }
    .pos-card.loss  { border: 2px solid rgba(255,68,68,0.5); }
    .pos-card.flat  { border: 2px solid rgba(255,204,0,0.5); }

    .pos-card.gain::before  { content:''; position:absolute; top:0; left:0; right:0; height:3px; background:linear-gradient(90deg,#00c864,#00ff8a); }
    .pos-card.loss::before  { content:''; position:absolute; top:0; left:0; right:0; height:3px; background:linear-gradient(90deg,#ff4444,#ff8888); }
    .pos-card.flat::before  { content:''; position:absolute; top:0; left:0; right:0; height:3px; background:linear-gradient(90deg,#ffcc00,#ffe066); }

    .pos-symbol { font-size: 1.15rem; font-weight: 800; letter-spacing: 0.5px; }
    .pos-name   { font-size: 0.7rem;  color: #8ba7d0; margin-bottom: 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .pos-row    { display: flex; justify-content: space-between; font-size: 0.73rem; margin: 2px 0; }
    .pos-label  { color: #8ba7d0; }
    .pos-pnl-pct { font-size: 1.05rem; font-weight: 700; text-align: center; margin-top: 8px; }
    .pos-pnl-usd { font-size: 0.8rem;  text-align: center; margin-top: 2px; }

    .clr-gain { color: #00c864; }
    .clr-loss { color: #ff4444; }
    .clr-flat { color: #ffcc00; }

    .total-pnl-bar {
        background: linear-gradient(135deg, rgba(13,18,38,0.9), rgba(26,42,74,0.6));
        border-radius: 14px;
        padding: 18px 28px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 20px;
        flex-wrap: wrap;
        margin-bottom: 16px;
        border: 1px solid rgba(74,158,255,0.2);
    }
    .total-pnl-item { text-align: center; }
    .total-pnl-label { font-size: 0.78rem; color: #8ba7d0; margin-bottom: 2px; }
    .total-pnl-value { font-size: 1.35rem; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

# ---- Veri: DB'den al, yoksa mock kullan ----
def load_open_positions():
    """Load open positions from DB or return mock data."""
    DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'johnny.db')
    mock_positions = [
        {"symbol": "HOOD",  "name": "Robinhood Markets",      "entry": 28.40, "current": 90.75,  "position_usd": 2000},
        {"symbol": "MSTR",  "name": "Strategy Inc",           "entry": 140.00,"current": 166.52, "position_usd": 2500},
        {"symbol": "SERV",  "name": "Serve Robotics",         "entry": 8.50,  "current": 9.57,   "position_usd": 500},
        {"symbol": "SOUN",  "name": "SoundHound AI",          "entry": 7.20,  "current": 8.08,   "position_usd": 600},
        {"symbol": "IONQ",  "name": "IonQ Inc",               "entry": 39.50, "current": 46.09,  "position_usd": 800},
        {"symbol": "PLTR",  "name": "Palantir Technologies",  "entry": 145.00,"current": 146.39, "position_usd": 1500},
        {"symbol": "NVDA",  "name": "NVIDIA Corporation",     "entry": 198.00,"current": 201.68, "position_usd": 2000},
        {"symbol": "AMD",   "name": "Advanced Micro Devices", "entry": 268.00,"current": 278.39, "position_usd": 1200},
        {"symbol": "RXRX",  "name": "Recursion Pharma",       "entry": 4.20,  "current": 3.78,   "position_usd": 300},
        {"symbol": "APLD",  "name": "Applied Digital",        "entry": 30.00, "current": 31.53,  "position_usd": 700},
        {"symbol": "QUBT",  "name": "Quantum Computing",      "entry": 8.30,  "current": 9.57,   "position_usd": 400},
        {"symbol": "RGTI",  "name": "Rigetti Computing",      "entry": 22.00, "current": 19.81,  "position_usd": 350},
        {"symbol": "RKLB",  "name": "Rocket Lab",             "entry": 80.00, "current": 84.80,  "position_usd": 900},
        {"symbol": "TSM",   "name": "Taiwan Semiconductor",   "entry": 365.00,"current": 370.50, "position_usd": 1800},
        {"symbol": "CRWD",  "name": "CrowdStrike Holdings",   "entry": 420.00,"current": 423.95, "position_usd": 1000},
        {"symbol": "APP",   "name": "AppLovin Corporation",   "entry": 452.00,"current": 477.20, "position_usd": 800},
        {"symbol": "SMCI",  "name": "Super Micro Computer",   "entry": 31.00, "current": 28.56,  "position_usd": 250},
        {"symbol": "LUNR",  "name": "Intuitive Machines",     "entry": 24.00, "current": 27.58,  "position_usd": 400},
        {"symbol": "CAVA",  "name": "CAVA Group",             "entry": 89.00, "current": 94.78,  "position_usd": 600},
        {"symbol": "ARM",   "name": "Arm Holdings",           "entry": 162.00,"current": 166.73, "position_usd": 500},
    ]
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT sembol, sirket_adi, guncel_fiyat, entry_point FROM moonshot")
        rows = cursor.fetchall()
        conn.close()
        if rows:
            # Merge DB current prices into mock positions
            db_prices = {r[0]: r[2] for r in rows}
            for pos in mock_positions:
                if pos["symbol"] in db_prices:
                    pos["current"] = db_prices[pos["symbol"]]
    except Exception:
        pass
    return mock_positions

positions = load_open_positions()

# Calculate P&L for each position
def calc_pnl(pos):
    pnl_pct = (pos["current"] - pos["entry"]) / pos["entry"] * 100
    pnl_usd = pos["position_usd"] * pnl_pct / 100
    return pnl_pct, pnl_usd

# Total P&L
total_invested = sum(p["position_usd"] for p in positions)
total_pnl_usd  = sum(calc_pnl(p)[1] for p in positions)
total_pnl_pct  = total_pnl_usd / total_invested * 100
winner_count   = sum(1 for p in positions if calc_pnl(p)[0] > 0.5)
loser_count    = sum(1 for p in positions if calc_pnl(p)[0] < -0.5)
flat_count     = len(positions) - winner_count - loser_count

tpnl_color = "clr-gain" if total_pnl_pct >= 0 else "clr-loss"
tpnl_sign  = "+" if total_pnl_pct >= 0 else ""

# Total P&L Bar
st.markdown(f"""
<div class="total-pnl-bar">
    <div class="total-pnl-item">
        <div class="total-pnl-label">💰 Toplam Yatırım</div>
        <div class="total-pnl-value">${total_invested:,.0f}</div>
    </div>
    <div class="total-pnl-item">
        <div class="total-pnl-label">📊 Toplam P&L (USD)</div>
        <div class="total-pnl-value {tpnl_color}">{tpnl_sign}${total_pnl_usd:,.0f}</div>
    </div>
    <div class="total-pnl-item">
        <div class="total-pnl-label">📈 Toplam P&L (%)</div>
        <div class="total-pnl-value {tpnl_color}">{tpnl_sign}{total_pnl_pct:.1f}%</div>
    </div>
    <div class="total-pnl-item">
        <div class="total-pnl-label">✅ Kazanan</div>
        <div class="total-pnl-value clr-gain">{winner_count}</div>
    </div>
    <div class="total-pnl-item">
        <div class="total-pnl-label">❌ Kaybeden</div>
        <div class="total-pnl-value clr-loss">{loser_count}</div>
    </div>
    <div class="total-pnl-item">
        <div class="total-pnl-label">➖ Flat</div>
        <div class="total-pnl-value clr-flat">{flat_count}</div>
    </div>
    <div class="total-pnl-item">
        <div class="total-pnl-label">📌 Açık Pozisyon</div>
        <div class="total-pnl-value">{len(positions)}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Build card HTML for all positions
def position_card_html(pos):
    pnl_pct, pnl_usd = calc_pnl(pos)
    if pnl_pct > 0.5:
        card_cls, clr, emoji = "gain", "clr-gain", "🟢"
        sign = "+"
    elif pnl_pct < -0.5:
        card_cls, clr, emoji = "loss", "clr-loss", "🔴"
        sign = ""
    else:
        card_cls, clr, emoji = "flat", "clr-flat", "🟡"
        sign = "+" if pnl_pct >= 0 else ""

    pos_label = f"${pos['position_usd']:,.0f}"
    entry_str   = f"${pos['entry']:,.2f}"
    current_str = f"${pos['current']:,.2f}"
    pnl_pct_str = f"{sign}{pnl_pct:.1f}%"
    pnl_usd_str = f"{sign}${abs(pnl_usd):,.0f}"

    tooltip = (
        f"Sembol: {pos['symbol']} | "
        f"Entry: {entry_str} | Current: {current_str} | "
        f"Pozisyon: {pos_label} | P&L: {pnl_pct_str} ({pnl_usd_str})"
    )

    return f"""
    <div class="pos-card {card_cls}" title="{tooltip}">
        <div>
            <div class="pos-symbol">{pos['symbol']} {emoji}</div>
            <div class="pos-name">{pos['name']}</div>
            <div class="pos-row"><span class="pos-label">Entry</span><span>{entry_str}</span></div>
            <div class="pos-row"><span class="pos-label">Mevcut</span><span>{current_str}</span></div>
            <div class="pos-row"><span class="pos-label">Pozisyon</span><span>{pos_label}</span></div>
        </div>
        <div>
            <div class="pos-pnl-pct {clr}">{pnl_pct_str}</div>
            <div class="pos-pnl-usd {clr}">{pnl_usd_str}</div>
        </div>
    </div>
    """

cards_html = "".join(position_card_html(p) for p in positions)
st.markdown(f'<div class="positions-grid">{cards_html}</div>', unsafe_allow_html=True)

st.caption(f"📌 Toplam {len(positions)} açık pozisyon gösteriliyor · Simülasyon/Mock verisi · Son güncelleme: {datetime.now().strftime('%H:%M:%S')}")

st.divider()

# ===== PORTFÖY DAĞILIMI =====
st.subheader("📋 Portföy Dağılımı")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### Kategori Tahsisi
    
    | Kategori | Yüzde | Miktar |
    |----------|------|--------|
    | 🔗 Blockchain | 25% | 5.000 USD |
    | 💻 Mega Cap | 30% | 6.000 USD |
    | 🤖 YZ & Tech | 25% | 5.000 USD |
    | ⚡ Enerji | 15% | 3.000 USD |
    | 🚀 Moonshot | 5% | 1.000 USD |
    | **TOPLAM** | **100%** | **20.000 USD** |
    """)

with col2:
    st.markdown("""
    ### Top 5 Hisse (Güncel)
    
    | Hisse | Fiyat | 1Y Getiri |
    |-------|-------|----------|
    | 🚀 HUT | $74.90 | +603% |
    | 💻 INTC | $68.50 | +263% |
    | ⚡ PLUG | $2.78 | +251% |
    | 🤖 AMD | $278.39 | +225% |
    | ⚡ SEDG | $38.30 | +216% |
    """)

st.divider()

# ===== İSTATİSTİKLER =====
st.subheader("📊 İstatistikler")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Ortalama Getiri (1Y)", "+87.3%", "+3.2%")

with col2:
    st.metric("Kazanan Hisse", "32/39", "+2")

with col3:
    st.metric("Kaybeden Hisse", "6/39", "-1")

with col4:
    st.metric("Risk Seviyesi", "Yüksek", "↔️")

st.divider()

# ===== STRATEJY NOTLARI =====
st.subheader("🎯 Strateji Notları")

st.info("""
### Johnny'nin 3 Ay Planı

**Nisan (Ay 1):** +12%
- HOOD, TEM kademeli alım başlangıcı
- Moonshot: SERV, MSTR pozisyon açılması
- Blockchain: HUT, MSTR, COIN güçlendirilmesi

**Mayıs (Ay 2):** +14.5% (Toplam +26.5%)
- Moonshot: SOUN, RXRX, APLD alım
- YZ & Tech: AMD, INTC %50 kazançta kısmi sat
- Portfolio rebalancing

**Haziran (Ay 3):** +15% (Toplam +41.5%)
- Moonshot: LUNR, IONQ teknik sinyal bekleme
- Enerji sektörü takibi (PLUG, SEDG)
- Volatilite ve risk yönetimi

**Temmuz (Bitiş):** +8.5% (Toplam +50%)
- Final push +50% hedefine
- Moonshot: Tüm pozisyonlar kapat (3 ay kural)
- Kar al ve yeni dönem planlaması

### Uyarılar ⚠️

- **Agresif Hedef:** +50 / 3 ay çok risk yüksek
- **Moonshot Riski:** %100 kaybetme ihtimali
- **Market Downturn:** Tüm hedefler reset olabilir
- **Komisyon:** Sık trading = %15 eroyon riski
""")

st.divider()

# ===== SAYFA LİNKLERİ =====
st.subheader("📖 Diğer Sayfalar")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 📌 Ana Sayfalar
    - 🔍 **Araştırmalar** — 39 hissenin tamamı
    - 📰 **Bilgilendirme** — Okuyabileceğin format
    - ⭐ **Özel Tavsiyeler** — HOOD + TEM
    - 🚀 **Moonshot** — 20 high-upside hisse
    """)

with col2:
    st.markdown("""
    ### 📊 Veri Kaynakları
    - SQLite Database (johnny.db)
    - FastAPI Server (port 8000)
    - Streamlit Cache (1 saat TTL)
    - Google News RSS
    """)

with col3:
    st.markdown("""
    ### 🔧 Teknoloji
    - Python + Streamlit
    - YFinance (veri)
    - SQLite (database)
    - FastAPI (API)
    """)

st.divider()

st.markdown("""
<div style="text-align: center; color: #8ba7d0; padding: 20px;">
    <p><b>🔄 Bu sayfa her 15 saniyede otomatik yenilenir</b></p>
    <p>Son güncelleme: {} — Sonraki: {}s</p>
</div>
""".format(
    datetime.now().strftime("%H:%M:%S"),
    int(15 - (time.time() - st.session_state.last_refresh))
), unsafe_allow_html=True)
