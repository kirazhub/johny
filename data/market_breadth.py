"""
JOHNY — Piyasa Genişliği
S&P 500 breadth indicators
"""
import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import yfinance as yf

from johny_config import US_SEMBOLLER, SEKTOR_GRUPLARI

logger = logging.getLogger(__name__)


class PiyasaGenisligi:
    """S&P 500 piyasa genişliği analizi"""

    def __init__(self):
        self._cache: dict = {}

    def sektor_performansi_cek(self) -> Dict[str, dict]:
        """Sektör performans verisi"""
        sektor_etf_map = {
            "Teknoloji": "XLK",
            "Finans": "XLF",
            "Sağlık": "XLV",
            "Enerji": "XLE",
            "Tüketim": "XLP",
            "Sanayi": "XLI",
            "Yarı İletkenler": "SOXX",
        }
        sonuclar: Dict[str, dict] = {}
        try:
            semboller = list(sektor_etf_map.values())
            tickers = yf.download(
                semboller,
                period="5d",
                interval="1d",
                group_by="ticker",
                auto_adjust=True,
                progress=False,
            )
            for sektor, etf in sektor_etf_map.items():
                try:
                    if len(semboller) == 1:
                        df = tickers
                    else:
                        if etf not in tickers.columns.get_level_values(0):
                            continue
                        df = tickers[etf]
                    if df.empty or len(df) < 2:
                        continue
                    bugun = float(df["Close"].iloc[-1])
                    dun = float(df["Close"].iloc[-2])
                    degisim = (bugun - dun) / dun if dun > 0 else 0.0
                    haftalik = float(df["Close"].pct_change(5).iloc[-1]) if len(df) >= 5 else degisim
                    sonuclar[sektor] = {
                        "etf": etf,
                        "fiyat": bugun,
                        "degisim": degisim,
                        "degisim_yuzde": degisim * 100,
                        "haftalik": haftalik * 100,
                        "hacim": float(df["Volume"].iloc[-1]) if "Volume" in df else 0,
                    }
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Sektör performans hatası: {e}")
        return sonuclar

    def portfoy_sektor_dagilimi(self, pozisyonlar: List[dict]) -> Dict[str, dict]:
        """Portföy sektör dağılımı"""
        dagilim: Dict[str, dict] = {}
        total_deger = sum(p.get("deger_usd", 0) for p in pozisyonlar)
        if total_deger == 0:
            return {}
        for sektor, semboller in SEKTOR_GRUPLARI.items():
            sektor_deger = 0.0
            sektor_pozisyonlar: List[str] = []
            for poz in pozisyonlar:
                if poz.get("sembol") in semboller:
                    sektor_deger += poz.get("deger_usd", 0)
                    sektor_pozisyonlar.append(poz["sembol"])
            if sektor_deger > 0:
                dagilim[sektor] = {
                    "deger": sektor_deger,
                    "yuzde": (sektor_deger / total_deger) * 100,
                    "semboller": sektor_pozisyonlar,
                }
        return dagilim

    def treemap_verisi_hazirla(self, fiyat_verisi: Dict[str, dict]) -> List[dict]:
        """Treemap için veri hazırla"""
        sonuc: List[dict] = []
        for sektor, semboller in SEKTOR_GRUPLARI.items():
            for sembol in semboller:
                if sembol in fiyat_verisi:
                    veri = fiyat_verisi[sembol]
                    sonuc.append({
                        "sembol": sembol,
                        "sektor": sektor,
                        "degisim_yuzde": veri.get("degisim_yuzde", 0),
                        "hacim": veri.get("hacim", 0),
                        "fiyat": veri.get("fiyat", 0),
                    })
        return sonuc

    def advance_decline_cek(self, fiyat_verisi: Dict[str, dict]) -> dict:
        """Yükselen/Düşen hisse sayısı"""
        yukselen = 0
        dusen = 0
        degismez = 0
        for sembol, veri in fiyat_verisi.items():
            degisim = veri.get("degisim", 0)
            if degisim > 0.001:
                yukselen += 1
            elif degisim < -0.001:
                dusen += 1
            else:
                degismez += 1
        total = yukselen + dusen + degismez
        return {
            "yukselen": yukselen,
            "dusen": dusen,
            "degismez": degismez,
            "oran": (yukselen / (yukselen + dusen)) if (yukselen + dusen) > 0 else 0.5,
            "kararlilik": "Boğa" if yukselen > dusen else "Ayı" if dusen > yukselen else "Nötr",
        }
