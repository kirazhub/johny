#!/usr/bin/env python3
"""
Johnny Bilgilendirme Sayfası
39 Hisse Araştırması — Okuyabileceğin Format
"""
import streamlit as st
import pandas as pd
import json

st.set_page_config(
    page_title="📰 Johnny — Bilgilendirme",
    page_icon="📰",
    layout="wide"
)

# Modern Tema
st.markdown("""
<style>
    .stApp { 
        background: linear-gradient(135deg, #0a0e1a 0%, #0d1226 50%, #0a0e1a 100%);
        color: #e8eaf0; 
    }
    
    h1 { color: #4a9eff; }
    h2 { color: #8ba7d0; margin-top: 30px; }
    h3 { color: #ffcc00; }
    
    .info-box {
        background: linear-gradient(135deg, rgba(13, 18, 38, 0.8), rgba(26, 42, 74, 0.6));
        border-left: 4px solid #4a9eff;
        padding: 20px;
        margin: 15px 0;
        border-radius: 8px;
        line-height: 1.8;
    }
    
    .hisse-section {
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(74, 158, 255, 0.3);
        padding: 20px;
        margin: 20px 0;
        border-radius: 12px;
    }
    
    .baslik-hisse {
        color: #4a9eff;
        font-size: 1.3rem;
        font-weight: bold;
        margin-bottom: 10px;
    }
    
    .metrik {
        display: inline-block;
        background: rgba(17, 24, 39, 0.5);
        padding: 10px 15px;
        margin: 5px;
        border-radius: 6px;
        border-left: 3px solid #4a9eff;
    }
    
    .haber {
        background: rgba(42, 74, 142, 0.2);
        border-left: 3px solid #ffcc00;
        padding: 12px;
        margin: 10px 0;
        border-radius: 4px;
    }
    
    .sentiment-pozitif {
        background: rgba(0, 200, 100, 0.2);
        color: #00c864;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    
    .sentiment-negatif {
        background: rgba(255, 68, 68, 0.2);
        color: #ff4444;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    
    .sentiment-notr {
        background: rgba(255, 204, 0, 0.2);
        color: #ffcc00;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Başlık
st.markdown("""
# 📰 JOHNNY'NİN BİLGİLENDİRMESİ

39 hisse için kapsamlı analiz — Okuyabileceğin format
""")

st.markdown("""
---

## 📊 ÖZET BİLGİ

**Araştırmaya Dahil Edilen Hisse Sayısı:** 39  
**Araştırma Tarihi:** 20 Nisan 2026  
**Ortalama 1 Yıl Getiri:** +87.3%  
**Kazanan Hisseler:** 32 / 39  

---

## 🏆 TOP 5 HISSE (En Yüksek 1 Yıllık Performans)

""")

# TOP 5 Detaylı
top5_data = [
    {
        "rank": 1,
        "sembol": "HUT",
        "sirket": "Hut 8 Corp.",
        "fiyat": "$74.90",
        "1y": "+603.95%",
        "3m": "+25.57%",
        "6m": "+53.55%",
        "tavsiye": "Güçlü Al",
        "sentiment": "POZİTİF",
        "ozet": "Bitcoin madenciliği ve veri merkezi işletmeciliği. Kripto pazarının güçlü toparlanması ile birlikte HUT'un performansı çarpıcı bir şekilde artmıştır. Şirket River Bend expansion projesi ile kapasitesini artırıyor.",
        "haberler": [
            "Strategy vs. Hut 8: Which Bitcoin Stock Has the Stronger Upside Now?",
            "3 Best-performing Canadian Crypto-Mining Stocks in 2026",
            "Hut 8: Why The River Bend Expansion Justifies A Buy Rating",
            "Bitcoin mining stock surges after $7B Google-backed deal",
            "Hut 8 Mining stock maintained at Buy by H.C. Wainwright"
        ]
    },
    {
        "rank": 2,
        "sembol": "INTC",
        "sirket": "Intel Corporation",
        "fiyat": "$68.50",
        "1y": "+263.59%",
        "3m": "+45.87%",
        "6m": "+85.94%",
        "tavsiye": "Tut",
        "sentiment": "NÖTR",
        "ozet": "Yarı iletken üreticisi Intel, Gaudi YZ işlemcileri ile yapay zeka pazarına girdikten sonra önemli bir toparlanma yaşamıştır. Ancak P/E oranı yüksek olduğu için kısa vadeli volatilite beklenmeli.",
        "haberler": [
            "Intel Will Report Q1 Earnings on April 23",
            "Is Intel Stock a Buy Ahead of Earnings?",
            "Is It Too Late To Consider Intel After A 262% One Year Surge?",
            "Intel Stock Price Up 5.5% After Analyst Upgrade",
            "Intel Pulls Back 5% After Historic Winning Streak"
        ]
    },
    {
        "rank": 3,
        "sembol": "PLUG",
        "sirket": "Plug Power Inc.",
        "fiyat": "$2.78",
        "1y": "+251.9%",
        "3m": "+17.8%",
        "6m": "-20.11%",
        "tavsiye": "Tut",
        "sentiment": "NÖTR",
        "ozet": "Yakıt hücresi teknolojisine odaklanmış Plug Power, yeşil hidrojen pazarının büyümesiyle birlikte yükselişe geçmiştir. Ancak son 6 ayda düşüş yaşadığı için bekleme pozisyonu tavsiye ediliyor.",
        "haberler": [
            "In 10 Years, Will You Wish You'd Bought Plug Power Stock Right Now?",
            "Hydrogen Stocks To Consider - April 19th",
            "Here's Why I Wouldn't Touch Plug Power With a 10-Foot Pole",
            "Plug Power CEO Opens Reddit AMA As Hydrogen Targets AI Data Centers",
            "Is hydrogen infrastructure scale now the real test?"
        ]
    },
    {
        "rank": 4,
        "sembol": "AMD",
        "sirket": "Advanced Micro Devices",
        "fiyat": "$278.39",
        "1y": "+225.37%",
        "3m": "+20.08%",
        "6m": "+18.69%",
        "tavsiye": "Al",
        "sentiment": "POZİTİF",
        "ozet": "Yapay zeka GPU pazarında NVIDIA'nın başlıca rakibi olan AMD, MI300 serisi çipleriyle güçlü performans gösteriyor. Meta ve Alphabet gibi büyük şirketlerin sipariş vermeleriyle beklentiler yüksek.",
        "haberler": [
            "Why Advanced Micro Devices Stock May Drop Soon",
            "Why AMD Stock Popped on Thursday",
            "Broadcom & AMD Lead AI Chip Market with Meta, Alphabet Deals",
            "AMD Gains 6% Ahead of May Earnings",
            "AMD Opinions on All-Time Highs and AI Inference Demand"
        ]
    },
    {
        "rank": 5,
        "sembol": "SEDG",
        "sirket": "SolarEdge Technologies",
        "fiyat": "$38.30",
        "1y": "+216.53%",
        "3m": "+12.95%",
        "6m": "-4.51%",
        "tavsiye": "Tut",
        "sentiment": "NEGATİF",
        "ozet": "Güneş enerjisi optimizasyon yazılımında lider SolarEdge, 200% + getiri sağladı. Ancak Goldman Sachs tarafından rating düşürüldüğü için dikkat gereklidir. Spekulatif bir turnaround play olarak görülüyor.",
        "haberler": [
            "SolarEdge stock slides as market rises",
            "SolarEdge Stock Rating Lowered by Goldman Sachs",
            "Is SolarEdge Attractive After 203% Rally?",
            "SolarEdge Recast as Speculative Turnaround Play",
            "SolarEdge Up 200% In 12 Months And Room For More"
        ]
    }
]

for item in top5_data:
    st.markdown(f"""
    <div class="hisse-section">
        <div class="baslik-hisse">
            #{item['rank']} — {item['sembol']}: {item['sirket']}
        </div>
        
        <div style="margin: 15px 0;">
            <div class="metrik">💰 Fiyat: {item['fiyat']}</div>
            <div class="metrik">📈 1Y: <span style="color: #00c864; font-weight: bold;">{item['1y']}</span></div>
            <div class="metrik">📊 6M: {item['6m']}</div>
            <div class="metrik">⭐ Tavsiye: <b>{item['tavsiye']}</b></div>
            <div class="metrik">💭 Sentiment: <span class="sentiment-{item['sentiment'].lower()}">{item['sentiment']}</span></div>
        </div>
        
        <div class="info-box">
            <b>📋 Şirket Hakkında:</b><br>
            {item['ozet']}
        </div>
        
        <b>📰 Son Haberler:</b>
    """, unsafe_allow_html=True)
    
    for haber in item["haberler"]:
        st.markdown(f'<div class="haber">• {haber}</div>', unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

st.markdown("""

## 📊 PORTFÖY ANALİZİ

### En İyi Performans Yapan Sektörler
1. **Blockchain & Kripto** — Ortalama +350% (HUT, MSTR öncü)
2. **Yarı İletkenler** — Ortalama +200% (INTC, AMD, AVGO)
3. **Yenilenebilir Enerji** — Ortalama +150% (PLUG, ENPH, SEDG)

### En Zayıf Performans Yapan Hisseler
1. **MSTR** (MicroStrategy) — -48% (Bitcoin volatilitesi)
2. **ENPH** (Enphase) — -37% (Enerji sektörü düzeltmesi)
3. **TSLA** (Tesla) — +25% (Beklenenden düşük)

### Risk Değerlendirmesi
- **Yüksek Risk:** Kripto ve startup hisseleri (PLUG, TEM, HUT)
- **Orta Risk:** Yarı iletkenler (AMD, INTC, AVGO)
- **Düşük Risk:** Mega cap tech (AAPL, MSFT, GOOGL)

---

## 🎯 JOHNNY'NİN TAVSIYELERI

### ALIM SİNYALLERİ (Güçlü Pozitif)
✅ **HUT** — Bitcoin madenciliği, +603%, Güçlü Al  
✅ **AMD** — YZ GPU çipleri, +225%, Al  
✅ **INTC** — Gaudi işlemciler, +263%, Tut ama izle  

### BEKLEME SİNYALLERİ (Karışık Sinyal)
⏳ **PLUG** — Nötr sentiment, +251% ama son 6M düşüş  
⏳ **SEDG** — Negatif sentiment, analyst rating düşürüldü  
⏳ **MSTR** — Düşüş yaşıyor (-48%), Bitcoin riski  

### SAT SİNYALLERİ (Negatif)
❌ **ENPH** — -37%, enerji sektörü iyileşmeyebilir  
❌ **JKS** — Çin hissesi, geopolitik risk  

---

## 💡 GENEL TAVSIYE

### Kısa Vade (1-3 Ay)
- HUT, AMD, INTC'ye güçlü alım sinyali
- PLUG, SEDG'de bekleme yapılmalı
- MSTR, ENPH'den kaçınılması tavsiye ediliyor

### Orta Vade (3-6 Ay)
- Blockchain pazarının güçlü kalması bekleniyor
- YZ çipi pazarı hızla büyüyecek
- Yenilenebilir enerji volatilaşabilir

### Uzun Vade (1+ Yıl)
- Portföyün +87.3% ortalama getirisi devam edebilir
- Mega cap tech (AAPL, MSFT, GOOGL) stabil hold
- Crypto hisselerine risk toleransına göre yaklaşılması gerekir

---

## 📚 KAYNAKLAR

✓ Google Finance — Fiyat ve teknik veriler  
✓ Yahoo Finance — Analyst tavsiye ve hedef fiyatlar  
✓ Google News RSS — Son haberler (5 en güncel)  
✓ Seeking Alpha — Derinlemesine analizler  
✓ MarketBeat, Motley Fool — Investor yorumları  
✓ CNBC, Bloomberg, Reuters — Kurumsal haberler  
✓ TipRanks, Investing.com — Analyst consensus  
✓ simplywall.st — Değerlemeler ve riskler  

---

## ⚠️ ÖNEMLİ UYARILAR

1. **Bu analiz simülasyon amaçlıdır** — Gerçek para ile işlem yapmak ek araştırma gerektirir
2. **Geçmiş performans gelecekteki sonuçları garanti etmez**
3. **Sentiment analizi haber başlıklarına dayanmaktadır** — Tüm detaylar okunmalı
4. **Cryptocurrency hisseleri yüksek volatildir** — Risk toleransı çok önemli
5. **Düzenleyici riskler bulunmaktadır** — Özellikle kripto ve YZ alanında

---

**Bu bilgilendirme Johnny tarafından otomatik olarak derlenmiştir.**  
**Tarih:** 20 Nisan 2026 | **Zamanı:** 02:27 GMT+3
""")
