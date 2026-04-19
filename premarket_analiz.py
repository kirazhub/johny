"""
JOHNY — Pre-Market Analiz
16:00–16:25 İstanbul arası çalışır (ABD piyasası açılmadan ~30 dk önce).
- Pre-market fiyatlar (yfinance prepost=True)
- Gece haberleri (Google News RSS)
- Vadeli göstergeler: SPY, QQQ, IWM pre-market değişimi
- Gap analizi: dün kapanış vs bugün pre-market
Sonucu ~/Projects/johny/premarket_raporu.txt dosyasına yazar.
"""
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pytz
import yfinance as yf

logger = logging.getLogger(__name__)

# İstanbul: UTC+3, EDT: UTC-4 → fark 7 saat
ISTANBUL_TZ = pytz.timezone("Europe/Istanbul")
EST_TZ = pytz.timezone("America/New_York")

# Pre-market pencere saatleri (İstanbul): 16:00 – 16:25
PREMARKET_BASLANGIC_SAAT = 16
PREMARKET_BASLANGIC_DAKIKA = 0
PREMARKET_BITIS_SAAT = 16
PREMARKET_BITIS_DAKIKA = 25

# Gap eşikleri
GAP_MOMENTUM_ESIK = 0.02    # %2: momentum al sinyali
GAP_FILL_ESIK_ALT = 0.005   # %0.5: gap fill alt sınırı
GAP_FILL_ESIK_UST = 0.015   # %1.5: gap fill üst sınırı

# Takip edilecek vadeli göstergeler
VADELI_SEMBOLLER = ["SPY", "QQQ", "IWM"]

# Gece haberleri için RSS
GECE_HABER_RSS = [
    "https://news.google.com/rss/search?q=stock+market+premarket&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=futures+nasdaq+dow+jones&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=earnings+report+guidance&hl=en-US&gl=US&ceid=US:en",
]


class PreMarketAnalizci:
    """Pre-market analiz ve rapor üretici"""

    def __init__(self, rapor_dosya: Optional[str] = None):
        from johny_config import PREMARKET_RAPOR_DOSYA, US_SEMBOLLER
        self.rapor_dosya = rapor_dosya or os.path.join(
            os.path.dirname(__file__), PREMARKET_RAPOR_DOSYA
        )
        self.semboller = US_SEMBOLLER

    # ------------------------------------------------------------------ #
    #  Saat kontrolü                                                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def premarket_penceresi_mi() -> bool:
        """
        Şu an İstanbul saatiyle 16:00–16:25 arasında mı?
        (ABD piyasası açılmadan önce ~30 dakika pencere)
        """
        simdi = datetime.now(ISTANBUL_TZ)
        baslangic = simdi.replace(
            hour=PREMARKET_BASLANGIC_SAAT,
            minute=PREMARKET_BASLANGIC_DAKIKA,
            second=0,
            microsecond=0,
        )
        bitis = simdi.replace(
            hour=PREMARKET_BITIS_SAAT,
            minute=PREMARKET_BITIS_DAKIKA,
            second=0,
            microsecond=0,
        )
        return baslangic <= simdi <= bitis

    # ------------------------------------------------------------------ #
    #  Pre-market fiyat çekme                                               #
    # ------------------------------------------------------------------ #

    def premarket_fiyat_cek(self, sembol: str) -> Optional[dict]:
        """
        yfinance ile pre-market fiyatını çek.
        Döner: {"sembol", "premarket_fiyat", "onceki_kapanis", "gap_pct"}
        """
        try:
            ticker = yf.Ticker(sembol)
            df = ticker.history(period="2d", prepost=True, interval="1m")
            if df is None or df.empty:
                return None

            # Dün kapanış: prepost=False ile son kapanış
            df_normal = ticker.history(period="2d", prepost=False)
            if df_normal is None or df_normal.empty:
                return None

            onceki_kapanis = float(df_normal["Close"].iloc[-1])

            # Pre-market: son 1 dakikalık veri
            bugun = datetime.now(EST_TZ).date()
            df_bugun = df[df.index.date == bugun]
            if df_bugun.empty:
                return None

            premarket_fiyat = float(df_bugun["Close"].iloc[-1])
            gap_pct = (premarket_fiyat - onceki_kapanis) / onceki_kapanis if onceki_kapanis > 0 else 0.0

            return {
                "sembol": sembol,
                "premarket_fiyat": round(premarket_fiyat, 2),
                "onceki_kapanis": round(onceki_kapanis, 2),
                "gap_pct": round(gap_pct * 100, 2),
                "gap_yonu": "UP" if gap_pct > 0 else "DOWN",
            }
        except Exception as e:
            logger.debug(f"Pre-market fiyat alınamadı {sembol}: {e}")
            return None

    # ------------------------------------------------------------------ #
    #  Gece haberleri                                                       #
    # ------------------------------------------------------------------ #

    def gece_haberlerini_cek(self, limit: int = 30) -> List[dict]:
        """Gece yayınlanan haberleri Google News RSS'den çek"""
        haberler: List[dict] = []
        try:
            import feedparser
        except ImportError:
            logger.warning("feedparser kurulu değil")
            return []

        for url in GECE_HABER_RSS:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[: limit // len(GECE_HABER_RSS)]:
                    haberler.append({
                        "baslik": getattr(entry, "title", ""),
                        "link":   getattr(entry, "link", ""),
                        "tarih":  getattr(entry, "published", ""),
                    })
            except Exception as e:
                logger.debug(f"RSS çekilemedi: {e}")

        return haberler

    # ------------------------------------------------------------------ #
    #  Gap analizi                                                          #
    # ------------------------------------------------------------------ #

    def gap_analiz_et(self, gap_pct: float, haber_var: bool = False) -> dict:
        """
        Gap büyüklüğüne ve habere göre öneri üret.
        gap_pct: yüzde olarak (örn. 2.3 = %2.3 up gap)
        """
        abs_gap = abs(gap_pct)
        yon = "UP" if gap_pct > 0 else "DOWN"

        if abs_gap < 0.5:
            return {
                "sinyal": "IGNORE",
                "aciklama": f"Küçük gap ({gap_pct:+.1f}%) — dikkate alma",
            }

        if abs_gap >= 2.0:
            if yon == "UP" and haber_var:
                return {
                    "sinyal": "MOMENTUM_AL",
                    "aciklama": f"Gap up {gap_pct:+.1f}% + haber var → ilk 15dk momentum AL",
                }
            elif yon == "DOWN":
                return {
                    "sinyal": "DIKKAT_SHORT",
                    "aciklama": f"Gap down {gap_pct:+.1f}% → dikkat, short fırsatı olabilir",
                }
            else:
                return {
                    "sinyal": "MOMENTUM_AL",
                    "aciklama": f"Gap up {gap_pct:+.1f}% — momentumu takip et",
                }

        if GAP_FILL_ESIK_ALT * 100 <= abs_gap <= GAP_FILL_ESIK_UST * 100:
            ters_yön = "SAT" if yon == "UP" else "AL"
            return {
                "sinyal": f"GAP_FILL_{ters_yön}",
                "aciklama": f"Gap fill fırsatı ({gap_pct:+.1f}%) → {ters_yön} — gap kapanacak beklenir",
            }

        return {
            "sinyal": "IZLE",
            "aciklama": f"Gap {gap_pct:+.1f}% — izle",
        }

    # ------------------------------------------------------------------ #
    #  Ana rapor                                                            #
    # ------------------------------------------------------------------ #

    def analiz_calistir(self) -> dict:
        """
        Tam pre-market analizi çalıştır.
        Döner: {"vadeli", "semboller", "haberler", "ozet"}
        """
        now_ist = datetime.now(ISTANBUL_TZ).strftime("%Y-%m-%d %H:%M")
        logger.info(f"Pre-market analizi başlatıldı — {now_ist} İstanbul")

        # 1. Vadeli göstergeler
        vadeli: Dict[str, dict] = {}
        for s in VADELI_SEMBOLLER:
            sonuc = self.premarket_fiyat_cek(s)
            if sonuc:
                vadeli[s] = sonuc

        # 2. Haberler
        haberler = self.gece_haberlerini_cek()
        haber_basliklar = " ".join(h["baslik"].lower() for h in haberler)

        # 3. Önemli semboller için gap analizi
        sembol_analizleri: List[dict] = []
        for s in self.semboller[:20]:  # Rate limit için ilk 20
            sonuc = self.premarket_fiyat_cek(s)
            if sonuc is None:
                continue
            gap_pct = sonuc["gap_pct"]
            haber_var = s.lower() in haber_basliklar
            gap_oneri = self.gap_analiz_et(gap_pct, haber_var)
            sembol_analizleri.append({**sonuc, **gap_oneri})

        # 4. Piyasa genel yönü (SPY gap'e göre)
        spy = vadeli.get("SPY", {})
        spy_gap = spy.get("gap_pct", 0.0)
        if spy_gap > 1.0:
            piyasa_yonu = "BULLISH_OPEN"
        elif spy_gap < -1.0:
            piyasa_yonu = "BEARISH_OPEN"
        else:
            piyasa_yonu = "FLAT_OPEN"

        return {
            "tarih": now_ist,
            "piyasa_yonu": piyasa_yonu,
            "vadeli": vadeli,
            "semboller": sembol_analizleri,
            "haberler": haberler[:10],
            "spy_gap_pct": spy_gap,
        }

    # ------------------------------------------------------------------ #
    #  Rapor dosyasına yaz                                                 #
    # ------------------------------------------------------------------ #

    def rapor_yaz(self, analiz: Optional[dict] = None) -> str:
        """Analiz sonucunu rapor dosyasına yaz, dosya yolunu döner"""
        if analiz is None:
            analiz = self.analiz_calistir()

        satirlar = [
            "=" * 60,
            f"JOHNY PRE-MARKET RAPORU — {analiz['tarih']}",
            "=" * 60,
            f"Piyasa Yönü: {analiz['piyasa_yonu']}",
            f"SPY Gap: {analiz['spy_gap_pct']:+.2f}%",
            "",
            "── Vadeli Göstergeler ──────────────────────────────────────",
        ]
        for sembol, veri in analiz.get("vadeli", {}).items():
            satirlar.append(
                f"  {sembol}: ${veri['premarket_fiyat']:.2f} "
                f"(önceki kapanış: ${veri['onceki_kapanis']:.2f}) "
                f"Gap: {veri['gap_pct']:+.2f}%"
            )

        satirlar += [
            "",
            "── Gap Analizi (Önemli Semboller) ──────────────────────────",
        ]
        for sa in analiz.get("semboller", []):
            if sa.get("sinyal", "IGNORE") == "IGNORE":
                continue
            satirlar.append(
                f"  {sa['sembol']}: {sa['aciklama']} "
                f"(gap {sa['gap_pct']:+.2f}%)"
            )

        satirlar += [
            "",
            "── Son Haberler ─────────────────────────────────────────────",
        ]
        for h in analiz.get("haberler", [])[:8]:
            satirlar.append(f"  • {h['baslik'][:100]}")

        satirlar += ["", "=" * 60]
        icerik = "\n".join(satirlar)

        try:
            with open(self.rapor_dosya, "w", encoding="utf-8") as f:
                f.write(icerik)
            logger.info(f"Pre-market raporu yazıldı: {self.rapor_dosya}")
        except Exception as e:
            logger.error(f"Rapor yazma hatası: {e}")

        return icerik

    # ------------------------------------------------------------------ #
    #  Raporu oku (main.py entegrasyonu)                                    #
    # ------------------------------------------------------------------ #

    def raporu_oku(self) -> str:
        """Mevcut pre-market raporunu dosyadan oku"""
        try:
            with open(self.rapor_dosya, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return "Pre-market raporu bulunamadı"
        except Exception as e:
            return f"Rapor okunamadı: {e}"

    def analize_gore_sinyaller(self, analiz: Optional[dict] = None) -> List[dict]:
        """
        Rapordaki gap analizlerine göre sinyal listesi döner.
        [{"sembol", "sinyal", "aciklama", "gap_pct"}]
        """
        if analiz is None:
            try:
                with open(self.rapor_dosya, "r", encoding="utf-8") as _f:
                    pass  # dosya var
            except FileNotFoundError:
                return []
            return []  # dosyadan parse yapmak yerine cache'i kullan

        sinyaller = []
        for sa in analiz.get("semboller", []):
            sinyal_kodu = sa.get("sinyal", "IGNORE")
            if sinyal_kodu not in ("IGNORE", "IZLE"):
                sinyaller.append({
                    "sembol": sa["sembol"],
                    "sinyal": sinyal_kodu,
                    "aciklama": sa.get("aciklama", ""),
                    "gap_pct": sa.get("gap_pct", 0.0),
                })
        return sinyaller
