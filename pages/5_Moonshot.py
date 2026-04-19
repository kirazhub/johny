#!/usr/bin/env python3
"""
Johnny Moonshot Sayfası
Önümüzdeki 3 ay içinde en yüksek kar potansiyeli olan 20 hisse
"""
import streamlit as st
import pandas as pd
import json

st.set_page_config(
    page_title="🚀 Johnny — Moonshot",
    page_icon="🚀",
    layout="wide"
)

# Modern Tema
st.markdown("""
<style>
    .stApp { 
        background: linear-gradient(135deg, #0a0e1a 0%, #0d1226 50%, #0a0e1a 100%);
        color: #e8eaf0; 
    }
    
    h1 { color: #ff6b6b; text-shadow: 0 0 20px rgba(255, 107, 107, 0.3); }
    h2 { color: #ff8787; }
    
    .moonshot-card {
        background: linear-gradient(135deg, rgba(255, 107, 107, 0.1), rgba(255, 136, 136, 0.05));
        border: 2px solid rgba(255, 107, 107, 0.3);
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 8px 32px rgba(255, 107, 107, 0.15);
    }
    
    .moonshot-card:hover {
        border: 2px solid rgba(255, 107, 107, 0.6);
        box-shadow: 0 12px 40px rgba(255, 107, 107, 0.25);
        transform: translateY(-5px);
    }
    
    .high-potential {
        color: #ff6b6b;
        font-weight: bold;
        font-size: 1.2rem;
    }
    
    .catalyst {
        background: rgba(17, 24, 39, 0.6);
        border-left: 3px solid #ff8787;
        padding: 12px;
        margin: 8px 0;
        border-radius: 4px;
    }
    
    .risk-high {
        color: #ff4444;
        font-weight: bold;
    }
    
    .risk-veryHigh {
        color: #ff0000;
        font-weight: bold;
    }
    
    .metrik {
        display: inline-block;
        background: rgba(17, 24, 39, 0.5);
        padding: 10px 15px;
        margin: 5px;
        border-radius: 6px;
        border-left: 3px solid #ff8787;
    }
</style>
""", unsafe_allow_html=True)

# Başlık
st.markdown("""
<div style="text-align: center; margin-bottom: 30px;">
    <h1>🚀 MOONSHOT HİSSELER</h1>
    <p style="color: #ff8787; font-size: 1.2rem;">Önümüzdeki 3 Ay — En Yüksek Kar Potansiyeli (20 Hisse)</p>
    <p style="color: #ffaa00; font-size: 0.9rem;">⚠️ UYARI: Yüksek Risk, Yüksek Getiri — Simülasyon Amaçlı</p>
</div>
""", unsafe_allow_html=True)

# Moonshot verilerini yükle
try:
    with open("moonshot/stocks.json", "r", encoding="utf-8") as f:
        moonshot_data = json.load(f)
except:
    st.error("Moonshot verileri yüklenemedi")
    moonshot_data = []

# CSV de yükle
try:
    df_moonshot = pd.read_csv("moonshot/stocks_summary.csv")
except:
    df_moonshot = pd.DataFrame()

# ===== ÖZETİ METRİKLER =====
st.subheader("📊 Moonshot Araştırması Özeti")

if moonshot_data:
    total_stocks = len(moonshot_data)
    avg_potential = sum([float(str(s.get('potential', '0')).replace('%', '')) for s in moonshot_data]) / total_stocks if moonshot_data else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🚀 Toplam Hisse", total_stocks)
    with col2:
        st.metric("📈 Ort. Potansiyel", f"+{avg_potential:.1f}%")
    with col3:
        st.metric("⏰ Zaman Aralığı", "3 Ay")
    with col4:
        st.metric("⚠️ Risk Seviyesi", "YÜKSEK")

st.markdown("---")

# ===== TOP 5 DETAYLI KARTLARı =====
st.subheader("🏆 Top 5 Moonshot Hisseler")

top5_info = [
    {
        "rank": 1,
        "sembol": "SERV",
        "sirket": "Serve Robotics",
        "fiyat": "$9.57",
        "hedef": "$18.00",
        "potansiyel": "+88%",
        "risk": "ÇOK YÜKSEK",
        "desc": "NVIDIA'nın desteklediği otonom teslimat robotları. Uber Eats ortaklığı genişlemesiyle momentum artıyor.",
        "kataliz": [
            "NVIDIA'nın direkt yatırımı",
            "Uber Eats ortaklığı genişlemesi",
            "Son mil teslimat pazarı büyümesi",
            "Los Angeles/SF agresif genişlemesi"
        ],
        "risk_list": [
            "Short float yüksek (%27.6)",
            "Henüz kârsız (cash burn)",
            "Amazon/Starship rekabeti",
            "Regülasyon riski"
        ]
    },
    {
        "rank": 2,
        "sembol": "MSTR",
        "sirket": "Strategy Inc (MicroStrategy)",
        "fiyat": "$166.52",
        "hedef": "$310.00",
        "potansiyel": "+86%",
        "risk": "YÜKSEK",
        "desc": "450.000+ Bitcoin tutan şirket. Bitcoin rallisinin kaldıraç etkisi ile %2-3x potansiyel.",
        "kataliz": [
            "Bitcoin rallisi devamı",
            "Kurumsal BTC adaptasyonu",
            "ETF büyümesi",
            "Saylor'ın BTC satın alma açıklamaları"
        ],
        "risk_list": [
            "Bitcoin %30+ düşerse shiddetli kayıp",
            "Tamamen BTC'ye bağımlı",
            "Kripto regülasyon riski",
            "Short float %11"
        ]
    },
    {
        "rank": 3,
        "sembol": "SOUN",
        "sirket": "SoundHound AI",
        "fiyat": "$8.08",
        "hedef": "$14.00",
        "potansiyel": "+73%",
        "risk": "ÇOK YÜKSEK",
        "desc": "Yapay zeka tabanlı ses tanıma/NLU teknolojisi. Enterprise B2B büyümesi hızlanıyor.",
        "kataliz": [
            "YZ sesi recognition pazarı patlaması",
            "Enterprise customer acquisitions",
            "Automotive OEM partnership'ler",
            "Cloud integration genişlemesi"
        ],
        "risk_list": [
            "Henüz kârsız startup",
            "Google/Amazon rekabeti",
            "Customer concentration riski",
            "Patent litigation riski"
        ]
    },
    {
        "rank": 4,
        "sembol": "RXRX",
        "sirket": "Recursion Pharmaceuticals",
        "fiyat": "$3.78",
        "hedef": "$6.50",
        "potansiyel": "+72%",
        "risk": "YÜKSEK",
        "desc": "AI-powered drug discovery platformu. Klinik trial başarıları potansiyel katalizör.",
        "kataliz": [
            "Klinik trial pozitif sonuçlar (Q2-Q3)",
            "FDA breakthrough designation",
            "Partnership anouncements",
            "AI pharma megatrendi"
        ],
        "risk_list": [
            "Klinik trial başarısı garantili değil",
            "Biotech oynaklığı",
            "Cash burn devam ediyor",
            "FDA regülasyon riski"
        ]
    },
    {
        "rank": 5,
        "sembol": "APLD",
        "sirket": "Applied Digital Holdings",
        "fiyat": "$31.53",
        "hedef": "$47.00",
        "potansiyel": "+49%",
        "risk": "YÜKSEK",
        "desc": "YZ training/inference altyapısı sağlayıcı. Data center boom momentum.",
        "kataliz": [
            "YZ data center talebi patlaması",
            "Nvidia partnership'ler",
            "Earnings beat beklentileri",
            "Cloud computing capex artışı"
        ],
        "risk_list": [
            "Yüksek valuation (P/S ratio)",
            "Rekabetçi pazar (CoreWeave, Lambda)",
            "Enerji maliyetleri yüksek",
            "Ekonomik downturn riski"
        ]
    }
]

for item in top5_info:
    st.markdown(f"""
    <div class="moonshot-card">
        <h3>#{item['rank']} — {item['sembol']}: {item['sirket']}</h3>
        
        <div style="margin: 15px 0;">
            <div class="metrik">💰 Fiyat: {item['fiyat']}</div>
            <div class="metrik">🎯 Hedef: {item['hedef']}</div>
            <div class="metrik">📈 Potansiyel: <span class="high-potential">{item['potansiyel']}</span></div>
            <div class="metrik">⚠️ Risk: <span class="risk-{'veryHigh' if 'ÇOK' in item['risk'] else 'high'}">{item['risk']}</span></div>
        </div>
        
        <p style="margin: 10px 0; color: #d0d0d0;">{item['desc']}</p>
        
        <b style="color: #ff8787;">🔥 Ana Katalizörler:</b>
    """, unsafe_allow_html=True)
    
    for kataliz in item["kataliz"]:
        st.markdown(f'<div class="catalyst">• {kataliz}</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
        <b style="color: #ff6b6b;">⚠️ Risk Faktörleri:</b>
    """, unsafe_allow_html=True)
    
    for risk in item["risk_list"]:
        st.markdown(f'<div class="catalyst">❌ {risk}</div>', unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ===== TÜMEL TABLO =====
st.subheader("📊 Tüm 20 Moonshot Hisseler — Özet Tablo")

if not df_moonshot.empty:
    st.dataframe(df_moonshot, use_container_width=True, height=600, hide_index=True)
else:
    st.warning("Tablo verileri yüklenemedi")

st.markdown("---")

# ===== DOWNLOAD =====
st.subheader("💾 Moonshot Dosyalarını İndir")

col1, col2, col3 = st.columns(3)

with col1:
    try:
        with open("moonshot/stocks_summary.csv", "r") as f:
            csv_data = f.read()
        st.download_button(
            label="📥 CSV (20 Hisse)",
            data=csv_data,
            file_name="moonshot_hisseler.csv",
            mime="text/csv"
        )
    except:
        st.error("CSV indirme başarısız")

with col2:
    try:
        with open("moonshot/TOP5_MOONSHOT_REPORT.md", "r") as f:
            md_data = f.read()
        st.download_button(
            label="📥 Markdown (Top 5)",
            data=md_data,
            file_name="moonshot_top5_rapor.md",
            mime="text/markdown"
        )
    except:
        st.error("Markdown indirme başarısız")

with col3:
    try:
        with open("moonshot/stocks.json", "r") as f:
            json_data = f.read()
        st.download_button(
            label="📥 JSON (Tüm Veriler)",
            data=json_data,
            file_name="moonshot_tum.json",
            mime="application/json"
        )
    except:
        st.error("JSON indirme başarısız")

st.markdown("---")

# ===== UYARILAR =====
st.warning("""
### ⚠️ MOONSHOT HİSSELER UYARISI

**Bu hisseler düşük likidite, yüksek oynaklık ve kayıp riski taşır:**

1. **Yüksek Getiri ≠ Garantili Getiri**
   - %88 potansiyel = %88 kayıp de mümkün
   - Startup hisseleri çok değişken

2. **Risk Yönetimi Şart**
   - Portföyün max %3-5'ini moonshot'a ayır
   - Stop-loss mutlaka kur
   - Gelirden çok almayan paralarla oyna

3. **Zaman Aralığı: 3 Ay**
   - 3 aydan sonra pozisyon kapat (kar veya zarar)
   - Long-term hold değil, spec trade

4. **Katalizörleri Takip Et**
   - FDA haberlerini izle (ilaç hisseleri)
   - Earnings dates'ini not al
   - Partnership anuncements'ları dinle

5. **Simülasyon Amaçlı**
   - Johnny virtual trading yapıyor
   - Gerçek para için daha derinlemesine araştırma gerekli
   - Profesyonel danışmanlık alın

### 💡 Moonshot Stratejisi

```
Giriş Planı:
1. Günlük performans izle
2. Teknik sinyal bekle
3. Entry point'te (2-3 gun) kademeli gir
4. Stop-loss kur ve TUT
5. 3 ay sonra çık (kar/zarar fark etmiyor)

Pozisyon Boyutu:
- Tek moonshot: Portföyün %3-5'i
- Tüm moonshots (3-4 adete): Portföyün max %15'i
```

**BAŞARISIZ MOONSHOT ÖRNEĞİ:** SERV'e %5 giredin → Şirket kapatılırsa → -100%  
**BAŞARILI MOONSHOT ÖRNEĞİ:** SERV'e %5 giredin → %88 kazanç → +4.4% portföye katkı
""")

st.markdown("---")

st.markdown("""
<div style="text-align: center; color: #ff8787; padding: 20px;">
    <p><b>🚀 Johnny'nin Moonshot Araştırması</b> — 20 Hisse, 3 Ay</p>
    <p>Veriler 2026-04-20 tarihinde toplandı</p>
    <p style="color: #ffaa00; font-size: 0.9rem;">⚠️ Simülasyon Amaçlı — Yatırım Tavsiyesi Değildir</p>
</div>
""", unsafe_allow_html=True)
