"""
JOHNY — Breakout Stratejisi
52-week highs, resistance breaks, pivot seviyeleri
"""
import logging
from typing import Optional

import numpy as np
import pandas as pd

from strategies.base import BaseStrateji, SinyalSonucu
from strategies.momentum import hesapla_pivot_seviyeleri

logger = logging.getLogger(__name__)


class BreakoutStratejisi(BaseStrateji):
    """Breakout — destek/direnç kırılım sinyalleri"""

    def __init__(self):
        super().__init__("Breakout", agirlik=0.20)

    def analiz_et(
        self,
        sembol: str,
        df: pd.DataFrame,
        ek_veri: Optional[dict] = None
    ) -> Optional[SinyalSonucu]:
        try:
            if df is None or len(df) < 50:
                return None
            sinyaller = []
            detaylar = {}
            fiyat = float(df["Close"].iloc[-1])
            yuksek = float(df["High"].iloc[-1])

            # 52 haftalık yüksek kırılımı
            if "52H_Yuksek" in df.columns:
                y52_yuksek = float(df["52H_Yuksek"].iloc[-2]) if len(df) > 2 else 0
                y52_dusuk = float(df["52H_Dusuk"].iloc[-1]) if "52H_Dusuk" in df.columns else 0
                if y52_yuksek > 0:
                    yuksek_pct = (fiyat - y52_yuksek) / y52_yuksek
                    dusuk_pct = (fiyat - y52_dusuk) / y52_dusuk if y52_dusuk > 0 else 0
                    detaylar["52h_yuksek"] = round(y52_yuksek, 2)
                    detaylar["52h_dusuk"] = round(y52_dusuk, 2)
                    detaylar["52h_yuksek_fark"] = round(yuksek_pct * 100, 2)

                    if yuksek >= y52_yuksek:   # 52-week high kırıldı!
                        sinyaller.append(1.0)
                        detaylar["52h_kirildi"] = True
                    elif yuksek_pct > -0.03:   # %3 içinde
                        sinyaller.append(0.6)
                    elif yuksek_pct > -0.08:
                        sinyaller.append(0.2)
                    else:
                        sinyaller.append(0.0)

                    # 52-week low'a yakın → breakdown riski
                    if dusuk_pct < 0.05:
                        sinyaller.append(-0.7)

            # 20/50 günlük yüksek kırılımı
            son_20_yuksek = float(df["High"].rolling(20).max().iloc[-2]) if len(df) > 21 else 0
            son_50_yuksek = float(df["High"].rolling(50).max().iloc[-2]) if len(df) > 51 else 0
            if son_20_yuksek > 0 and yuksek > son_20_yuksek:
                sinyaller.append(0.7)
                detaylar["20g_kirildi"] = True
            if son_50_yuksek > 0 and yuksek > son_50_yuksek:
                sinyaller.append(0.8)
                detaylar["50g_kirildi"] = True

            # Hacim onayı — 1.5x ortalamanın üstündeyse sinyal güçlendirici
            if "Hacim_Oran" in df.columns:
                hacim_oran = float(df["Hacim_Oran"].iloc[-1])
                detaylar["hacim_oran"] = round(hacim_oran, 2)
                fiyat_yon = 1 if fiyat > float(df["Open"].iloc[-1]) else -1
                if hacim_oran > 2.0:
                    sinyaller.append(0.7 * fiyat_yon)   # Çok güçlü hacim
                elif hacim_oran > 1.5:
                    sinyaller.append(0.5 * fiyat_yon)   # Güçlendirilmiş breakout sinyali

            # Pivot destek/direnç kırılımı
            if len(df) >= 22:
                try:
                    pivotlar = hesapla_pivot_seviyeleri(df, window=20)
                    direncler = pivotlar["direnc"]
                    destekler = pivotlar["destek"]
                    detaylar["pivot_direnc_list"] = [round(d, 2) for d in direncler]
                    detaylar["pivot_destek_list"] = [round(d, 2) for d in destekler]
                    # Fiyat yakın direnç kırdıysa güçlü breakout
                    for d in direncler:
                        if d > 0 and fiyat > d and abs(fiyat - d) / d < 0.03:
                            sinyaller.append(0.6)
                            detaylar["pivot_direnc_kirildi"] = round(d, 2)
                            break
                    # Fiyat yakın desteği kırdıysa breakdown
                    for d in destekler:
                        if d > 0 and fiyat < d and abs(fiyat - d) / d < 0.03:
                            sinyaller.append(-0.5)
                            detaylar["pivot_destek_kirildi"] = round(d, 2)
                            break
                except Exception:
                    pass

            # Konsolidasyon sonrası kırılım
            if len(df) >= 20:
                son_20_std = float(df["Close"].pct_change().tail(20).std())
                prev_20_std = float(df["Close"].pct_change().iloc[-40:-20].std()) if len(df) >= 40 else son_20_std
                if prev_20_std > 0 and son_20_std < prev_20_std * 0.5:
                    detaylar["konsolidasyon"] = True
                    sinyaller.append(0.4)  # Daralan volatilite = breakout adayı

            # ATR tabanlı breakout
            if "ATR" in df.columns:
                atr = float(df["ATR"].iloc[-1])
                gunluk_hareket = float(df["High"].iloc[-1]) - float(df["Low"].iloc[-1])
                if atr > 0 and gunluk_hareket > 1.5 * atr:
                    detaylar["guclu_hareket"] = True
                    if fiyat > float(df["Open"].iloc[-1]):
                        sinyaller.append(0.5)
                    else:
                        sinyaller.append(-0.5)

            if not sinyaller:
                return None

            ham_skor = float(np.mean(sinyaller))
            sinyal = self._sinyal_normalize(ham_skor)
            guven = self._guven_hesapla(sinyaller)
            skor = sinyal * guven

            if detaylar.get("52h_kirildi"):
                aciklama = f"52-Haftalık Yüksek Kırıldı! Güçlü Breakout"
            elif sinyal > 0.4:
                aciklama = f"Breakout Sinyali — {detaylar.get('52h_yuksek_fark', 'N/A')}% to 52H"
            elif sinyal < -0.4:
                aciklama = f"Breakdown Riski"
            else:
                aciklama = f"Breakout Nötr"

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
            logger.error(f"Breakout analiz hatası {sembol}: {e}")
            return None
