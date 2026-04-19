"""
JOHNY — Relative Strength Scanner
Her saat çalışır.
- SPY günlük değişimine göre hisse relative strength skoru hesaplar
- rs_skoru = hisse_degisim / spy_degisim
- rs > 1.5: piyasadan güçlü → AL adayı
- rs < 0.5: zayıf → dikkat
- 5 günde rs > 1.2: GÜÇLÜ MOMENTUM sinyali
- Sonuç: rs_listesi.json
"""
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional

import yfinance as yf

from johny_config import (
    TUM_EVREN,
    RS_LISTESI_DOSYA,
    RS_GUCLU_ESIK,
    RS_ZAYIF_ESIK,
    RS_MOMENTUM_ESIK,
    RS_MOMENTUM_GUN,
)

logger = logging.getLogger("relative_strength")

BENCHMARK = "SPY"
BATCH_BOYUTU = 50


class RelativeStrengthScanner:
    """
    Her sembol için SPY'ya göre relative strength skoru hesaplar.
    5 günlük momentum takibi ile güçlü hisseleri tespit eder.
    """

    def __init__(self):
        self._rs_listesi: List[dict] = []
        self._spy_degisim: float = 0.0
        self._son_guncelleme: Optional[str] = None

    # ------------------------------------------------------------------ #
    #  Veri Çekme                                                          #
    # ------------------------------------------------------------------ #

    def _spy_gunluk_degisim(self) -> float:
        """SPY günlük % değişimini çeker."""
        try:
            ticker = yf.Ticker(BENCHMARK)
            info = ticker.fast_info
            prev = getattr(info, "previous_close", None)
            curr = getattr(info, "last_price", None)
            if prev and curr and float(prev) > 0:
                return (float(curr) - float(prev)) / float(prev) * 100
        except Exception as e:
            logger.warning(f"SPY veri hatası: {e}")
        return 0.0

    def _cok_gunluk_degisimler(self, semboller: List[str], gun: int = 6) -> Dict[str, List[float]]:
        """
        Her sembol için son N günlük kapanış değişimlerini çeker.
        Dönen: {sembol: [degisim_gün1, degisim_gün2, ...]}
        """
        sonuc: Dict[str, List[float]] = {}
        for i in range(0, len(semboller), BATCH_BOYUTU):
            batch = semboller[i:i + BATCH_BOYUTU]
            try:
                df = yf.download(
                    tickers=" ".join(batch),
                    period=f"{gun + 2}d",
                    interval="1d",
                    prepost=False,
                    group_by="ticker",
                    auto_adjust=True,
                    progress=False,
                    threads=True,
                )
                for sembol in batch:
                    try:
                        if len(batch) == 1:
                            hdf = df
                        else:
                            lvl0 = df.columns.get_level_values(0)
                            if sembol not in lvl0:
                                continue
                            hdf = df[sembol]
                        if hdf is None or hdf.empty or len(hdf) < 2:
                            continue
                        kapanislar = hdf["Close"].dropna()
                        degisimler = kapanislar.pct_change().dropna() * 100
                        sonuc[sembol] = list(degisimler.tail(gun))
                    except Exception:
                        pass
                time.sleep(0.2)
            except Exception as e:
                logger.warning(f"Batch RS veri hatası ({batch[:3]}...): {e}")
        return sonuc

    # ------------------------------------------------------------------ #
    #  Ana Hesaplama                                                        #
    # ------------------------------------------------------------------ #

    def hesapla(self, semboller: Optional[List[str]] = None) -> List[dict]:
        """
        Tüm semboller için RS skoru hesaplar.
        Returns: rs_skoru'na göre azalan sırada liste
        """
        if semboller is None:
            semboller = TUM_EVREN

        logger.info(f"Relative Strength hesabı başlıyor: {len(semboller)} sembol")

        # SPY bugünkü değişim
        self._spy_degisim = self._spy_gunluk_degisim()
        logger.info(f"SPY günlük değişim: {self._spy_degisim:+.2f}%")

        # Tüm semboller + SPY için çok günlük veriler
        tum_semboller = list(set(semboller + [BENCHMARK]))
        degisimler = self._cok_gunluk_degisimler(tum_semboller, gun=RS_MOMENTUM_GUN + 1)

        # SPY son N gün değişimleri
        spy_degisimler = degisimler.get(BENCHMARK, [])

        sonuclar: List[dict] = []
        for sembol in semboller:
            try:
                hisse_degisimler = degisimler.get(sembol, [])
                if not hisse_degisimler or not spy_degisimler:
                    continue

                # Bugünkü RS skoru
                bugun_hisse = hisse_degisimler[-1] if hisse_degisimler else 0.0
                bugun_spy = spy_degisimler[-1] if spy_degisimler else self._spy_degisim

                if abs(bugun_spy) < 0.01:  # SPY flat günlerde RS anlamlı değil
                    rs_bugun = 1.0
                else:
                    rs_bugun = bugun_hisse / bugun_spy

                # 5 günlük momentum: her gün rs > RS_MOMENTUM_ESIK mı?
                rs_5gun: List[float] = []
                for i in range(min(RS_MOMENTUM_GUN, len(hisse_degisimler), len(spy_degisimler))):
                    h = hisse_degisimler[-(i + 1)]
                    s = spy_degisimler[-(i + 1)]
                    if abs(s) > 0.01:
                        rs_5gun.append(h / s)
                    else:
                        rs_5gun.append(1.0)

                momentum_guclu = (
                    len(rs_5gun) >= RS_MOMENTUM_GUN and
                    all(r > RS_MOMENTUM_ESIK for r in rs_5gun)
                )

                # Sinyal belirleme
                sinyal = "NOTR"
                sinyal_deger = 0.0
                if momentum_guclu:
                    sinyal = "GUCLU_MOMENTUM"
                    sinyal_deger = 0.80
                elif rs_bugun > RS_GUCLU_ESIK:
                    sinyal = "GUCLU_AL_ADAYI"
                    sinyal_deger = 0.60
                elif rs_bugun < RS_ZAYIF_ESIK:
                    sinyal = "ZAYIF_DIKKAT"
                    sinyal_deger = -0.30

                sonuclar.append({
                    "sembol": sembol,
                    "rs_skoru": round(rs_bugun, 3),
                    "rs_5gun_ort": round(sum(rs_5gun) / len(rs_5gun) if rs_5gun else 0.0, 3),
                    "momentum_guclu": momentum_guclu,
                    "hisse_degisim_pct": round(bugun_hisse, 2),
                    "spy_degisim_pct": round(bugun_spy, 2),
                    "sinyal": sinyal,
                    "sinyal_deger": sinyal_deger,
                    "guncelleme": datetime.now().isoformat(),
                })
            except Exception as e:
                logger.debug(f"{sembol} RS hesaplama hatası: {e}")

        # RS skoruna göre sırala (yüksekten düşüğe)
        sonuclar.sort(key=lambda x: x["rs_skoru"], reverse=True)
        self._rs_listesi = sonuclar
        self._son_guncelleme = datetime.now().isoformat()

        guclu = sum(1 for s in sonuclar if s["sinyal"] in ("GUCLU_AL_ADAYI", "GUCLU_MOMENTUM"))
        logger.info(f"RS tarama tamamlandı: {len(sonuclar)} hisse, {guclu} güçlü sinyal")
        return sonuclar

    # ------------------------------------------------------------------ #
    #  Çıktı                                                               #
    # ------------------------------------------------------------------ #

    def kaydet(self, sonuclar: Optional[List[dict]] = None) -> None:
        """Sonuçları rs_listesi.json dosyasına kaydeder."""
        _s = sonuclar if sonuclar is not None else self._rs_listesi
        try:
            with open(RS_LISTESI_DOSYA, "w", encoding="utf-8") as f:
                json.dump({
                    "guncelleme": self._son_guncelleme or datetime.now().isoformat(),
                    "spy_degisim_pct": self._spy_degisim,
                    "hisse_sayisi": len(_s),
                    "rs_listesi": _s,
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"RS listesi kaydedildi: {RS_LISTESI_DOSYA}")
        except Exception as e:
            logger.error(f"RS listesi kaydetme hatası: {e}")

    def guclu_hisseler(self) -> List[dict]:
        """RS > 1.5 veya momentum güçlü olan hisseleri döner."""
        return [
            s for s in self._rs_listesi
            if s["sinyal"] in ("GUCLU_AL_ADAYI", "GUCLU_MOMENTUM")
        ]

    def sembol_sinyal_dict(self) -> Dict[str, float]:
        """johny_main.py entegrasyonu için {sembol: sinyal_deger} döner."""
        return {s["sembol"]: s["sinyal_deger"] for s in self._rs_listesi if s["sinyal_deger"] != 0.0}

    def ozet(self) -> str:
        """Kısa özet metin."""
        if not self._rs_listesi:
            return "📊 RS Scanner: veri yok"
        guclu = [s for s in self._rs_listesi if s["sinyal"] in ("GUCLU_AL_ADAYI", "GUCLU_MOMENTUM")]
        satirlar = [
            f"📊 Relative Strength (SPY: {self._spy_degisim:+.2f}%): "
            f"{len(self._rs_listesi)} hisse, {len(guclu)} güçlü"
        ]
        for s in guclu[:5]:
            m = "🔥" if s["momentum_guclu"] else "💪"
            satirlar.append(
                f"  {m} {s['sembol']}: RS={s['rs_skoru']:.2f} "
                f"({s['hisse_degisim_pct']:+.1f}%)"
            )
        return "\n".join(satirlar)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scanner = RelativeStrengthScanner()
    sonuclar = scanner.hesapla()
    scanner.kaydet()
    print(scanner.ozet())
