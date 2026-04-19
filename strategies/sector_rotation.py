"""
JOHNY — Sektör Rotasyonu Stratejisi
Tech vs Finance vs Energy rotation
"""
import logging
from typing import Dict, Optional

import numpy as np
import pandas as pd

from strategies.base import BaseStrateji, SinyalSonucu
from johny_config import SEKTOR_GRUPLARI

logger = logging.getLogger(__name__)


class SektorRotasyonStratejisi(BaseStrateji):
    """Sektör rotasyonu tabanlı sinyaller"""

    def __init__(self):
        super().__init__("Sektör Rotasyonu", agirlik=0.15)
        self._sektor_performans: Dict[str, float] = {}

    def sektor_performansini_guncelle(self, sektor_perf: Dict[str, dict]) -> None:
        """Sektör performans verilerini güncelle"""
        for sektor, veri in sektor_perf.items():
            self._sektor_performans[sektor] = veri.get("degisim", 0.0)

    def analiz_et(
        self,
        sembol: str,
        df: pd.DataFrame,
        ek_veri: Optional[dict] = None
    ) -> Optional[SinyalSonucu]:
        try:
            if df is None or len(df) < 20:
                return None
            sinyaller = []
            detaylar = {}

            # Sembolün sektörünü bul
            sembol_sektor = "Bilinmiyor"
            for sektor, semboller in SEKTOR_GRUPLARI.items():
                if sembol in semboller:
                    sembol_sektor = sektor
                    break
            detaylar["sektor"] = sembol_sektor

            # Sektör performansından sinyal
            sektor_perf = self._sektor_performans
            if ek_veri:
                sektor_perf = ek_veri.get("sektor_performans", self._sektor_performans)

            if sektor_perf and sembol_sektor in sektor_perf:
                kendi_sektor_perf = sektor_perf[sembol_sektor]
                diger_sektor_perf = [v for k, v in sektor_perf.items() if k != sembol_sektor]
                if diger_sektor_perf:
                    ort_diger = np.mean(diger_sektor_perf)
                    sektor_fark = kendi_sektor_perf - ort_diger
                    detaylar["sektor_fark"] = round(sektor_fark * 100, 2)
                    if sektor_fark > 0.01:
                        sinyaller.append(0.7)
                    elif sektor_fark > 0.005:
                        sinyaller.append(0.4)
                    elif sektor_fark < -0.01:
                        sinyaller.append(-0.7)
                    elif sektor_fark < -0.005:
                        sinyaller.append(-0.4)
                    else:
                        sinyaller.append(0.0)

            # Hisse vs sektör karşılaştırması
            if len(df) >= 20:
                hisse_1m = float(df["Close"].pct_change(21).iloc[-1]) if len(df) > 21 else 0
                hisse_3m = float(df["Close"].pct_change(63).iloc[-1]) if len(df) > 63 else 0
                detaylar["hisse_1m"] = round(hisse_1m * 100, 2)
                detaylar["hisse_3m"] = round(hisse_3m * 100, 2)

                # Momentum tabanlı rotasyon
                if hisse_1m > 0.05 and hisse_3m > 0.10:
                    sinyaller.append(0.6)
                elif hisse_1m < -0.05 and hisse_3m < -0.10:
                    sinyaller.append(-0.6)

            # Fear & Greed'den sektör etkisi
            if ek_veri:
                fg_deger = ek_veri.get("fear_greed", {}).get("deger", 50)
                detaylar["fear_greed"] = fg_deger
                # Extreme Greed → Defensif sektörler daha iyi
                # Extreme Fear → Teknoloji oversold olabilir
                if fg_deger > 75:
                    if sembol_sektor in ["Sağlık", "Tüketim", "Enerji"]:
                        sinyaller.append(0.4)  # Defensif → iyi
                    elif sembol_sektor in ["Teknoloji", "Büyüme"]:
                        sinyaller.append(-0.3)
                elif fg_deger < 25:
                    if sembol_sektor in ["Teknoloji", "Büyüme", "Yarı İletkenler"]:
                        sinyaller.append(0.5)  # Oversold growth
                    elif sembol_sektor in ["Sağlık", "Tüketim"]:
                        sinyaller.append(-0.2)

            # SPY relatif güç
            if ek_veri and "spy_getiri" in ek_veri:
                spy_1m = ek_veri.get("spy_getiri", 0)
                hisse_1m = detaylar.get("hisse_1m", 0) / 100
                relatif_guc = hisse_1m - spy_1m
                detaylar["relatif_guc"] = round(relatif_guc * 100, 2)
                if relatif_guc > 0.03:
                    sinyaller.append(0.5)
                elif relatif_guc < -0.03:
                    sinyaller.append(-0.5)

            if not sinyaller:
                return SinyalSonucu(
                    sembol=sembol,
                    strateji=self.ad,
                    sinyal=0.0,
                    guven=0.2,
                    skor=0.0,
                    aciklama="Sektör rotasyon verisi yetersiz",
                    detaylar=detaylar,
                )

            ham_skor = float(np.mean(sinyaller))
            sinyal = self._sinyal_normalize(ham_skor)
            guven = self._guven_hesapla(sinyaller)
            skor = sinyal * guven

            if sinyal > 0.3:
                aciklama = f"Sektör Rotasyon Olumlu — {sembol_sektor} lider"
            elif sinyal < -0.3:
                aciklama = f"Sektör Rotasyon Olumsuz — {sembol_sektor} geri kalıyor"
            else:
                aciklama = f"Sektör Rotasyon Nötr"

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
            logger.error(f"Sektör rotasyon hatası {sembol}: {e}")
            return None
