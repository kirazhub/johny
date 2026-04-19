"""
JOHNY — Backtest Metrikleri
Alpha, Beta, Sharpe, Sortino, Max Drawdown
"""
import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class BacktestMetrikleri:
    """Backtest performans metrikleri hesaplayıcı"""

    def __init__(self, risk_free_rate: float = 0.05):
        self.risk_free_rate = risk_free_rate  # Yıllık %5

    def tam_metrik_hesapla(
        self,
        portfoy_serisi: pd.Series,
        benchmark_serisi: Optional[pd.Series] = None,
    ) -> dict:
        """Tüm metrikleri hesapla"""
        try:
            if portfoy_serisi is None or portfoy_serisi.empty:
                return self._bos_metrik()

            portfoy_getiri = portfoy_serisi.pct_change().dropna()
            yillik_islem = 252

            # Temel metrikler
            toplam_getiri = float((portfoy_serisi.iloc[-1] / portfoy_serisi.iloc[0]) - 1)
            yillik_getiri = float((1 + toplam_getiri) ** (yillik_islem / len(portfoy_getiri)) - 1)
            volatilite = float(portfoy_getiri.std() * np.sqrt(yillik_islem))

            # Sharpe Ratio
            gunluk_rf = self.risk_free_rate / yillik_islem
            asiri_getiri = portfoy_getiri - gunluk_rf
            sharpe = float(asiri_getiri.mean() / asiri_getiri.std() * np.sqrt(yillik_islem)) if asiri_getiri.std() > 0 else 0.0

            # Sortino Ratio
            negatif = portfoy_getiri[portfoy_getiri < 0]
            downside_dev = float(negatif.std() * np.sqrt(yillik_islem)) if not negatif.empty else 0.001
            sortino = float((yillik_getiri - self.risk_free_rate) / downside_dev) if downside_dev > 0 else 0.0

            # Max Drawdown
            kumulatif = (1 + portfoy_getiri).cumprod()
            rolling_max = kumulatif.cummax()
            drawdown = (kumulatif - rolling_max) / rolling_max
            max_drawdown = float(drawdown.min())

            # Calmar Ratio
            calmar = float(yillik_getiri / abs(max_drawdown)) if max_drawdown < 0 else 0.0

            # Win Rate
            kazanan = (portfoy_getiri > 0).sum()
            toplam_gun = len(portfoy_getiri)
            kazanma_orani = float(kazanan / toplam_gun) if toplam_gun > 0 else 0.0

            metrikler = {
                "toplam_getiri": round(toplam_getiri * 100, 2),
                "yillik_getiri": round(yillik_getiri * 100, 2),
                "volatilite": round(volatilite * 100, 2),
                "sharpe": round(sharpe, 3),
                "sortino": round(sortino, 3),
                "calmar": round(calmar, 3),
                "max_drawdown": round(max_drawdown * 100, 2),
                "kazanma_orani": round(kazanma_orani * 100, 2),
                "gun_sayisi": toplam_gun,
            }

            # Benchmark karşılaştırma
            if benchmark_serisi is not None and not benchmark_serisi.empty:
                bm_getiri = benchmark_serisi.pct_change().dropna()
                bm_toplam = float((benchmark_serisi.iloc[-1] / benchmark_serisi.iloc[0]) - 1)
                bm_yillik = float((1 + bm_toplam) ** (yillik_islem / len(bm_getiri)) - 1)

                # Alpha & Beta
                ortak_idx = portfoy_getiri.index.intersection(bm_getiri.index)
                if len(ortak_idx) >= 20:
                    p_aligned = portfoy_getiri[ortak_idx]
                    b_aligned = bm_getiri[ortak_idx]
                    kovaryans = float(np.cov(p_aligned, b_aligned)[0, 1])
                    b_varyans = float(np.var(b_aligned))
                    beta = kovaryans / b_varyans if b_varyans > 0 else 1.0
                    alpha_yillik = yillik_getiri - (self.risk_free_rate + beta * (bm_yillik - self.risk_free_rate))
                    # Information Ratio
                    aktif_getiri = p_aligned - b_aligned
                    ir = float(aktif_getiri.mean() / aktif_getiri.std() * np.sqrt(yillik_islem)) if aktif_getiri.std() > 0 else 0.0
                    metrikler.update({
                        "beta": round(beta, 3),
                        "alpha": round(alpha_yillik * 100, 2),
                        "bilgi_orani": round(ir, 3),
                        "benchmark_getiri": round(bm_toplam * 100, 2),
                        "benchmark_yillik": round(bm_yillik * 100, 2),
                        "fazla_getiri": round((toplam_getiri - bm_toplam) * 100, 2),
                    })

            return metrikler
        except Exception as e:
            logger.error(f"Metrik hesaplama hatası: {e}")
            return self._bos_metrik()

    def rolling_sharpe(self, portfoy_serisi: pd.Series, pencere: int = 63) -> pd.Series:
        """Rolling Sharpe Ratio"""
        try:
            getiri = portfoy_serisi.pct_change().dropna()
            rf_gunluk = self.risk_free_rate / 252
            asiri = getiri - rf_gunluk
            return (asiri.rolling(pencere).mean() / asiri.rolling(pencere).std() * np.sqrt(252)).fillna(0)
        except Exception:
            return pd.Series(dtype=float)

    def drawdown_serisi(self, portfoy_serisi: pd.Series) -> pd.Series:
        """Drawdown serisi"""
        try:
            getiri = portfoy_serisi.pct_change().dropna()
            kumulatif = (1 + getiri).cumprod()
            rolling_max = kumulatif.cummax()
            return ((kumulatif - rolling_max) / rolling_max).fillna(0)
        except Exception:
            return pd.Series(dtype=float)

    def _bos_metrik(self) -> dict:
        return {
            "toplam_getiri": 0.0,
            "yillik_getiri": 0.0,
            "volatilite": 0.0,
            "sharpe": 0.0,
            "sortino": 0.0,
            "calmar": 0.0,
            "max_drawdown": 0.0,
            "kazanma_orani": 0.0,
            "gun_sayisi": 0,
        }
