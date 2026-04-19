"""
JOHNY — Piyasa Rejim Tespiti
SPY MA200 bazlı rejim analizi: BOGA / AYI / YATAY / VOLATIL
VIX yerine ATR kullanır.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class PiyasaRejimleri:
    BOGA = "BOGA"
    AYI = "AYI"
    YATAY = "YATAY"
    VOLATIL = "VOLATIL"


class PiyasaRejimTespiti:
    """
    SPY MA200 + ATR bazlı piyasa rejim tespiti.

    Rejime göre önerilen maksimum pozisyon yüzdeleri:
      BOGA    → %8
      AYI     → %4
      YATAY   → sadece breakout (dinamik hesap, %5 tavan)
      VOLATIL → %3
    """

    POZISYON_YUZDESI = {
        PiyasaRejimleri.BOGA: 0.08,
        PiyasaRejimleri.AYI: 0.04,
        PiyasaRejimleri.YATAY: 0.05,   # breakout filtresi dışarıda uygulanır
        PiyasaRejimleri.VOLATIL: 0.03,
    }

    # ATR/fiyat > bu eşik → VOLATIL rejim
    VOLATILITE_ESIK = 0.02  # %2 günlük hareket

    def __init__(self):
        self._cache: Optional[dict] = None
        self._cache_zaman: Optional[datetime] = None
        self._cache_sure_saniye: int = 3600  # 1 saat cache

    # ─── Ana metot ───────────────────────────────────────────────────────────

    def rejim_tespit(self, spy_df: Optional[pd.DataFrame] = None) -> dict:
        """
        SPY verisi üzerinde rejim tespiti.

        Parameters
        ----------
        spy_df : pd.DataFrame, optional
            Dışarıdan geçirilirse yfinance çağrısı atlanır.
            En az 200 günlük OHLCV verisi içermelidir.

        Returns
        -------
        dict
            rejim, aciklama, fiyat, ma200, ma50, atr_yuzde,
            max_pozisyon_yuzdesi, sadece_breakout
        """
        # Cache kontrolü
        if self._cache and self._cache_zaman:
            gecen = (datetime.now() - self._cache_zaman).total_seconds()
            if gecen < self._cache_sure_saniye:
                return self._cache

        try:
            if spy_df is None:
                spy_df = self._spy_yukle()

            if spy_df is None or len(spy_df) < 50:
                return self._varsayilan("Yetersiz SPY verisi")

            fiyat = float(spy_df["Close"].iloc[-1])
            ma200_s = spy_df["Close"].rolling(200).mean()
            ma50_s = spy_df["Close"].rolling(50).mean()
            ma200 = float(ma200_s.iloc[-1]) if not ma200_s.empty else fiyat
            ma50 = float(ma50_s.iloc[-1]) if not ma50_s.empty else fiyat

            # ATR hesapla (VIX yerine)
            atr = self._hesapla_atr(spy_df, periyot=14)
            atr_yuzde = atr / fiyat if fiyat > 0 else 0.0

            # Rejim kararı
            if atr_yuzde > self.VOLATILITE_ESIK:
                rejim = PiyasaRejimleri.VOLATIL
                aciklama = (
                    f"Yüksek volatilite: ATR=%{atr_yuzde*100:.1f} "
                    f"(eşik=%{self.VOLATILITE_ESIK*100:.0f})"
                )
            elif pd.isna(ma200) or len(spy_df) < 200:
                # Yeterli veri yok — MA50 bazlı karar
                if fiyat > ma50:
                    rejim = PiyasaRejimleri.BOGA
                    aciklama = "MA200 yok; fiyat MA50 üstü → geçici BOGA"
                else:
                    rejim = PiyasaRejimleri.AYI
                    aciklama = "MA200 yok; fiyat MA50 altı → geçici AYI"
            elif fiyat > ma200 and ma50 > ma200:
                rejim = PiyasaRejimleri.BOGA
                aciklama = f"Fiyat MA200 üstü ({fiyat:.1f}>{ma200:.1f}), MA50>MA200 — trend güçlü"
            elif fiyat < ma200 and ma50 < ma200:
                rejim = PiyasaRejimleri.AYI
                aciklama = f"Fiyat MA200 altı ({fiyat:.1f}<{ma200:.1f}), MA50<MA200 — trend zayıf"
            else:
                rejim = PiyasaRejimleri.YATAY
                fiyat_yon = "üstü" if fiyat > ma200 else "altı"
                ma50_yon = "üstü" if ma50 > ma200 else "altı"
                aciklama = (
                    f"Karma sinyal: Fiyat MA200 {fiyat_yon}, "
                    f"MA50 MA200 {ma50_yon} — yatay piyasa"
                )

            sonuc = {
                "rejim": rejim,
                "aciklama": aciklama,
                "fiyat": round(fiyat, 2),
                "ma200": round(ma200, 2) if not pd.isna(ma200) else None,
                "ma50": round(ma50, 2),
                "atr": round(atr, 3),
                "atr_yuzde": round(atr_yuzde * 100, 2),
                "max_pozisyon_yuzdesi": self.POZISYON_YUZDESI[rejim],
                "sadece_breakout": rejim == PiyasaRejimleri.YATAY,
                "tarih": datetime.now().isoformat(),
            }

            self._cache = sonuc
            self._cache_zaman = datetime.now()
            logger.info(f"Piyasa rejimi: {rejim} — {aciklama}")
            return sonuc

        except Exception as e:
            logger.error(f"Rejim tespit hatası: {e}")
            return self._varsayilan(str(e))

    # ─── Yardımcı metodlar ───────────────────────────────────────────────────

    def max_pozisyon_yuzdesi(self, rejim: Optional[str] = None) -> float:
        """Verilen rejim için maksimum pozisyon yüzdesini döndür."""
        if rejim is None:
            return 0.05
        return self.POZISYON_YUZDESI.get(rejim, 0.05)

    def rejim_ozeti(self) -> str:
        """Tek satır rejim özeti — log ve Telegram için."""
        bilgi = self.rejim_tespit()
        r = bilgi["rejim"]
        simgeler = {
            PiyasaRejimleri.BOGA: "📈 BOGA",
            PiyasaRejimleri.AYI: "📉 AYI",
            PiyasaRejimleri.YATAY: "➡️ YATAY",
            PiyasaRejimleri.VOLATIL: "⚡ VOLATIL",
        }
        etiket = simgeler.get(r, r)
        return (
            f"{etiket} | SPY ${bilgi['fiyat']} | "
            f"MA200=${bilgi['ma200']} | ATR%={bilgi['atr_yuzde']:.1f} | "
            f"MaxPoz=%{bilgi['max_pozisyon_yuzdesi']*100:.0f}"
        )

    # ─── Özel yardımcılar ────────────────────────────────────────────────────

    def _spy_yukle(self) -> Optional[pd.DataFrame]:
        """SPY verisini yfinance'den yükle."""
        try:
            import yfinance as yf
            ticker = yf.Ticker("SPY")
            df = ticker.history(period="1y", interval="1d")
            if df is not None and not df.empty:
                return df
        except Exception as e:
            logger.warning(f"SPY yüklenemedi: {e}")
        return None

    @staticmethod
    def _hesapla_atr(df: pd.DataFrame, periyot: int = 14) -> float:
        """ATR (Average True Range) hesapla."""
        try:
            high = df["High"]
            low = df["Low"]
            close = df["Close"]
            tr1 = high - low
            tr2 = (high - close.shift(1)).abs()
            tr3 = (low - close.shift(1)).abs()
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr_s = tr.ewm(com=periyot - 1, adjust=False).mean()
            val = float(atr_s.iloc[-1])
            return val if not pd.isna(val) else 0.0
        except Exception:
            return 0.0

    @staticmethod
    def _varsayilan(aciklama: str) -> dict:
        return {
            "rejim": PiyasaRejimleri.YATAY,
            "aciklama": aciklama,
            "fiyat": 0.0,
            "ma200": None,
            "ma50": 0.0,
            "atr": 0.0,
            "atr_yuzde": 0.0,
            "max_pozisyon_yuzdesi": 0.05,
            "sadece_breakout": True,
            "tarih": datetime.now().isoformat(),
        }


# ─── Singleton ───────────────────────────────────────────────────────────────

_rejim_tespiti: Optional[PiyasaRejimTespiti] = None


def get_rejim_tespiti() -> PiyasaRejimTespiti:
    """Global singleton döndür."""
    global _rejim_tespiti
    if _rejim_tespiti is None:
        _rejim_tespiti = PiyasaRejimTespiti()
    return _rejim_tespiti


# ─── CLI testi ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    tespit = PiyasaRejimTespiti()
    bilgi = tespit.rejim_tespit()
    print("\n=== JOHNY — Piyasa Rejim Raporu ===")
    for k, v in bilgi.items():
        print(f"  {k:<25}: {v}")
    print(f"\n  Özet: {tespit.rejim_ozeti()}")
