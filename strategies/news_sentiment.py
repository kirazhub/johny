"""
JOHNY — Haber Duygu Analizi Stratejisi
English keyword-based sentiment
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional

import numpy as np
import pandas as pd

from strategies.base import BaseStrateji, SinyalSonucu
from johny_config import POZITIF_HABERLER, NEGATIF_HABERLER

logger = logging.getLogger(__name__)


class NewsSentimentStratejisi(BaseStrateji):
    """Haber duygu analizi sinyalleri"""

    def __init__(self):
        super().__init__("News Sentiment", agirlik=0.20)

    def analiz_et(
        self,
        sembol: str,
        df: pd.DataFrame,
        ek_veri: Optional[dict] = None
    ) -> Optional[SinyalSonucu]:
        try:
            haberler: List[dict] = []
            if ek_veri:
                haberler = ek_veri.get("haberler", [])

            if not haberler:
                # Veri yok → nötr sinyal
                return SinyalSonucu(
                    sembol=sembol,
                    strateji=self.ad,
                    sinyal=0.0,
                    guven=0.1,
                    skor=0.0,
                    aciklama="Haber verisi yok",
                    detaylar={"haber_sayisi": 0},
                )

            pozitif = 0
            negatif = 0
            son_24h_pozitif = 0
            son_24h_negatif = 0
            simdi = datetime.now()
            detaylar = {}

            for haber in haberler:
                baslik = haber.get("baslik", "").lower()
                sinyal = haber.get("sinyal", 0)
                tarih_str = haber.get("tarih", "")

                # Zaman ağırlıklandırma
                try:
                    haber_tarih = datetime.strptime(tarih_str[:16], "%Y-%m-%d %H:%M")
                    saat_fark = (simdi - haber_tarih).total_seconds() / 3600
                    agirlik = 1.0 if saat_fark < 2 else 0.7 if saat_fark < 12 else 0.4
                except Exception:
                    agirlik = 0.5
                    saat_fark = 24

                if sinyal > 0:
                    pozitif += agirlik
                    if saat_fark < 24:
                        son_24h_pozitif += 1
                elif sinyal < 0:
                    negatif += agirlik
                    if saat_fark < 24:
                        son_24h_negatif += 1

            total = pozitif + negatif
            detaylar["haber_sayisi"] = len(haberler)
            detaylar["pozitif"] = pozitif
            detaylar["negatif"] = negatif
            detaylar["son_24h_pozitif"] = son_24h_pozitif
            detaylar["son_24h_negatif"] = son_24h_negatif

            if total == 0:
                return SinyalSonucu(
                    sembol=sembol,
                    strateji=self.ad,
                    sinyal=0.0,
                    guven=0.2,
                    skor=0.0,
                    aciklama="Sinyal haberleri yok",
                    detaylar=detaylar,
                )

            duygu_skoru = (pozitif - negatif) / total
            sinyal = self._sinyal_normalize(duygu_skoru)
            guven = min(total / 10.0, 1.0)  # 10+ haber = max güven
            guven = max(guven, 0.1)
            skor = sinyal * guven

            if sinyal > 0.3:
                aciklama = f"Pozitif Haber Akışı — {son_24h_pozitif} pozitif/24s"
            elif sinyal < -0.3:
                aciklama = f"Negatif Haber Akışı — {son_24h_negatif} negatif/24s"
            else:
                aciklama = f"Karışık/Nötr Haber"

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
            logger.error(f"News sentiment hatası {sembol}: {e}")
            return None

    def sembol_haber_analiz(self, sembol: str, haberler: List[dict]) -> float:
        """Tek sembol için haber skoru (0-1)"""
        if not haberler:
            return 0.5
        ilgili = [h for h in haberler if sembol in h.get("ilgili_semboller", "")]
        if not ilgili:
            return 0.5
        pozitif = sum(1 for h in ilgili if h.get("sinyal", 0) > 0)
        negatif = sum(1 for h in ilgili if h.get("sinyal", 0) < 0)
        total = len(ilgili)
        return (pozitif / total) if total > 0 else 0.5
