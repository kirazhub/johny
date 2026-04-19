#!/usr/bin/env python3
"""
Johnny Genel Bakış Sayfası
Tüm Tema Hisseleri, İstatistikler, Portföy Özeti
"""
import streamlit as st
import pandas as pd
import json

st.set_page_config(
    page_title="🇺🇸 Johnny — Genel Bakış",
    page_icon="🇺🇸",
    layout="wide"
)

# Tema
st.markdown("""
<style>
    .stApp { background-color: #0a0e1a; color: #e8eaf0; }
    h1 { color: #4a9eff; }
    h2, h3 { color: #8ba7d0; }
    .stMetric { background-color: #111827; border: 1px solid #1e3a5f; border-radius: 8px; }
    .hero-header {
        background: linear-gradient(135deg, #0d1f3c 0%, #1a3a6e 50%, #0d1f3c 100%);
        border: 1px solid #2a4a8e;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        text-align: center;
    }
    .info-card {
        background: linear-gradient(135deg, #0d1226, #1a2a4a);
        border: 1px solid #2a4a8e;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Hero Header
st.markdown("""
<div class="hero-header">
    <h1>🇺🇸 JOHNNY — ABD Borsası Simülasyon Ajanı</h1>
    <p style="color: #8ba7d0; font-size: 1.1rem;">
        NYSE & NASDAQ | Teknik Analiz + Tema Odaklı Yatırım | 20.000 USD Portföy
    </p>
</div>
""", unsafe_allow_html=True)

# Tema Hisseleri Veri Tabanı
tema_hisseler = {
    "🔗 Blockchain & Kripto": {
        "açıklama": "Blockchain teknolojisi, kripto paraları ve merkezi olmayan finans",
        "hisseler": [
            {"kod": "COIN", "şirket": "Coinbase", "açıklama": "Kripto exchange platform"},
            {"kod": "RIOT", "şirket": "Riot Platforms", "açıklama": "Bitcoin madenciliği"},
            {"kod": "HUT", "şirket": "Hut 8 Mining", "açıklama": "Bitcoin madenciliği + YZ datacenter"},
            {"kod": "CLSK", "şirket": "CleanSpark", "açıklama": "Bitcoin madenciliği (yenilenebilir)"},
            {"kod": "MSTR", "şirket": "MicroStrategy", "açıklama": "Bitcoin treasury + BI yazılımı"},
            {"kod": "SQ", "şirket": "Block (Square)", "açıklama": "Kripto ödeme + fintek"},
            {"kod": "PYPL", "şirket": "PayPal", "açıklama": "Kripto transfer, stablecoin"},
            {"kod": "HOOD", "şirket": "Robinhood", "açıklama": "Kripto trading platformu"},
            {"kod": "SOFI", "şirket": "SoFi Technologies", "açıklama": "Fintek + kripto"},
        ]
    },
    
    "💻 Teknoloji (Mega Cap)": {
        "açıklama": "Dünyanın en büyük teknoloji şirketleri",
        "hisseler": [
            {"kod": "AAPL", "şirket": "Apple", "açıklama": "Donanım, yazılım, hizmetler"},
            {"kod": "MSFT", "şirket": "Microsoft", "açıklama": "Cloud, AI, yazılım"},
            {"kod": "GOOGL", "şirket": "Alphabet", "açıklama": "Arama, reklam, cloud"},
            {"kod": "AMZN", "şirket": "Amazon", "açıklama": "E-ticaret, AWS cloud"},
            {"kod": "META", "şirket": "Meta", "açıklama": "Sosyal medya, VR"},
            {"kod": "TSLA", "şirket": "Tesla", "açıklama": "EV, enerji depolama"},
        ]
    },
    
    "🤖 Yapay Zeka & İleri Teknoloji": {
        "açıklama": "Yapay zeka, makine öğrenmesi, veri analitik odaklı şirketler",
        "hisseler": [
            {"kod": "NVDA", "şirket": "NVIDIA", "açıklama": "AI GPU çipleri"},
            {"kod": "AMD", "şirket": "AMD", "açıklama": "MI300 YZ GPU'ları"},
            {"kod": "INTC", "şirket": "Intel", "açıklama": "Gaudi YZ işlemciler"},
            {"kod": "ARM", "şirket": "ARM Holdings", "açıklama": "YZ-optimized CPU mimarisi"},
            {"kod": "QCOM", "şirket": "Qualcomm", "açıklama": "On-device AI çipleri"},
            {"kod": "CRM", "şirket": "Salesforce", "açıklama": "Enterprise AI (Einstein)"},
            {"kod": "PLTR", "şirket": "Palantir", "açıklama": "Veri analitik, savunma YZ"},
            {"kod": "DDOG", "şirket": "Datadog", "açıklama": "YZ-powered monitoring"},
            {"kod": "SNOW", "şirket": "Snowflake", "açıklama": "Data warehouse, YZ pipeline"},
            {"kod": "UPST", "şirket": "Upstart", "açıklama": "AI-powered kredi platformu"},
        ]
    },
    
    "⚡ Yenilenebilir Enerji": {
        "açıklama": "Güneş, rüzgar, pil, yakıt hücresi ve yeşil enerji teknolojileri",
        "hisseler": [
            {"kod": "ENPH", "şirket": "Enphase Energy", "açıklama": "Güneş inverter"},
            {"kod": "RUN", "şirket": "Sunrun", "açıklama": "Güneş panel kurulum"},
            {"kod": "SEDG", "şirket": "SolarEdge", "açıklama": "Güneş optimizasyonu"},
            {"kod": "JKS", "şirket": "Jinko Solar", "açıklama": "Güneş panel üretimi"},
            {"kod": "DQ", "şirket": "Daqo New Energy", "açıklama": "Polisilikon (güneş malz.)"},
            {"kod": "NEE", "şirket": "NextEra Energy", "açıklama": "Rüzgar + güneş üretimi"},
            {"kod": "PLUG", "şirket": "Plug Power", "açıklama": "Yakıt hücresi"},
            {"kod": "BLDP", "şirket": "Ballard Power", "açıklama": "Yakıt hücresi tech"},
            {"kod": "ICLN", "şirket": "iShares Clean Energy ETF", "açıklama": "Temiz enerji ETF"},
            {"kod": "TAN", "şirket": "Invesco Solar ETF", "açıklama": "Güneş ETF"},
        ]
    },
    
    "🚗 Elektrikli Araçlar & Mobilite": {
        "açıklama": "Elektrikli araç üreticileri ve otonom sürüş teknolojisi",
        "hisseler": [
            {"kod": "TSLA", "şirket": "Tesla", "açıklama": "EV lider, otonom sürüş"},
            {"kod": "RIVN", "şirket": "Rivian", "açıklama": "Elektrikli pickup/SUV"},
            {"kod": "NIO", "şirket": "NIO", "açıklama": "Çin EV markası"},
            {"kod": "XPEV", "şirket": "XPeng", "açıklama": "Çin EV, otonom tech"},
        ]
    },
}

# ===== ÖZETİ METRİKLER =====
st.subheader("📊 Portföy Özeti")
col1, col2, col3, col4, col5 = st.columns(5)

total_stocks = sum(len(tema["hisseler"]) for tema in tema_hisseler.values())
with col1:
    st.metric("📋 Takip Edilen Hisse", total_stocks)
with col2:
    st.metric("🎯 Tema Sayısı", len(tema_hisseler))
with col3:
    st.metric("💰 Portföy Boyutu", "20.000 USD")
with col4:
    st.metric("⭐ Mega Cap", "6")
with col5:
    st.metric("🔗 Blockchain", "9")

st.divider()

# ===== TEMA HİSSELERİ =====
st.subheader("🎯 Tema Bazlı Hisseler — Detaylı Liste")

# Tema özeti
tema_col1, tema_col2, tema_col3 = st.columns(3)

with tema_col1:
    st.markdown("#### 🔗 Blockchain & Kripto")
    st.markdown("**9 hisse**")
    coins = ", ".join([h["kod"] for h in tema_hisseler["🔗 Blockchain & Kripto"]["hisseler"]])
    st.code(coins, language="csv")

with tema_col2:
    st.markdown("#### 🤖 Yapay Zeka & Tech")
    st.markdown("**10 hisse**")
    ai = ", ".join([h["kod"] for h in tema_hisseler["🤖 Yapay Zeka & İleri Teknoloji"]["hisseler"]])
    st.code(ai, language="csv")

with tema_col3:
    st.markdown("#### ⚡ Yenilenebilir Enerji")
    st.markdown("**10 hisse**")
    energy = ", ".join([h["kod"] for h in tema_hisseler["⚡ Yenilenebilir Enerji"]["hisseler"]])
    st.code(energy, language="csv")

st.divider()

# ===== TÜMEL HİSSELER TABLOSU =====
st.subheader("📊 Tüm Tema Hisseleri — Detaylı Tablo")

all_stocks = []
for tema_adı, tema_data in tema_hisseler.items():
    for hisse in tema_data["hisseler"]:
        all_stocks.append({
            "Tema": tema_adı,
            "Sembol": hisse["kod"],
            "Şirket": hisse["şirket"],
            "Açıklama": hisse["açıklama"]
        })

df_all = pd.DataFrame(all_stocks).sort_values("Sembol").reset_index(drop=True)
st.dataframe(df_all, use_container_width=True, height=400, hide_index=True)

st.divider()

# ===== SİSTEM BİLGİLERİ =====
st.subheader("🔧 Sistem Bilgileri")

info_col1, info_col2, info_col3 = st.columns(3)

with info_col1:
    st.markdown("""
    **Piyasa Bilgileri:**
    - Piyasa: NYSE + NASDAQ
    - Zaman Dilimi: America/New_York (EST)
    - Veri Kaynağı: yfinance
    - Başlangıç: 20.000 USD
    """)

with info_col2:
    st.markdown("""
    **Teknik Analiz:**
    - RSI (14)
    - MACD (12/26/9)
    - Bollinger Bands (20/2σ)
    - Moving Averages (20/50/200)
    - Volume Analysis
    """)

with info_col3:
    st.markdown("""
    **Risk Yönetimi:**
    - Max Pozisyon: %25
    - Stop-Loss: -%4
    - Take-Profit: +%2.5
    - Trailing Stop: -%2
    - Portfolio Stop: -%10
    """)

st.divider()

# ===== PORTFÖY ÖĞÜŞÜ =====
st.subheader("📌 Önerilen Portföy Dağılımı")

portfoyu_col1, portfoyu_col2, portfoyu_col3, portfoyu_col4 = st.columns(4)

with portfoyu_col1:
    st.metric("🔗 Blockchain", "25%", "5.000 USD")
with portfoyu_col2:
    st.metric("💻 Mega Cap Tech", "30%", "6.000 USD")
with portfoyu_col3:
    st.metric("🤖 YZ & Tech", "25%", "5.000 USD")
with portfoyu_col4:
    st.metric("⚡ Enerji", "20%", "4.000 USD")

st.info("""
### 📚 Tema Stratejisi

**Johnny, tema bazlı yatırım yapar:**

1. **Tema Seçimi** — Blockchain, YZ, Enerji, Tech
2. **Hisse Seçimi** — Her tema içinde en iyi performans gösterenler
3. **Teknik Sinyal** — RSI, MACD, Bollinger, MA
4. **Risk Kontrol** — Stop-loss, take-profit, max position
5. **Portföy Dinamikliği** — Sektör rotasyonu, tema taşımacılığı

**Avantajları:**
- ✅ Çeşitlendirme (5 tema)
- ✅ Trend takibi (teknik analiz)
- ✅ Risk kontrollü (stop-loss, position size)
- ✅ Gerçekçi komisyonlar (%0.30)

---
**NOT:** Bu sistem kağıt portföy simülasyonudur. Gerçek para işlemi yapmaz.
""")

st.divider()

# ===== DOWNLOAD =====
st.subheader("💾 Dışa Aktar")

# CSV
csv_data = df_all.to_csv(index=False)
st.download_button(
    label="📥 CSV İndir",
    data=csv_data,
    file_name="johnny_tema_hisseler.csv",
    mime="text/csv"
)

# JSON
json_data = json.dumps({
    "sistem": {
        "ad": "Johnny",
        "piyasa": "NYSE + NASDAQ",
        "portfoy": "20.000 USD",
        "temalar": len(tema_hisseler),
        "hisseler": total_stocks
    },
    "temalar": {
        tema_adı: {
            "açıklama": tema_data["açıklama"],
            "hisseler": tema_data["hisseler"]
        }
        for tema_adı, tema_data in tema_hisseler.items()
    }
}, indent=2, ensure_ascii=False)

st.download_button(
    label="📥 JSON İndir",
    data=json_data,
    file_name="johnny_tema_hisseler.json",
    mime="application/json"
)

st.divider()

# Footer
st.markdown("""
---
**Johnny v1.0** — ABD Borsası Simülasyon Ajanı  
🔗 GitHub: https://github.com/kirazhub/johny  
📊 Dashboard Port: 8511  
⏰ Güncellenmiş: 2026-04-20
""")
