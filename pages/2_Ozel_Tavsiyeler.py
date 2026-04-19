#!/usr/bin/env python3
"""
Johnny Özel Tavsiyeler
Raif'in seçtikleri hisseler: HOOD (Robinhood) + TEM (Tempus AI)
"""
import streamlit as st

st.set_page_config(
    page_title="⭐ Johnny — Özel Tavsiyeler",
    page_icon="⭐",
    layout="wide"
)

# Modern Tema
st.markdown("""
<style>
    .stApp { 
        background: linear-gradient(135deg, #0a0e1a 0%, #0d1226 50%, #0a0e1a 100%);
        color: #e8eaf0; 
    }
    
    h1 { color: #ffd700; text-shadow: 0 0 20px rgba(255, 215, 0, 0.3); font-size: 2.5rem; }
    h2 { color: #ffcc00; }
    
    .special-card {
        background: linear-gradient(135deg, rgba(255, 215, 0, 0.1), rgba(255, 200, 0, 0.05));
        border: 2px solid #ffd700;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 0 30px rgba(255, 215, 0, 0.2);
    }
    
    .buy-signal {
        background: linear-gradient(135deg, rgba(0, 200, 100, 0.15), rgba(0, 150, 80, 0.1));
        border-left: 4px solid #00c864;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .wait-signal {
        background: linear-gradient(135deg, rgba(255, 200, 0, 0.15), rgba(255, 150, 0, 0.1));
        border-left: 4px solid #ffcc00;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .metric-box {
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(255, 215, 0, 0.4);
        border-radius: 12px;
        padding: 15px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Hero
st.markdown("""
<div style="text-align: center; margin-bottom: 30px;">
    <h1>⭐ ÖZEL TAVSIYELER</h1>
    <p style="color: #ffd700; font-size: 1.2rem;">Raif'in Seçtiği Hisseler</p>
</div>
""", unsafe_allow_html=True)

# ===== ROBINHOOD (HOOD) =====
st.markdown("## 1️⃣ ROBINHOOD (HOOD)")

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("""
    <div class="special-card">
    <b>📊 HOOD</b><br>
    Robinhood Markets<br><br>
    🌐 Fintek + Kripto<br>
    💰 Trading Platform<br>
    🚀 Büyüme Potansiyeli
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    **Ne Yapıyor?**
    - Hisse, kripto, opsiyon ticareti
    - Yeni nesil perakende yatırımcıları hedefliyor
    - Düşük komisyonlar, kullanıcı dostu platform
    
    **Neden İlginç?**
    - Fintek sektöründe güçlü büyüme
    - Kripto entegrasyonu (popüler taş)
    - Genç kullanıcı tabanı (expansion opportunity)
    - Gen-Z ve Millennials'ı çekiyor
    """)

st.markdown("""
<div class="buy-signal">
    <b>✅ ALIM TAVSİYESİ</b><br>
    <b>Strateji:</b> Kademeli alım (DCA — Dollar Cost Averaging)<br>
    • Toplam alım: 5.000 USD (20K portföyün %25'i)<br>
    • Aylık alım: 1.000-1.500 USD<br>
    • Bekleme süresi: 6-12 ay minimum<br>
    • Hedef Fiyat: Uzun vadede x2-x3
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="wait-signal">
    <b>⏳ BEKLEME STRATEJİSİ</b><br>
    • Alım yapılırken bir an ağırbaşlı olunacak<br>
    • Aylar içinde yavaş yavaş pozisyon açılacak<br>
    • Kısa vadeli dalgalanmalara aldırılmayacak<br>
    • Uzun dönem (1-2 yıl) elde tutulacak
</div>
""", unsafe_allow_html=True)

# ===== TEMPUS (TEM) =====
st.markdown("## 2️⃣ TEMPUS AI (TEM)")

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("""
    <div class="special-card">
    <b>🧬 TEM</b><br>
    Tempus AI<br><br>
    🤖 Precision Oncology<br>
    🧠 YZ + Biyoteknoloji<br>
    💊 Kanser Tedavisi
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    **Ne Yapıyor?**
    - AI-powered kanser teşhisi ve tedavi
    - Genomik data analizi
    - Hastalar için kişiselleştirilmiş tedavi
    
    **Neden İlginç?**
    - Sağlık AI'nin en önemli alanlarından biri
    - Büyük pazar potansiyeli (kanser tedavisi)
    - Yapay zeka + biyoteknoloji kombinasyonu
    - Startup momentum (IPO sonrası büyüme)
    """)

st.markdown("""
<div class="buy-signal">
    <b>✅ ALIM TAVSİYESİ</b><br>
    <b>Strateji:</b> Agresif ama kontrollü alım<br>
    • Toplam alım: 3.000 USD (20K portföyün %15'i)<br>
    • Aylık alım: 500-750 USD<br>
    • Bekleme süresi: 2-3 yıl minimum<br>
    • Hedef Fiyat: Başarı durumunda x5-x10
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="wait-signal">
    <b>⏳ BEKLEME STRATEJİSİ</b><br>
    • Tempatif (startuplar volatile olabilir)<br>
    • Yavaş yavaş pozisyon oluşturulacak<br>
    • Aşırı alımdan kaçınılacak<br>
    • Uzun dönem elde tutulacak (şirket büyüyene kadar)
</div>
""", unsafe_allow_html=True)

# ===== ÖZET TABLO =====
st.divider()

st.subheader("📊 Karşılaştırma")

comp_data = {
    "Hisse": ["HOOD", "TEM"],
    "Sektör": ["Fintek + Kripto", "Healthcare AI"],
    "Risk": ["Orta", "Yüksek"],
    "Potansiyel": ["x2-x3", "x5-x10"],
    "Bekleme": ["6-12 ay", "2-3 yıl"],
    "Alım": ["5.000 USD", "3.000 USD"],
    "Strateji": ["DCA (Aylık)", "DCA (Aylık)"]
}

import pandas as pd
df = pd.DataFrame(comp_data)
st.dataframe(df, use_container_width=True, hide_index=True)

# ===== GENEL TAVSİYE =====
st.divider()

st.subheader("🎯 Genel Strateji")

st.markdown("""
### Raif'in Portföy Planı

**Johnny'nin 20.000 USD portföyünden:**

1. **HOOD'a 5.000 USD (25%)**
   - Fintek büyümesi + kripto trend
   - Momentum play, orta vadeli

2. **TEM'e 3.000 USD (15%)**
   - Healthcare AI megatrendi
   - Uzun vadeli büyüme

3. **Diğer tema hisseleri: 12.000 USD (60%)**
   - Blockchain (25%) → Kripto hedge
   - Mega Cap (30%) → Stability
   - YZ & Tech (25%) → Growth
   - Enerji (20%) → Diversification

### 📅 Zaman Çizelgesi

```
Ay 1: HOOD 1.500 USD + TEM 750 USD
Ay 2: HOOD 1.200 USD + TEM 600 USD  
Ay 3: HOOD 1.200 USD + TEM 600 USD
Ay 4: HOOD 1.100 USD + TEM 1.050 USD

6 Ay Sonrası: Pozisyonları değerlendir
```

### ⚙️ Risk Yönetimi

- **Stop-Loss:** -%8 (başlangıç fiyatından)
- **Take-Profit:** %50 kazanç → kısmi sat (1/3)
- **Monitoring:** Aylık review
- **Bekleme:** Kısa vadeli fiyat dalgalanmalarına takılmamak

### 💡 Dikkat Noktaları

⚠️ **HOOD (Orta Risk)**
- Regulatory risk (fintek düzenlemeleri)
- Kripto volatilitesi
- Rekabet (E-TRADE, TD Ameritrade)

⚠️ **TEM (Yüksek Risk)**
- Startup (IPO sonrası)
- Klinik trial başarısı kritik
- Biyoteknoloji doğal volatilitesi

### ✅ Yapılacaklar

- [ ] Aylık alım takvimi oluştur
- [ ] Stop-loss order'larını kur
- [ ] Portföy rebalancing (3 ayda bir)
- [ ] Haberleri takip et (FDA, earnings)
- [ ] Bekleme disiplini göster (panic selling yok!)
""")

st.divider()

st.markdown("""
<div style="text-align: center; color: #ffd700; padding: 20px; border: 1px solid rgba(255, 215, 0, 0.3); border-radius: 8px;">
    <p><b>⭐ Bu tavsiyeler Raif tarafından seçilmiştir.</b></p>
    <p>Johnny, bu hisseleri portföyüne kademeli olarak alacak ve uzun vadede bekleyecektir.</p>
    <p>💰 Hediflenen Getiri: %200-300+ (2-3 yıl)</p>
</div>
""", unsafe_allow_html=True)
