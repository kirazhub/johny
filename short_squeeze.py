"""
JOHNY — Short Squeeze Tracker
Her gün sabah güncellenir.
- yfinance shortPercentOfFloat çeker
- short_float > %20 olan hisseleri listeler
- Son 5 günde hacim artışı > %50 olanları filtreler → potansiyel short squeeze
- Sonuç: short_squeeze_listesi.json
"""
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional

import yfinance as yf

from johny_config import TUM_EVREN, SHORT_SQUEEZE_DOSYA, SHORT_FLOAT_ESIK, SHORT_HACIM_ARTIS

logger = logging.getLogger("short_squeeze")

BATCH_BOYUTU = 20  # Tek seferde yf.Ticker.info çeken sembol sayısı


class ShortSqueezeTracker:
    """
    Yüksek short float + hacim artışı olan hisseleri tespit eder.
    Short squeeze potansiyeli: yüksek short float + güçlü hacim artışı.
    """

    def __init__(self):
        self._squeeze_listesi: List[dict] = []
        self._son_guncelleme: Optional[str] = None

    # ------------------------------------------------------------------ #
    #  Veri Çekme                                                          #
    # ------------------------------------------------------------------ #

    def _short_verisi_cek(self, semboller: List[str]) -> Dict[str, float]:
        """
        yfinance.info üzerinden shortPercentOfFloat çeker.
        Returns: {sembol: short_float_pct}  (0.0 - 1.0 arası)
        """
        sonuc: Dict[str, float] = {}
        for sembol in semboller:
            try:
                info = yf.Ticker(sembol).info
                spof = info.get("shortPercentOfFloat") or info.get("shortRatio")
                if spof is not None:
                    # shortPercentOfFloat zaten 0-1 arasında gelir (örn: 0.25 = %25)
                    val = float(spof)
                    if val > 1.0:  # Bazı kaynaklar 0-100 verir
                        val = val / 100.0
                    sonuc[sembol] = val
            except Exception:
                pass
        return sonuc

    def _hacim_artisi(self, semboller: List[str]) -> Dict[str, float]:
        """
        Son 5 gün hacim ortalamasını önceki 20 gün ortallamasıyla karşılaştırır.
        Returns: {sembol: hacim_artisi_pct}  (örn: 0.5 = %50 artış)
        """
        sonuc: Dict[str, float] = {}
        for i in range(0, len(semboller), 50):
            batch = semboller[i:i + 50]
            try:
                df = yf.download(
                    tickers=" ".join(batch),
                    period="30d",
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
                        if hdf is None or hdf.empty or len(hdf) < 10:
                            continue
                        hacimler = hdf["Volume"].dropna()
                        son_5 = hacimler.tail(5).mean()
                        onceki_20 = hacimler.head(20).mean()
                        if onceki_20 > 0:
                            sonuc[sembol] = (son_5 - onceki_20) / onceki_20  # 0.5 = %50
                    except Exception:
                        pass
                time.sleep(0.2)
            except Exception as e:
                logger.warning(f"Hacim artış hatası ({batch[:3]}...): {e}")
        return sonuc

    # ------------------------------------------------------------------ #
    #  Ana Tarama                                                          #
    # ------------------------------------------------------------------ #

    def tara(self, semboller: Optional[List[str]] = None) -> List[dict]:
        """
        Yüksek short float olan hisseleri tarar.
        Returns: squeeze_skoru'na göre sıralı liste
        """
        if semboller is None:
            semboller = TUM_EVREN

        logger.info(f"Short squeeze taraması başlıyor: {len(semboller)} sembol")

        # Aşama 1: Short float verisini çek
        short_verileri = self._short_verisi_cek(semboller)
        logger.info(f"Short float verisi alındı: {len(short_verileri)} hisse")

        # Aşama 2: Yüksek short float filtresi (>%20)
        yuksek_short = {
            sembol: pct
            for sembol, pct in short_verileri.items()
            if pct >= SHORT_FLOAT_ESIK
        }
        logger.info(f"Yüksek short float (>%{SHORT_FLOAT_ESIK*100:.0f}): {len(yuksek_short)} hisse")

        if not yuksek_short:
            self._squeeze_listesi = []
            return []

        # Aşama 3: Hacim artışını kontrol et
        hacim_artislari = self._hacim_artisi(list(yuksek_short.keys()))

        sonuclar: List[dict] = []
        for sembol, short_pct in yuksek_short.items():
            hacim_artis = hacim_artislari.get(sembol, 0.0)
            potansiyel_squeeze = hacim_artis >= SHORT_HACIM_ARTIS

            # Skor hesapla (0-1 arası)
            squeeze_skoru = min(1.0, (short_pct / 0.5) * 0.6 + min(1.0, hacim_artis) * 0.4)

            sonuclar.append({
                "sembol": sembol,
                "short_float_pct": round(short_pct * 100, 1),
                "hacim_artisi_pct": round(hacim_artis * 100, 1),
                "potansiyel_squeeze": potansiyel_squeeze,
                "squeeze_skoru": round(squeeze_skoru, 3),
                "sinyal_deger": round(squeeze_skoru * 0.7, 3) if potansiyel_squeeze else 0.0,
                "guncelleme": datetime.now().isoformat(),
            })

        # Skor'a göre sırala
        sonuclar.sort(key=lambda x: x["squeeze_skoru"], reverse=True)
        self._squeeze_listesi = sonuclar
        self._son_guncelleme = datetime.now().isoformat()

        squeeze_adaylari = sum(1 for s in sonuclar if s["potansiyel_squeeze"])
        logger.info(
            f"Short squeeze tarama tamamlandı: "
            f"{len(sonuclar)} yüksek short, {squeeze_adaylari} potansiyel squeeze"
        )
        return sonuclar

    # ------------------------------------------------------------------ #
    #  Çıktı                                                               #
    # ------------------------------------------------------------------ #

    def kaydet(self, sonuclar: Optional[List[dict]] = None) -> None:
        """Sonuçları short_squeeze_listesi.json dosyasına kaydeder."""
        _s = sonuclar if sonuclar is not None else self._squeeze_listesi
        try:
            with open(SHORT_SQUEEZE_DOSYA, "w", encoding="utf-8") as f:
                json.dump({
                    "guncelleme": self._son_guncelleme or datetime.now().isoformat(),
                    "toplam_hisse": len(_s),
                    "squeeze_adaylari": sum(1 for s in _s if s["potansiyel_squeeze"]),
                    "liste": _s,
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"Short squeeze listesi kaydedildi: {SHORT_SQUEEZE_DOSYA}")
        except Exception as e:
            logger.error(f"Short squeeze kaydetme hatası: {e}")

    def potansiyel_squeeze_listesi(self) -> List[dict]:
        """Potansiyel short squeeze adaylarını döner."""
        return [s for s in self._squeeze_listesi if s["potansiyel_squeeze"]]

    def sembol_sinyal_dict(self) -> Dict[str, float]:
        """johny_main.py entegrasyonu için {sembol: sinyal_deger} döner."""
        return {
            s["sembol"]: s["sinyal_deger"]
            for s in self._squeeze_listesi
            if s["sinyal_deger"] > 0
        }

    def ozet(self) -> str:
        """Kısa özet metin."""
        if not self._squeeze_listesi:
            return "📊 Short Squeeze: veri yok"
        adaylar = self.potansiyel_squeeze_listesi()
        satirlar = [
            f"📊 Short Squeeze Tracker: "
            f"{len(self._squeeze_listesi)} yüksek short, {len(adaylar)} aday"
        ]
        for s in adaylar[:5]:
            satirlar.append(
                f"  🎯 {s['sembol']}: Short %{s['short_float_pct']:.1f} | "
                f"Hacim +%{s['hacim_artisi_pct']:.0f}"
            )
        return "\n".join(satirlar)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    tracker = ShortSqueezeTracker()
    sonuclar = tracker.tara()
    tracker.kaydet()
    print(tracker.ozet())
