"""
JOHNY — US Markets Dashboard
10 Sayfa | Port: 8503 | Türkçe UI
"""
import sys
import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from johny_config import (
    US_SEMBOLLER, SEKTOR_GRUPLARI, SEKTOR_RENKLERI, DASHBOARD_TITLE,
    PORTFOY_PARAMETRELERI, VERSIYON
)

logger = logging.getLogger(__name__)

# ─── Streamlit Sayfa Ayarları ─────────────────────────────────────────────────
st.set_page_config(
    page_title="🇺🇸 JOHNY — US Markets",
    page_icon="🇺🇸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Koyu Lacivert Tema ───────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Ana arka plan — koyu lacivert */
    .stApp { background-color: #0a0e1a; color: #e8eaf0; }
    section[data-testid="stSidebar"] { background-color: #0d1226; border-right: 1px solid #1e2a4a; }
    .stMetric { background-color: #111827; border-radius: 8px; padding: 12px; border: 1px solid #1e3a5f; }
    .stMetric label { color: #8ba7d0 !important; font-size: 0.75rem !important; }
    .stMetric [data-testid="stMetricValue"] { color: #ffffff !important; font-weight: bold; }
    .stButton>button {
        background: linear-gradient(135deg, #1a3a6e, #0d5cbf);
        color: white; border: none; border-radius: 6px;
    }
    .stButton>button:hover { background: linear-gradient(135deg, #0d5cbf, #1a3a6e); }
    h1 { color: #4a9eff; }
    h2, h3 { color: #8ba7d0; }
    .stDataFrame { border: 1px solid #1e3a5f; border-radius: 8px; }
    .stSelectbox label, .stSlider label { color: #8ba7d0; }
    div[data-testid="stTab"] button { color: #8ba7d0; }
    div[data-testid="stTab"] button[aria-selected="true"] { color: #4a9eff; border-bottom-color: #4a9eff; }
    .hero-header {
        background: linear-gradient(135deg, #0d1f3c 0%, #1a3a6e 50%, #0d1f3c 100%);
        border: 1px solid #2a4a8e;
        border-radius: 12px; padding: 20px; margin-bottom: 20px;
        text-align: center;
    }
    .sinyal-al { background: rgba(0,200,100,0.15); border-left: 3px solid #00c864; padding: 4px 8px; border-radius: 4px; }
    .sinyal-sat { background: rgba(220,50,50,0.15); border-left: 3px solid #dc3232; padding: 4px 8px; border-radius: 4px; }
    .sinyal-notr { background: rgba(200,200,50,0.1); border-left: 3px solid #c8c832; padding: 4px 8px; border-radius: 4px; }
    .stars { color: #ffd700; font-size: 1.2rem; }
</style>
""", unsafe_allow_html=True)

# ─── Ajan Singleton ──────────────────────────────────────────────────────────
@st.cache_resource
def get_ajan():
    """JOHNY ajanını oluştur"""
    try:
        from johny_main import JohnyAjani
        ajan = JohnyAjani()
        return ajan
    except Exception as e:
        st.error(f"Ajan yüklenemedi: {e}")
        return None


def veri_guncelle_cached(ajan) -> None:
    """Otomatik veri güncelleme"""
    if ajan is None:
        return
    son_guncelleme = st.session_state.get("son_guncelleme", 0)
    if time.time() - son_guncelleme > 30:
        try:
            ajan.veri_guncelle()
            st.session_state["son_guncelleme"] = time.time()
        except Exception as e:
            logger.error(f"Veri güncelleme hatası: {e}")


# ─── Yardımcı Fonksiyonlar ────────────────────────────────────────────────────
def renk_html(deger: float, format_str: str = "+.2f") -> str:
    """Renkli sayı HTML"""
    renk = "#00c864" if deger >= 0 else "#ff4444"
    return f'<span style="color:{renk};font-weight:bold">{deger:{format_str}}</span>'


def piyasa_durumu_badge(durum: str, renk: str) -> str:
    renkler = {"green": "#00c864", "orange": "#ff9500", "red": "#ff4444", "blue": "#4a9eff", "gray": "#888"}
    hex_r = renkler.get(renk, "#888")
    return f'<span style="background:{hex_r};color:white;padding:3px 10px;border-radius:12px;font-size:0.85rem;font-weight:bold">{durum}</span>'


# ─── SAYFA 1: Genel Bakış ─────────────────────────────────────────────────────
def sayfa_genel_bakis(ajan) -> None:
    st.markdown("""
    <div class="hero-header">
        <h1 style="margin:0;font-size:2.5rem">🇺🇸 JOHNY</h1>
        <p style="color:#8ba7d0;margin:4px 0">US Stock Market Simülasyon Ajanı</p>
        <p class="stars">★ ★ ★ ★ ★</p>
    </div>
    """, unsafe_allow_html=True)

    if ajan is None:
        st.error("Ajan yüklenemedi.")
        return

    ozet = ajan.portfoy.pozisyon_ozeti()
    piyasa = ajan.piyasa_durumu_cache or {}
    usdtry = ajan.usdtry_cache or 32.0
    fg = ajan.fear_greed_cache or {}

    # Piyasa durumu
    durum = piyasa.get("durum", "Bilinmiyor")
    renk = piyasa.get("renk", "gray")
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        st.markdown(f"**Piyasa:** {piyasa_durumu_badge(durum, renk)}", unsafe_allow_html=True)
    with c2:
        est_saat = piyasa.get("simdi_est", "N/A")
        st.markdown(f"**EST:** `{est_saat}`", unsafe_allow_html=True)
    with c3:
        st.markdown(f"**USD/TRY:** `{usdtry:.2f}`", unsafe_allow_html=True)

    if piyasa.get("acik"):
        kapanisina = piyasa.get("kapanisina", "")
        if kapanisina:
            st.info(f"⏱ Kapanışa: **{kapanisina}**")
    elif piyasa.get("pre_market"):
        acilisina = piyasa.get("acilisina", "")
        if acilisina:
            st.info(f"🌅 Pre-Market — Açılışa: **{acilisina}**")

    st.divider()

    # Ana metrikler
    portfoy_usd = ozet.get("portfoy_degeri_usd", 0)
    portfoy_tl = portfoy_usd * usdtry
    kz_usd = ozet.get("toplam_kar_zarar_usd", 0)
    kz_pct = (kz_usd / PORTFOY_PARAMETRELERI["baslangic_sermayesi"]) * 100 if PORTFOY_PARAMETRELERI["baslangic_sermayesi"] > 0 else 0
    bugun_kz = ozet.get("bugun_kar_zarar_usd", 0)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("💰 Portföy (USD)", f"${portfoy_usd:,.2f}", f"${kz_usd:+,.2f}")
    with col2:
        st.metric("🇹🇷 Portföy (TL)", f"₺{portfoy_tl:,.0f}")
    with col3:
        kz_delta = f"{kz_pct:+.2f}%"
        st.metric("📊 Toplam K/Z", f"${kz_usd:+,.2f}", kz_delta)
    with col4:
        st.metric("📅 Bugün K/Z", f"${bugun_kz:+,.2f}")
    with col5:
        nakit = ozet.get("nakit_usd", 0)
        st.metric("💵 Nakit", f"${nakit:,.2f}")

    st.divider()

    # Fear & Greed + Açık Pozisyonlar
    left_col, right_col = st.columns([1, 2])

    with left_col:
        st.subheader("🧭 Fear & Greed Index")
        fg_deger = fg.get("deger", 50)
        fg_sinif = fg.get("siniflandirma", "Neutral")
        fg_renk = "#ff4444" if fg_deger < 25 else "#ff9500" if fg_deger < 45 else "#ffcc00" if fg_deger < 55 else "#80cc44" if fg_deger < 75 else "#00c864"
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=fg_deger,
            title={"text": fg_sinif, "font": {"color": "#8ba7d0"}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#8ba7d0"},
                "bar": {"color": fg_renk},
                "bgcolor": "#111827",
                "steps": [
                    {"range": [0, 25], "color": "#3d0f0f"},
                    {"range": [25, 45], "color": "#3d2000"},
                    {"range": [45, 55], "color": "#2d2d00"},
                    {"range": [55, 75], "color": "#0d2d0d"},
                    {"range": [75, 100], "color": "#0d3d0d"},
                ],
                "threshold": {"line": {"color": "white", "width": 2}, "thickness": 0.75, "value": fg_deger},
            },
            number={"font": {"color": fg_renk, "size": 40}},
        ))
        fig_gauge.update_layout(
            height=220, paper_bgcolor="#111827", font_color="#8ba7d0", margin=dict(t=30, b=10)
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

        # SPY benchmark
        st.subheader("📈 SPY Karşılaştırma")
        poz_sayisi = ozet.get("pozisyon_sayisi", 0)
        st.metric("Açık Pozisyon", f"{poz_sayisi} / {PORTFOY_PARAMETRELERI['max_pozisyon_sayisi']}")
        nakit_pct = (ozet.get("nakit_usd", 0) / portfoy_usd * 100) if portfoy_usd > 0 else 100
        st.metric("Nakit Oranı", f"{nakit_pct:.1f}%")

    with right_col:
        st.subheader("📁 Açık Pozisyonlar")
        pozisyonlar = ozet.get("pozisyonlar", [])
        if pozisyonlar:
            poz_df = pd.DataFrame(pozisyonlar)
            display_cols = ["sembol", "lot", "giris_fiyat", "mevcut_fiyat", "kar_zarar_usd", "kar_zarar_pct", "deger_usd", "strateji"]
            existing = [c for c in display_cols if c in poz_df.columns]

            def stil_uygula(val):
                if isinstance(val, (int, float)):
                    return "color: #00c864" if val >= 0 else "color: #ff4444"
                return ""

            poz_df_display = poz_df[existing].copy()
            poz_df_display.columns = ["Sembol", "Lot", "Giriş $", "Mevcut $", "K/Z $", "K/Z %", "Değer $", "Strateji"][:len(existing)]
            st.dataframe(poz_df_display, use_container_width=True, hide_index=True)
        else:
            st.info("📭 Açık pozisyon yok")

    # Sinyaller
    st.divider()
    st.subheader("🔔 Güncel Sinyaller")
    sinyaller = ajan.sinyaller
    if sinyaller:
        sinyal_listesi = sinyaller[:10]
        cols = st.columns(len(sinyal_listesi) if len(sinyal_listesi) <= 5 else 5)
        for i, s in enumerate(sinyal_listesi[:5]):
            with cols[i]:
                sembol = s.get("sembol", "")
                sinyal = s.get("birlesik_sinyal", 0)
                tavsiye = s.get("tavsiye", "")
                renk_s = "#00c864" if sinyal > 0.3 else "#ff4444" if sinyal < -0.3 else "#ffcc00"
                st.markdown(
                    f'<div style="background:#111827;border:1px solid {renk_s};border-radius:8px;padding:10px;text-align:center">'
                    f'<b style="color:{renk_s}">{sembol}</b><br>'
                    f'<small style="color:#8ba7d0">{tavsiye}</small><br>'
                    f'<b style="color:{renk_s}">{sinyal:+.3f}</b>'
                    f'</div>',
                    unsafe_allow_html=True
                )
    else:
        st.info("Henüz sinyal yok. Verileri güncelleyin.")


# ─── SAYFA 2: S&P Isı Haritası ───────────────────────────────────────────────
def sayfa_isi_haritasi(ajan) -> None:
    st.header("🌡️ S&P 500 Isı Haritası")

    if ajan is None:
        st.error("Ajan yüklenemedi.")
        return

    fiyat_verisi = ajan.fiyat_verisi or {}
    if not fiyat_verisi:
        st.warning("Fiyat verisi yükleniyor...")
        if st.button("Veriyi Yenile"):
            ajan.veri_guncelle(zorunlu=True)
            st.rerun()
        return

    # Treemap verisi hazırla
    semboller_lst = []
    sektorler = []
    degisimler = []
    renkler = []
    fiyatlar = []
    boyutlar = []

    for sektor, sembol_listesi in SEKTOR_GRUPLARI.items():
        for sembol in sembol_listesi:
            if sembol in fiyat_verisi:
                v = fiyat_verisi[sembol]
                degisim = v.get("degisim_yuzde", 0)
                fiyat = v.get("fiyat", 1)
                semboller_lst.append(sembol)
                sektorler.append(sektor)
                degisimler.append(degisim)
                renkler.append(degisim)
                fiyatlar.append(fiyat)
                boyutlar.append(max(abs(fiyat), 1))

    if not semboller_lst:
        st.warning("Treemap için veri yok")
        return

    # Plotly treemap
    fig = go.Figure(go.Treemap(
        labels=semboller_lst,
        parents=sektorler,
        values=boyutlar,
        customdata=list(zip(fiyatlar, degisimler)),
        hovertemplate="<b>%{label}</b><br>Fiyat: $%{customdata[0]:.2f}<br>Değişim: %{customdata[1]:+.2f}%<extra></extra>",
        texttemplate="<b>%{label}</b><br>%{customdata[1]:+.1f}%",
        textfont={"size": 12, "color": "white"},
        marker={
            "colors": renkler,
            "colorscale": [
                [0.0, "#8b0000"],
                [0.3, "#cc3333"],
                [0.45, "#444444"],
                [0.55, "#444444"],
                [0.7, "#336633"],
                [1.0, "#00aa44"],
            ],
            "cmid": 0,
            "showscale": True,
            "colorbar": {
                "title": "% Değişim",
                "tickfont": {"color": "#8ba7d0"},
                "titlefont": {"color": "#8ba7d0"},
            },
        },
    ))
    fig.update_layout(
        height=600,
        paper_bgcolor="#0a0e1a",
        plot_bgcolor="#0a0e1a",
        font_color="#8ba7d0",
        margin=dict(t=10, b=10, l=10, r=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Sektör özet tablosu
    st.subheader("📊 Sektör Özeti")
    sektor_ozet: List[dict] = []
    for sektor, sembol_listesi in SEKTOR_GRUPLARI.items():
        degisim_listesi = []
        for s in sembol_listesi:
            if s in fiyat_verisi:
                degisim_listesi.append(fiyat_verisi[s].get("degisim_yuzde", 0))
        if degisim_listesi:
            sektor_ozet.append({
                "Sektör": sektor,
                "Ort. Değişim %": round(np.mean(degisim_listesi), 2),
                "En İyi": max(degisim_listesi),
                "En Kötü": min(degisim_listesi),
                "Hisse Sayısı": len(degisim_listesi),
            })
    if sektor_ozet:
        st.dataframe(pd.DataFrame(sektor_ozet), use_container_width=True, hide_index=True)


# ─── SAYFA 3: Hisse Tarayıcı ─────────────────────────────────────────────────
def sayfa_hisse_tarayici(ajan) -> None:
    st.header("📡 Hisse Tarayıcı")

    if ajan is None:
        st.error("Ajan yüklenemedi.")
        return

    # Filtreler
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        sektor_filtre = st.selectbox("Sektör", ["Tümü"] + list(SEKTOR_GRUPLARI.keys()))
    with col_f2:
        sinyal_filtre = st.selectbox("Sinyal", ["Tümü", "AL", "SAT", "NÖTR"])
    with col_f3:
        sort_by = st.selectbox("Sırala", ["Değişim %", "Hacim", "Sinyal Skoru", "Sembol"])
    with col_f4:
        if st.button("🔄 Tara"):
            ajan.veri_guncelle(zorunlu=True)
            ajan.sinyal_taramasi_yap()
            st.rerun()

    fiyat_verisi = ajan.fiyat_verisi or {}
    sinyaller_dict = {s.get("sembol", ""): s for s in (ajan.sinyaller or [])}

    satırlar: List[dict] = []
    semboller_goster = []

    if sektor_filtre == "Tümü":
        semboller_goster = US_SEMBOLLER
    else:
        semboller_goster = SEKTOR_GRUPLARI.get(sektor_filtre, [])

    for sembol in semboller_goster:
        veri = fiyat_verisi.get(sembol, {})
        sinyal_data = sinyaller_dict.get(sembol, {})
        sinyal_skoru = sinyal_data.get("birlesik_sinyal", 0)
        tavsiye = sinyal_data.get("tavsiye", "—")

        fiyat = veri.get("fiyat", 0)
        degisim = veri.get("degisim_yuzde", 0)
        hacim = veri.get("hacim", 0)

        if sinyal_filtre == "AL" and sinyal_skoru <= 0.3:
            continue
        if sinyal_filtre == "SAT" and sinyal_skoru >= -0.3:
            continue
        if sinyal_filtre == "NÖTR" and abs(sinyal_skoru) > 0.3:
            continue

        sektor = "—"
        for s, lst in SEKTOR_GRUPLARI.items():
            if sembol in lst:
                sektor = s
                break

        satırlar.append({
            "Sembol": sembol,
            "Fiyat $": fiyat,
            "Değişim %": degisim,
            "Hacim (M)": round(hacim / 1_000_000, 1),
            "Sinyal": round(sinyal_skoru, 3),
            "Tavsiye": tavsiye,
            "Sektör": sektor,
        })

    if not satırlar:
        st.warning("Filtreye uygun hisse bulunamadı")
        return

    df_tarayici = pd.DataFrame(satırlar)

    if sort_by == "Değişim %":
        df_tarayici = df_tarayici.sort_values("Değişim %", ascending=False)
    elif sort_by == "Hacim":
        df_tarayici = df_tarayici.sort_values("Hacim (M)", ascending=False)
    elif sort_by == "Sinyal Skoru":
        df_tarayici = df_tarayici.sort_values("Sinyal", ascending=False)

    # Renkli gösterim
    def renk_degisim(val):
        if isinstance(val, float):
            return f"color: #00c864" if val >= 0 else f"color: #ff4444"
        return ""

    styled = df_tarayici.style.applymap(renk_degisim, subset=["Değişim %", "Sinyal"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # Mini bar chart
    if len(df_tarayici) > 0:
        fig_bar = px.bar(
            df_tarayici.head(20),
            x="Sembol", y="Değişim %",
            color="Değişim %",
            color_continuous_scale=["#cc3333", "#444444", "#00aa44"],
            color_continuous_midpoint=0,
            title="Top 20 Günlük Değişim",
        )
        fig_bar.update_layout(
            height=300, paper_bgcolor="#0a0e1a", plot_bgcolor="#111827",
            font_color="#8ba7d0", showlegend=False,
        )
        fig_bar.update_traces(textfont_color="white")
        st.plotly_chart(fig_bar, use_container_width=True)


# ─── SAYFA 4: Hisse Detay ────────────────────────────────────────────────────
def sayfa_hisse_detay(ajan) -> None:
    st.header("🔍 Hisse Detay")

    if ajan is None:
        st.error("Ajan yüklenemedi.")
        return

    col_s1, col_s2 = st.columns([1, 3])
    with col_s1:
        sembol = st.selectbox("Sembol Seç", US_SEMBOLLER)
    with col_s2:
        donem = st.selectbox("Dönem", ["1mo", "3mo", "6mo", "1y", "2y"], index=2)

    if not sembol:
        return

    # Veri çek
    with st.spinner(f"{sembol} verisi yükleniyor..."):
        df = ajan.fetcher.hisse_verisi_cek(sembol, donem=donem)
        df_teknik = ajan.fetcher.teknik_gostergeler_hesapla(df) if df is not None else None

    if df_teknik is None or df_teknik.empty:
        st.warning(f"{sembol} için veri bulunamadı")
        return

    # Detaylı bilgi
    with st.spinner("Detaylı bilgi alınıyor..."):
        try:
            detay = ajan.fetcher.detayli_hisse_bilgisi(sembol)
        except Exception:
            detay = {}

    info = detay.get("info", {})
    put_call = detay.get("put_call_orani", 1.0)
    earnings = detay.get("earnings_tarihi", "N/A")

    # Üst bilgi
    uzun_ad = info.get("long_name", sembol)
    sektor = info.get("sektor", "N/A")
    piyasa_d = info.get("piyasa_degeri", 0)
    fiyat_verisi = ajan.fiyat_verisi.get(sembol, {})
    fiyat = fiyat_verisi.get("fiyat", float(df_teknik["Close"].iloc[-1]))
    degisim = fiyat_verisi.get("degisim_yuzde", 0)

    st.markdown(f"### {uzun_ad} ({sembol})")
    mc1, mc2, mc3, mc4, mc5 = st.columns(5)
    with mc1:
        st.metric("Fiyat", f"${fiyat:.2f}", f"{degisim:+.2f}%")
    with mc2:
        st.metric("Sektör", sektor)
    with mc3:
        mc_str = f"${piyasa_d/1e12:.2f}T" if piyasa_d >= 1e12 else f"${piyasa_d/1e9:.1f}B"
        st.metric("Piyasa Değeri", mc_str)
    with mc4:
        st.metric("P/E Oranı", f"{info.get('pe_orani', 'N/A')}")
    with mc5:
        st.metric("Beta", f"{info.get('beta', 'N/A')}")

    # Candlestick + Göstergeler
    st.subheader("📊 Teknik Analiz")
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.5, 0.15, 0.2, 0.15],
        subplot_titles=["Mum Grafiği", "Hacim", "MACD", "RSI"],
    )

    # Mum grafiği
    fig.add_trace(go.Candlestick(
        x=df_teknik.index,
        open=df_teknik["Open"],
        high=df_teknik["High"],
        low=df_teknik["Low"],
        close=df_teknik["Close"],
        name=sembol,
        increasing_fillcolor="#00c864",
        decreasing_fillcolor="#ff4444",
        increasing_line_color="#00c864",
        decreasing_line_color="#ff4444",
    ), row=1, col=1)

    # EMAs
    for ema, renk, isim in [("EMA21", "#4a9eff", "EMA21"), ("EMA50", "#ff9500", "EMA50"), ("EMA200", "#ff69b4", "EMA200")]:
        if ema in df_teknik.columns:
            fig.add_trace(go.Scatter(x=df_teknik.index, y=df_teknik[ema], name=isim, line=dict(color=renk, width=1)), row=1, col=1)

    # Bollinger Bands
    if "BB_Ust" in df_teknik.columns:
        fig.add_trace(go.Scatter(x=df_teknik.index, y=df_teknik["BB_Ust"], name="BB Üst", line=dict(color="#666", width=1, dash="dot"), showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_teknik.index, y=df_teknik["BB_Alt"], name="BB Alt", line=dict(color="#666", width=1, dash="dot"), fill="tonexty", fillcolor="rgba(100,100,200,0.05)", showlegend=False), row=1, col=1)

    # Hacim
    hacim_renkler = ["#00c864" if c >= o else "#ff4444" for c, o in zip(df_teknik["Close"], df_teknik["Open"])]
    fig.add_trace(go.Bar(x=df_teknik.index, y=df_teknik["Volume"], name="Hacim", marker_color=hacim_renkler, showlegend=False), row=2, col=1)
    if "Hacim_MA" in df_teknik.columns:
        fig.add_trace(go.Scatter(x=df_teknik.index, y=df_teknik["Hacim_MA"], name="Hacim MA", line=dict(color="#ff9500", width=1), showlegend=False), row=2, col=1)

    # MACD
    if "MACD" in df_teknik.columns:
        macd_renkler = ["#00c864" if v >= 0 else "#ff4444" for v in df_teknik["MACD_Hist"]]
        fig.add_trace(go.Bar(x=df_teknik.index, y=df_teknik["MACD_Hist"], name="MACD Hist", marker_color=macd_renkler, showlegend=False), row=3, col=1)
        fig.add_trace(go.Scatter(x=df_teknik.index, y=df_teknik["MACD"], name="MACD", line=dict(color="#4a9eff", width=1), showlegend=False), row=3, col=1)
        fig.add_trace(go.Scatter(x=df_teknik.index, y=df_teknik["MACD_Sinyal"], name="Sinyal", line=dict(color="#ff9500", width=1), showlegend=False), row=3, col=1)

    # RSI
    if "RSI" in df_teknik.columns:
        fig.add_trace(go.Scatter(x=df_teknik.index, y=df_teknik["RSI"], name="RSI", line=dict(color="#9b59b6", width=1.5), showlegend=False), row=4, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="#ff4444", row=4, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="#00c864", row=4, col=1)

    fig.update_layout(
        height=700, paper_bgcolor="#0a0e1a", plot_bgcolor="#111827",
        font_color="#8ba7d0", xaxis_rangeslider_visible=False,
        legend=dict(bgcolor="#111827", font_color="#8ba7d0"),
        margin=dict(t=40, b=20),
    )
    fig.update_xaxes(gridcolor="#1e2a4a", showgrid=True)
    fig.update_yaxes(gridcolor="#1e2a4a", showgrid=True)
    st.plotly_chart(fig, use_container_width=True)

    # Alt bilgi kartları
    st.subheader("📋 Detay Bilgiler")
    d1, d2, d3, d4 = st.columns(4)
    with d1:
        st.markdown("**📅 Earnings Tarihi**")
        st.info(earnings)
    with d2:
        st.markdown("**📊 Options Put/Call**")
        pc_renk = "green" if put_call < 0.8 else "orange" if put_call < 1.2 else "red"
        st.markdown(f'<span style="color:{pc_renk};font-size:1.5rem;font-weight:bold">{put_call:.2f}</span>', unsafe_allow_html=True)
        st.caption("< 0.8 Bullish | > 1.2 Bearish")
    with d3:
        st.markdown("**🎯 Hedef Fiyat**")
        hedef = info.get("hedef_fiyat")
        if hedef:
            potansiyel = ((hedef - fiyat) / fiyat) * 100
            st.markdown(f"${hedef:.2f} ({potansiyel:+.1f}%)")
        else:
            st.markdown("N/A")
    with d4:
        st.markdown("**📣 Analist Tavsiyesi**")
        st.info(info.get("tavsiye", "N/A").upper())


# ─── SAYFA 5: Backtest ───────────────────────────────────────────────────────
def sayfa_backtest(ajan) -> None:
    st.header("📊 Backtest — 2 Yıl Simülasyon")

    if ajan is None:
        st.error("Ajan yüklenemedi.")
        return

    if "backtest_sonuc" not in st.session_state:
        st.session_state["backtest_sonuc"] = None

    col_bt1, col_bt2 = st.columns([2, 1])
    with col_bt1:
        st.info("Backtest, seçili semboller üzerinde 2 yıllık geriye dönük simülasyon yapar. SPY benchmark ile karşılaştırır.")
    with col_bt2:
        if st.button("🚀 Backtest Başlat", type="primary"):
            progress_bar = st.progress(0)
            status = st.empty()

            def ilerleme(mesaj, pct):
                progress_bar.progress(pct)
                status.text(mesaj)

            with st.spinner("Backtest çalışıyor..."):
                sonuc = ajan.backtest_calistir(ilerleme_fn=ilerleme)
                st.session_state["backtest_sonuc"] = sonuc
            progress_bar.empty()
            status.empty()
            st.success("✅ Backtest tamamlandı!")
            st.rerun()

    sonuc = st.session_state.get("backtest_sonuc")
    if sonuc and "hata" not in sonuc:
        metrikler = sonuc.get("metrikler", {})

        # Metrik kartları
        st.subheader("📈 Performans Metrikleri")
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        with m1:
            st.metric("Toplam Getiri", f"{metrikler.get('toplam_getiri', 0):+.2f}%")
        with m2:
            st.metric("Yıllık Getiri", f"{metrikler.get('yillik_getiri', 0):+.2f}%")
        with m3:
            sharpe = metrikler.get("sharpe", 0)
            st.metric("Sharpe Ratio", f"{sharpe:.3f}", delta="İyi" if sharpe > 1 else "Zayıf")
        with m4:
            st.metric("Max Drawdown", f"{metrikler.get('max_drawdown', 0):.2f}%")
        with m5:
            st.metric("Kazanma Oranı", f"{metrikler.get('kazanma_orani', 0):.1f}%")
        with m6:
            st.metric("Toplam İşlem", f"{sonuc.get('toplam_islem', 0)}")

        # Alpha & Beta (varsa)
        if "alpha" in metrikler:
            a1, a2, a3, a4 = st.columns(4)
            with a1:
                st.metric("Alpha (Yıllık)", f"{metrikler['alpha']:+.2f}%")
            with a2:
                st.metric("Beta", f"{metrikler.get('beta', 1):.3f}")
            with a3:
                st.metric("Bilgi Oranı", f"{metrikler.get('bilgi_orani', 0):.3f}")
            with a4:
                st.metric("SPY vs Fazla Getiri", f"{metrikler.get('fazla_getiri', 0):+.2f}%")

        # Portföy vs Benchmark grafik
        pf_serisi = sonuc.get("portfoy_serisi", [])
        bm_serisi = sonuc.get("benchmark_serisi", {})

        if pf_serisi:
            pf_df = pd.DataFrame(pf_serisi)
            pf_df["tarih"] = pd.to_datetime(pf_df["tarih"])
            pf_df = pf_df.sort_values("tarih")

            fig_bt = go.Figure()
            fig_bt.add_trace(go.Scatter(
                x=pf_df["tarih"], y=pf_df["deger"],
                name="🇺🇸 JOHNY",
                line=dict(color="#4a9eff", width=2),
                fill="tozeroy", fillcolor="rgba(74,158,255,0.1)",
            ))

            if bm_serisi:
                bm_dates = [pd.Timestamp(k) for k in bm_serisi.keys()]
                bm_vals = list(bm_serisi.values())
                fig_bt.add_trace(go.Scatter(
                    x=bm_dates, y=bm_vals,
                    name="SPY Benchmark",
                    line=dict(color="#ff9500", width=1.5, dash="dot"),
                ))

            fig_bt.update_layout(
                title="Portföy Değeri vs SPY", height=400,
                paper_bgcolor="#0a0e1a", plot_bgcolor="#111827",
                font_color="#8ba7d0", xaxis=dict(gridcolor="#1e2a4a"),
                yaxis=dict(gridcolor="#1e2a4a", tickprefix="$"),
                legend=dict(bgcolor="#111827"),
            )
            st.plotly_chart(fig_bt, use_container_width=True)

        # Rolling Sharpe
        rolling = sonuc.get("rolling_sharpe", {})
        if rolling:
            rs_dates = [pd.Timestamp(k) for k in rolling.keys()]
            rs_vals = list(rolling.values())
            fig_rs = go.Figure(go.Scatter(
                x=rs_dates, y=rs_vals, name="Rolling Sharpe (63G)",
                line=dict(color="#9b59b6", width=1.5),
                fill="tozeroy", fillcolor="rgba(155,89,182,0.1)",
            ))
            fig_rs.add_hline(y=1.0, line_dash="dot", line_color="#00c864")
            fig_rs.add_hline(y=0.0, line_dash="dot", line_color="#888")
            fig_rs.update_layout(
                title="Rolling Sharpe Ratio", height=250,
                paper_bgcolor="#0a0e1a", plot_bgcolor="#111827",
                font_color="#8ba7d0",
            )
            st.plotly_chart(fig_rs, use_container_width=True)

    elif sonuc and "hata" in sonuc:
        st.error(f"Backtest hatası: {sonuc['hata']}")


# ─── SAYFA 6: Risk Paneli ────────────────────────────────────────────────────
def sayfa_risk_paneli(ajan) -> None:
    st.header("⚠️ Risk Paneli")

    if ajan is None:
        st.error("Ajan yüklenemedi.")
        return

    ozet = ajan.portfoy.pozisyon_ozeti()
    portfoy_degeri = ozet.get("portfoy_degeri_usd", 0)
    bugun_kz = ozet.get("bugun_kar_zarar_usd", 0)
    pozisyonlar = ozet.get("pozisyonlar", [])

    # Risk skoru
    from risk.limits import RiskLimitleri
    from risk.var import VaRHesaplayici
    from risk.correlation import KorelasyonAnalizci

    risk_limit = RiskLimitleri()
    risk_sk = risk_limit.risk_skoru_hesapla(
        portfoy_degeri,
        PORTFOY_PARAMETRELERI["baslangic_sermayesi"],
        bugun_kz,
        len(pozisyonlar),
    )
    risk_skoru = risk_sk.get("risk_skoru", 0)
    risk_seviyesi = risk_sk.get("seviye", "Bilinmiyor")

    r1, r2, r3 = st.columns(3)
    with r1:
        renk_map = {"Düşük": "#00c864", "Orta": "#ffcc00", "Yüksek": "#ff9500", "Kritik": "#ff4444"}
        r_renk = renk_map.get(risk_seviyesi, "#888")
        st.markdown(
            f'<div style="background:#111827;border:2px solid {r_renk};border-radius:10px;padding:15px;text-align:center">'
            f'<h3 style="color:{r_renk};margin:0">Risk Skoru</h3>'
            f'<p style="font-size:3rem;color:{r_renk};margin:5px 0;font-weight:bold">{risk_skoru:.0f}</p>'
            f'<p style="color:#8ba7d0">{risk_seviyesi}</p>'
            f'</div>',
            unsafe_allow_html=True
        )
    with r2:
        limit_kontrol = risk_limit.gunluk_kayip_kontrolu(portfoy_degeri, PORTFOY_PARAMETRELERI["baslangic_sermayesi"], bugun_kz)
        st.metric("Günlük Kayıp", f"{limit_kontrol['gunluk_kayip_pct']:+.2f}%", f"Limit: {limit_kontrol['gunluk_limit_pct']:.1f}%")
        st.metric("Portföy Kayıp", f"{limit_kontrol['portfoy_kayip_pct']:+.2f}%")
    with r3:
        islem_yapilabilir = limit_kontrol.get("islem_yapilabilir", True)
        durum_renk = "#00c864" if islem_yapilabilir else "#ff4444"
        durum_metin = "✅ İşlem Yapılabilir" if islem_yapilabilir else "🚫 İşlem Durduruldu"
        st.markdown(
            f'<div style="background:#111827;border:1px solid {durum_renk};border-radius:8px;padding:15px;text-align:center">'
            f'<p style="color:{durum_renk};font-size:1.1rem;font-weight:bold;margin:0">{durum_metin}</p>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.divider()

    # VaR Hesaplama
    st.subheader("📉 Value at Risk (VaR)")
    var_calc = VaRHesaplayici()
    fiyat_gecmisi: Dict = {}
    for poz in pozisyonlar[:5]:
        sembol = poz.get("sembol", "")
        df = ajan.teknik_veriler.get(sembol)
        if df is not None:
            fiyat_gecmisi[sembol] = df

    var_sonuc = var_calc.portfoy_var_hesapla(pozisyonlar, fiyat_gecmisi, portfoy_degeri)
    v1, v2, v3 = st.columns(3)
    with v1:
        st.metric("1-Günlük VaR (95%)", f"${var_sonuc.get('var_usd', 0):,.2f}", f"{var_sonuc.get('var_pct', 0):.2f}%")
    with v2:
        st.metric("Expected Shortfall", f"${var_sonuc.get('es_usd', 0):,.2f}")
    with v3:
        st.metric("Parametrik VaR", f"${var_sonuc.get('parametrik_var_usd', 0):,.2f}")

    # Stres Testi
    st.subheader("🌩️ Stres Testi Senaryoları")
    stres = var_calc.stres_testi(portfoy_degeri)
    stres_df = pd.DataFrame([
        {"Senaryo": k, "Tahmini Kayıp $": round(v, 2), "Kayıp %": round(v / portfoy_degeri * 100, 2) if portfoy_degeri > 0 else 0}
        for k, v in stres.items()
    ])
    st.dataframe(stres_df, use_container_width=True, hide_index=True)

    # Sektör riski
    st.subheader("🏭 Sektör Riski")
    from data.market_breadth import PiyasaGenisligi
    piyasa_genisligi = PiyasaGenisligi()
    sektor_dagilim = piyasa_genisligi.portfoy_sektor_dagilimi(pozisyonlar)
    if sektor_dagilim:
        sektor_df = pd.DataFrame([
            {"Sektör": s, "Değer $": round(v["deger"], 2), "% Ağırlık": round(v["yuzde"], 2), "Semboller": ", ".join(v["semboller"])}
            for s, v in sektor_dagilim.items()
        ])
        fig_pie = px.pie(
            sektor_df, names="Sektör", values="% Ağırlık",
            color="Sektör", color_discrete_map=SEKTOR_RENKLERI,
            hole=0.4,
        )
        fig_pie.update_layout(
            height=300, paper_bgcolor="#0a0e1a", font_color="#8ba7d0",
            legend=dict(bgcolor="#111827"),
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        st.dataframe(sektor_df, use_container_width=True, hide_index=True)


# ─── SAYFA 7: Strateji Analizi ───────────────────────────────────────────────
def sayfa_strateji_analizi(ajan) -> None:
    st.header("🧠 Strateji Analizi")

    if ajan is None:
        st.error("Ajan yüklenemedi.")
        return

    sinyaller = ajan.sinyaller or []
    if not sinyaller:
        st.warning("Sinyal verisi yok. Tarama yapın.")
        if st.button("🔄 Sinyal Tara"):
            ajan.sinyal_taramasi_yap()
            st.rerun()
        return

    # Strateji performans özeti
    st.subheader("⚡ Strateji Sinyal Dağılımı")
    strateji_isimleri = ["momentum", "mean_reversion", "breakout", "news_sentiment", "sector_rotation"]
    strateji_guzel = {
        "momentum": "Momentum",
        "mean_reversion": "Mean Reversion",
        "breakout": "Breakout",
        "news_sentiment": "Haber Duygu",
        "sector_rotation": "Sektör Rotasyon",
    }

    strateji_verileri: Dict[str, List] = {k: [] for k in strateji_isimleri}
    for s in sinyaller:
        detaylar = s.get("strateji_sonuclari", {})
        for st_ad in strateji_isimleri:
            st_sonuc = detaylar.get(st_ad)
            if st_sonuc:
                strateji_verileri[st_ad].append(st_sonuc.get("sinyal", 0))

    # Radar chart
    kategoriler = [strateji_guzel[k] for k in strateji_isimleri]
    ortalar = [np.mean(strateji_verileri[k]) if strateji_verileri[k] else 0 for k in strateji_isimleri]
    fig_radar = go.Figure(go.Scatterpolar(
        r=[abs(o) for o in ortalar] + [abs(ortalar[0])],
        theta=kategoriler + [kategoriler[0]],
        fill="toself",
        fillcolor="rgba(74,158,255,0.2)",
        line=dict(color="#4a9eff"),
        name="Ortalama Güç",
    ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1], gridcolor="#1e2a4a", color="#8ba7d0"),
            angularaxis=dict(gridcolor="#1e2a4a", color="#8ba7d0"),
            bgcolor="#111827",
        ),
        paper_bgcolor="#0a0e1a", font_color="#8ba7d0", height=350,
        showlegend=False,
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    # En güçlü sinyaller
    st.subheader("🏆 En Güçlü Sinyaller")
    guclu_al = [s for s in sinyaller if s.get("birlesik_sinyal", 0) >= 0.5]
    guclu_sat = [s for s in sinyaller if s.get("birlesik_sinyal", 0) <= -0.5]

    c_al, c_sat = st.columns(2)
    with c_al:
        st.markdown("**🟢 AL Sinyalleri**")
        for s in guclu_al[:8]:
            sinyal = s.get("birlesik_sinyal", 0)
            sembol = s.get("sembol", "")
            tavsiye = s.get("tavsiye", "")
            st.markdown(f'<div class="sinyal-al"><b>{sembol}</b> — {sinyal:+.3f} — {tavsiye}</div>', unsafe_allow_html=True)
    with c_sat:
        st.markdown("**🔴 SAT Sinyalleri**")
        for s in guclu_sat[:8]:
            sinyal = s.get("birlesik_sinyal", 0)
            sembol = s.get("sembol", "")
            tavsiye = s.get("tavsiye", "")
            st.markdown(f'<div class="sinyal-sat"><b>{sembol}</b> — {sinyal:+.3f} — {tavsiye}</div>', unsafe_allow_html=True)

    # Detaylı sinyal tablosu
    st.subheader("📋 Tüm Sinyal Tablosu")
    sinyal_satir: List[dict] = []
    for s in sinyaller[:30]:
        sinyal_satir.append({
            "Sembol": s.get("sembol", ""),
            "Birleşik Sinyal": round(s.get("birlesik_sinyal", 0), 3),
            "Tavsiye": s.get("tavsiye", ""),
            "Öncelik": s.get("oncelik", 0),
            "Momentum": round(s.get("strateji_sonuclari", {}).get("momentum", {}).get("sinyal", 0) if s.get("strateji_sonuclari", {}).get("momentum") else 0, 2),
            "Mean Rev.": round(s.get("strateji_sonuclari", {}).get("mean_reversion", {}).get("sinyal", 0) if s.get("strateji_sonuclari", {}).get("mean_reversion") else 0, 2),
            "Breakout": round(s.get("strateji_sonuclari", {}).get("breakout", {}).get("sinyal", 0) if s.get("strateji_sonuclari", {}).get("breakout") else 0, 2),
        })
    if sinyal_satir:
        sinyal_df = pd.DataFrame(sinyal_satir).sort_values("Birleşik Sinyal", ascending=False)
        st.dataframe(sinyal_df, use_container_width=True, hide_index=True)


# ─── SAYFA 8: Haberler ───────────────────────────────────────────────────────
def sayfa_haberler(ajan) -> None:
    st.header("📰 US Piyasa Haberleri")

    if ajan is None:
        st.error("Ajan yüklenemedi.")
        return

    col_h1, col_h2 = st.columns([3, 1])
    with col_h2:
        if st.button("🔄 Haberleri Güncelle"):
            ajan._son_haber_guncelleme = 0
            ajan.veri_guncelle()
            st.rerun()
        sembol_haber = st.selectbox("Sembol Filtrele", ["Tümü"] + US_SEMBOLLER[:20])

    haberler = ajan.haberler or []

    # Earnings takvimi
    st.subheader("📅 Yaklaşan Earnings")
    with st.spinner("Earnings takvimi yükleniyor..."):
        try:
            earnings = ajan.haber_fetcher.earnings_takvimi_cek(US_SEMBOLLER[:20])
            if earnings:
                earn_df = pd.DataFrame(earnings[:10])
                st.dataframe(earn_df, use_container_width=True, hide_index=True)
            else:
                st.info("Earnings verisi bulunamadı")
        except Exception as e:
            st.warning(f"Earnings hatası: {e}")

    st.divider()

    # Haber akışı
    st.subheader("📰 Son Haberler")
    if not haberler:
        st.info("Haber yükleniyor...")
        return

    for haber in haberler[:20]:
        sinyal = haber.get("sinyal", 0)
        sinyal_renk = "#00c864" if sinyal > 0 else "#ff4444" if sinyal < 0 else "#888"
        onem_renk = "#ff9500" if haber.get("onem") == "Yüksek" else "#555"
        baslik = haber.get("baslik", "")
        tarih = haber.get("tarih", "")
        kaynak = haber.get("kaynak", "")
        onem = haber.get("onem", "Normal")
        ilgili = haber.get("ilgili_semboller", "")

        st.markdown(
            f'<div style="background:#111827;border-left:3px solid {sinyal_renk};border-radius:6px;padding:10px;margin-bottom:8px">'
            f'<div style="display:flex;justify-content:space-between;align-items:center">'
            f'<span style="color:{onem_renk};font-size:0.75rem">[{onem}]</span>'
            f'<span style="color:#555;font-size:0.75rem">{tarih} — {kaynak}</span>'
            f'</div>'
            f'<p style="margin:4px 0;color:#e8eaf0">{baslik}</p>'
            f'<span style="color:#4a9eff;font-size:0.75rem">{ilgili}</span>'
            f'</div>',
            unsafe_allow_html=True
        )


# ─── SAYFA 9: İşlem Geçmişi ──────────────────────────────────────────────────
def sayfa_islem_gecmisi(ajan) -> None:
    st.header("📈 İşlem Geçmişi")

    if ajan is None:
        st.error("Ajan yüklenemedi.")
        return

    islemler = ajan.db.islemleri_al(limit=200)
    istatistik = ajan.db.istatistikleri_al()

    # İstatistik kartları
    i1, i2, i3, i4, i5 = st.columns(5)
    with i1:
        st.metric("Toplam İşlem", istatistik.get("toplam_islem", 0))
    with i2:
        st.metric("Kazanan", istatistik.get("kazanilan", 0))
    with i3:
        st.metric("Kaybeden", istatistik.get("kaybedilen", 0))
    with i4:
        st.metric("Kazanma Oranı", f"{istatistik.get('kazanma_orani', 0):.1f}%")
    with i5:
        toplam_kz = istatistik.get("toplam_kar_zarar", 0)
        st.metric("Toplam K/Z", f"${toplam_kz:+,.2f}")

    # Komisyon özeti
    toplam_komisyon = istatistik.get("toplam_komisyon", 0)
    st.info(f"💸 Toplam Komisyon: ${toplam_komisyon:,.2f}")

    st.divider()

    if not islemler:
        st.info("📭 Henüz işlem kaydı yok.")
        st.markdown("""
        **Demo işlem oluşturmak için:**
        - Hisse Tarayıcı sayfasından sinyal tarama yapın
        - Yeterli sinyal puanı elde eden hisseler otomatik alınır
        - Stop-loss / take-profit tetiklendiğinde otomatik satılır
        """)
        return

    # İşlem tablosu
    st.subheader("📋 İşlem Listesi")
    islem_df = pd.DataFrame(islemler)
    display_cols = [c for c in ["tarih", "sembol", "islem_tipi", "lot", "fiyat", "komisyon", "kar_zarar", "neden"] if c in islem_df.columns]
    if display_cols:
        islem_df_display = islem_df[display_cols].copy()
        islem_df_display.columns = [
            "Tarih", "Sembol", "İşlem", "Lot", "Fiyat $", "Komisyon $", "K/Z $", "Neden"
        ][:len(display_cols)]
        st.dataframe(islem_df_display, use_container_width=True, hide_index=True)

    # K/Z grafiği
    sat_islemleri = [i for i in islemler if i.get("islem_tipi") == "SAT" and i.get("kar_zarar", 0) != 0]
    if sat_islemleri:
        st.subheader("📊 K/Z Dağılımı")
        kz_df = pd.DataFrame(sat_islemleri)
        fig_kz = px.bar(
            kz_df,
            x="tarih", y="kar_zarar",
            color="kar_zarar",
            color_continuous_scale=["#cc3333", "#444444", "#00aa44"],
            color_continuous_midpoint=0,
            labels={"kar_zarar": "K/Z ($)", "tarih": "Tarih"},
        )
        fig_kz.update_layout(
            height=300, paper_bgcolor="#0a0e1a", plot_bgcolor="#111827",
            font_color="#8ba7d0", showlegend=False,
        )
        st.plotly_chart(fig_kz, use_container_width=True)


# ─── SAYFA 10: Ayarlar ───────────────────────────────────────────────────────
def sayfa_ayarlar(ajan) -> None:
    st.header("⚙️ Ayarlar & Konfigürasyon")

    if ajan is None:
        st.error("Ajan yüklenemedi.")
        return

    tab1, tab2, tab3, tab4 = st.tabs(["🔧 Risk Parametreleri", "📡 Strateji Ağırlıkları", "🔔 Telegram", "ℹ️ Sistem"])

    with tab1:
        st.subheader("Risk Parametreleri")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            stop_loss = st.slider("Stop-Loss %", 1.0, 10.0, PORTFOY_PARAMETRELERI["stop_loss_yuzdesi"] * 100, 0.5)
            take_profit = st.slider("Take-Profit %", 2.0, 20.0, PORTFOY_PARAMETRELERI["take_profit_yuzdesi"] * 100, 0.5)
            trailing_stop = st.slider("Trailing Stop %", 1.0, 8.0, PORTFOY_PARAMETRELERI["trailing_stop_yuzdesi"] * 100, 0.5)
        with col_r2:
            max_pozisyon = st.slider("Max Pozisyon Sayısı", 3, 20, PORTFOY_PARAMETRELERI["max_pozisyon_sayisi"])
            max_poz_pct = st.slider("Max Pozisyon %", 3.0, 25.0, PORTFOY_PARAMETRELERI["max_pozisyon_yuzdesi"] * 100, 1.0)
            gunluk_limit = st.slider("Günlük Kayıp Limiti %", 1.0, 10.0, PORTFOY_PARAMETRELERI["gunluk_kayip_limiti"] * 100, 0.5)

        if st.button("💾 Risk Parametrelerini Kaydet"):
            yeni_params = {
                "stop_loss_yuzdesi": stop_loss / 100,
                "take_profit_yuzdesi": take_profit / 100,
                "trailing_stop_yuzdesi": trailing_stop / 100,
                "max_pozisyon_sayisi": max_pozisyon,
                "max_pozisyon_yuzdesi": max_poz_pct / 100,
                "gunluk_kayip_limiti": gunluk_limit / 100,
            }
            ajan.db.ayar_kaydet("risk_parametreleri", yeni_params)
            st.success("✅ Kaydedildi!")

    with tab2:
        st.subheader("Strateji Ağırlıkları")
        from johny_config import STRATEJI_AGIRLIKLARI
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            mom_w = st.slider("Momentum", 0.0, 1.0, STRATEJI_AGIRLIKLARI["momentum"], 0.05)
            mr_w = st.slider("Mean Reversion", 0.0, 1.0, STRATEJI_AGIRLIKLARI["mean_reversion"], 0.05)
            bo_w = st.slider("Breakout", 0.0, 1.0, STRATEJI_AGIRLIKLARI["breakout"], 0.05)
        with col_s2:
            ns_w = st.slider("News Sentiment", 0.0, 1.0, STRATEJI_AGIRLIKLARI["news_sentiment"], 0.05)
            sr_w = st.slider("Sektör Rotasyon", 0.0, 1.0, STRATEJI_AGIRLIKLARI["sector_rotation"], 0.05)
        toplam = mom_w + mr_w + bo_w + ns_w + sr_w
        st.metric("Toplam Ağırlık", f"{toplam:.2f}", delta="Hedef: 1.00")
        if st.button("💾 Ağırlıkları Kaydet"):
            ajan.orkestrator.agirliklar = {
                "momentum": mom_w, "mean_reversion": mr_w, "breakout": bo_w,
                "news_sentiment": ns_w, "sector_rotation": sr_w,
            }
            st.success("✅ Ağırlıklar güncellendi!")

    with tab3:
        st.subheader("Telegram Bildirimleri")
        token = st.text_input("Bot Token", type="password", value="")
        chat_id = st.text_input("Chat ID", value="")
        if st.button("📲 Kaydet & Test Et"):
            if token and chat_id:
                from johny_telegram import TelegramBildirici
                test_bot = TelegramBildirici(token, chat_id)
                basarili = test_bot.mesaj_gonder("🇺🇸 JOHNY Telegram bağlantısı başarılı!")
                if basarili:
                    ajan.db.ayar_kaydet("telegram_token", token)
                    ajan.db.ayar_kaydet("telegram_chat_id", chat_id)
                    st.success("✅ Telegram bağlantısı başarılı!")
                else:
                    st.error("❌ Bağlantı başarısız. Token ve Chat ID kontrol edin.")

    with tab4:
        st.subheader("Sistem Bilgisi")
        s1, s2 = st.columns(2)
        with s1:
            st.markdown(f"**Versiyon:** {VERSIYON}")
            st.markdown(f"**Sembol Sayısı:** {len(US_SEMBOLLER)}")
            st.markdown(f"**Strateji Sayısı:** 5")
            st.markdown(f"**Piyasa:** NYSE + NASDAQ")
        with s2:
            st.markdown(f"**Para Birimi:** USD")
            st.markdown(f"**Başlangıç Sermayesi:** ${PORTFOY_PARAMETRELERI['baslangic_sermayesi']:,.0f}")
            st.markdown(f"**Komisyon:** $0.005/hisse min $1")
            st.markdown(f"**Dashboard Port:** 8503")

        if st.button("🗑️ Veritabanını Temizle", type="secondary"):
            st.warning("⚠️ Bu işlem geri alınamaz!")
            if st.button("Emin miyim? EVET", type="primary"):
                try:
                    import os
                    from johny_config import DB_DOSYASI
                    if os.path.exists(DB_DOSYASI):
                        os.remove(DB_DOSYASI)
                    st.success("Veritabanı temizlendi.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Temizleme hatası: {e}")


# ─── ANA DASHBOARD ──────────────────────────────────────────────────────────
def main():
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:15px 0">
            <h2 style="color:#4a9eff;margin:0">🇺🇸 JOHNY</h2>
            <p style="color:#8ba7d0;font-size:0.85rem;margin:4px 0">US Markets Agent</p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        sayfa = st.radio(
            "Sayfa",
            [
                "🇺🇸 Genel Bakış",
                "🌡️ S&P Isı Haritası",
                "📡 Hisse Tarayıcı",
                "🔍 Hisse Detay",
                "📊 Backtest",
                "⚠️ Risk Paneli",
                "🧠 Strateji Analizi",
                "📰 US Haberleri",
                "📈 İşlem Geçmişi",
                "⚙️ Ayarlar",
            ],
            label_visibility="collapsed",
        )
        st.divider()

        ajan = get_ajan()
        if ajan:
            piyasa = ajan.piyasa_durumu_cache or {}
            durum = piyasa.get("durum", "Yükleniyor...")
            renk_p = piyasa.get("renk", "gray")
            renk_css = {"green": "#00c864", "orange": "#ff9500", "red": "#ff4444", "blue": "#4a9eff", "gray": "#888"}.get(renk_p, "#888")
            st.markdown(f'<div style="text-align:center"><span style="color:{renk_css}">● {durum}</span></div>', unsafe_allow_html=True)

            usdtry = ajan.usdtry_cache or 32.0
            st.markdown(f'<div style="text-align:center;color:#8ba7d0;font-size:0.85rem">USD/TRY: {usdtry:.2f}</div>', unsafe_allow_html=True)
            st.divider()

            if st.button("🔄 Veriyi Güncelle", use_container_width=True):
                with st.spinner("Güncelleniyor..."):
                    ajan.veri_guncelle(zorunlu=True)
                    ajan.sinyal_taramasi_yap()
                st.success("✅ Güncellendi!")
                st.rerun()

            if st.button("📡 Sinyal Tara", use_container_width=True):
                with st.spinner("Taranıyor..."):
                    ajan.sinyal_taramasi_yap()
                st.success(f"✅ {len(ajan.sinyaller)} sinyal")
                st.rerun()

        st.divider()
        st.markdown(f'<div style="color:#555;font-size:0.75rem;text-align:center">JOHNY v{VERSIYON}<br>🇺🇸 NYSE + NASDAQ</div>', unsafe_allow_html=True)

    # Ajan al ve veri güncelle
    ajan = get_ajan()
    veri_guncelle_cached(ajan)

    # Sayfa yönlendirmesi
    if "Genel Bakış" in sayfa:
        sayfa_genel_bakis(ajan)
    elif "Isı Haritası" in sayfa:
        sayfa_isi_haritasi(ajan)
    elif "Tarayıcı" in sayfa:
        sayfa_hisse_tarayici(ajan)
    elif "Detay" in sayfa:
        sayfa_hisse_detay(ajan)
    elif "Backtest" in sayfa:
        sayfa_backtest(ajan)
    elif "Risk" in sayfa:
        sayfa_risk_paneli(ajan)
    elif "Strateji" in sayfa:
        sayfa_strateji_analizi(ajan)
    elif "Haber" in sayfa:
        sayfa_haberler(ajan)
    elif "İşlem" in sayfa:
        sayfa_islem_gecmisi(ajan)
    elif "Ayarlar" in sayfa:
        sayfa_ayarlar(ajan)


if __name__ == "__main__":
    main()
