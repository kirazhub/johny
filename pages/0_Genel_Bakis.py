#!/usr/bin/env python3
"""
Johnny Genel Bakış Sayfası — Cool & Modern Design
Tüm Tema Hisseleri, İstatistikler, Portföy Özeti
"""
import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(
    page_title="🇺🇸 Johnny — Genel Bakış",
    page_icon="🇺🇸",
    layout="wide"
)

# Modern Tema - Glassmorphism + Gradients
st.markdown("""
<style>
    /* Ana stil */
    .stApp { 
        background: linear-gradient(135deg, #0a0e1a 0%, #0d1226 50%, #0a0e1a 100%);
        color: #e8eaf0; 
    }
    
    /* Başlık */
    h1 { color: #4a9eff; text-shadow: 0 0 20px rgba(74, 158, 255, 0.3); font-size: 2.5rem; }
    h2 { color: #8ba7d0; text-shadow: 0 0 10px rgba(139, 167, 208, 0.2); }
    h3 { color: #8ba7d0; }
    
    /* Metrikler - Glassmorphism */
    .stMetric {
        background: rgba(17, 24, 39, 0.6);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(42, 74, 142, 0.3);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }
    
    .stMetric:hover {
        background: rgba(17, 24, 39, 0.8);
        border: 1px solid rgba(74, 158, 255, 0.5);
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(74, 158, 255, 0.15);
    }
    
    .stMetric label { color: #8ba7d0 !important; font-size: 0.8rem !important; text-transform: uppercase; letter-spacing: 1px; }
    .stMetric [data-testid="stMetricValue"] { color: #4a9eff !important; font-weight: bold; font-size: 2rem; }
    
    /* Hero Header */
    .hero-header {
        background: linear-gradient(135deg, #0d1f3c 0%, #1a3a6e 50%, #0d1f3c 100%);
        border: 2px solid;
        border-image: linear-gradient(135deg, #4a9eff, #2a6aae) 1;
        border-radius: 16px;
        padding: 30px;
        margin-bottom: 30px;
        text-align: center;
        box-shadow: 0 0 40px rgba(74, 158, 255, 0.1), inset 0 0 20px rgba(74, 158, 255, 0.05);
        backdrop-filter: blur(10px);
    }
    
    .hero-header h1 { margin: 0; padding: 10px 0; }
    .hero-subtitle { color: #8ba7d0; font-size: 1.2rem; margin-top: 10px; }
    
    /* Card Tasarımı */
    .info-card {
        background: rgba(13, 18, 38, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(42, 74, 142, 0.4);
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }
    
    .info-card:hover {
        border: 1px solid rgba(74, 158, 255, 0.6);
        box-shadow: 0 8px 32px rgba(74, 158, 255, 0.15);
        transform: translateX(5px);
    }
    
    /* Tema Kartları */
    .tema-card {
        background: linear-gradient(135deg, rgba(13, 18, 38, 0.8), rgba(26, 42, 74, 0.6));
        border: 1px solid rgba(74, 158, 255, 0.3);
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    
    .tema-title { 
        color: #4a9eff; 
        font-weight: bold; 
        font-size: 1.1rem;
        text-shadow: 0 0 10px rgba(74, 158, 255, 0.2);
    }
    
    .tema-count { color: #8ba7d0; font-size: 0.9rem; }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: linear-gradient(90deg, rgba(74, 158, 255, 0.1), transparent);
        border-radius: 8px;
    }
    
    /* Divider */
    hr { 
        border: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(74, 158, 255, 0.5), transparent);
        margin: 30px 0;
    }
    
    /* DataFrame */
    .stDataFrame {
        background: rgba(17, 24, 39, 0.5);
        border: 1px solid rgba(42, 74, 142, 0.3);
        border-radius: 8px;
        backdrop-filter: blur(10px);
    }
    
    /* Download Button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #4a9eff, #2a6aae);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(74, 158, 255, 0.3);
        transition: all 0.3s ease;
    }
    
    .stDownloadButton > button:hover {
        box-shadow: 0 6px 25px rgba(74, 158, 255, 0.5);
        transform: translateY(-2px);
    }
    
    /* Code Block */
    .stCode {
        background: rgba(17, 24, 39, 0.8);
        border: 1px solid rgba(74, 158, 255, 0.2);
        border-radius: 8px;
    }
    
    /* Info Box */
    .stInfo {
        background: linear-gradient(135deg, rgba(0, 200, 100, 0.1), rgba(42, 74, 142, 0.1));
        border-left: 4px solid #00c864;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Hero Header
st.markdown("""
<div class="hero-header">
    <h1>🇺🇸 JOHNNY</h1>
    <div class="hero-subtitle">ABD Borsası Simülasyon Ajanı</div>
    <div style="color: #4a9eff; margin-top: 15px; font-size: 0.95rem;">
        💰 20.000 USD • 📊 39 Tema Hissesi • 🤖 Teknik + YZ Analiz
    </div>
</div>
""", unsafe_allow_html=True)

# Tema Hisseleri
tema_hisseler = {
    "🔗 Blockchain & Kripto": {
        "emoji": "⛓️",
        "açıklama": "Blockchain, kripto paraları ve merkezi olmayan finans",
        "hisseler": [
            {"kod": "COIN", "şirket": "Coinbase", "açıklama": "Kripto exchange"},
            {"kod": "RIOT", "şirket": "Riot Platforms", "açıklama": "Bitcoin madenciliği"},
            {"kod": "HUT", "şirket": "Hut 8 Mining", "açıklama": "BTC + YZ datacenter"},
            {"kod": "CLSK", "şirket": "CleanSpark", "açıklama": "Yeşil Bitcoin"},
            {"kod": "MSTR", "şirket": "MicroStrategy", "açıklama": "BTC treasury"},
            {"kod": "SQ", "şirket": "Block", "açıklama": "Kripto ödeme"},
            {"kod": "PYPL", "şirket": "PayPal", "açıklama": "Stablecoin"},
            {"kod": "HOOD", "şirket": "Robinhood", "açıklama": "Kripto trading"},
            {"kod": "SOFI", "şirket": "SoFi", "açıklama": "Fintek + kripto"},
        ]
    },
    
    "💻 Teknoloji Mega Cap": {
        "emoji": "🖥️",
        "açıklama": "Dünyanın en büyük teknoloji şirketleri",
        "hisseler": [
            {"kod": "AAPL", "şirket": "Apple", "açıklama": "Donanım + yazılım"},
            {"kod": "MSFT", "şirket": "Microsoft", "açıklama": "Cloud + AI"},
            {"kod": "GOOGL", "şirket": "Alphabet", "açıklama": "Arama + reklam"},
            {"kod": "AMZN", "şirket": "Amazon", "açıklama": "E-ticaret + AWS"},
            {"kod": "META", "şirket": "Meta", "açıklama": "Sosyal medya + VR"},
            {"kod": "TSLA", "şirket": "Tesla", "açıklama": "EV + enerji"},
        ]
    },
    
    "🤖 Yapay Zeka & İleri Tech": {
        "emoji": "🧠",
        "açıklama": "YZ, makine öğrenmesi, veri analitik şirketleri",
        "hisseler": [
            {"kod": "NVDA", "şirket": "NVIDIA", "açıklama": "AI GPU çipleri"},
            {"kod": "AMD", "şirket": "AMD", "açıklama": "MI300 GPU"},
            {"kod": "INTC", "şirket": "Intel", "açıklama": "Gaudi işlemciler"},
            {"kod": "ARM", "şirket": "ARM Holdings", "açıklama": "CPU mimarisi"},
            {"kod": "QCOM", "şirket": "Qualcomm", "açıklama": "On-device AI"},
            {"kod": "CRM", "şirket": "Salesforce", "açıklama": "Einstein AI"},
            {"kod": "PLTR", "şirket": "Palantir", "açıklama": "Veri analitik"},
            {"kod": "DDOG", "şirket": "Datadog", "açıklama": "AI monitoring"},
            {"kod": "SNOW", "şirket": "Snowflake", "açıklama": "Data warehouse"},
            {"kod": "UPST", "şirket": "Upstart", "açıklama": "AI kredi"},
        ]
    },
    
    "⚡ Yenilenebilir Enerji": {
        "emoji": "☀️",
        "açıklama": "Güneş, rüzgar, pil, yakıt hücresi teknolojileri",
        "hisseler": [
            {"kod": "ENPH", "şirket": "Enphase", "açıklama": "Güneş inverter"},
            {"kod": "RUN", "şirket": "Sunrun", "açıklama": "Güneş kurulum"},
            {"kod": "SEDG", "şirket": "SolarEdge", "açıklama": "Güneş optimizasyon"},
            {"kod": "JKS", "şirket": "Jinko Solar", "açıklama": "Panel üretimi"},
            {"kod": "DQ", "şirket": "Daqo", "açıklama": "Polisilikon"},
            {"kod": "NEE", "şirket": "NextEra", "açıklama": "Rüzgar + güneş"},
            {"kod": "PLUG", "şirket": "Plug Power", "açıklama": "Yakıt hücresi"},
            {"kod": "BLDP", "şirket": "Ballard", "açıklama": "Hücre teknolojisi"},
            {"kod": "ICLN", "şirket": "iShares ETF", "açıklama": "Clean energy"},
            {"kod": "TAN", "şirket": "Invesco ETF", "açıklama": "Solar ETF"},
        ]
    },
    
    "🚗 Elektrikli Araçlar": {
        "emoji": "⚡🚗",
        "açıklama": "EV üreticileri ve otonom sürüş teknolojisi",
        "hisseler": [
            {"kod": "TSLA", "şirket": "Tesla", "açıklama": "EV lider"},
            {"kod": "RIVN", "şirket": "Rivian", "açıklama": "Pickup/SUV"},
            {"kod": "NIO", "şirket": "NIO", "açıklama": "Çin EV"},
            {"kod": "XPEV", "şirket": "XPeng", "açıklama": "Otonom tech"},
        ]
    },
}

# ===== ÖZET METRİKLER =====
st.subheader("📊 Portföy Özeti")

total_stocks = sum(len(tema["hisseler"]) for tema in tema_hisseler.values())
col1, col2, col3, col4, col5 = st.columns(5)

metrics_data = [
    ("📋 Hisse", str(total_stocks), "tema"),
    ("🎯 Tema", str(len(tema_hisseler)), "tema"),
    ("💰 Portföy", "20.000 USD", "para"),
    ("⭐ Mega Cap", "6", "hisse"),
    ("🔗 Blockchain", "9", "hisse")
]

for i, (label, value, _) in enumerate(metrics_data):
    with [col1, col2, col3, col4, col5][i]:
        st.metric(label, value)

st.markdown("---")

# ===== TEMA HİSSELERİ PREVIEW =====
st.subheader("🎯 Tema Portföyü — Hisseler")

tema_cols = st.columns(len(tema_hisseler))

for idx, (tema_adı, tema_data) in enumerate(tema_hisseler.items()):
    with tema_cols[idx]:
        st.markdown(f"""
        <div class="tema-card">
            <div class="tema-title">{tema_adı}</div>
            <div class="tema-count">• {len(tema_data['hisseler'])} hisse</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Hisse kodları
        hisse_kodlar = ", ".join([h["kod"] for h in tema_data["hisseler"]])
        st.code(hisse_kodlar, language="csv")

st.markdown("---")

# ===== DETAYLI TABLO =====
st.subheader("📊 Tüm Tema Hisseleri — Detaylı Tablo")

all_stocks = []
for tema_adı, tema_data in tema_hisseler.items():
    for hisse in tema_data["hisseler"]:
        all_stocks.append({
            "🎯 Tema": tema_adı,
            "📌 Sembol": hisse["kod"],
            "🏢 Şirket": hisse["şirket"],
            "📝 Açıklama": hisse["açıklama"]
        })

df_all = pd.DataFrame(all_stocks).sort_values("📌 Sembol").reset_index(drop=True)
st.dataframe(df_all, use_container_width=True, height=400, hide_index=True)

st.markdown("---")

# ===== SİSTEM KARTLERİ =====
st.subheader("🔧 Sistem Bilgileri")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="info-card">
    <b>📊 Piyasa Bilgileri</b><br>
    ✓ NYSE + NASDAQ<br>
    ✓ EST Zamanı<br>
    ✓ yfinance Veri<br>
    ✓ 20.000 USD
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="info-card">
    <b>📈 Teknik Analiz</b><br>
    ✓ RSI (14)<br>
    ✓ MACD (12/26/9)<br>
    ✓ Bollinger (20/2σ)<br>
    ✓ EMA (20/50/200)
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="info-card">
    <b>⚔️ Risk Yönetimi</b><br>
    ✓ Max Pos: %25<br>
    ✓ SL: -%4<br>
    ✓ TP: +%2.5<br>
    ✓ Portfolio: -%10
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ===== PORTFÖY DAĞILIMI =====
st.subheader("💼 Önerilen Portföy Dağılımı")

# Pie Chart
portfoy_data = {
    "🔗 Blockchain": 25,
    "💻 Mega Cap Tech": 30,
    "🤖 YZ & Tech": 25,
    "⚡ Enerji": 20
}

fig = go.Figure(data=[go.Pie(
    labels=list(portfoy_data.keys()),
    values=list(portfoy_data.values()),
    hole=0.3,
    marker=dict(
        colors=["#4a9eff", "#00c864", "#ff9500", "#ff4444"],
        line=dict(color="#0a0e1a", width=2)
    )
)])

fig.update_layout(
    title_text="Tema Dağılımı (% cinsinden)",
    template="plotly_dark",
    paper_bgcolor="rgba(10, 14, 26, 0.5)",
    plot_bgcolor="rgba(10, 14, 26, 0.5)",
    font=dict(color="#8ba7d0"),
    height=400
)

st.plotly_chart(fig, use_container_width=True)

# Metrikler
col1, col2, col3, col4 = st.columns(4)
dolarlar = [("🔗 Blockchain", "25%", "5.000 USD"),
            ("💻 Mega Cap", "30%", "6.000 USD"),
            ("🤖 YZ & Tech", "25%", "5.000 USD"),
            ("⚡ Enerji", "20%", "4.000 USD")]

for col, (label, pct, usd) in zip([col1, col2, col3, col4], dolarlar):
    with col:
        st.metric(label, pct, usd)

st.markdown("---")

# ===== EXPORT =====
st.subheader("💾 Dışa Aktar")

col1, col2 = st.columns(2)

with col1:
    csv_data = df_all.to_csv(index=False)
    st.download_button(
        label="📥 CSV İndir",
        data=csv_data,
        file_name="johnny_tema_hisseler.csv",
        mime="text/csv"
    )

with col2:
    json_data = json.dumps(tema_hisseler, indent=2, ensure_ascii=False)
    st.download_button(
        label="📥 JSON İndir",
        data=json_data,
        file_name="johnny_tema_hisseler.json",
        mime="application/json"
    )

st.markdown("---")

# Footer
st.markdown("""
<div style="text-align: center; color: #8ba7d0; margin-top: 40px; padding: 20px; border-top: 1px solid rgba(42, 74, 142, 0.2);">
    <p>🇺🇸 <b>Johnny v1.0</b> — ABD Borsası Simülasyon Ajanı</p>
    <p>🔗 <a href="https://github.com/kirazhub/johny" target="_blank" style="color: #4a9eff;">GitHub</a> • 
    📊 Port 8511 • ⏰ 2026-04-20</p>
</div>
""", unsafe_allow_html=True)
