"""
JOHNY — Strateji Optimizer
Grid search ile parametre optimizasyonu
"""
import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class StratejiOptimizatoru:
    """Basit grid search parametresi optimizasyonu"""

    def __init__(self):
        self.sonuclar: List[dict] = []

    def rsi_parametreleri_optimize(
        self,
        df: pd.DataFrame,
        periyotlar: Optional[List[int]] = None,
        asiri_alim_seviyeleri: Optional[List[int]] = None,
        asiri_satim_seviyeleri: Optional[List[int]] = None,
    ) -> dict:
        """RSI parametrelerini optimize et"""
        if periyotlar is None:
            periyotlar = [10, 14, 21]
        if asiri_alim_seviyeleri is None:
            asiri_alim_seviyeleri = [65, 70, 75]
        if asiri_satim_seviyeleri is None:
            asiri_satim_seviyeleri = [25, 30, 35]

        en_iyi_sharpe = -999.0
        en_iyi_params: dict = {}
        tum_sonuclar: List[dict] = []

        for periyot in periyotlar:
            for aa in asiri_alim_seviyeleri:
                for asat in asiri_satim_seviyeleri:
                    try:
                        sonuc = self._rsi_strateji_simule(df, periyot, aa, asat)
                        if sonuc and sonuc.get("sharpe", -999) > en_iyi_sharpe:
                            en_iyi_sharpe = sonuc["sharpe"]
                            en_iyi_params = {"periyot": periyot, "asiri_alim": aa, "asiri_satim": asat}
                        if sonuc:
                            tum_sonuclar.append({
                                "periyot": periyot, "asiri_alim": aa, "asiri_satim": asat,
                                **sonuc
                            })
                    except Exception:
                        pass

        tum_sonuclar.sort(key=lambda x: x.get("sharpe", -999), reverse=True)
        return {
            "en_iyi_params": en_iyi_params,
            "en_iyi_sharpe": round(en_iyi_sharpe, 3),
            "tum_sonuclar": tum_sonuclar[:10],
        }

    def _rsi_strateji_simule(
        self,
        df: pd.DataFrame,
        periyot: int,
        asiri_alim: int,
        asiri_satim: int,
    ) -> Optional[dict]:
        """RSI stratejisi simüle et"""
        try:
            close = df["Close"].copy()
            delta = close.diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            avg_g = gain.ewm(com=periyot - 1, adjust=False).mean()
            avg_l = loss.ewm(com=periyot - 1, adjust=False).mean()
            rs = avg_g / (avg_l + 1e-10)
            rsi = 100 - (100 / (1 + rs))

            pozisyon = 0
            nakit = 1000.0
            hisse = 0.0
            giris = 0.0

            for i in range(periyot, len(close)):
                fiyat = float(close.iloc[i])
                r = float(rsi.iloc[i])
                if r < asiri_satim and pozisyon == 0 and nakit > fiyat:
                    hisse = nakit / fiyat
                    giris = fiyat
                    nakit = 0.0
                    pozisyon = 1
                elif r > asiri_alim and pozisyon == 1:
                    nakit = hisse * fiyat
                    hisse = 0.0
                    pozisyon = 0

            son_deger = nakit + hisse * float(close.iloc[-1])
            toplam_getiri = (son_deger - 1000.0) / 1000.0
            getiri_serisi = pd.Series([son_deger])
            sharpe = toplam_getiri  # Basit yaklaşım

            return {
                "toplam_getiri": round(toplam_getiri * 100, 2),
                "sharpe": round(toplam_getiri, 3),
                "son_deger": round(son_deger, 2),
            }
        except Exception:
            return None
