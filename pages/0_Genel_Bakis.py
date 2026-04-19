#!/usr/bin/env python3
"""
Johnny Genel Bakış Sayfası
Ana dashboard — 15 saniyede otomatik yenileme
"""
import streamlit as st
import time
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
