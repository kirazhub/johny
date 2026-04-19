"""
JOHNY — Kazanç Açıklaması Stratejisi
Earnings plays: 3 gün önce gir, kazanç gününde yarıya indir,
kazanç sonrası ilk 15 dakikada yeniden değerlendir.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf

from strategies.base import BaseStrateji, SinyalSonucu

logger = logging.getLogger(__name__)


class KazancStratejisi(BaseStrateji):
    """Kazanç açıklaması tabanlı sinyal üretici"""

    def __init__(self):
        super().__init__("Kazanç Stratejisi", agirlik=0.20)
        # {sembol: {"tarih": date, "whisper": float, "son_guncelleme": float}}
        self._earnings_cache: Dict[str, dict] = {}
        self._cache_ttl = 3600.0  # 1 saat

    # ------------------------------------------------------------------ #
    #  Kazanç takvimi                                                      #
    # ------------------------------------------------------------------ #

    def yaklasan_kazanc_cek(self, sembol: str) -> Optional[dict]:
        """
        yfinance.Ticker.calendar ile bir sonraki kazanç tarihini çek.
        Döner: {"tarih": date, "gün_kala": int} veya None
        """
        import time
        cached = self._earnings_cache.get(sembol, {})
        if cached and (time.time() - cached.get("son_guncelleme", 0)) < self._cache_ttl:
            return cached.get("takvim")

        try:
            ticker = yf.Ticker(sembol)
            cal = ticker.calendar
            if cal is None:
                return None

            # calendar farklı versiyonlarda dict veya DataFrame gelebilir
            earnings_date = None
            if isinstance(cal, dict):
                earnings_date = cal.get("Earnings Date")
                if isinstance(earnings_date, (list, tuple)) and len(earnings_date) > 0:
                    earnings_date = earnings_date[0]
            elif hasattr(cal, "columns"):
                if "Earnings Date" in cal.columns:
                    earnings_date = cal["Earnings Date"].iloc[0]

            if earnings_date is None:
                return None

            # Pandas Timestamp veya datetime.date'e dönüştür
            if hasattr(earnings_date, "date"):
                earnings_date = earnings_date.date()

            bugun = datetime.now().date()
            gun_kala = (earnings_date - bugun).days

            sonuc = {"tarih": earnings_date, "gun_kala": gun_kala}
            self._earnings_cache[sembol] = {
                "takvim": sonuc,
                "son_guncelleme": time.time(),
            }
            return sonuc
        except Exception as e:
            logger.debug(f"Kazanç takvimi alınamadı {sembol}: {e}")
            return None

    # ------------------------------------------------------------------ #
    #  Whisper number                                                      #
    # ------------------------------------------------------------------ #

    def whisper_number_hesapla(self, sembol: str) -> float:
        """
        Son 4 çeyreğin EPS sürpriz ortalamasını hesapla.
        Pozitif → piyasa beklentinin üstünü bekliyor.
        """
        try:
            ticker = yf.Ticker(sembol)
            earnings = ticker.quarterly_earnings
            if earnings is None or earnings.empty:
                return 0.0

            # En son 4 çeyrek
            son_4 = earnings.head(4)
            if "Surprise(%)" in son_4.columns:
                surpriz_listesi = son_4["Surprise(%)"].dropna().tolist()
            elif "Reported EPS" in son_4.columns and "EPS Estimate" in son_4.columns:
                est = son_4["EPS Estimate"].fillna(0)
                rep = son_4["Reported EPS"].fillna(0)
                surpriz_listesi = [
                    ((r - e) / abs(e) * 100) if e != 0 else 0.0
                    for r, e in zip(rep, est)
                ]
            else:
                return 0.0

            if not surpriz_listesi:
                return 0.0

            return float(np.mean(surpriz_listesi))
        except Exception as e:
            logger.debug(f"Whisper number hesaplanamadı {sembol}: {e}")
            return 0.0

    # ------------------------------------------------------------------ #
    #  Analist beklentisi                                                  #
    # ------------------------------------------------------------------ #

    def analist_beklentisi_al(self, sembol: str) -> dict:
        """EPS tahmini ve önceki dönem karşılaştırması"""
        try:
            ticker = yf.Ticker(sembol)
            info = ticker.info or {}
            return {
                "eps_forward":  info.get("forwardEps", None),
                "eps_trailing": info.get("trailingEps", None),
                "tahminci_sayi": info.get("numberOfAnalystOpinions", 0),
                "hedef_fiyat":  info.get("targetMeanPrice", None),
                "oneri":        info.get("recommendationKey", "hold"),
            }
        except Exception as e:
            logger.debug(f"Analist beklentisi alınamadı {sembol}: {e}")
            return {}

    # ------------------------------------------------------------------ #
    #  Kazanç günü pozisyon boyutu çarpanı                                 #
    # ------------------------------------------------------------------ #

    def pozisyon_carpani_hesapla(
        self,
        gun_kala: int,
        whisper: float,
        oneri: str,
    ) -> Tuple[float, str]:
        """
        Kazanç durumuna göre pozisyon boyutu çarpanı döner (0.0 – 1.0).
        Returns: (çarpan, açıklama)
        """
        if gun_kala < 0:
            # Kazanç geçti
            return 1.0, "Kazanç geçti, normal pozisyon"

        if gun_kala == 0:
            # Kazanç günü: yarıya indir
            return 0.5, "Kazanç günü — pozisyon yarıya indirildi (risk azaltma)"

        if 1 <= gun_kala <= 3:
            # 1-3 gün önce: beklentiye göre boyutla
            if whisper > 5.0 and oneri in ("buy", "strongBuy"):
                return 1.0, f"Güçlü beklenti (whisper +{whisper:.1f}%), normal pozisyon"
            elif whisper < -2.0 or oneri in ("sell", "strongSell"):
                return 0.5, f"Düşme riski yüksek (whisper {whisper:.1f}%), yarım pozisyon"
            else:
                return 0.75, f"Nötr beklenti (whisper {whisper:.1f}%), %75 pozisyon"

        # 4+ gün kala: normal
        return 1.0, "Kazanç uzak, normal pozisyon"

    # ------------------------------------------------------------------ #
    #  Ana analiz                                                          #
    # ------------------------------------------------------------------ #

    def analiz_et(
        self,
        sembol: str,
        df: pd.DataFrame,
        ek_veri: Optional[dict] = None,
    ) -> Optional[SinyalSonucu]:
        try:
            if df is None or len(df) < 10:
                return None

            sinyaller: List[float] = []
            detaylar: dict = {}

            # 1. Kazanç takvimi
            takvim = self.yaklasan_kazanc_cek(sembol)
            if takvim is None:
                return SinyalSonucu(
                    sembol=sembol,
                    strateji=self.ad,
                    sinyal=0.0,
                    guven=0.1,
                    skor=0.0,
                    aciklama="Kazanç takvimi bulunamadı",
                    detaylar={},
                )

            gun_kala = takvim["gun_kala"]
            detaylar["kazanc_tarihi"] = str(takvim["tarih"])
            detaylar["gun_kala"] = gun_kala

            # 2. Whisper number
            whisper = self.whisper_number_hesapla(sembol)
            detaylar["whisper_pct"] = round(whisper, 2)

            # 3. Analist beklentisi
            beklenti = self.analist_beklentisi_al(sembol)
            oneri = beklenti.get("oneri", "hold")
            detaylar["analist_oneri"] = oneri
            detaylar["eps_forward"] = beklenti.get("eps_forward")

            # 4. Sinyal üret
            if 0 <= gun_kala <= 3:
                # Kazanç yakın → beklentiye göre sinyal
                if whisper > 3.0:
                    sinyaller.append(0.7)
                elif whisper > 1.0:
                    sinyaller.append(0.4)
                elif whisper < -3.0:
                    sinyaller.append(-0.6)
                elif whisper < -1.0:
                    sinyaller.append(-0.3)
                else:
                    sinyaller.append(0.1)  # hafif bullish kazanç döneminde

                # Analist önerisini ekle
                oneri_skor = {
                    "strongBuy": 0.5,
                    "buy": 0.3,
                    "hold": 0.0,
                    "sell": -0.3,
                    "strongSell": -0.5,
                }.get(oneri, 0.0)
                sinyaller.append(oneri_skor)

            elif gun_kala < 0:
                # Kazanç geçti, kazanç sonrası 15 dakika değerlendirmesi için
                # Momentum sinyali: son gün değişimi
                if len(df) >= 2:
                    son_degisim = float(df["Close"].pct_change().iloc[-1])
                    detaylar["kazanc_sonrasi_degisim_pct"] = round(son_degisim * 100, 2)
                    if son_degisim > 0.03:
                        sinyaller.append(0.6)   # beat → momentum devam
                    elif son_degisim < -0.03:
                        sinyaller.append(-0.5)  # miss → devam edebilir

            # 5. Pozisyon boyutu çarpanı
            carpan, carpan_aciklama = self.pozisyon_carpani_hesapla(gun_kala, whisper, oneri)
            detaylar["pozisyon_carpani"] = carpan
            detaylar["carpan_aciklama"] = carpan_aciklama

            if not sinyaller:
                return SinyalSonucu(
                    sembol=sembol,
                    strateji=self.ad,
                    sinyal=0.0,
                    guven=0.1,
                    skor=0.0,
                    aciklama=f"Kazanç {gun_kala} gün uzakta, sinyal yok",
                    detaylar=detaylar,
                )

            ham_skor = float(np.mean(sinyaller))
            sinyal = self._sinyal_normalize(ham_skor)
            guven = self._guven_hesapla(sinyaller)
            # Kazanç günü güveni düşür
            if gun_kala == 0:
                guven *= 0.6
            skor = sinyal * guven * carpan

            if gun_kala == 0:
                aciklama = f"Kazanç GÜNÜ — pozisyon yarıya indirildi, whisper {whisper:+.1f}%"
            elif 1 <= gun_kala <= 3:
                aciklama = f"Kazanç {gun_kala} gün kala — whisper {whisper:+.1f}% | {carpan_aciklama}"
            elif gun_kala < 0:
                aciklama = f"Kazanç sonrası değerlendirme — {detaylar.get('kazanc_sonrasi_degisim_pct', 0):+.1f}%"
            else:
                aciklama = f"Kazanç {gun_kala} gün uzakta"

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
            logger.error(f"Kazanç stratejisi hatası {sembol}: {e}")
            return None

    # ------------------------------------------------------------------ #
    #  Toplu tarama                                                        #
    # ------------------------------------------------------------------ #

    def yaklasan_kazanclar_listele(self, semboller: List[str], gun_esik: int = 7) -> List[dict]:
        """
        Yaklaşan kazançları listele (gun_esik gün içinde).
        """
        sonuclar = []
        for sembol in semboller:
            try:
                takvim = self.yaklasan_kazanc_cek(sembol)
                if takvim and 0 <= takvim["gun_kala"] <= gun_esik:
                    sonuclar.append({
                        "sembol": sembol,
                        "tarih": str(takvim["tarih"]),
                        "gun_kala": takvim["gun_kala"],
                    })
            except Exception:
                pass
        sonuclar.sort(key=lambda x: x["gun_kala"])
        return sonuclar
