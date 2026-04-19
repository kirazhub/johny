"""
JOHNY — Gap & Go Scanner
Her gün 16:25 İstanbul'da (~09:25 EST) çalıştırılır.
700+ hissenin dün kapanış vs. bugün pre-market fiyatını karşılaştırır.
Gap up >%3 VE hacim 3x: GÜÇLÜ AL
Gap up >%5: ÇOK GÜÇLÜ AL
Gap down <%3 VE haber varsa: SHORT fikri
Sonuç: gap_go_listesi.json
"""
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional

import yfinance as yf

from johny_config import (
    TUM_EVREN,
    GAP_GO_LISTESI_DOSYA,
    GAP_GUCLU_PCT,
    GAP_COK_GUCLU_PCT,
    GAP_HACIM_KATSAYI,
    GAP_SHORT_PCT,
)

logger = logging.getLogger("gap_go_scanner")

BATCH_BOYUTU = 50  # Tek seferde kaç sembol indirilir


class GapGoScanner:
    """
    Büyük evrende (TUM_EVREN) pre-market gap fırsatlarını tarar.
    gap_pct = (premarket_fiyat - dun_kapanis) / dun_kapanis * 100
    """

    def __init__(self):
        self._sonuclar: List[dict] = []
        self._son_tarama: Optional[str] = None

    # ------------------------------------------------------------------ #
    #  Veri Çekme                                                          #
    # ------------------------------------------------------------------ #

    def _batch_kapanislar(self, semboller: List[str]) -> Dict[str, dict]:
        """Batch halinde son 5 günlük kapanış + hacim verisi çeker."""
        veri: Dict[str, dict] = {}
        for i in range(0, len(semboller), BATCH_BOYUTU):
            batch = semboller[i:i + BATCH_BOYUTU]
            try:
                df = yf.download(
                    tickers=" ".join(batch),
                    period="5d",
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
                        hacimler = hdf["Volume"].dropna()
                        if len(kapanislar) < 2:
                            continue
                        veri[sembol] = {
                            "dun_kapanis": float(kapanislar.iloc[-1]),
                            "hacim_son": float(hacimler.iloc[-1]),
                            "hacim_ort": float(hacimler.mean()),
                        }
                    except Exception:
                        pass
                time.sleep(0.3)
            except Exception as e:
                logger.warning(f"Batch veri hatası ({batch[:3]}...): {e}")
        return veri

    def _premarket_fiyatlar(self, semboller: List[str]) -> Dict[str, float]:
        """Pre-market anlık fiyatları çeker (yfinance fast_info)."""
        sonuc: Dict[str, float] = {}
        for sembol in semboller:
            try:
                info = yf.Ticker(sembol).fast_info
                pm = getattr(info, "pre_market_price", None)
                if pm is None or float(pm) <= 0:
                    pm = getattr(info, "last_price", None)
                if pm and float(pm) > 0:
                    sonuc[sembol] = float(pm)
            except Exception:
                pass
        return sonuc

    # ------------------------------------------------------------------ #
    #  Ana Tarama                                                           #
    # ------------------------------------------------------------------ #

    def tara(self, semboller: Optional[List[str]] = None) -> List[dict]:
        """
        Verilen sembol listesini tarar; gap sinyallerini döner.
        Returns: sinyal_deger mutlak değerine göre sıralı liste
        """
        if semboller is None:
            semboller = TUM_EVREN

        logger.info(f"Gap & Go taraması başlıyor: {len(semboller)} sembol")
        kapanislar = self._batch_kapanislar(semboller)
        logger.info(f"Kapanış verisi: {len(kapanislar)} hisse")

        pm_fiyatlar = self._premarket_fiyatlar(list(kapanislar.keys()))
        logger.info(f"Pre-market fiyat: {len(pm_fiyatlar)} hisse")

        sonuclar: List[dict] = []
        for sembol, d in kapanislar.items():
            try:
                kapanis = d["dun_kapanis"]
                if kapanis <= 0:
                    continue
                pm = pm_fiyatlar.get(sembol, kapanis)
                gap_pct = (pm - kapanis) / kapanis * 100
                hacim_oran = d["hacim_son"] / d["hacim_ort"] if d["hacim_ort"] > 0 else 0.0

                sinyal: Optional[str] = None
                sinyal_deger = 0.0

                if gap_pct >= GAP_COK_GUCLU_PCT:
                    sinyal = "COK_GUCLU_AL"
                    sinyal_deger = 0.90
                elif gap_pct >= GAP_GUCLU_PCT and hacim_oran >= GAP_HACIM_KATSAYI:
                    sinyal = "GUCLU_AL"
                    sinyal_deger = 0.75
                elif gap_pct >= GAP_GUCLU_PCT:
                    sinyal = "AL_ADAYI"
                    sinyal_deger = 0.55
                elif gap_pct <= GAP_SHORT_PCT:
                    sinyal = "SHORT_FIKIR"
                    sinyal_deger = -0.65

                if sinyal is None:
                    continue

                sonuclar.append({
                    "sembol": sembol,
                    "gap_pct": round(gap_pct, 2),
                    "hacim_orani": round(hacim_oran, 2),
                    "dun_kapanis": round(kapanis, 2),
                    "premarket_fiyat": round(pm, 2),
                    "sinyal": sinyal,
                    "sinyal_deger": sinyal_deger,
                    "tarama_zamani": datetime.now().isoformat(),
                })
            except Exception as e:
                logger.debug(f"{sembol} gap hesaplama hatası: {e}")

        sonuclar.sort(key=lambda x: abs(x["sinyal_deger"]), reverse=True)
        self._sonuclar = sonuclar
        self._son_tarama = datetime.now().isoformat()
        logger.info(f"Gap & Go tamamlandı: {len(sonuclar)} sinyal bulundu")
        return sonuclar

    # ------------------------------------------------------------------ #
    #  Çıktı                                                               #
    # ------------------------------------------------------------------ #

    def kaydet(self, sonuclar: Optional[List[dict]] = None) -> None:
        """Sonuçları gap_go_listesi.json dosyasına kaydeder."""
        _s = sonuclar if sonuclar is not None else self._sonuclar
        try:
            with open(GAP_GO_LISTESI_DOSYA, "w", encoding="utf-8") as f:
                json.dump({
                    "tarama_zamani": self._son_tarama or datetime.now().isoformat(),
                    "sonuc_sayisi": len(_s),
                    "gaplar": _s,
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"Gap listesi kaydedildi: {GAP_GO_LISTESI_DOSYA} ({len(_s)} kayıt)")
        except Exception as e:
            logger.error(f"Gap listesi kaydetme hatası: {e}")

    def en_iyi_5(self) -> List[dict]:
        """En iyi 5 AL sinyalini döner."""
        al = [s for s in self._sonuclar if s["sinyal_deger"] > 0]
        return al[:5]

    def sembol_listesi(self) -> List[str]:
        """Gap sinyali olan sembolleri döner (johny_main.py entegrasyonu için)."""
        return [s["sembol"] for s in self._sonuclar]

    def ozet(self) -> str:
        """Özet metin üretir."""
        if not self._sonuclar:
            return "📊 Gap & Go: fırsat bulunamadı"
        etiket = {
            "COK_GUCLU_AL": "🚀", "GUCLU_AL": "💚",
            "AL_ADAYI": "🟢", "SHORT_FIKIR": "🔴",
        }
        satirlar = [f"📊 Gap & Go Tarama: {len(self._sonuclar)} fırsat"]
        for s in self._sonuclar[:10]:
            e = etiket.get(s["sinyal"], "")
            satirlar.append(
                f"{e} {s['sembol']}: {s['gap_pct']:+.1f}% | "
                f"Hacim {s['hacim_orani']:.1f}x | {s['sinyal']}"
            )
        return "\n".join(satirlar)


# ------------------------------------------------------------------ #
#  Bağımsız çalıştırma                                                 #
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scanner = GapGoScanner()
    sonuclar = scanner.tara()
    scanner.kaydet()
    print(scanner.ozet())
    print("\nEn İyi 5 Fırsat:")
    for s in scanner.en_iyi_5():
        print(f"  {s['sembol']}: Gap {s['gap_pct']:+.1f}% | {s['sinyal']}")
