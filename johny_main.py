"""
JOHNY — US Stock Market Trading Agent
Ana döngü ve orkestrasyon
"""
import logging
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

import pytz

from johny_config import (
    US_SEMBOLLER, GUNCELLEME_ARALIGI, LOG_DOSYASI, LOG_SEVIYESI,
    TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, VERSIYON, AGENT_ADI,
    MAX_DRAWDOWN_PCT,
)

# Logging kurulumu
logging.basicConfig(
    level=getattr(logging, LOG_SEVIYESI, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DOSYASI, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger("johny_main")

ISTANBUL_TZ = pytz.timezone("Europe/Istanbul")

# After-hours işlem için büyük kap hisseler
AFTER_HOURS_SEMBOLLER: List[str] = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META"]

# After-hours pozisyon küçültme çarpanı (%50 küçük)
AFTER_HOURS_CARPAN: float = 0.50


def _istanbul_saat() -> tuple:
    """(saat, dakika) İstanbul yerel saatiyle"""
    now = datetime.now(ISTANBUL_TZ)
    return now.hour, now.minute


class JohnyAjani:
    """JOHNY Ana Ajan Sınıfı"""

    def __init__(self):
        logger.info(f"{'='*60}")
        logger.info(f"🇺🇸 {AGENT_ADI} v{VERSIYON} başlatılıyor...")
        logger.info(f"{'='*60}")

        # Temel modüller
        from data.fetcher import VeriFetcher
        from data.news import HaberFetcher
        from data.market_breadth import PiyasaGenisligi
        from strategies.orchestrator import StratejiOrkestratori
        from risk.var import VaRHesaplayici
        from risk.correlation import KorelasyonAnalizci
        from johny_portfolio import JohnyPortfoy
        from johny_database import JohnyDatabase
        from johny_telegram import TelegramBildirici
        from backtest.engine import BacktestEngine

        # Yeni profesyonel modüller
        from strategies.earnings_strategy import KazancStratejisi
        from sector_rotation import MacroSektorRotasyonu
        from premarket_analiz import PreMarketAnalizci
        from korelasyon import KorelasyonTicareti
        from gap_strategy import GapStratejisi
        from makro_takvim import MakroTakvim

        self.fetcher = VeriFetcher()
        self.haber_fetcher = HaberFetcher()
        self.market_breadth = PiyasaGenisligi()
        self.orkestrator = StratejiOrkestratori()
        self.var_calc = VaRHesaplayici()
        self.korelasyon_analiz = KorelasyonAnalizci()
        self.db = JohnyDatabase()
        self.portfoy = JohnyPortfoy(db=self.db)
        self.telegram = TelegramBildirici(TELEGRAM_TOKEN or "", TELEGRAM_CHAT_ID or "")
        self.backtest_engine = BacktestEngine()

        # Profesyonel modüller
        self.kazanc_stratejisi = KazancStratejisi()
        self.macro_sektor = MacroSektorRotasyonu()
        self.premarket_analizci = PreMarketAnalizci()
        self.korelasyon_ticareti = KorelasyonTicareti()
        self.gap_stratejisi = GapStratejisi()
        self.makro_takvim = MakroTakvim()

        # Durum
        self._calisıyor = False
        self._son_fiyat_guncelleme = 0.0
        self._son_haber_guncelleme = 0.0
        self._son_teknik_guncelleme = 0.0
        self._son_sektor_guncelleme = 0.0
        self._son_korelasyon_guncelleme = 0.0

        # Zaman bazlı tetikleyici takibi
        self._premarket_tamamlandi_gun: Optional[str] = None
        self._gap_analiz_tamamlandi_gun: Optional[str] = None
        self._premarket_analiz_sonucu: Optional[dict] = None

        # 7/24 mod takibi
        self._son_mod: str = ""
        self._son_hourly_optimize: float = 0.0   # Son hourly_optimize çalışma zamanı
        self._son_backtest_gece: str = ""         # Son gece backtesti (tarih)
        self._sabah_raporu_tamamlandi: Optional[str] = None  # Tarih damgası
        self._hazirlik_tamamlandi_gun: Optional[str] = None  # Hazırlık modu tamamlama

        # Önbellek
        self.fiyat_verisi: Dict[str, dict] = {}
        self.teknik_veriler: Dict = {}
        self.haberler: List[dict] = []
        self.sinyaller: List[dict] = []
        self.piyasa_durumu_cache: dict = {}
        self.fear_greed_cache: dict = {}
        self.usdtry_cache: float = 32.0
        self.sektor_performans_cache: Dict[str, dict] = {}

        # Gap sinyalleri önbelleği
        self._gap_sinyalleri: List[dict] = []
        self._korelasyon_sinyalleri: List[dict] = []

        logger.info(f"✅ JOHNY modülleri yüklendi (profesyonel seviye)")

    # ------------------------------------------------------------------ #
    #  Veri güncelleme                                                      #
    # ------------------------------------------------------------------ #

    def veri_guncelle(self, zorunlu: bool = False) -> None:
        """Veri güncelleme döngüsü"""
        simdi = time.time()

        # Fiyat güncellemesi
        if zorunlu or (simdi - self._son_fiyat_guncelleme) >= GUNCELLEME_ARALIGI["fiyat"]:
            try:
                self.fiyat_verisi = self.fetcher.toplu_fiyat_cek()
                self.portfoy.fiyatları_guncelle(self.fiyat_verisi)
                self._son_fiyat_guncelleme = simdi
                logger.debug(f"Fiyatlar güncellendi: {len(self.fiyat_verisi)} sembol")
            except Exception as e:
                logger.error(f"Fiyat güncelleme hatası: {e}")

        # Haber güncellemesi
        if zorunlu or (simdi - self._son_haber_guncelleme) >= GUNCELLEME_ARALIGI["haber"]:
            try:
                self.haberler = self.haber_fetcher.haberler_cek(limit=30)
                self.fear_greed_cache = self.fetcher.fear_greed_cek()
                self.usdtry_cache = self.fetcher.usdtry_kuru_cek()
                self._son_haber_guncelleme = simdi
                logger.debug(f"Haberler güncellendi: {len(self.haberler)} haber")
            except Exception as e:
                logger.error(f"Haber güncelleme hatası: {e}")

        # Teknik göstergeler
        if zorunlu or (simdi - self._son_teknik_guncelleme) >= GUNCELLEME_ARALIGI["teknik"]:
            try:
                self._teknik_verileri_guncelle()
                self._son_teknik_guncelleme = simdi
            except Exception as e:
                logger.error(f"Teknik güncelleme hatası: {e}")

        # Piyasa durumu
        try:
            self.piyasa_durumu_cache = self.fetcher.piyasa_durumu()
        except Exception as e:
            logger.error(f"Piyasa durumu hatası: {e}")

        # Sektör rotasyonu (saatlik)
        if zorunlu or (simdi - self._son_sektor_guncelleme) >= 3600:
            try:
                self.macro_sektor.guncelle()
                self._son_sektor_guncelleme = simdi
            except Exception as e:
                logger.debug(f"Sektör rotasyon güncelleme hatası: {e}")

        # Korelasyon ticareti (15 dakikalık)
        try:
            yeni_korel = self.korelasyon_ticareti.guncelle()
            if yeni_korel:
                self._korelasyon_sinyalleri = yeni_korel
                self._son_korelasyon_guncelleme = simdi
        except Exception as e:
            logger.debug(f"Korelasyon güncelleme hatası: {e}")

    def _teknik_verileri_guncelle(self) -> None:
        """Teknik göstergeleri hesapla"""
        for sembol in US_SEMBOLLER[:30]:  # Rate limit için ilk 30
            try:
                df = self.fetcher.hisse_verisi_cek(sembol, donem="6mo")
                if df is not None and not df.empty:
                    df_teknik = self.fetcher.teknik_gostergeler_hesapla(df)
                    if df_teknik is not None:
                        self.teknik_veriler[sembol] = df_teknik
            except Exception as e:
                logger.warning(f"Teknik veri hatası {sembol}: {e}")

    # ------------------------------------------------------------------ #
    #  Zaman bazlı tetikleyiciler                                           #
    # ------------------------------------------------------------------ #

    def zaman_bazli_gorevler(self) -> None:
        """
        Her döngüde saat kontrolü yaparak zamanlanmış görevleri çalıştırır.
        16:00-16:25 İstanbul → pre-market analiz
        16:25-16:35 İstanbul → gap analizi
        """
        saat, dakika = _istanbul_saat()
        bugun = datetime.now(ISTANBUL_TZ).strftime("%Y-%m-%d")

        # 16:00 – 16:25: Pre-market analizi (günde bir kez)
        if (
            16 <= saat < 16 and 0 <= dakika <= 25  # noqa: SIM300 — saat==16 her zaman
            or (saat == 16 and dakika <= 25)
        ) and self._premarket_tamamlandi_gun != bugun:
            try:
                logger.info("Pre-market analizi başlatılıyor...")
                self._premarket_analiz_sonucu = self.premarket_analizci.analiz_calistir()
                icerik = self.premarket_analizci.rapor_yaz(self._premarket_analiz_sonucu)
                self._premarket_tamamlandi_gun = bugun
                piyasa_yonu = self._premarket_analiz_sonucu.get("piyasa_yonu", "")
                spy_gap = self._premarket_analiz_sonucu.get("spy_gap_pct", 0.0)
                logger.info(f"Pre-market raporu hazır: {piyasa_yonu}, SPY gap {spy_gap:+.2f}%")
                self.telegram.mesaj_gonder(
                    f"📊 <b>Pre-Market Raporu</b>\n"
                    f"Piyasa Yönü: {piyasa_yonu}\n"
                    f"SPY Gap: {spy_gap:+.2f}%"
                )
            except Exception as e:
                logger.error(f"Pre-market analiz hatası: {e}")

        # 16:25 – 16:35: Gap analizi (günde bir kez)
        if (
            saat == 16 and 25 <= dakika <= 35
        ) and self._gap_analiz_tamamlandi_gun != bugun:
            try:
                logger.info("Gap analizi başlatılıyor...")
                gap_sinyalleri = self.gap_stratejisi.toplu_gap_tara(US_SEMBOLLER[:20])
                self._gap_sinyalleri = gap_sinyalleri
                self._gap_analiz_tamamlandi_gun = bugun
                if gap_sinyalleri:
                    ozet = self.gap_stratejisi.ozet(gap_sinyalleri)
                    logger.info(ozet)
                    self.telegram.mesaj_gonder(f"📈 <b>Gap Analizi</b>\n{ozet[:500]}")
            except Exception as e:
                logger.error(f"Gap analiz hatası: {e}")

    # ------------------------------------------------------------------ #
    #  Makro takvim kontrolü                                                #
    # ------------------------------------------------------------------ #

    def makro_risk_kontrol(self) -> dict:
        """Makro takvime göre risk ayarı döner"""
        try:
            return self.makro_takvim.risk_ayari_al()
        except Exception as e:
            logger.debug(f"Makro risk kontrol hatası: {e}")
            return {"durum": "NORMAL", "pozisyon_carpani": 1.0, "stop_loss_carpani": 1.0,
                    "sadece_teknik": False, "mesaj": "Normal gün"}

    # ------------------------------------------------------------------ #
    #  Max Drawdown kontrolü                                                #
    # ------------------------------------------------------------------ #

    def max_drawdown_kontrol_ve_kapat(self) -> bool:
        """
        -%8 drawdown kontrolü: tetiklenirse tüm pozisyonları kapat.
        Returns: True ise pozisyonlar kapatıldı (24h bekleme)
        """
        try:
            portfoy_degeri = self.portfoy.portfoy_degeri()
            dd_sonuc = self.portfoy.risk_limitleri.max_drawdown_kontrol(portfoy_degeri)

            if dd_sonuc.get("tum_pozisyonlari_kapat") and self.portfoy.pozisyonlar:
                logger.warning(
                    f"MAX DRAWDOWN TETİKLENDİ: {dd_sonuc['drawdown_pct']:.1f}% — "
                    f"TÜM {len(self.portfoy.pozisyonlar)} POZİSYON KAPATILIYOR"
                )
                self.telegram.mesaj_gonder(
                    f"🚨 <b>MAX DRAWDOWN!</b>\n"
                    f"Drawdown: {dd_sonuc['drawdown_pct']:.1f}%\n"
                    f"Tüm pozisyonlar kapatılıyor, 24 saat bekleniyor."
                )
                for sembol in list(self.portfoy.pozisyonlar.keys()):
                    fiyat = self.fiyat_verisi.get(sembol, {}).get("fiyat",
                            self.portfoy.pozisyonlar[sembol].mevcut_fiyat)
                    self.portfoy.sat(sembol, fiyat, "Max Drawdown Koruması")
                return True
        except Exception as e:
            logger.error(f"Max drawdown kontrol hatası: {e}")
        return False

    # ------------------------------------------------------------------ #
    #  Sinyal tarama                                                        #
    # ------------------------------------------------------------------ #

    def sinyal_taramasi_yap(self) -> List[dict]:
        """Tüm sembolleri tara (makro ve kazanç sinyalleri dahil)"""
        try:
            # Sektör rotasyon ağırlıkları
            sektor_agirlıklar = self.macro_sektor._sektor_agirliklari or {}
            sektor_perf_dict = {
                s: v.get("degisim", 0)
                for s, v in self.sektor_performans_cache.items()
            }
            sektor_perf_dict.update(sektor_agirlıklar)

            ek_veri = {
                "haberler": self.haberler,
                "fear_greed": self.fear_greed_cache,
                "sektor_performans": sektor_perf_dict,
            }
            self.sinyaller = self.orkestrator.toplu_tarama(
                US_SEMBOLLER,
                self.teknik_veriler,
                ek_veri,
            )

            # Gap sinyallerini ana sinyal listesine ekle (açılışta)
            if self._gap_sinyalleri:
                for gs in self._gap_sinyalleri:
                    self.sinyaller.append({
                        "sembol": gs["sembol"],
                        "birlesik_sinyal": gs["sinyal_deger"],
                        "tavsiye": f"Gap {gs['sinyal_tipi']}",
                        "aciklama": gs["aciklama"],
                        "_gap_sinyal": True,
                    })

            # Korelasyon sinyalleri
            if self._korelasyon_sinyalleri:
                for ks in self._korelasyon_sinyalleri:
                    self.sinyaller.append({
                        "sembol": ks["sembol"],
                        "birlesik_sinyal": ks["sinyal_deger"],
                        "tavsiye": f"Korelasyon {ks['sinyal']}",
                        "aciklama": ks["aciklama"],
                        "_korelasyon_sinyal": True,
                    })

            return self.sinyaller
        except Exception as e:
            logger.error(f"Sinyal tarama hatası: {e}")
            return []

    # ------------------------------------------------------------------ #
    #  Otomatik işlem                                                       #
    # ------------------------------------------------------------------ #

    def otomatik_islem(self) -> List[dict]:
        """Otomatik alım/satım (makro + kazanç risk ayarlarıyla)"""
        islemler: List[dict] = []

        # Max drawdown kontrolü önce
        if self.max_drawdown_kontrol_ve_kapat():
            return islemler

        makro_risk = self.makro_risk_kontrol()
        pozisyon_carpani = makro_risk.get("pozisyon_carpani", 1.0)
        sadece_teknik = makro_risk.get("sadece_teknik", False)

        if makro_risk["durum"] != "NORMAL":
            logger.info(f"Makro risk: {makro_risk['mesaj']}")

        try:
            # Stop-loss kontrolü (dinamik ATR bazlı)
            stop_tetiklenenler = self._dinamik_stop_kontrol()
            for tetik in stop_tetiklenenler:
                sembol = tetik["sembol"]
                fiyat = tetik["fiyat"]
                neden = tetik["neden"]
                sonuc = self.portfoy.sat(sembol, fiyat, neden)
                if sonuc["basarili"]:
                    islem = sonuc["islem"]
                    islemler.append(islem)
                    self.telegram.sat_bildirimi(
                        sembol, islem["lot"], fiyat,
                        islem["kar_zarar"], neden,
                        self.portfoy.portfoy_degeri()
                    )

            # Yeni alım sinyalleri (piyasa açıksa)
            if self.piyasa_durumu_cache.get("acik", False):
                # Makro kritik günde sadece teknik sinyallere bak
                aktif_sinyaller = [
                    s for s in self.sinyaller[:20]
                    if not sadece_teknik or not s.get("_gap_sinyal") and not s.get("_korelasyon_sinyal")
                ]

                for sinyal in aktif_sinyaller:
                    sembol = sinyal.get("sembol", "")
                    birlesik = sinyal.get("birlesik_sinyal", 0)
                    tavsiye = sinyal.get("tavsiye", "")

                    if birlesik >= 0.35 and sembol not in self.portfoy.pozisyonlar:
                        if sembol not in self.fiyat_verisi:
                            continue
                        fiyat = self.fiyat_verisi[sembol]["fiyat"]
                        df = self.teknik_veriler.get(sembol)
                        atr = float(df["ATR"].iloc[-1]) if df is not None and "ATR" in df.columns else None

                        # Kazanç yaklaşıyor mu?
                        kazanc_bilgi = self.kazanc_stratejisi.yaklasan_kazanc_cek(sembol)
                        kazanc_gun_kala = kazanc_bilgi["gun_kala"] if kazanc_bilgi else 99

                        # Whisper ve analist bilgisi
                        whisper = 0.0
                        oneri = "hold"
                        if kazanc_gun_kala <= 3:
                            whisper = self.kazanc_stratejisi.whisper_number_hesapla(sembol)
                            beklenti = self.kazanc_stratejisi.analist_beklentisi_al(sembol)
                            oneri = beklenti.get("oneri", "hold")

                        kazanc_carpani, carpan_acik = self.kazanc_stratejisi.pozisyon_carpani_hesapla(
                            kazanc_gun_kala, whisper, oneri
                        )

                        # Toplam çarpan = makro × kazanç
                        efektif_carpan = pozisyon_carpani * kazanc_carpani
                        if efektif_carpan < 1.0:
                            logger.info(f"{sembol} pozisyon küçültüldü: çarpan={efektif_carpan:.2f} ({carpan_acik})")

                        # Dinamik stop-loss yüzdesi
                        kazanc_oncesi_flag = 0 <= kazanc_gun_kala <= 3
                        makro_kritik_flag = makro_risk["durum"] in ("KRITIK_GUN",)

                        # Ortalama ATR
                        ortalama_atr: Optional[float] = None
                        if df is not None and "ATR" in df.columns:
                            ortalama_atr = float(df["ATR"].mean())

                        stop_bilgi = self.portfoy.risk_limitleri.dinamik_stop_loss_hesapla(
                            giris_fiyat=fiyat,
                            atr=atr,
                            ortalama_atr=ortalama_atr,
                            kazanc_oncesi=kazanc_oncesi_flag,
                            makro_kritik_gun=makro_kritik_flag,
                        )

                        # sinyal_guven'i çarpanla ayarla
                        efektif_guven = abs(birlesik) * efektif_carpan
                        sonuc = self.portfoy.al(
                            sembol, fiyat,
                            sinyal_guven=efektif_guven,
                            strateji=tavsiye,
                            atr=atr,
                        )
                        if sonuc["basarili"]:
                            islem = sonuc["islem"]
                            islemler.append(islem)
                            # Stop fiyatını dinamik değerle güncelle
                            if sembol in self.portfoy.pozisyonlar:
                                self.portfoy.pozisyonlar[sembol].stop_fiyat = stop_bilgi["stop_fiyat"]
                            self.telegram.al_bildirimi(
                                sembol, islem["lot"], fiyat,
                                tavsiye, self.portfoy.portfoy_degeri()
                            )
                            if stop_bilgi["durum"] != "NORMAL":
                                logger.info(f"  {stop_bilgi['aciklama']}")

        except Exception as e:
            logger.error(f"Otomatik işlem hatası: {e}")
        return islemler

    def _dinamik_stop_kontrol(self) -> List[dict]:
        """
        Her pozisyon için dinamik stop-loss kontrolü.
        Piyasa koşuluna göre stop yüzdesi ayarlanır.
        """
        makro_risk = self.makro_risk_kontrol()
        makro_kritik = makro_risk["durum"] == "KRITIK_GUN"
        tetiklenenler: List[dict] = []

        for sembol, poz in list(self.portfoy.pozisyonlar.items()):
            if sembol not in self.fiyat_verisi:
                continue
            fiyat = self.fiyat_verisi[sembol].get("fiyat", poz.mevcut_fiyat)

            # Kazanç durumu
            kazanc_bilgi = self.kazanc_stratejisi.yaklasan_kazanc_cek(sembol)
            kazanc_gun_kala = kazanc_bilgi["gun_kala"] if kazanc_bilgi else 99
            kazanc_oncesi = 0 <= kazanc_gun_kala <= 3

            # ATR
            df = self.teknik_veriler.get(sembol)
            atr: Optional[float] = None
            ortalama_atr: Optional[float] = None
            if df is not None and "ATR" in df.columns:
                atr = float(df["ATR"].iloc[-1])
                ortalama_atr = float(df["ATR"].mean())

            stop_bilgi = self.portfoy.risk_limitleri.dinamik_stop_loss_hesapla(
                giris_fiyat=poz.giris_fiyat,
                atr=atr,
                ortalama_atr=ortalama_atr,
                kazanc_oncesi=kazanc_oncesi,
                makro_kritik_gun=makro_kritik,
            )

            kontrol = self.portfoy.risk_limitleri.stop_loss_kontrolu(
                sembol, poz.giris_fiyat, fiyat, poz.trailing_max,
                stop_pct_override=stop_bilgi["stop_pct"],
            )
            if kontrol["cikis_gerekli"]:
                tetiklenenler.append({
                    "sembol": sembol,
                    "fiyat": fiyat,
                    "neden": kontrol["cikis_nedeni"],
                    **kontrol,
                })
        return tetiklenenler

    # ------------------------------------------------------------------ #
    #  Durum raporu                                                         #
    # ------------------------------------------------------------------ #

    def durum_raporu(self) -> dict:
        """Mevcut durum raporu"""
        ozet = self.portfoy.pozisyon_ozeti()
        ozet["usdtry"] = self.usdtry_cache
        ozet["portfoy_degeri_tl"] = ozet["portfoy_degeri_usd"] * self.usdtry_cache
        ozet["piyasa_durumu"] = self.piyasa_durumu_cache
        ozet["fear_greed"] = self.fear_greed_cache
        ozet["sinyal_sayisi"] = len(self.sinyaller)
        ozet["son_guncelleme"] = datetime.now().isoformat()
        # Makro takvim özeti
        try:
            ozet["makro_ozet"] = self.makro_takvim.ozet()
        except Exception:
            pass
        return ozet

    # ------------------------------------------------------------------ #
    #  Backtest                                                             #
    # ------------------------------------------------------------------ #

    def backtest_calistir(self, ilerleme_fn=None) -> dict:
        """Backtest çalıştır"""
        logger.info("Backtest başlatılıyor...")
        return self.backtest_engine.backtest_calistir(
            semboller=US_SEMBOLLER[:15],
            strateji_sinyal_fn=self._sinyal_fn_wrapper,
            ilerleme_fn=ilerleme_fn,
        )

    def _sinyal_fn_wrapper(self, sembol, df):
        """Backtest için sinyal fonksiyonu wrapper"""
        try:
            df_teknik = self.fetcher.teknik_gostergeler_hesapla(df)
            if df_teknik is None:
                return None
            return self.orkestrator.analiz_et(sembol, df_teknik)
        except Exception:
            return None

    # ------------------------------------------------------------------ #
    #  Piyasa modu                                                          #
    # ------------------------------------------------------------------ #

    def piyasa_durumu_al(self) -> str:
        """İstanbul saatine göre piyasa modunu döner: ACIK / AFTER_HOURS / OGRENME / HAZIRLIK"""
        now = datetime.now(ISTANBUL_TZ)
        saat = now.hour
        dakika = now.minute
        saat_dakika = saat * 60 + dakika
        if 16 * 60 + 30 <= saat_dakika < 23 * 60:
            return "ACIK"
        elif saat_dakika >= 23 * 60 or saat_dakika < 3 * 60:
            return "AFTER_HOURS"
        elif 3 * 60 <= saat_dakika < 9 * 60:
            return "OGRENME"
        else:
            return "HAZIRLIK"

    def _mod_degisimi_bildir(self, eski: str, yeni: str) -> None:
        """Mod değişimini logla ve Telegram'a bildir"""
        EMOJI = {"ACIK": "🟢", "AFTER_HOURS": "🌙", "OGRENME": "📚", "HAZIRLIK": "☀️"}
        ACIKLAMA = {
            "ACIK": "Tam strateji aktif — tüm sinyaller",
            "AFTER_HOURS": "Büyük kap ve earnings hisseleri — %50 pozisyon",
            "OGRENME": "Gece öğrenme modu — backtest & optimizasyon",
            "HAZIRLIK": "Sabah hazırlık — tarama & strateji belirleme",
        }
        e = EMOJI.get(yeni, "🔄")
        acik = ACIKLAMA.get(yeni, yeni)
        logger.info(f"{'='*55}")
        logger.info(f"{e} MOD: {eski or 'BAŞLANGIC'} → {yeni}")
        logger.info(f"   {acik}")
        logger.info(f"{'='*55}")
        try:
            self.telegram.mesaj_gonder(
                f"{e} <b>JOHNY Mod Değişimi</b>\n"
                f"{eski or 'BAŞLANGIÇ'} → <b>{yeni}</b>\n"
                f"{acik}"
            )
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    #  ACIK modu döngüsü                                                    #
    # ------------------------------------------------------------------ #

    def _acik_dongu(self) -> None:
        """Piyasa açıkken — tam strateji, tüm sinyaller"""
        self.zaman_bazli_gorevler()
        self.veri_guncelle()
        self.sinyal_taramasi_yap()
        self.otomatik_islem()

    # ------------------------------------------------------------------ #
    #  AFTER-HOURS modu döngüsü                                             #
    # ------------------------------------------------------------------ #

    def _after_hours_dongu(self) -> None:
        """After-hours: sadece büyük kap + earnings hisseleri, %50 küçük pozisyon"""
        # Veri güncelle (fiyat ve haberler)
        self.veri_guncelle()

        # After-hours aktif semboller: büyük kap + bugün earnings açıklayan hisseler
        aktif = list(AFTER_HOURS_SEMBOLLER)
        try:
            from johny_config import US_SEMBOLLER as _US
            yaklasan = self.kazanc_stratejisi.yaklasan_kazanclar_listele(_US[:30], gun_esik=1)
            for kayit in yaklasan:
                s = kayit.get("sembol", "")
                if s and s not in aktif:
                    aktif.append(s)
        except Exception as e:
            logger.debug(f"After-hours earnings listesi hatası: {e}")

        logger.debug(f"After-hours aktif semboller ({len(aktif)}): {aktif[:10]}")

        # Mevcut pozisyonlarda stop kontrolü
        try:
            stop_tetiklenenler = self._dinamik_stop_kontrol()
            for tetik in stop_tetiklenenler:
                sembol = tetik["sembol"]
                fiyat = tetik["fiyat"]
                neden = tetik["neden"]
                sonuc = self.portfoy.sat(sembol, fiyat, neden)
                if sonuc["basarili"]:
                    islem = sonuc["islem"]
                    self.telegram.sat_bildirimi(
                        sembol, islem["lot"], fiyat,
                        islem["kar_zarar"], neden,
                        self.portfoy.portfoy_degeri()
                    )
        except Exception as e:
            logger.error(f"After-hours stop kontrol hatası: {e}")

        # After-hours alım — sadece aktif semboller, sinyal güvenini yarıya indir
        try:
            for sembol in aktif:
                if sembol not in self.fiyat_verisi:
                    continue
                if sembol in self.portfoy.pozisyonlar:
                    continue
                # Sinyal bul
                sinyal = next(
                    (s for s in self.sinyaller if s.get("sembol") == sembol), None
                )
                if sinyal is None:
                    continue
                birlesik = sinyal.get("birlesik_sinyal", 0)
                tavsiye = sinyal.get("tavsiye", "")
                # After-hours eşiği biraz daha yüksek tutuyoruz
                if birlesik < 0.45:
                    continue
                fiyat = self.fiyat_verisi[sembol]["fiyat"]
                df = self.teknik_veriler.get(sembol)
                atr = float(df["ATR"].iloc[-1]) if df is not None and "ATR" in df.columns else None

                # %50 küçük pozisyon
                efektif_guven = abs(birlesik) * AFTER_HOURS_CARPAN
                sonuc = self.portfoy.al(
                    sembol, fiyat,
                    sinyal_guven=efektif_guven,
                    strateji=f"[AH] {tavsiye}",
                    atr=atr,
                )
                if sonuc["basarili"]:
                    islem = sonuc["islem"]
                    self.telegram.al_bildirimi(
                        sembol, islem["lot"], fiyat,
                        f"[AFTER-HOURS] {tavsiye}",
                        self.portfoy.portfoy_degeri()
                    )
        except Exception as e:
            logger.error(f"After-hours alım hatası: {e}")

    # ------------------------------------------------------------------ #
    #  OGRENME modu döngüsü (03:00 – 09:00)                                #
    # ------------------------------------------------------------------ #

    def _ogrenme_dongu(self) -> None:
        """Gece öğrenme modu: optimizasyon, backtest, hazırlık listeleri"""
        simdi = time.time()
        bugun = datetime.now(ISTANBUL_TZ).strftime("%Y-%m-%d")
        now = datetime.now(ISTANBUL_TZ)
        saat = now.hour

        # Saatlik: hourly_optimize.py çalıştır
        if simdi - self._son_hourly_optimize >= 3600:
            logger.info("Gece öğrenme: hourly_optimize.py başlatılıyor...")
            try:
                proje_dizin = "/Users/kiraz/Projects/johny"
                sonuc = subprocess.run(
                    [sys.executable, "hourly_optimize.py"],
                    capture_output=True, text=True,
                    cwd=proje_dizin, timeout=300
                )
                if sonuc.returncode == 0:
                    logger.info("hourly_optimize.py tamamlandı")
                else:
                    logger.warning(f"hourly_optimize.py hata kodu: {sonuc.returncode}")
                    if sonuc.stderr:
                        logger.debug(f"hourly_optimize stderr: {sonuc.stderr[:300]}")
            except subprocess.TimeoutExpired:
                logger.warning("hourly_optimize.py zaman aşımı (300s)")
            except Exception as e:
                logger.error(f"hourly_optimize.py çalıştırma hatası: {e}")
            self._son_hourly_optimize = simdi

        # Gece backtest (günde bir kez, 04:00-05:00 arası)
        if saat == 4 and self._son_backtest_gece != bugun:
            logger.info("Gece öğrenme: backtest kombinasyonları başlatılıyor...")
            try:
                self.backtest_calistir()
                self._son_backtest_gece = bugun
                logger.info("Gece backtest tamamlandı")
            except Exception as e:
                logger.error(f"Gece backtest hatası: {e}")

        # Gap & Go listesi hazırla (05:00-06:00 arası, günde bir kez)
        if saat == 5 and self._gap_analiz_tamamlandi_gun != bugun:
            logger.info("Gece öğrenme: Gap & Go listesi hazırlanıyor...")
            try:
                from johny_config import US_SEMBOLLER as _US
                gap_sinyalleri = self.gap_stratejisi.toplu_gap_tara(_US[:30])
                self._gap_sinyalleri = gap_sinyalleri
                self._gap_analiz_tamamlandi_gun = bugun
                logger.info(f"Gap & Go listesi hazır: {len(gap_sinyalleri)} sinyal")
            except Exception as e:
                logger.error(f"Gece gap listesi hatası: {e}")

        # Pre-market scanner hazırla (07:00-08:00 arası)
        if saat == 7 and self._premarket_tamamlandi_gun != bugun:
            logger.info("Gece öğrenme: Pre-market scanner çalıştırılıyor...")
            try:
                self._premarket_analiz_sonucu = self.premarket_analizci.analiz_calistir()
                self.premarket_analizci.rapor_yaz(self._premarket_analiz_sonucu)
                self._premarket_tamamlandi_gun = bugun
                piyasa_yonu = self._premarket_analiz_sonucu.get("piyasa_yonu", "")
                spy_gap = self._premarket_analiz_sonucu.get("spy_gap_pct", 0.0)
                logger.info(f"Pre-market scanner hazır: {piyasa_yonu}, SPY gap {spy_gap:+.2f}%")
            except Exception as e:
                logger.error(f"Pre-market scanner hatası: {e}")

        # Sabah raporu (08:00-08:30 arası, günde bir kez)
        if saat == 8 and self._sabah_raporu_tamamlandi != bugun:
            logger.info("Gece öğrenme: Sabah raporu hazırlanıyor...")
            try:
                rapor = self.durum_raporu()
                makro_risk = self.makro_risk_kontrol()
                piyasa_yonu = ""
                spy_gap = 0.0
                if self._premarket_analiz_sonucu:
                    piyasa_yonu = self._premarket_analiz_sonucu.get("piyasa_yonu", "")
                    spy_gap = self._premarket_analiz_sonucu.get("spy_gap_pct", 0.0)
                gap_sayisi = len(self._gap_sinyalleri)
                self.telegram.mesaj_gonder(
                    f"🌅 <b>Sabah Raporu — {bugun}</b>\n"
                    f"Portföy: ${rapor['portfoy_degeri_usd']:.2f} | "
                    f"K/Z: ${rapor['toplam_kar_zarar_usd']:+.2f}\n"
                    f"Pre-market: {piyasa_yonu} | SPY gap: {spy_gap:+.2f}%\n"
                    f"Gap & Go fırsatı: {gap_sayisi} hisse\n"
                    f"Makro: {makro_risk.get('mesaj', 'Normal')}"
                )
                self._sabah_raporu_tamamlandi = bugun
                logger.info("Sabah raporu Telegram'a gönderildi")
            except Exception as e:
                logger.error(f"Sabah raporu hatası: {e}")

    # ------------------------------------------------------------------ #
    #  HAZIRLIK modu döngüsü (09:00 – 16:30)                               #
    # ------------------------------------------------------------------ #

    def _hazirlik_dongu(self) -> None:
        """Sabah hazırlık modu: tarama, rotasyon güncelleme, strateji belirleme"""
        bugun = datetime.now(ISTANBUL_TZ).strftime("%Y-%m-%d")

        # Hazırlık görevlerini günde bir kez çalıştır
        if self._hazirlik_tamamlandi_gun == bugun:
            # Sadece sektör rotasyonunu saatlik güncelle
            simdi = time.time()
            if simdi - self._son_sektor_guncelleme >= 3600:
                try:
                    self.macro_sektor.guncelle()
                    self._son_sektor_guncelleme = simdi
                    logger.debug("Hazırlık: sektör rotasyonu güncellendi")
                except Exception as e:
                    logger.debug(f"Sektör rotasyon güncelleme hatası: {e}")
            return

        logger.info(f"Sabah hazırlık modu başladı — {bugun}")

        # 1. Pre-market tarama
        try:
            if self._premarket_tamamlandi_gun != bugun:
                logger.info("Hazırlık: Pre-market tarama çalıştırılıyor...")
                self._premarket_analiz_sonucu = self.premarket_analizci.analiz_calistir()
                self.premarket_analizci.rapor_yaz(self._premarket_analiz_sonucu)
                self._premarket_tamamlandi_gun = bugun
                piyasa_yonu = self._premarket_analiz_sonucu.get("piyasa_yonu", "")
                spy_gap = self._premarket_analiz_sonucu.get("spy_gap_pct", 0.0)
                logger.info(f"Pre-market hazır: {piyasa_yonu}, SPY gap {spy_gap:+.2f}%")
        except Exception as e:
            logger.error(f"Hazırlık pre-market hatası: {e}")

        # 2. Sektör rotasyon güncelle
        try:
            logger.info("Hazırlık: Sektör rotasyonu güncelleniyor...")
            self.macro_sektor.guncelle()
            self._son_sektor_guncelleme = time.time()
            logger.info("Sektör rotasyonu güncellendi")
        except Exception as e:
            logger.error(f"Hazırlık sektör rotasyon hatası: {e}")

        # 3. Earnings calendar kontrol
        try:
            logger.info("Hazırlık: Earnings takvimi kontrol ediliyor...")
            from johny_config import US_SEMBOLLER as _US
            earnings_listesi = []
            for sembol in _US[:20]:
                try:
                    kazanc = self.kazanc_stratejisi.yaklasan_kazanc_cek(sembol)
                    if kazanc and kazanc.get("gun_kala", 99) <= 5:
                        earnings_listesi.append(f"{sembol}({kazanc['gun_kala']}g)")
                except Exception:
                    continue
            if earnings_listesi:
                logger.info(f"Yaklaşan earnings: {', '.join(earnings_listesi)}")
        except Exception as e:
            logger.error(f"Hazırlık earnings kontrol hatası: {e}")

        # 4. Universe scanner (teknik veri güncelle)
        try:
            logger.info("Hazırlık: Universe scanner çalıştırılıyor...")
            self._teknik_verileri_guncelle()
            self._son_teknik_guncelleme = time.time()
            logger.info(f"Universe scanner tamamlandı: {len(self.teknik_veriler)} sembol")
        except Exception as e:
            logger.error(f"Hazırlık universe scanner hatası: {e}")

        # 5. Fırsat listesi hazırla (sinyal tarama)
        try:
            logger.info("Hazırlık: Fırsat listesi hazırlanıyor...")
            self.veri_guncelle()
            self.sinyal_taramasi_yap()
            al_sinyalleri = [
                s for s in self.sinyaller
                if s.get("birlesik_sinyal", 0) >= 0.45
            ]
            logger.info(f"Hazırlık fırsat listesi: {len(al_sinyalleri)} potansiyel sinyal")
        except Exception as e:
            logger.error(f"Hazırlık fırsat listesi hatası: {e}")

        # 6. Makro takvim — gün stratejisi belirle
        try:
            makro_risk = self.makro_risk_kontrol()
            logger.info(f"Hazırlık: Gün stratejisi → {makro_risk.get('mesaj', 'Normal gün')}")
            ozet = self.makro_takvim.ozet() if hasattr(self.makro_takvim, "ozet") else ""
            if ozet:
                logger.info(ozet)
        except Exception as e:
            logger.debug(f"Hazırlık makro kontrol hatası: {e}")

        self._hazirlik_tamamlandi_gun = bugun
        logger.info("Sabah hazırlık modu tamamlandı ✓")

    # ------------------------------------------------------------------ #
    #  Ana döngü                                                            #
    # ------------------------------------------------------------------ #

    def calistir(self, max_dongu: int = 0) -> None:
        """Ana çalışma döngüsü — 7/24 mod destekli (ACIK / AFTER_HOURS / OGRENME / HAZIRLIK)"""
        self._calisıyor = True
        dongu = 0

        # Makro takvim başlangıç özeti
        try:
            makro_ozet = self.makro_takvim.ozet()
            logger.info(makro_ozet)
        except Exception:
            pass

        baslangic_mod = self.piyasa_durumu_al()
        logger.info("🚀 JOHNY 7/24 borsacı olarak başlatıldı (profesyonel modül seti aktif)")
        logger.info(f"Başlangıç modu: {baslangic_mod}")
        self.telegram.mesaj_gonder(
            "🇺🇸 <b>JOHNY 7/24 başlatıldı!</b>\n"
            f"Başlangıç modu: <b>{baslangic_mod}</b>\n"
            "Modüller: Earnings, Gap, Korelasyon, Makro Takvim, Pre-Market"
        )

        try:
            while self._calisıyor:
                dongu += 1
                try:
                    # Güncel modu belirle
                    mod = self.piyasa_durumu_al()

                    # Mod değişimi bildirimi
                    if mod != self._son_mod:
                        self._mod_degisimi_bildir(self._son_mod, mod)
                        self._son_mod = mod

                    # Moda göre döngü
                    if mod == "ACIK":
                        self._acik_dongu()
                        uyku = GUNCELLEME_ARALIGI["portfoy"]   # 10s

                    elif mod == "AFTER_HOURS":
                        self._after_hours_dongu()
                        uyku = 30   # 30s — after-hours daha az sık

                    elif mod == "OGRENME":
                        self._ogrenme_dongu()
                        uyku = 60   # 60s — gece görevler saatlik, sık kontrol gerekmez

                    else:  # HAZIRLIK
                        self._hazirlik_dongu()
                        uyku = 60   # 60s — hazırlık görevleri günde bir kez

                    # Durum logu
                    try:
                        rapor = self.durum_raporu()
                        logger.info(
                            f"[{mod}] #{dongu} | "
                            f"Portföy: ${rapor['portfoy_degeri_usd']:.2f} | "
                            f"K/Z: ${rapor['toplam_kar_zarar_usd']:+.2f} | "
                            f"Poz: {rapor['pozisyon_sayisi']}"
                        )
                    except Exception as re:
                        logger.debug(f"Durum raporu hatası: {re}")

                    if max_dongu > 0 and dongu >= max_dongu:
                        break
                    time.sleep(uyku)

                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.error(f"Ana döngü hatası: {e}")
                    time.sleep(5)
        finally:
            self._calisıyor = False
            logger.info("JOHNY durduruldu")


def main():
    """Ana giriş noktası"""
    ajan = JohnyAjani()
    if len(sys.argv) > 1 and sys.argv[1] == "--tek-seferlik":
        ajan.veri_guncelle(zorunlu=True)
        ajan.sinyal_taramasi_yap()
        rapor = ajan.durum_raporu()
        makro_risk = ajan.makro_risk_kontrol()
        print(f"\n{'='*50}")
        print(f"🇺🇸 JOHNY Durum Raporu")
        print(f"Portföy: ${rapor['portfoy_degeri_usd']:.2f}")
        print(f"K/Z: ${rapor['toplam_kar_zarar_usd']:+.2f}")
        print(f"Pozisyon: {rapor['pozisyon_sayisi']}")
        print(f"Fear & Greed: {rapor['fear_greed'].get('deger', 'N/A')}")
        print(f"Makro Durum: {makro_risk['mesaj']}")
        print(rapor.get("makro_ozet", ""))
        print(f"{'='*50}")
    elif len(sys.argv) > 1 and sys.argv[1] == "--premarket":
        # Sadece pre-market analizi çalıştır
        analizci = ajan.premarket_analizci
        analiz = analizci.analiz_calistir()
        icerik = analizci.rapor_yaz(analiz)
        print(icerik)
    else:
        ajan.calistir()


if __name__ == "__main__":
    main()
