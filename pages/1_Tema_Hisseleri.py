#!/usr/bin/env python3
"""
Johnny Tema Hisseleri Sayfası
Blockchain, Teknoloji, YZ, Yenilenebilir Enerji
"""
import streamlit as st
import pandas as pd
import json

st.set_page_config(
    page_title="🎯 Johnny — Tema Hisseleri",
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
    .tema-card {
        background: linear-gradient(135deg, #0d1226, #1a2a4a);
        border: 1px solid #2a4a8e;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    .tema-title { color: #4a9eff; font-weight: bold; font-size: 1.1rem; }
    .tema-count { color: #8ba7d0; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

st.title("🎯 Johnny — Tema Bazlı Hisseler")
st.markdown("**Blockchain, Teknoloji, Yapay Zeka, Yenilenebilir Enerji**")

# Tema Hisseleri
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

# Özet Metrikleri
st.subheader("📊 Genel Bakış")
col1, col2, col3, col4 = st.columns(4)

total_hisses = sum(len(tema["hisseler"]) for tema in tema_hisseler.values())
with col1:
    st.metric("📋 Toplam Hisse", total_hisses)
with col2:
    st.metric("🎯 Tema Sayısı", len(tema_hisseler))
with col3:
    st.metric("🔗 Blockchain", len(tema_hisseler.get("🔗 Blockchain & Kripto", {}).get("hisseler", [])))
with col4:
    st.metric("⚡ Yenilenebilir", len(tema_hisseler.get("⚡ Yenilenebilir Enerji", {}).get("hisseler", [])))

st.divider()

# Temalar
for tema_adı, tema_data in tema_hisseler.items():
    hisseler = tema_data["hisseler"]
    
    with st.expander(f"**{tema_adı}** ({len(hisseler)} hisse)", expanded=True):
        st.markdown(f"*{tema_data['açıklama']}*")
        
        # Tablo
        df_tema = pd.DataFrame(hisseler)
        st.dataframe(df_tema, use_container_width=True, hide_index=True)
        
        # Hisse listesi (CSV)
        hisse_listesi = ", ".join([h["kod"] for h in hisseler])
        st.code(hisse_listesi, language="csv")

st.divider()

# Tüm Hisseler Tablosu
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
st.dataframe(df_all, use_container_width=True, height=600, hide_index=True)

st.divider()

# Export
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

# İstatistikler
st.subheader("📈 Tema İstatistikleri")

col1, col2, col3 = st.columns(3)

with col1:
    st.write("**Hisse Sayısına Göre Top Tema:**")
    tema_counts = [(k, len(v["hisseler"])) for k, v in tema_hisseler.items()]
    tema_counts.sort(key=lambda x: x[1], reverse=True)
    for tema, count in tema_counts:
        st.write(f"  • {tema}: **{count}**")

with col2:
    st.write("**Tema Kategorileri:**")
    for tema in tema_hisseler.keys():
        st.write(f"  • {tema}")

with col3:
    st.write("**Hisse Örnekleri:**")
    samples = ["COIN", "NVDA", "ENPH", "TSLA"]
    for symbol in samples:
        found = False
        for tema, data in tema_hisseler.items():
            if any(h["kod"] == symbol for h in data["hisseler"]):
                st.write(f"  ✅ {symbol}")
                found = True
                break
        if not found:
            st.write(f"  ❌ {symbol}")

st.divider()

# Portföy Önerisi
st.info("""
### 📌 Johnny Portföyü — Tema Odaklı

Bu hisseler Johnny'nin 20.000 USD portföyüne eklenebilir:

**Dağılım Önerisi:**
- 🔗 Blockchain/Kripto: %25 (COIN, HUT, MSTR)
- 💻 Mega Cap Tech: %30 (AAPL, MSFT, GOOGL)
- 🤖 YZ & İleri Tech: %25 (NVDA, AMD, PLTR)
- ⚡ Yenilenebilir Enerji: %20 (ENPH, RUN, NEE)

**Risk Yönetimi:**
- Max Pozisyon: %25 (750 USD)
- Stop-Loss: -%4
- Take-Profit: +%2.5

**Strateji:**
- Teknik analiz (RSI, MACD, Bollinger)
- Tema rotasyonu (sektör taşımacılığı)
- News sentiment (haber analizi)

---
**Not:** Bu sayfadaki hisseler Johnny'nin portföyüne otomatik olarak eklenmez. 
Manuel olarak config'e eklenebilir veya trading algoritması tarafından seçilebilir.
""")
