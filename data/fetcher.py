"""
JOHNY — Veri Çekici
US Market data via yfinance
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf

from johny_config import (
    US_SEMBOLLER, TEKNIK_PARAMETRELER, VERI_KAYNAKLARI, PIYASA_SAATLERI,
    PIYASA_TATILLERI, PREMARKET_ESIK
)

logger = logging.getLogger(__name__)


class VeriFetcher:
    """US piyasası veri çekici"""

    def __init__(self):
        self._cache: Dict[str, Tuple[pd.DataFrame, float]] = {}
        self._fiyat_cache: Dict[str, Tuple[dict, float]] = {}
        self._cache_ttl = 30  # saniye
        self._usdtry_cache: Optional[Tuple[float, float]] = None

    def hisse_verisi_cek(
        self,
        sembol: str,
        donem: str = "6mo",
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """Hisse senedi OHLCV verisi çek"""
        cache_key = f"{sembol}_{donem}_{interval}"
        now = time.time()
        if cache_key in self._cache:
            df, ts = self._cache[cache_key]
            if now - ts < self._cache_ttl * 10:
                return df

        try:
            ticker = yf.Ticker(sembol)
            df = ticker.history(period=donem, interval=interval)
            if df.empty:
                return None
            df.index = pd.to_datetime(df.index)
            self._cache[cache_key] = (df, now)
            return df
        except Exception as e:
            logger.error(f"Veri çekme hatası {sembol}: {e}")
            return None

    def toplu_fiyat_cek(self, semboller: Optional[List[str]] = None) -> Dict[str, dict]:
        """Tüm sembollerin güncel fiyatlarını çek"""
        if semboller is None:
            semboller = US_SEMBOLLER
        sonuclar: Dict[str, dict] = {}
        try:
            tickers = yf.download(
                semboller,
                period="2d",
                interval="1d",
                group_by="ticker",
                auto_adjust=True,
                progress=False,
                threads=True
            )
            for sembol in semboller:
                try:
                    if len(semboller) == 1:
                        df = tickers
                    else:
                        if sembol not in tickers.columns.get_level_values(0):
                            continue
                        df = tickers[sembol]
                    if df.empty or len(df) < 2:
                        continue
                    bugun = df.iloc[-1]
                    dun = df.iloc[-2]
                    fiyat = float(bugun["Close"])
                    onceki = float(dun["Close"])
                    degisim = (fiyat - onceki) / onceki if onceki > 0 else 0.0
                    sonuclar[sembol] = {
                        "sembol": sembol,
                        "fiyat": fiyat,
                        "onceki_kapanis": onceki,
                        "degisim": degisim,
                        "degisim_yuzde": degisim * 100,
                        "acilis": float(bugun.get("Open", fiyat)),
                        "yuksek": float(bugun.get("High", fiyat)),
                        "dusuk": float(bugun.get("Low", fiyat)),
                        "hacim": float(bugun.get("Volume", 0)),
                        "guncelleme": datetime.now().isoformat(),
                    }
                except Exception as e:
                    logger.warning(f"{sembol} işleme hatası: {e}")
        except Exception as e:
            logger.error(f"Toplu fiyat hatası: {e}")
            # Fallback: bireysel çek
            for sembol in semboller[:10]:
                veri = self._tekil_fiyat_cek(sembol)
                if veri:
                    sonuclar[sembol] = veri
        return sonuclar

    def _tekil_fiyat_cek(self, sembol: str) -> Optional[dict]:
        """Tek hisse fiyat çek"""
        try:
            ticker = yf.Ticker(sembol)
            hist = ticker.history(period="2d")
            if hist.empty or len(hist) < 1:
                return None
            bugun = hist.iloc[-1]
            onceki = float(hist.iloc[-2]["Close"]) if len(hist) >= 2 else float(bugun["Close"])
            fiyat = float(bugun["Close"])
            degisim = (fiyat - onceki) / onceki if onceki > 0 else 0.0
            return {
                "sembol": sembol,
                "fiyat": fiyat,
                "onceki_kapanis": onceki,
                "degisim": degisim,
                "degisim_yuzde": degisim * 100,
                "acilis": float(bugun.get("Open", fiyat)),
                "yuksek": float(bugun.get("High", fiyat)),
                "dusuk": float(bugun.get("Low", fiyat)),
                "hacim": float(bugun.get("Volume", 0)),
                "guncelleme": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.warning(f"Tekil fiyat hatası {sembol}: {e}")
            return None

    def detayli_hisse_bilgisi(self, sembol: str) -> dict:
        """Hisse detaylı bilgisi (info, earnings, calendar)"""
        sonuc: dict = {}
        try:
            ticker = yf.Ticker(sembol)
            info = ticker.info or {}
            sonuc["info"] = {
                "long_name": info.get("longName", sembol),
                "sektor": info.get("sector", "N/A"),
                "sanayi": info.get("industry", "N/A"),
                "piyasa_degeri": info.get("marketCap", 0),
                "pe_orani": info.get("trailingPE", None),
                "eps": info.get("trailingEps", None),
                "52h_yuksek": info.get("fiftyTwoWeekHigh", None),
                "52h_dusuk": info.get("fiftyTwoWeekLow", None),
                "ortalama_hacim": info.get("averageVolume", 0),
                "beta": info.get("beta", None),
                "hedef_fiyat": info.get("targetMeanPrice", None),
                "tavsiye": info.get("recommendationKey", "N/A"),
            }
        except Exception as e:
            logger.warning(f"Info hatası {sembol}: {e}")
            sonuc["info"] = {}

        try:
            ticker = yf.Ticker(sembol)
            cal = ticker.calendar
            if cal is not None and not (isinstance(cal, dict) and len(cal) == 0):
                if isinstance(cal, dict):
                    sonuc["earnings_tarihi"] = str(cal.get("Earnings Date", "N/A"))
                else:
                    sonuc["earnings_tarihi"] = str(cal)
            else:
                sonuc["earnings_tarihi"] = "N/A"
        except Exception:
            sonuc["earnings_tarihi"] = "N/A"

        try:
            ticker = yf.Ticker(sembol)
            options = ticker.options
            sonuc["options_tarihleri"] = list(options) if options else []
            if options and len(options) > 0:
                try:
                    chain = ticker.option_chain(options[0])
                    call_hacim = chain.calls["volume"].sum() if not chain.calls.empty else 0
                    put_hacim = chain.puts["volume"].sum() if not chain.puts.empty else 0
                    total = call_hacim + put_hacim
                    sonuc["put_call_orani"] = float(put_hacim / call_hacim) if call_hacim > 0 else 1.0
                    sonuc["call_hacim"] = float(call_hacim)
                    sonuc["put_hacim"] = float(put_hacim)
                except Exception:
                    sonuc["put_call_orani"] = 1.0
            else:
                sonuc["put_call_orani"] = 1.0
        except Exception as e:
            logger.warning(f"Options hatası {sembol}: {e}")
            sonuc["put_call_orani"] = 1.0

        return sonuc

    def teknik_gostergeler_hesapla(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Teknik göstergeleri hesapla"""
        if df is None or df.empty or len(df) < 30:
            return None
        try:
            tp = TEKNIK_PARAMETRELER
            close = df["Close"]
            high = df["High"]
            low = df["Low"]
            volume = df["Volume"]

            # RSI
            delta = close.diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            avg_gain = gain.ewm(com=tp["rsi_periyot"] - 1, adjust=False).mean()
            avg_loss = loss.ewm(com=tp["rsi_periyot"] - 1, adjust=False).mean()
            rs = avg_gain / (avg_loss + 1e-10)
            df = df.copy()
            df["RSI"] = 100 - (100 / (1 + rs))

            # MACD
            ema_h = close.ewm(span=tp["macd_hizli"], adjust=False).mean()
            ema_y = close.ewm(span=tp["macd_yavas"], adjust=False).mean()
            df["MACD"] = ema_h - ema_y
            df["MACD_Sinyal"] = df["MACD"].ewm(span=tp["macd_sinyal"], adjust=False).mean()
            df["MACD_Hist"] = df["MACD"] - df["MACD_Sinyal"]

            # Bollinger Bands
            bb_ma = close.rolling(tp["bb_periyot"]).mean()
            bb_std = close.rolling(tp["bb_periyot"]).std()
            df["BB_Orta"] = bb_ma
            df["BB_Ust"] = bb_ma + tp["bb_std"] * bb_std
            df["BB_Alt"] = bb_ma - tp["bb_std"] * bb_std
            df["BB_Genislik"] = (df["BB_Ust"] - df["BB_Alt"]) / (df["BB_Orta"] + 1e-10)

            # EMAs
            df["EMA9"] = close.ewm(span=tp["ema_kisa"], adjust=False).mean()
            df["EMA21"] = close.ewm(span=tp["ema_orta"], adjust=False).mean()
            df["EMA50"] = close.ewm(span=tp["ema_uzun"], adjust=False).mean()
            df["EMA200"] = close.ewm(span=tp["ema_cok_uzun"], adjust=False).mean()

            # Volume MA
            df["Hacim_MA"] = volume.rolling(tp["hacim_ma_periyot"]).mean()
            df["Hacim_Oran"] = volume / (df["Hacim_MA"] + 1e-10)

            # ATR
            tr1 = high - low
            tr2 = (high - close.shift()).abs()
            tr3 = (low - close.shift()).abs()
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            df["ATR"] = tr.rolling(tp["atr_periyot"]).mean()

            # 52-week high/low
            df["52H_Yuksek"] = high.rolling(252).max()
            df["52H_Dusuk"] = low.rolling(252).min()

            # Fiyat momentum
            df["Mom_1M"] = close.pct_change(21)
            df["Mom_3M"] = close.pct_change(63)
            df["Mom_6M"] = close.pct_change(126)

            return df
        except Exception as e:
            logger.error(f"Teknik gösterge hatası: {e}")
            return None

    def usdtry_kuru_cek(self) -> float:
        """USD/TRY kuru çek"""
        now = time.time()
        if self._usdtry_cache:
            kur, ts = self._usdtry_cache
            if now - ts < 300:  # 5 dakika cache
                return kur
        try:
            ticker = yf.Ticker(VERI_KAYNAKLARI["usdtry_sembol"])
            hist = ticker.history(period="1d")
            if not hist.empty:
                kur = float(hist["Close"].iloc[-1])
                self._usdtry_cache = (kur, now)
                return kur
        except Exception as e:
            logger.warning(f"USD/TRY kur hatası: {e}")
        # Fallback
        if self._usdtry_cache:
            return self._usdtry_cache[0]
        return 32.0  # Yaklaşık değer

    def fear_greed_cek(self) -> dict:
        """Fear & Greed Index çek"""
        try:
            import requests
            url = VERI_KAYNAKLARI["fear_greed_api"]
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data and "data" in data and len(data["data"]) > 0:
                    latest = data["data"][0]
                    return {
                        "deger": int(latest.get("value", 50)),
                        "siniflandirma": latest.get("value_classification", "Neutral"),
                        "tarih": latest.get("timestamp", ""),
                    }
        except Exception as e:
            logger.warning(f"Fear & Greed hatası: {e}")
        return {"deger": 50, "siniflandirma": "Neutral", "tarih": ""}

    def piyasa_durumu(self) -> dict:
        """Mevcut piyasa durumunu kontrol et"""
        import pytz
        try:
            est = pytz.timezone("America/New_York")
            simdi_est = datetime.now(est)
            simdi_utc = datetime.utcnow()
            saat = simdi_est.strftime("%H:%M")
            gun = simdi_est.weekday()  # 0=Pazartesi, 6=Pazar
            tarih_str = simdi_est.strftime("%Y-%m-%d")

            # Hafta sonu
            if gun >= 5:
                return self._piyasa_kapalı_durumu(simdi_est, "Hafta Sonu")

            # Tatil günü
            if tarih_str in PIYASA_TATILLERI:
                return self._piyasa_kapalı_durumu(simdi_est, "Resmi Tatil")

            # Saat kontrolü
            if "04:00" <= saat < "09:30":
                durum = "Pre-Market"
                acilisina = self._sure_hesapla(simdi_est, 9, 30)
                return {
                    "durum": durum,
                    "acik": False,
                    "pre_market": True,
                    "after_market": False,
                    "simdi_est": saat,
                    "simdi_istanbul": simdi_est.strftime("%H:%M") + " (EST)",
                    "acilisina": acilisina,
                    "kapanisina": None,
                    "renk": "orange",
                }
            elif "09:30" <= saat < "16:00":
                durum = "Piyasa Açık"
                kapanisina = self._sure_hesapla(simdi_est, 16, 0)
                return {
                    "durum": durum,
                    "acik": True,
                    "pre_market": False,
                    "after_market": False,
                    "simdi_est": saat,
                    "simdi_istanbul": saat,
                    "acilisina": None,
                    "kapanisina": kapanisina,
                    "renk": "green",
                }
            elif "16:00" <= saat < "20:00":
                durum = "After-Hours"
                return {
                    "durum": durum,
                    "acik": False,
                    "pre_market": False,
                    "after_market": True,
                    "simdi_est": saat,
                    "simdi_istanbul": saat,
                    "acilisina": None,
                    "kapanisina": None,
                    "renk": "blue",
                }
            else:
                return self._piyasa_kapalı_durumu(simdi_est, "Kapalı")
        except Exception as e:
            logger.error(f"Piyasa durumu hatası: {e}")
            return {
                "durum": "Bilinmiyor",
                "acik": False,
                "pre_market": False,
                "after_market": False,
                "simdi_est": "N/A",
                "simdi_istanbul": "N/A",
                "acilisina": None,
                "kapanisina": None,
                "renk": "gray",
            }

    def _piyasa_kapalı_durumu(self, simdi_est: datetime, neden: str) -> dict:
        """Piyasa kapalı durumu"""
        return {
            "durum": f"Kapalı ({neden})",
            "acik": False,
            "pre_market": False,
            "after_market": False,
            "simdi_est": simdi_est.strftime("%H:%M"),
            "simdi_istanbul": simdi_est.strftime("%H:%M") + " (EST)",
            "acilisina": None,
            "kapanisina": None,
            "renk": "red",
        }

    def _sure_hesapla(self, simdi: datetime, hedef_saat: int, hedef_dakika: int) -> str:
        """Kalan süre hesapla"""
        try:
            hedef = simdi.replace(hour=hedef_saat, minute=hedef_dakika, second=0, microsecond=0)
            delta = hedef - simdi
            total_sn = int(delta.total_seconds())
            if total_sn < 0:
                return "Geçti"
            saat = total_sn // 3600
            dakika = (total_sn % 3600) // 60
            return f"{saat:02d}:{dakika:02d}"
        except Exception:
            return "N/A"

    def spy_benchmark_cek(self) -> Optional[pd.DataFrame]:
        """SPY benchmark verisi çek"""
        return self.hisse_verisi_cek("SPY", donem="2y")

    def premarket_hareketleri_cek(self, semboller: Optional[List[str]] = None) -> Dict[str, dict]:
        """Pre-market önemli hareketleri tespit et"""
        if semboller is None:
            semboller = US_SEMBOLLER
        sonuclar: Dict[str, dict] = {}
        try:
            for sembol in semboller[:20]:  # Rate limit için limit
                try:
                    ticker = yf.Ticker(sembol)
                    # Pre-market fiyatı info'dan al
                    info = ticker.info
                    pre_fiyat = info.get("preMarketPrice", None)
                    kapanis = info.get("previousClose", None)
                    if pre_fiyat and kapanis and kapanis > 0:
                        degisim = (pre_fiyat - kapanis) / kapanis
                        if abs(degisim) >= PREMARKET_ESIK:
                            sonuclar[sembol] = {
                                "sembol": sembol,
                                "pre_fiyat": pre_fiyat,
                                "kapanis": kapanis,
                                "degisim": degisim,
                                "degisim_yuzde": degisim * 100,
                                "onemli": True,
                            }
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Pre-market veri hatası: {e}")
        return sonuclar

    def piyasa_genisligi_cek(self) -> dict:
        """Piyasa genişliği verisi (S&P 500 için)"""
        try:
            spy = yf.Ticker("^GSPC")
            vix = yf.Ticker("^VIX")
            spy_hist = spy.history(period="5d")
            vix_hist = vix.history(period="5d")
            sonuc = {}
            if not spy_hist.empty:
                sp500_fiyat = float(spy_hist["Close"].iloc[-1])
                sp500_degisim = float(spy_hist["Close"].pct_change().iloc[-1]) * 100
                sonuc["sp500"] = sp500_fiyat
                sonuc["sp500_degisim"] = sp500_degisim
            if not vix_hist.empty:
                vix_deger = float(vix_hist["Close"].iloc[-1])
                sonuc["vix"] = vix_deger
                sonuc["korku_seviyesi"] = "Yüksek Korku" if vix_deger > 30 else "Orta" if vix_deger > 20 else "Düşük"
            return sonuc
        except Exception as e:
            logger.error(f"Piyasa genişliği hatası: {e}")
            return {}
