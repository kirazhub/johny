"""
JOHNY — Mean Reversion Stratejisi
Bollinger Bands + RSI extremes
"""
import logging
from typing import Optional

import numpy as np
import pandas as pd

from strategies.base import BaseStrateji, SinyalSonucu
from johny_config import TEKNIK_PARAMETRELER

logger = logging.getLogger(__name__)


class MeanReversionStratejisi(BaseStrateji):
    """Mean Reversion — ortalamaya dönüş sinyalleri"""

    def __init__(self):
        super().__init__("Mean Reversion", agirlik=0.20)

    def analiz_et(
        self,
        sembol: str,
        df: pd.DataFrame,
        ek_veri: Optional[dict] = None
    ) -> Optional[SinyalSonucu]:
        try:
            if df is None or len(df) < 30:
                return None
            tp = TEKNIK_PARAMETRELER
            sinyaller = []
            detaylar = {}
            fiyat = float(df["Close"].iloc[-1])

            # Bollinger Band pozisyonu
            if "BB_Ust" in df.columns and "BB_Alt" in df.columns:
                bb_ust = float(df["BB_Ust"].iloc[-1])
                bb_alt = float(df["BB_Alt"].iloc[-1])
                bb_orta = float(df["BB_Orta"].iloc[-1])
                bb_genislik = float(df["BB_Genislik"].iloc[-1]) if "BB_Genislik" in df.columns else 0

                bb_pct = (fiyat - bb_alt) / (bb_ust - bb_alt) if (bb_ust - bb_alt) > 0 else 0.5
                detaylar["bb_pct"] = round(bb_pct, 3)
                detaylar["bb_genislik"] = round(bb_genislik, 4)

                if bb_pct < 0.1:      # Alt banda yakın → Al
                    sinyaller.append(0.8)
                elif bb_pct < 0.25:
                    sinyaller.append(0.5)
                elif bb_pct > 0.9:    # Üst banda yakın → Sat
                    sinyaller.append(-0.8)
                elif bb_pct > 0.75:
                    sinyaller.append(-0.5)
                else:
                    sinyaller.append(0.0)

                # BB genişlik — dar band = breakout yakın
                detaylar["bb_dar"] = bb_genislik < 0.05

            # RSI aşırı satım/alım
            if "RSI" in df.columns:
                rsi = float(df["RSI"].iloc[-1])
                rsi_prev = float(df["RSI"].iloc[-2]) if len(df) > 2 else rsi
                detaylar["rsi"] = round(rsi, 2)
                # RSI dönüş sinyali
                if rsi <= 25:
                    sinyaller.append(0.9)
                elif rsi <= 30 and rsi > rsi_prev:
                    sinyaller.append(0.7)
                elif rsi <= 35:
                    sinyaller.append(0.4)
                elif rsi >= 75:
                    sinyaller.append(-0.9)
                elif rsi >= 70 and rsi < rsi_prev:
                    sinyaller.append(-0.7)
                elif rsi >= 65:
                    sinyaller.append(-0.4)
                else:
                    sinyaller.append(0.0)

            # EMA sapma
            if "EMA21" in df.columns:
                ema21 = float(df["EMA21"].iloc[-1])
                sapma = (fiyat - ema21) / ema21
                detaylar["ema21_sapma"] = round(sapma * 100, 2)
                if sapma < -0.05:     # %5 altında → Al
                    sinyaller.append(0.6)
                elif sapma < -0.10:   # %10 altında → Güçlü Al
                    sinyaller.append(0.9)
                elif sapma > 0.05:    # %5 üstünde → Sat
                    sinyaller.append(-0.6)
                elif sapma > 0.10:    # %10 üstünde → Güçlü Sat
                    sinyaller.append(-0.9)
                else:
                    sinyaller.append(0.0)

            # Uzun düşüş/yükseliş sonrası dönüş
            son_3_gun = df["Close"].pct_change().tail(3)
            ard_arda_asagi = all(son_3_gun < -0.01)
            ard_arda_yukari = all(son_3_gun > 0.01)
            if ard_arda_asagi:
                sinyaller.append(0.5)  # 3 gün düşüş → dönüş olabilir
                detaylar["ard_arda_asagi"] = True
            elif ard_arda_yukari:
                sinyaller.append(-0.5)
                detaylar["ard_arda_yukari"] = True

            # Fibonacci seviyeleri (son 20 günlük high-low)
            if len(df) >= 20:
                try:
                    son_20 = df.tail(20)
                    periyot_yuksek = float(son_20["High"].max())
                    periyot_dusuk = float(son_20["Low"].min())
                    aralik = periyot_yuksek - periyot_dusuk
                    if aralik > 0:
                        fib_382 = periyot_yuksek - aralik * 0.382
                        fib_500 = periyot_yuksek - aralik * 0.500
                        fib_618 = periyot_yuksek - aralik * 0.618
                        detaylar["fib_382"] = round(fib_382, 2)
                        detaylar["fib_500"] = round(fib_500, 2)
                        detaylar["fib_618"] = round(fib_618, 2)
                        tolerans = aralik * 0.025  # %2.5 tolerans
                        # Fib desteğine yakınsa +1 sinyal puanı
                        if abs(fiyat - fib_618) <= tolerans:
                            sinyaller.append(1.0)
                            detaylar["fib_destek"] = "61.8%"
                        elif abs(fiyat - fib_500) <= tolerans:
                            sinyaller.append(0.7)
                            detaylar["fib_destek"] = "50%"
                        elif abs(fiyat - fib_382) <= tolerans:
                            sinyaller.append(0.5)
                            detaylar["fib_destek"] = "38.2%"
                except Exception:
                    pass

            if not sinyaller:
                return None

            ham_skor = float(np.mean(sinyaller))
            sinyal = self._sinyal_normalize(ham_skor)
            guven = self._guven_hesapla(sinyaller)
            skor = sinyal * guven

            if sinyal > 0.3:
                aciklama = f"Mean Rev. Oversold Al — BB%: {detaylar.get('bb_pct', 'N/A')}"
            elif sinyal < -0.3:
                aciklama = f"Mean Rev. Overbought Sat — BB%: {detaylar.get('bb_pct', 'N/A')}"
            else:
                aciklama = f"Mean Rev. Nötr"

            return SinyalSonucu(
                sembol=sembol,
                strateji=self.ad,
                sinyal=sinyal,
                guven=guven,
                skor=skor,
                aciklama=aciklama,
                detaylar=detaylar,
            )
        except Exception as e:
            logger.error(f"Mean Reversion analiz hatası {sembol}: {e}")
            return None
