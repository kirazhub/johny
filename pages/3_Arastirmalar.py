#!/usr/bin/env python3
"""
Johnny Araştırmalar Sayfası
39 hissenin kapsamlı analizi - Haberler, Fiyat Geçmişi, Sentiment
"""
import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(
    page_title="🔍 Johnny — Araştırmalar",
    page_icon="🔍",
    layout="wide"
)

# Modern Tema
st.markdown("""
<style>
    .stApp { 
        background: linear-gradient(135deg, #0a0e1a 0%, #0d1226 50%, #0a0e1a 100%);
        color: #e8eaf0; 
    }
    
    h1 { color: #4a9eff; text-shadow: 0 0 20px rgba(74, 158, 255, 0.3); }
    h2 { color: #8ba7d0; }
    
    .hisse-card {
        background: linear-gradient(135deg, rgba(13, 18, 38, 0.8), rgba(26, 42, 74, 0.6));
        border: 2px solid rgba(74, 158, 255, 0.3);
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 8px 32px rgba(74, 158, 255, 0.1);
    }
    
    .hisse-card:hover {
        border: 2px solid rgba(74, 158, 255, 0.6);
        box-shadow: 0 12px 40px rgba(74, 158, 255, 0.2);
        transform: translateY(-5px);
    }
    
    .sentiment-pozitif { color: #00c864; font-weight: bold; }
    .sentiment-negatif { color: #ff4444; font-weight: bold; }
    .sentiment-notr { color: #ffcc00; font-weight: bold; }
    
    .haber-item {
        background: rgba(17, 24, 39, 0.6);
        border-left: 3px solid #4a9eff;
        padding: 12px;
        margin: 8px 0;
        border-radius: 4px;
    }
    
    .metrik-box {
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(74, 158, 255, 0.3);
        padding: 12px;
        border-radius: 8px;
        margin: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Başlık
st.markdown("""
<div style="text-align: center; margin-bottom: 30px;">
    <h1>🔍 JOHNNY'NİN ARAŞTIRMASI</h1>
    <p style="color: #8ba7d0; font-size: 1.1rem;">39 Hisse — Haberler, Fiyat, Sentiment Analizi</p>
</div>
""", unsafe_allow_html=True)

# Veri yükleme
arastirma_dir = "/Users/kiraz/.openclaw/agents/kiraz/workspace/johny/arastirmalar"

# CSV yükle
df_hisseler = pd.read_csv(f"{arastirma_dir}/hisseler_tablosu.csv")

# Top 5 verilerini hardcode (rapor dosyasından çıkartıldı)
top5_data = {
    "1": {
        "sembol": "HUT",
        "sirket": "Hut 8 Corp.",
        "fiyat": "$74.9",
        "1y_perf": "+603.95%",
        "tavsiye": "Güçlü Al",
        "sentiment": "POZİTİF",
        "haberler": [
            "Strategy vs. Hut 8: Which Bitcoin Stock Has the Stronger Upside Now?",
            "3 Best-performing Canadian Crypto-Mining Stocks in 2026",
            "Hut 8: Why The River Bend Expansion Justifies A Buy Rating",
            "Bitcoin mining stock surges after $7B Google-backed deal",
            "Hut 8 Mining stock maintained at Buy by H.C. Wainwright"
        ]
    },
    "2": {
        "sembol": "INTC",
        "sirket": "Intel Corporation",
        "fiyat": "$68.5",
        "1y_perf": "+263.59%",
        "tavsiye": "Tut",
        "sentiment": "NÖTR",
        "haberler": [
            "Intel Will Report Q1 Earnings on April 23 — Here's Who Owns INTC Stock",
            "Is Intel Stock a Buy Ahead of Earnings?",
            "Is It Too Late To Consider Intel After A 262% One Year Surge?",
            "Intel Stock Price Up 5.5% After Analyst Upgrade",
            "Intel Pulls Back 5% After Historic Winning Streak: Bubble Warning?"
        ]
    },
    "3": {
        "sembol": "PLUG",
        "sirket": "Plug Power Inc.",
        "fiyat": "$2.78",
        "1y_perf": "+251.9%",
        "tavsiye": "Tut",
        "sentiment": "NÖTR",
        "haberler": [
            "In 10 Years, Will You Wish You'd Bought Plug Power Stock Right Now?",
            "Hydrogen Stocks To Consider - April 19th",
            "Here's Why I Wouldn't Touch Plug Power With a 10-Foot Pole",
            "Plug Power CEO Opens Reddit AMA As Hydrogen Targets AI Data Centers",
            "Is hydrogen infrastructure scale now the real test?"
        ]
    },
    "4": {
        "sembol": "AMD",
        "sirket": "Advanced Micro Devices",
        "fiyat": "$278.39",
        "1y_perf": "+225.37%",
        "tavsiye": "Al",
        "sentiment": "POZİTİF",
        "haberler": [
            "Why Advanced Micro Devices Stock May Drop Soon",
            "Why AMD Stock Popped on Thursday",
            "Broadcom & AMD Lead AI Chip Market with Meta, Alphabet Deals",
            "AMD Gains 6% Ahead of May Earnings",
            "AMD Opinions on All-Time Highs and AI Inference Demand"
        ]
    },
    "5": {
        "sembol": "SEDG",
        "sirket": "SolarEdge Technologies",
        "fiyat": "$38.3",
        "1y_perf": "+216.53%",
        "tavsiye": "Tut",
        "sentiment": "NEGATİF",
        "haberler": [
            "SolarEdge stock slides as market rises",
            "SolarEdge Stock Rating Lowered by Goldman Sachs",
            "Is SolarEdge Attractive After 203% Rally?",
            "SolarEdge Recast as Speculative Turnaround Play",
            "SolarEdge Up 200% In 12 Months And Room For More"
        ]
    }
}

# ===== ÖZETİ METRİKLER =====
st.subheader("📊 Portföy Araştırması Özeti")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📋 Araştırılan Hisse", "39")
with col2:
    st.metric("🚀 Kazanan", "32/39")
with col3:
    st.metric("📈 Ort. 1Y Getiri", "+87.3%")
with col4:
    st.metric("⭐ Top Hisse", "HUT (+603%)")

st.markdown("---")

# ===== TOP 5 KARTLARı =====
st.subheader("🏆 Top 5 Hisse (1 Yıllık Performans)")

for rank, data in top5_data.items():
    sentiment_class = {
        "POZİTİF": "sentiment-pozitif",
        "NEGATİF": "sentiment-negatif",
        "NÖTR": "sentiment-notr"
    }.get(data["sentiment"], "sentiment-notr")
    
    st.markdown(f"""
    <div class="hisse-card">
        <h3>#{rank} — {data["sembol"]}: {data["sirket"]}</h3>
        
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 15px 0;">
            <div class="metrik-box">
                <b>Fiyat</b><br>
                {data["fiyat"]}
            </div>
            <div class="metrik-box">
                <b>1Y Performans</b><br>
                <span style="color: #00c864; font-weight: bold;">{data["1y_perf"]}</span>
            </div>
            <div class="metrik-box">
                <b>Tavsiye</b><br>
                {data["tavsiye"]}
            </div>
            <div class="metrik-box">
                <b>Sentiment</b><br>
                <span class="{sentiment_class}">{data["sentiment"]}</span>
            </div>
        </div>
        
        <b>📰 Son Haberler:</b><br>
    """, unsafe_allow_html=True)
    
    for i, haber in enumerate(data["haberler"], 1):
        st.markdown(f"<div class='haber-item'>• {haber}</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ===== TÜMEL TABLO =====
st.subheader("📊 Tüm 39 Hisse — Detaylı Tablo")

# Tabloyu göster
st.dataframe(df_hisseler, use_container_width=True, height=600, hide_index=True)

st.markdown("---")

# ===== DOWNLOAD =====
st.subheader("💾 Araştırma Dosyalarını İndir")

col1, col2, col3 = st.columns(3)

with col1:
    with open(f"{arastirma_dir}/hisseler_tablosu.csv", "r") as f:
        csv_data = f.read()
    st.download_button(
        label="📥 CSV (Tüm Hisseler)",
        data=csv_data,
        file_name="johnny_arastirma_hisseler.csv",
        mime="text/csv"
    )

with col2:
    with open(f"{arastirma_dir}/top5_hisse_raporu.md", "r") as f:
        md_data = f.read()
    st.download_button(
        label="📥 Markdown (Top 5)",
        data=md_data,
        file_name="johnny_top5_rapor.md",
        mime="text/markdown"
    )

with col3:
    with open(f"{arastirma_dir}/tum_hisseler.json", "r") as f:
        json_data = f.read()
    st.download_button(
        label="📥 JSON (Tüm Veriler)",
        data=json_data,
        file_name="johnny_arastirma_tum.json",
        mime="application/json"
    )

st.markdown("---")

# ===== BİLGİ =====
st.info("""
### 📚 Araştırma Kaynakları

✅ **Veri Kaynakları:**
- Google Finance & Yahoo Finance (Fiyat, P/E, Beta)
- Google News RSS Feeds (Son Haberler)
- Seeking Alpha, MarketBeat, The Motley Fool
- CNBC, Bloomberg, Reuters, TipRanks
- Investing.com, simplywall.st

✅ **Her Hisse İçin:**
- 52-haftalık fiyat aralığı
- 3 ay, 6 ay, 1 yıl performans (%)
- Analyst tavsiyesi (Al/Tut/Sat)
- Hedef fiyat
- Piyasa değeri (market cap)
- Beta (oynaklık)
- Son 5 haber başlığı

✅ **Sentiment Analizi:**
- Pozitif: Haberler ve analyst raporları olumlu
- Nötr: Karışık sinyal, belirsizlik
- Negatif: Haberler ve raporlar olumsuz

### 🎯 Nasıl Kullanılır?

1. Top 5 hisseyi detaylı oku (kazanı yatırımlar)
2. Tam tablodan diğer hisseleri keşfet
3. Sentiment'e göre risk değerlendirmesi yap
4. CSV'yi excel'de analiz et

**Tavsiye:** Positive sentiment + yüksek performans = güçlü alım sinyali
""")

st.markdown("---")

st.markdown("""
<div style="text-align: center; color: #8ba7d0; padding: 20px;">
    <p><b>🔍 Johnny'nin Araştırması</b> — Güncel Haberler + Teknik Analiz</p>
    <p>Tüm veriler 2026-04-20 tarihinde toplandı</p>
</div>
""", unsafe_allow_html=True)
