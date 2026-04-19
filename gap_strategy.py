"""
JOHNY — Gap Trading Stratejisi
16:25 İstanbul'da (09:25 EST) açılış öncesi gap analizi yapar.
Gap up >%1.5 → ilk 15 dk momentum al, sonra profit al
Gap fill stratejisi: gap %0.5-1.5 → gap kapanacak, zıt yön
Küçük gap (<0.5%) → ignore
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pytz
import yfinance as yf

logger = logging.getLogger(__name__)

ISTANBUL_TZ = pytz.timezone("Europe/Istanbul")
EST_TZ = pytz.timezone("America/New_York")

# Gap eşikleri
GAP_MOMENTUM_ESIK = 0.015   # %1.5: momentum sinyali
GAP_FILL_ALT = 0.005         # %0.5: gap fill alt sınırı
GAP_FILL_UST = 0.015         # %1.5: gap fill üst sınırı
GAP_KUCUK_ESIK = 0.005       # %0.5 altı: görmezden gel

# Gap analiz penceresi: İstanbul 16:20 – 16:35
GAP_ANALIZ_BASLANGIC = (16, 20)
GAP_ANALIZ_BITIS = (16, 35)


class GapStratejisi:
    """
    Açılış gap'lerini analiz eder ve işlem sinyali üretir.
    """

    def __init__(self):
        self._gap_cache: Dict[str, dict] = {}
        self._analiz_yapildi: bool = False
        self._son_analiz_gunu: Optional[str] = None

    # ------------------------------------------------------------------ #
    #  Saat kontrolü                                                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def analiz_penceresi_mi() -> bool:
        """İstanbul saatiyle 16:20–16:35 arası mı?"""
        simdi = datetime.now(ISTANBUL_TZ)
        bas_saat, bas_dakika = GAP_ANALIZ_BASLANGIC
        bit_saat, bit_dakika = GAP_ANALIZ_BITIS
        bas = simdi.replace(hour=bas_saat, minute=bas_dakika, second=0, microsecond=0)
        bit = simdi.replace(hour=bit_saat, minute=bit_dakika, second=0, microsecond=0)
        return bas <= simdi <= bit

    # ------------------------------------------------------------------ #
    #  Fiyat çekme                                                          #
    # ------------------------------------------------------------------ #

    def _onceki_kapanis_cek(self, sembol: str) -> Optional[float]:
        """Dün kapanış fiyatını çek"""
        try:
            ticker = yf.Ticker(sembol)
            df = ticker.history(period="5d", prepost=False)
            if df is None or df.empty or len(df) < 2:
                return None
            return float(df["Close"].iloc[-1])
        except Exception as e:
            logger.debug(f"Dün kapanış alınamadı {sembol}: {e}")
            return None

    def _premarket_fiyat_cek(self, sembol: str) -> Optional[float]:
        """Pre-market anlık fiyatını çek"""
        try:
            ticker = yf.Ticker(sembol)
            df = ticker.history(period="1d", interval="1m", prepost=True)
            if df is None or df.empty:
                return None
            bugun = datetime.now(EST_TZ).date()
            df_bugun = df[df.index.date == bugun]
            if df_bugun.empty:
                return None
            return float(df_bugun["Close"].iloc[-1])
        except Exception as e:
            logger.debug(f"Pre-market fiyat alınamadı {sembol}: {e}")
            return None

    # ------------------------------------------------------------------ #
    #  Gap hesaplama                                                         #
    # ------------------------------------------------------------------ #

    def gap_hesapla(self, sembol: str) -> Optional[dict]:
        """
        Dün kapanış ile bugün pre-market fiyatı karşılaştır.
        Döner: {"sembol", "gap_pct", "dun_kapanis", "premarket", "tip"}
        """
        if sembol in self._gap_cache:
            return self._gap_cache[sembol]

        dun_kapanis = self._onceki_kapanis_cek(sembol)
        premarket = self._premarket_fiyat_cek(sembol)

        if dun_kapanis is None or premarket is None or dun_kapanis == 0:
            return None

        gap_pct = (premarket - dun_kapanis) / dun_kapanis
        abs_gap = abs(gap_pct)

        if abs_gap < GAP_KUCUK_ESIK:
            tip = "KUCUK"
        elif abs_gap >= GAP_MOMENTUM_ESIK:
            tip = "MOMENTUM_UP" if gap_pct > 0 else "MOMENTUM_DOWN"
        elif GAP_FILL_ALT <= abs_gap < GAP_FILL_UST:
            tip = "GAP_FILL"
        else:
            tip = "ORTA"

        sonuc = {
            "sembol": sembol,
            "gap_pct": round(gap_pct * 100, 2),
            "dun_kapanis": round(dun_kapanis, 2),
            "premarket_fiyat": round(premarket, 2),
            "tip": tip,
        }
        self._gap_cache[sembol] = sonuc
        return sonuc

    # ------------------------------------------------------------------ #
    #  Sinyal üretme                                                        #
    # ------------------------------------------------------------------ #

    def sinyal_uret(self, gap_sonuc: dict) -> Tuple[str, float, str]:
        """
        Gap sonucuna göre işlem sinyali üret.
        Returns: (sinyal_tipi, sinyal_deger, aciklama)
        sinyal_tipi: "AL", "SAT", "GAP_FILL_AL", "GAP_FILL_SAT", "IGNORE"
        sinyal_deger: -1.0 ile +1.0
        """
        tip = gap_sonuc.get("tip", "KUCUK")
        gap_pct = gap_sonuc.get("gap_pct", 0.0)
        sembol = gap_sonuc.get("sembol", "")

        if tip == "KUCUK":
            return "IGNORE", 0.0, f"{sembol}: Küçük gap ({gap_pct:+.1f}%) — dikkate alma"

        if tip == "MOMENTUM_UP":
            return (
                "AL",
                0.75,
                f"{sembol}: Gap up {gap_pct:+.1f}% → ilk 15dk momentum AL, sonra kâr al",
            )

        if tip == "MOMENTUM_DOWN":
            return (
                "SAT",
                -0.70,
                f"{sembol}: Gap down {gap_pct:+.1f}% → dikkat, short fırsatı",
            )

        if tip == "GAP_FILL":
            if gap_pct > 0:
                # Gap up → SAT (gap kapanacak beklenir)
                return (
                    "GAP_FILL_SAT",
                    -0.55,
                    f"{sembol}: Gap up {gap_pct:+.1f}% gap fill bekleniyor → SAT",
                )
            else:
                # Gap down → AL (gap kapanacak beklenir)
                return (
                    "GAP_FILL_AL",
                    +0.55,
                    f"{sembol}: Gap down {gap_pct:+.1f}% gap fill bekleniyor → AL",
                )

        return "IGNORE", 0.0, f"{sembol}: Orta gap ({gap_pct:+.1f}%) — izle"

    # ------------------------------------------------------------------ #
    #  Toplu tarama                                                         #
    # ------------------------------------------------------------------ #

    def toplu_gap_tara(self, semboller: List[str]) -> List[dict]:
        """
        Tüm sembolleri tara, gap sinyallerini döner.
        [{"sembol", "sinyal_tipi", "sinyal_deger", "gap_pct", "aciklama"}]
        """
        bugun = datetime.now().strftime("%Y-%m-%d")

        # Günlük cache sıfırla
        if self._son_analiz_gunu != bugun:
            self._gap_cache.clear()
            self._analiz_yapildi = False
            self._son_analiz_gunu = bugun

        sinyaller: List[dict] = []
        for sembol in semboller:
            try:
                gap = self.gap_hesapla(sembol)
                if gap is None:
                    continue
                sin_tip, sin_deger, aciklama = self.sinyal_uret(gap)
                if sin_tip == "IGNORE":
                    continue
                sinyaller.append({
                    "sembol": sembol,
                    "sinyal_tipi": sin_tip,
                    "sinyal_deger": sin_deger,
                    "gap_pct": gap["gap_pct"],
                    "dun_kapanis": gap["dun_kapanis"],
                    "premarket_fiyat": gap["premarket_fiyat"],
                    "aciklama": aciklama,
                    "zaman": datetime.now().isoformat(),
                })
                logger.info(aciklama)
            except Exception as e:
                logger.debug(f"Gap tarama hatası {sembol}: {e}")

        self._analiz_yapildi = True
        # Gap büyüklüğüne göre sırala (en büyük gap önce)
        sinyaller.sort(key=lambda x: abs(x["gap_pct"]), reverse=True)
        return sinyaller

    # ------------------------------------------------------------------ #
    #  Momentum al → 15 dakika profit al kontrolü                          #
    # ------------------------------------------------------------------ #

    def momentum_kar_al_kontrol(
        self,
        sembol: str,
        giris_fiyat: float,
        giris_zaman: datetime,
        mevcut_fiyat: float,
    ) -> Tuple[bool, str]:
        """
        Gap momentum alımlarında ilk 15 dakika sonunda kâr al sinyali.
        Returns: (kapat_mi, neden)
        """
        sure = (datetime.now() - giris_zaman.replace(tzinfo=None)).total_seconds() / 60
        kazanc = (mevcut_fiyat - giris_fiyat) / giris_fiyat if giris_fiyat > 0 else 0

        if sure >= 15 and kazanc > 0.005:
            return True, f"Gap momentum 15dk kâr al: {kazanc*100:+.1f}%"
        if sure >= 15 and kazanc <= 0:
            return True, f"Gap momentum 15dk zarar: {kazanc*100:+.1f}% — çık"
        return False, ""

    # ------------------------------------------------------------------ #
    #  Özet                                                                 #
    # ------------------------------------------------------------------ #

    def ozet(self, sinyaller: List[dict]) -> str:
        """Sinyal listesinden okunabilir özet üret"""
        if not sinyaller:
            return "Gap analizi: önemli gap bulunamadı"
        satirlar = ["Gap Analizi Sinyalleri:"]
        for s in sinyaller:
            satirlar.append(f"  {s['sinyal_tipi']}: {s['sembol']} ({s['gap_pct']:+.1f}%) — {s['aciklama']}")
        return "\n".join(satirlar)
