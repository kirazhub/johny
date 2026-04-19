"""
Johny — Momentum Scalp Stratejisi
Hızlı %3 kâr hedefi, dar stop-loss, kısa süre tutma
"""
import logging
import pandas as pd
import numpy as np
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

# Scalp parametreleri
HEDEF_KAR_PCT = 0.03       # %3 kar al
STOP_LOSS_PCT = 0.015      # %1.5 stop
MAX_SURE_DAKIKA = 120      # 2 saat max tut
MIN_HACIM_KATSAYI = 2.0    # Normalin 2x+ hacim
MIN_RSI = 55               # Momentum başlamış olmalı
MAX_RSI = 75               # Aşırı alım değil
MAX_POZ_YUZDE = 0.04       # Max %4 sermaye


def scalp_skoru_hesapla(df: pd.DataFrame, fiyat: float) -> Dict:
    """Momentum scalp için skor hesapla (0-10)"""
    skor = 0
    nedenler = []

    try:
        if df is None or len(df) < 20:
            return {"skor": 0, "nedenler": ["Yetersiz veri"], "giris_uygun": False}

        # RSI kontrolü
        if "RSI" in df.columns:
            rsi = float(df["RSI"].iloc[-1])
            if MIN_RSI <= rsi <= MAX_RSI:
                skor += 2
                nedenler.append(f"RSI={rsi:.1f} momentum bölgesi")
            elif rsi > MAX_RSI:
                nedenler.append(f"RSI={rsi:.1f} aşırı alım — scalp uygun değil")
                return {"skor": 0, "nedenler": nedenler, "giris_uygun": False}

        # RSI yükseliyor mu?
        if "RSI" in df.columns and len(df) >= 3:
            rsi_trend = df["RSI"].iloc[-1] - df["RSI"].iloc[-3]
            if rsi_trend > 2:
                skor += 2
                nedenler.append(f"RSI yükseliyor (+{rsi_trend:.1f})")

        # Hacim kontrolü
        if "Volume" in df.columns:
            ort_hacim = df["Volume"].iloc[-20:-1].mean()
            son_hacim = df["Volume"].iloc[-1]
            hacim_oran = son_hacim / ort_hacim if ort_hacim > 0 else 1
            if hacim_oran >= MIN_HACIM_KATSAYI:
                skor += 3
                nedenler.append(f"Yüksek hacim: {hacim_oran:.1f}x")
            elif hacim_oran < 1.2:
                nedenler.append(f"Düşük hacim: {hacim_oran:.1f}x")

        # MA üzerinde mi?
        if "MA20" in df.columns:
            ma20 = float(df["MA20"].iloc[-1])
            if fiyat > ma20:
                skor += 2
                nedenler.append(f"Fiyat MA20 üzerinde")

        # MACD pozitif mi?
        if "MACD" in df.columns and "MACD_Signal" in df.columns:
            macd = float(df["MACD"].iloc[-1])
            signal = float(df["MACD_Signal"].iloc[-1])
            if macd > signal and macd > 0:
                skor += 1
                nedenler.append("MACD pozitif kesişim")

    except Exception as e:
        logger.debug(f"Scalp skor hatası: {e}")

    giris_uygun = skor >= 6
    return {
        "skor": skor,
        "nedenler": nedenler,
        "giris_uygun": giris_uygun,
        "hedef": round(fiyat * (1 + HEDEF_KAR_PCT), 2),
        "stop": round(fiyat * (1 - STOP_LOSS_PCT), 2),
    }


def scalp_cikis_kontrol(alis_fiyati: float, guncel_fiyat: float, alis_zamani: datetime) -> Dict:
    """Scalp pozisyondan çıkma zamanı mı?"""
    kar_pct = (guncel_fiyat - alis_fiyati) / alis_fiyati

    # Kar hedefine ulaştı
    if kar_pct >= HEDEF_KAR_PCT:
        return {"cik": True, "neden": f"HEDEF ULAŞILDI: %{kar_pct*100:.1f} kar"}

    # Stop-loss
    if kar_pct <= -STOP_LOSS_PCT:
        return {"cik": True, "neden": f"STOP-LOSS: %{kar_pct*100:.1f}"}

    # Zaman aşımı
    sure = (datetime.now() - alis_zamani).total_seconds() / 60
    if sure >= MAX_SURE_DAKIKA:
        return {"cik": True, "neden": f"ZAMAN AŞIMI: {sure:.0f} dakika"}

    return {"cik": False, "neden": None}
