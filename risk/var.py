"""
JOHNY — Value at Risk (VaR)
USD tabanlı risk hesaplamaları
"""
import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class VaRHesaplayici:
    """Historical VaR ve Expected Shortfall hesaplamaları"""

    def __init__(self, guven_seviyesi: float = 0.95):
        self.guven_seviyesi = guven_seviyesi

    def portfoy_var_hesapla(
        self,
        pozisyonlar: List[dict],
        fiyat_gecmisi: Dict[str, pd.DataFrame],
        portfoy_degeri: float,
        gun_sayisi: int = 1,
    ) -> dict:
        """Portföy VaR hesapla"""
        try:
            if not pozisyonlar or not fiyat_gecmisi or portfoy_degeri <= 0:
                return self._bos_var_sonucu()

            getiri_matrisi = {}
            agirliklar = {}

            for poz in pozisyonlar:
                sembol = poz.get("sembol", "")
                deger = poz.get("deger_usd", 0)
                if deger <= 0 or sembol not in fiyat_gecmisi:
                    continue
                df = fiyat_gecmisi[sembol]
                if df is None or df.empty:
                    continue
                getiriler = df["Close"].pct_change().dropna()
                if len(getiriler) < 20:
                    continue
                getiri_matrisi[sembol] = getiriler.tail(252)
                agirliklar[sembol] = deger / portfoy_degeri

            if not getiri_matrisi:
                return self._bos_var_sonucu()

            # Portföy getiri serisi
            portfoy_getirileri = pd.Series(0.0, index=list(getiri_matrisi.values())[0].index)
            for sembol, getiriler in getiri_matrisi.items():
                agirlik = agirliklar.get(sembol, 0)
                ortak_idx = portfoy_getirileri.index.intersection(getiriler.index)
                portfoy_getirileri[ortak_idx] += getiriler[ortak_idx] * agirlik

            portfoy_getirileri = portfoy_getirileri.dropna()
            if len(portfoy_getirileri) < 10:
                return self._bos_var_sonucu()

            # Historical VaR
            var_pct = float(np.percentile(portfoy_getirileri, (1 - self.guven_seviyesi) * 100))
            var_usd = abs(var_pct) * portfoy_degeri * np.sqrt(gun_sayisi)

            # Expected Shortfall (CVaR)
            es_getiriler = portfoy_getirileri[portfoy_getirileri <= var_pct]
            es_pct = float(es_getiriler.mean()) if not es_getiriler.empty else var_pct
            es_usd = abs(es_pct) * portfoy_degeri * np.sqrt(gun_sayisi)

            # Parametrik VaR
            std = float(portfoy_getirileri.std())
            from scipy import stats as scipy_stats
            z = scipy_stats.norm.ppf(1 - self.guven_seviyesi)
            parametrik_var = abs(z * std) * portfoy_degeri * np.sqrt(gun_sayisi)

            return {
                "var_pct": round(var_pct * 100, 3),
                "var_usd": round(var_usd, 2),
                "es_pct": round(es_pct * 100, 3),
                "es_usd": round(es_usd, 2),
                "parametrik_var_usd": round(parametrik_var, 2),
                "portfoy_degeri": portfoy_degeri,
                "guven_seviyesi": self.guven_seviyesi,
                "gun_sayisi": gun_sayisi,
                "pozisyon_sayisi": len(getiri_matrisi),
            }
        except Exception as e:
            logger.error(f"VaR hesaplama hatası: {e}")
            return self._bos_var_sonucu()

    def _bos_var_sonucu(self) -> dict:
        return {
            "var_pct": 0.0,
            "var_usd": 0.0,
            "es_pct": 0.0,
            "es_usd": 0.0,
            "parametrik_var_usd": 0.0,
            "portfoy_degeri": 0.0,
            "guven_seviyesi": self.guven_seviyesi,
            "gun_sayisi": 1,
            "pozisyon_sayisi": 0,
        }

    def sektor_var_hesapla(
        self,
        pozisyonlar: List[dict],
        sektor_dagilimi: Dict[str, dict],
        portfoy_degeri: float,
    ) -> Dict[str, float]:
        """Sektör bazında VaR"""
        sektor_var: Dict[str, float] = {}
        for sektor, veri in sektor_dagilimi.items():
            sektor_pct = veri.get("yuzde", 0) / 100
            # Basit yaklaşım: sektör ağırlığı × portföy VaR
            sektor_deger = sektor_pct * portfoy_degeri
            sektor_var[sektor] = round(sektor_deger * 0.03, 2)  # %3 varsayılan VaR
        return sektor_var

    def stres_testi(self, portfoy_degeri: float) -> dict:
        """Stres testi senaryoları"""
        return {
            "Piyasa Çöküşü (-20%)": -portfoy_degeri * 0.20,
            "Büyük Düzeltme (-10%)": -portfoy_degeri * 0.10,
            "Orta Düzeltme (-5%)": -portfoy_degeri * 0.05,
            "2008 Krizi (-37%)": -portfoy_degeri * 0.37,
            "COVID Düşüşü (-34%)": -portfoy_degeri * 0.34,
            "Flash Crash (-10% 1 gün)": -portfoy_degeri * 0.10,
        }
