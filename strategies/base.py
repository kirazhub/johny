"""
JOHNY — Strateji Baz Sınıfı
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd


@dataclass
class SinyalSonucu:
    """Strateji sinyal sonucu"""
    sembol: str
    strateji: str
    sinyal: float              # -1.0 (güçlü sat) → +1.0 (güçlü al)
    guven: float               # 0.0 → 1.0
    skor: float                # Ağırlıklı skor
    aciklama: str
    detaylar: Dict = field(default_factory=dict)
    zaman: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "sembol": self.sembol,
            "strateji": self.strateji,
            "sinyal": self.sinyal,
            "guven": self.guven,
            "skor": self.skor,
            "aciklama": self.aciklama,
            "detaylar": self.detaylar,
            "zaman": self.zaman,
        }


class BaseStrateji(ABC):
    """Tüm stratejilerin baz sınıfı"""

    def __init__(self, ad: str, agirlik: float = 1.0):
        self.ad = ad
        self.agirlik = agirlik
        self._aktif = True

    @abstractmethod
    def analiz_et(
        self,
        sembol: str,
        df: pd.DataFrame,
        ek_veri: Optional[dict] = None
    ) -> Optional[SinyalSonucu]:
        """Sinyal üret"""
        pass

    def aktif_mi(self) -> bool:
        return self._aktif

    def aktif_yap(self) -> None:
        self._aktif = True

    def pasif_yap(self) -> None:
        self._aktif = False

    def _sinyal_normalize(self, ham_skor: float) -> float:
        """Ham skoru -1 ile +1 arasına normalize et"""
        return max(-1.0, min(1.0, ham_skor))

    def _guven_hesapla(self, sinyaller: List[float]) -> float:
        """Birden fazla gösterge uyumuna göre güven hesapla"""
        if not sinyaller:
            return 0.0
        pozitif = sum(1 for s in sinyaller if s > 0)
        negatif = sum(1 for s in sinyaller if s < 0)
        total = len(sinyaller)
        max_taraf = max(pozitif, negatif)
        return max_taraf / total
