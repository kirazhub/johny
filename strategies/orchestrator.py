"""
JOHNY — Strateji Orkestratörü
Tüm stratejileri birleştirir
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd

from strategies.base import SinyalSonucu
from strategies.momentum import MomentumStratejisi
from strategies.mean_reversion import MeanReversionStratejisi
from strategies.breakout import BreakoutStratejisi
from strategies.news_sentiment import NewsSentimentStratejisi
from strategies.sector_rotation import SektorRotasyonStratejisi
from johny_config import STRATEJI_AGIRLIKLARI, SINYAL_ESLIKLERI

logger = logging.getLogger(__name__)


class StratejiOrkestratori:
    """Tüm stratejileri yönetir ve birleşik sinyal üretir"""

    def __init__(self):
        self.momentum = MomentumStratejisi()
        self.mean_reversion = MeanReversionStratejisi()
        self.breakout = BreakoutStratejisi()
        self.news_sentiment = NewsSentimentStratejisi()
        self.sector_rotation = SektorRotasyonStratejisi()
        self.agirliklar = STRATEJI_AGIRLIKLARI.copy()
        self._strateji_istatistik: Dict[str, dict] = {}

    def analiz_et(
        self,
        sembol: str,
        df: pd.DataFrame,
        ek_veri: Optional[dict] = None
    ) -> dict:
        """Tüm stratejileri çalıştır ve birleşik sinyal üret"""
        sonuclar: Dict[str, Optional[SinyalSonucu]] = {}
        toplam_agirlik = 0.0
        agirlikli_sinyal = 0.0

        strateji_map = {
            "momentum": self.momentum,
            "mean_reversion": self.mean_reversion,
            "breakout": self.breakout,
            "news_sentiment": self.news_sentiment,
            "sector_rotation": self.sector_rotation,
        }

        for ad, strateji in strateji_map.items():
            try:
                if not strateji.aktif_mi():
                    continue
                sonuc = strateji.analiz_et(sembol, df, ek_veri)
                sonuclar[ad] = sonuc
                if sonuc is not None:
                    agirlik = self.agirliklar.get(ad, 0.2)
                    agirlikli_sinyal += sonuc.skor * agirlik
                    toplam_agirlik += agirlik
            except Exception as e:
                logger.error(f"Strateji {ad} hatası {sembol}: {e}")
                sonuclar[ad] = None

        # Normalize
        if toplam_agirlik > 0:
            birlesik_sinyal = agirlikli_sinyal / toplam_agirlik
        else:
            birlesik_sinyal = 0.0

        birlesik_sinyal = max(-1.0, min(1.0, birlesik_sinyal))
        tavsiye = self._sinyal_tavsiyeye_donustur(birlesik_sinyal)
        oncelik = self._oncelik_hesapla(birlesik_sinyal, sonuclar)

        return {
            "sembol": sembol,
            "birlesik_sinyal": round(birlesik_sinyal, 4),
            "tavsiye": tavsiye,
            "oncelik": oncelik,
            "strateji_sonuclari": {
                k: v.to_dict() if v else None
                for k, v in sonuclar.items()
            },
            "zaman": datetime.now().isoformat(),
        }

    def _sinyal_tavsiyeye_donustur(self, sinyal: float) -> str:
        """Sinyal skorunu tavsiyeye çevir"""
        if sinyal >= SINYAL_ESLIKLERI["guclu_al"]:
            return "💚 GÜÇLÜ AL"
        elif sinyal >= SINYAL_ESLIKLERI["al"]:
            return "🟢 AL"
        elif sinyal >= SINYAL_ESLIKLERI["notr"]:
            return "🟡 TUT"
        elif sinyal >= SINYAL_ESLIKLERI["sat"]:
            return "🟠 GÖZETİM"
        elif sinyal >= SINYAL_ESLIKLERI["guclu_sat"]:
            return "🔴 SAT"
        else:
            return "⛔ GÜÇLÜ SAT"

    def _oncelik_hesapla(
        self,
        sinyal: float,
        sonuclar: Dict[str, Optional[SinyalSonucu]]
    ) -> int:
        """İşlem önceliği (1-5)"""
        mutlak = abs(sinyal)
        uyum = sum(
            1 for s in sonuclar.values()
            if s and (s.sinyal > 0) == (sinyal > 0)
        )
        toplam = sum(1 for s in sonuclar.values() if s is not None)
        uyum_orani = uyum / toplam if toplam > 0 else 0
        if mutlak > 0.6 and uyum_orani > 0.7:
            return 5
        elif mutlak > 0.5 and uyum_orani > 0.6:
            return 4
        elif mutlak > 0.4:
            return 3
        elif mutlak > 0.3:
            return 2
        return 1

    def toplu_tarama(
        self,
        semboller: List[str],
        teknik_veriler: Dict[str, pd.DataFrame],
        ek_veri: Optional[dict] = None
    ) -> List[dict]:
        """Tüm sembolleri tara ve öncelikli sinyalleri döndür"""
        sonuclar = []
        for sembol in semboller:
            df = teknik_veriler.get(sembol)
            if df is None or df.empty:
                continue
            try:
                analiz = self.analiz_et(sembol, df, ek_veri)
                sonuclar.append(analiz)
            except Exception as e:
                logger.error(f"Toplu tarama hatası {sembol}: {e}")

        # Önceliğe göre sırala
        sonuclar.sort(key=lambda x: (x["oncelik"], abs(x["birlesik_sinyal"])), reverse=True)
        return sonuclar

    def istatistik_guncelle(self, sembol: str, basarili: bool) -> None:
        """Strateji istatistiklerini güncelle"""
        if sembol not in self._strateji_istatistik:
            self._strateji_istatistik[sembol] = {"basarili": 0, "basarisiz": 0}
        if basarili:
            self._strateji_istatistik[sembol]["basarili"] += 1
        else:
            self._strateji_istatistik[sembol]["basarisiz"] += 1

    def istatistik_al(self) -> Dict[str, dict]:
        return self._strateji_istatistik.copy()
