"""
JOHNY — Momentum Stratejisi
RSI, fiyat momentumu, hacim, OBV, pivot destek/direnç
"""
import logging
from typing import Optional, List

import numpy as np
import pandas as pd

from strategies.base import BaseStrateji, SinyalSonucu
from johny_config import TEKNIK_PARAMETRELER

logger = logging.getLogger(__name__)


def hesapla_obv(df: pd.DataFrame) -> pd.Series:
    """On-Balance Volume hesapla"""
    obv = [0.0]
    closes = df["Close"].values
    volumes = df["Volume"].values
    for i in range(1, len(df)):
        if closes[i] > closes[i - 1]:
            obv.append(obv[-1] + float(volumes[i]))
        elif closes[i] < closes[i - 1]:
            obv.append(obv[-1] - float(volumes[i]))
        else:
            obv.append(obv[-1])
    return pd.Series(obv, index=df.index)


def hesapla_pivot_seviyeleri(df: pd.DataFrame, window: int = 20) -> dict:
    """Son N mumdaki pivot yüksek/düşük noktalarını tespit et"""
    recent = df.tail(window + 2)
    direnc: List[float] = []
    destek: List[float] = []
    highs = recent["High"].values
    lows = recent["Low"].values
    for i in range(1, len(recent) - 1):
        if highs[i] > highs[i - 1] and highs[i] > highs[i + 1]:
            direnc.append(float(highs[i]))
        if lows[i] < lows[i - 1] and lows[i] < lows[i + 1]:
            destek.append(float(lows[i]))
    return {
        "direnc": sorted(direnc, reverse=True)[:3],
        "destek": sorted(destek)[:3],
    }


class MomentumStratejisi(BaseStrateji):
    """Momentum tabanlı al/sat sinyalleri"""

    def __init__(self):
        super().__init__("Momentum", agirlik=0.25)

    def analiz_et(
        self,
        sembol: str,
        df: pd.DataFrame,
        ek_veri: Optional[dict] = None
    ) -> Optional[SinyalSonucu]:
        try:
            if df is None or len(df) < 50:
                return None
            tp = TEKNIK_PARAMETRELER
            sinyaller = []
            detaylar = {}

            # RSI
            rsi = float(df["RSI"].iloc[-1]) if "RSI" in df.columns else None
            if rsi is not None:
                detaylar["rsi"] = round(rsi, 2)
                if rsi > 55 and rsi < tp["rsi_asiri_alim"]:
                    sinyaller.append(0.6)
                elif rsi < 45 and rsi > tp["rsi_asiri_satim"]:
                    sinyaller.append(-0.6)
                elif rsi >= tp["rsi_asiri_alim"]:
                    sinyaller.append(-0.3)  # Aşırı alım = zayıf sat
                elif rsi <= tp["rsi_asiri_satim"]:
                    sinyaller.append(0.3)   # Aşırı satım = zayıf al
                else:
                    sinyaller.append(0.0)

            # MACD
            if "MACD" in df.columns and "MACD_Sinyal" in df.columns:
                macd = float(df["MACD"].iloc[-1])
                macd_sinyal = float(df["MACD_Sinyal"].iloc[-1])
                macd_hist = float(df["MACD_Hist"].iloc[-1]) if "MACD_Hist" in df.columns else 0
                macd_hist_prev = float(df["MACD_Hist"].iloc[-2]) if "MACD_Hist" in df.columns and len(df) > 2 else 0
                detaylar["macd"] = round(macd, 4)
                detaylar["macd_hist"] = round(macd_hist, 4)
                if macd > macd_sinyal and macd_hist > macd_hist_prev:
                    sinyaller.append(0.7)
                elif macd < macd_sinyal and macd_hist < macd_hist_prev:
                    sinyaller.append(-0.7)
                elif macd > macd_sinyal:
                    sinyaller.append(0.4)
                else:
                    sinyaller.append(-0.4)

            # EMA pozisyon
            if "EMA21" in df.columns and "EMA50" in df.columns:
                fiyat = float(df["Close"].iloc[-1])
                ema21 = float(df["EMA21"].iloc[-1])
                ema50 = float(df["EMA50"].iloc[-1])
                ema200 = float(df["EMA200"].iloc[-1]) if "EMA200" in df.columns else None
                detaylar["fiyat_ema21_oran"] = round(fiyat / ema21, 4)
                if fiyat > ema21 > ema50:
                    sinyaller.append(0.8)
                elif fiyat < ema21 < ema50:
                    sinyaller.append(-0.8)
                elif fiyat > ema21:
                    sinyaller.append(0.4)
                else:
                    sinyaller.append(-0.4)
                if ema200:
                    if fiyat > ema200:
                        sinyaller.append(0.3)
                    else:
                        sinyaller.append(-0.3)

            # Hacim onayı + OBV
            if "Hacim_Oran" in df.columns:
                hacim_oran = float(df["Hacim_Oran"].iloc[-1])
                detaylar["hacim_oran"] = round(hacim_oran, 2)
                fiyat_degisim = float(df["Close"].pct_change().iloc[-1])
                # 1.5x hacim = sinyal güçlendirici
                if hacim_oran > 1.5 and fiyat_degisim > 0:
                    sinyaller.append(0.8)  # güçlendirildi
                elif hacim_oran > 1.5 and fiyat_degisim < 0:
                    sinyaller.append(-0.8)  # güçlendirildi
                elif hacim_oran > 1.0:
                    sinyaller.append(0.1 if fiyat_degisim > 0 else -0.1)

            # OBV trendi
            if "Volume" in df.columns and len(df) >= 20:
                try:
                    obv = hesapla_obv(df)
                    obv_ema = obv.ewm(span=20, adjust=False).mean()
                    obv_son = float(obv.iloc[-1])
                    obv_ema_son = float(obv_ema.iloc[-1])
                    detaylar["obv_trend"] = "YUKARI" if obv_son > obv_ema_son else "ASAGI"
                    if obv_son > obv_ema_son:
                        sinyaller.append(0.4)
                    else:
                        sinyaller.append(-0.4)
                except Exception:
                    pass

            # Pivot destek/direnç konumu
            fiyat_son = float(df["Close"].iloc[-1])
            if len(df) >= 22:
                try:
                    pivotlar = hesapla_pivot_seviyeleri(df, window=20)
                    destekler = pivotlar["direnc_list"] if "direnc_list" in pivotlar else pivotlar["destek"]
                    direncler = pivotlar["direnc"]
                    detaylar["pivot_destek"] = round(destekler[0], 2) if destekler else None
                    detaylar["pivot_direnc"] = round(direncler[0], 2) if direncler else None
                    # Fiyat pivot desteğine yakınsa +0.3
                    if destekler and abs(fiyat_son - destekler[0]) / fiyat_son < 0.02:
                        sinyaller.append(0.3)
                        detaylar["pivot_destek_yakin"] = True
                    # Fiyat pivot direncine yakınsa -0.2
                    if direncler and abs(fiyat_son - direncler[0]) / fiyat_son < 0.02:
                        sinyaller.append(-0.2)
                        detaylar["pivot_direnc_yakin"] = True
                except Exception:
                    pass

            # 1M + 3M momentum
            if "Mom_1M" in df.columns:
                mom_1m = float(df["Mom_1M"].iloc[-1])
                mom_3m = float(df["Mom_3M"].iloc[-1]) if "Mom_3M" in df.columns else 0
                detaylar["mom_1m"] = round(mom_1m * 100, 2)
                detaylar["mom_3m"] = round(mom_3m * 100, 2)
                if mom_1m > 0.05 and mom_3m > 0.10:
                    sinyaller.append(0.7)
                elif mom_1m < -0.05 and mom_3m < -0.10:
                    sinyaller.append(-0.7)
                elif mom_1m > 0:
                    sinyaller.append(0.3)
                else:
                    sinyaller.append(-0.3)

            if not sinyaller:
                return None

            ham_skor = float(np.mean(sinyaller))
            sinyal = self._sinyal_normalize(ham_skor)
            guven = self._guven_hesapla(sinyaller)
            skor = sinyal * guven

            if sinyal > 0.3:
                aciklama = f"Momentum Güçlü Al — Skor: {skor:.2f}, RSI: {detaylar.get('rsi', 'N/A')}"
            elif sinyal < -0.3:
                aciklama = f"Momentum Güçlü Sat — Skor: {skor:.2f}, RSI: {detaylar.get('rsi', 'N/A')}"
            else:
                aciklama = f"Momentum Nötr — Skor: {skor:.2f}"

            return SinyalSonucu(
                sembol=sembol,
                strateji=self.ad,
                sinyal=sinyal,
                guven=guven,
                skor=skor,
                aciklama=aciklama,
                detaylar=detaylar,
            )
        except Exception as e:
            logger.error(f"Momentum analiz hatası {sembol}: {e}")
            return None
