"""
JOHNY — US Haber Modülü
Yahoo Finance & diğer US kaynaklar
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re

logger = logging.getLogger(__name__)


class HaberFetcher:
    """US piyasası haber çekici"""

    def __init__(self):
        self._cache: Dict[str, tuple] = {}
        self._cache_ttl = 300  # 5 dakika

    def haberler_cek(self, sembol: Optional[str] = None, limit: int = 20) -> List[dict]:
        """Yahoo Finance haberlerini çek"""
        cache_key = f"haberler_{sembol or 'genel'}_{limit}"
        now = time.time()
        if cache_key in self._cache:
            haberler, ts = self._cache[cache_key]
            if now - ts < self._cache_ttl:
                return haberler

        haberler: List[dict] = []
        try:
            import yfinance as yf
            if sembol:
                ticker = yf.Ticker(sembol)
                news = ticker.news or []
            else:
                # Genel piyasa haberleri için SPY + QQQ
                haberler = []
                for s in ["SPY", "QQQ", "AAPL", "MSFT", "NVDA"]:
                    try:
                        t = yf.Ticker(s)
                        news_list = t.news or []
                        haberler.extend(news_list)
                    except Exception:
                        pass
                news = haberler[:limit * 3]

            for item in news[:limit * 2]:
                try:
                    baslik = item.get("title", "")
                    link = item.get("link", "")
                    ts_unix = item.get("providerPublishTime", 0)
                    kaynak = item.get("publisher", "Yahoo Finance")
                    ilgili = item.get("relatedTickers", [])

                    haber_tarih = datetime.fromtimestamp(ts_unix) if ts_unix else datetime.now()
                    sinyal = self._haber_sinyal_analiz(baslik)
                    semboller_str = ", ".join(ilgili[:5]) if ilgili else (sembol or "")

                    haberler.append({
                        "baslik": baslik,
                        "link": link,
                        "kaynak": kaynak,
                        "tarih": haber_tarih.strftime("%Y-%m-%d %H:%M"),
                        "tarih_obj": haber_tarih,
                        "sinyal": sinyal,
                        "sinyal_renk": "green" if sinyal > 0 else "red" if sinyal < 0 else "gray",
                        "ilgili_semboller": semboller_str,
                        "onem": self._onem_belirle(baslik),
                    })
                except Exception:
                    pass

            # Tarihe göre sırala
            haberler.sort(key=lambda x: x.get("tarih_obj", datetime.min), reverse=True)
            haberler = haberler[:limit]
            self._cache[cache_key] = (haberler, now)
            return haberler
        except Exception as e:
            logger.error(f"Haber çekme hatası: {e}")
            return []

    def _haber_sinyal_analiz(self, baslik: str) -> int:
        """Haber başlığından sinyal analizi (-1, 0, 1)"""
        from johny_config import POZITIF_HABERLER, NEGATIF_HABERLER
        baslik_lower = baslik.lower()
        pozitif = 0
        negatif = 0
        for kelime in POZITIF_HABERLER:
            if kelime.lower() in baslik_lower:
                pozitif += 1
        for kelime in NEGATIF_HABERLER:
            if kelime.lower() in baslik_lower:
                negatif += 1
        if pozitif > negatif:
            return 1
        elif negatif > pozitif:
            return -1
        return 0

    def _onem_belirle(self, baslik: str) -> str:
        """Haber önem seviyesi"""
        yuksek_onem = [
            "fed", "federal reserve", "interest rate", "cpi", "inflation",
            "earnings", "FDA", "merger", "acquisition", "bankruptcy",
            "guidance", "quarterly results",
        ]
        baslik_lower = baslik.lower()
        for kelime in yuksek_onem:
            if kelime in baslik_lower:
                return "Yüksek"
        return "Normal"

    def earnings_takvimi_cek(self, semboller: Optional[List[str]] = None) -> List[dict]:
        """Yaklaşan earnings tarihlerini çek"""
        from johny_config import US_SEMBOLLER
        if semboller is None:
            semboller = US_SEMBOLLER[:30]
        sonuclar: List[dict] = []
        try:
            import yfinance as yf
            for sembol in semboller:
                try:
                    ticker = yf.Ticker(sembol)
                    cal = ticker.calendar
                    if cal is None:
                        continue
                    if isinstance(cal, dict):
                        earnings = cal.get("Earnings Date", None)
                        if earnings:
                            if isinstance(earnings, list):
                                tarih = str(earnings[0])
                            else:
                                tarih = str(earnings)
                            sonuclar.append({
                                "sembol": sembol,
                                "tarih": tarih,
                                "eps_beklenti": cal.get("Earnings Average", None),
                                "eps_dusuk": cal.get("Earnings Low", None),
                                "eps_yuksek": cal.get("Earnings High", None),
                                "gelir_beklenti": cal.get("Revenue Average", None),
                            })
                except Exception:
                    pass
            # Tarihe göre sırala
            sonuclar.sort(key=lambda x: x.get("tarih", "9999"), reverse=False)
            return sonuclar
        except Exception as e:
            logger.error(f"Earnings takvimi hatası: {e}")
            return []

    def analyst_tavsiyeleri_cek(self, sembol: str) -> dict:
        """Analist tavsiyelerini çek"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(sembol)
            rec = ticker.recommendations
            if rec is None or rec.empty:
                return {}
            son_30 = rec.tail(30)
            al = son_30[son_30["To Grade"].isin(["Buy", "Strong Buy", "Overweight", "Outperform"])].shape[0]
            tut = son_30[son_30["To Grade"].isin(["Hold", "Neutral", "Equal Weight", "Market Perform"])].shape[0]
            sat = son_30[son_30["To Grade"].isin(["Sell", "Strong Sell", "Underweight", "Underperform"])].shape[0]
            total = al + tut + sat
            return {
                "al": al,
                "tut": tut,
                "sat": sat,
                "total": total,
                "al_yuzde": (al / total * 100) if total > 0 else 0,
                "son_tavsiye": rec.iloc[-1]["To Grade"] if not rec.empty else "N/A",
            }
        except Exception as e:
            logger.warning(f"Analist tavsiye hatası {sembol}: {e}")
            return {}

    def ekonomik_takvim_cek(self) -> List[dict]:
        """Yaklaşan ekonomik events (Fed, CPI vb.)"""
        # Statik önemli tarihler - normalde investing.com API'den çekilir
        return [
            {"tarih": "Haftalık", "olay": "Initial Jobless Claims", "onem": "Orta"},
            {"tarih": "Aylık", "olay": "CPI Report", "onem": "Yüksek"},
            {"tarih": "Aylık", "olay": "Non-Farm Payrolls", "onem": "Yüksek"},
            {"tarih": "8x yıllık", "olay": "FOMC Meeting", "onem": "Çok Yüksek"},
            {"tarih": "Aylık", "olay": "PCE Price Index", "onem": "Yüksek"},
            {"tarih": "Çeyreklik", "olay": "GDP Report", "onem": "Yüksek"},
        ]
