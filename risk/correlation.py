"""
JOHNY — Korelasyon Analizi
Portföy korelasyon matrisi
"""
import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class KorelasyonAnalizci:
    """Portföy korelasyon analizi"""

    def korelasyon_matrisi_hesapla(
        self,
        fiyat_verisi: Dict[str, pd.DataFrame],
        semboller: Optional[List[str]] = None,
    ) -> Optional[pd.DataFrame]:
        """Korelasyon matrisi hesapla"""
        try:
            if not fiyat_verisi:
                return None
            if semboller is None:
                semboller = list(fiyat_verisi.keys())

            getiriler = {}
            for sembol in semboller:
                df = fiyat_verisi.get(sembol)
                if df is not None and not df.empty:
                    getiri = df["Close"].pct_change().dropna().tail(63)
                    if len(getiri) >= 20:
                        getiriler[sembol] = getiri

            if len(getiriler) < 2:
                return None

            getiri_df = pd.DataFrame(getiriler).dropna()
            korr = getiri_df.corr()
            return korr
        except Exception as e:
            logger.error(f"Korelasyon matrisi hatası: {e}")
            return None

    def portfoy_korelasyonu_kontrol(
        self,
        yeni_sembol: str,
        mevcut_semboller: List[str],
        fiyat_verisi: Dict[str, pd.DataFrame],
        esik: float = 0.8,
    ) -> dict:
        """Yeni pozisyon korelasyon kontrolü"""
        try:
            if not mevcut_semboller:
                return {"kabul_edilebilir": True, "max_korelasyon": 0.0, "yuksek_korelasyon": []}

            tum_semboller = mevcut_semboller + [yeni_sembol]
            korr_mat = self.korelasyon_matrisi_hesapla(fiyat_verisi, tum_semboller)
            if korr_mat is None or yeni_sembol not in korr_mat.columns:
                return {"kabul_edilebilir": True, "max_korelasyon": 0.0, "yuksek_korelasyon": []}

            yeni_korelasyonlar = korr_mat[yeni_sembol].drop(yeni_sembol)
            yuksek = yeni_korelasyonlar[yeni_korelasyonlar.abs() > esik]
            max_korr = float(yeni_korelasyonlar.abs().max())

            return {
                "kabul_edilebilir": len(yuksek) == 0,
                "max_korelasyon": round(max_korr, 3),
                "yuksek_korelasyon": [(idx, round(float(val), 3)) for idx, val in yuksek.items()],
            }
        except Exception as e:
            logger.error(f"Korelasyon kontrolü hatası: {e}")
            return {"kabul_edilebilir": True, "max_korelasyon": 0.0, "yuksek_korelasyon": []}

    def portfoy_beta_hesapla(
        self,
        pozisyonlar: List[dict],
        fiyat_verisi: Dict[str, pd.DataFrame],
        benchmark_df: Optional[pd.DataFrame] = None,
    ) -> float:
        """Portföy beta hesapla"""
        try:
            if not pozisyonlar or benchmark_df is None or benchmark_df.empty:
                return 1.0

            spy_getiri = benchmark_df["Close"].pct_change().dropna().tail(252)
            portfoy_degeri = sum(p.get("deger_usd", 0) for p in pozisyonlar)
            if portfoy_degeri == 0:
                return 1.0

            betalar = []
            agirliklar = []

            for poz in pozisyonlar:
                sembol = poz.get("sembol", "")
                deger = poz.get("deger_usd", 0)
                if deger <= 0 or sembol not in fiyat_verisi:
                    continue
                df = fiyat_verisi[sembol]
                if df is None or df.empty:
                    continue
                hisse_getiri = df["Close"].pct_change().dropna().tail(252)
                ortak = spy_getiri.index.intersection(hisse_getiri.index)
                if len(ortak) < 20:
                    continue
                x = spy_getiri[ortak]
                y = hisse_getiri[ortak]
                kovaryans = float(np.cov(y, x)[0, 1])
                varyans = float(np.var(x))
                beta = kovaryans / varyans if varyans > 0 else 1.0
                betalar.append(beta)
                agirliklar.append(deger / portfoy_degeri)

            if not betalar:
                return 1.0
            return float(np.average(betalar, weights=agirliklar))
        except Exception as e:
            logger.error(f"Beta hesaplama hatası: {e}")
            return 1.0
