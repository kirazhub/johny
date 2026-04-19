"""
JOHNY — Pre-Market Movers
16:00–16:25 İstanbul arası çalışır (ABD açılışından ~30 dk önce).
- yfinance prepost=True ile pre-market fiyat çeker
- En çok yükselen/düşen 10 hisse listeler
- Kazanç açıklaması yapan hisseleri özel işaretler
- Haber + pre-market hareket kombinasyonu = güçlendirilmiş sinyal
- Sonuç: premarket_raporu.txt (mevcut dosyaya ek bölüm)
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

import yfinance as yf

from johny_config import TUM_EVREN, PREMARKET_RAPOR_DOSYA

logger = logging.getLogger("premarket_movers")

CIKTI_DOSYA = PREMARKET_RAPOR_DOSYA  # premarket_raporu.txt
MOVERS_JSON = "premarket_movers.json"
TOP_N = 10  # Kaç tane hisse raporlanacak
BATCH_BOYUTU = 30


class PremarketMovers:
    """
    Pre-market en çok hareket eden hisseleri tespit eder.
    Kazanç açıklaması + pre-market hareket = güçlendirilmiş sinyal.
    """

    def __init__(self):
        self._movers: List[dict] = []
        self._son_guncelleme: Optional[str] = None

    # ------------------------------------------------------------------ #
    #  Veri Çekme                                                          #
    # ------------------------------------------------------------------ #

    def _premarket_degisimler(self, semboller: List[str]) -> List[dict]:
        """Her sembol için pre-market % değişimi hesaplar."""
        sonuclar: List[dict] = []
        for i in range(0, len(semboller), BATCH_BOYUTU):
            batch = semboller[i:i + BATCH_BOYUTU]
            for sembol in batch:
                try:
                    ticker = yf.Ticker(sembol)
                    info = ticker.fast_info
                    pm_fiyat = getattr(info, "pre_market_price", None)
                    son_kapanis = getattr(info, "previous_close", None) or getattr(info, "regular_market_previous_close", None)

                    if pm_fiyat and son_kapanis and float(son_kapanis) > 0:
                        pm_fiyat = float(pm_fiyat)
                        son_kapanis = float(son_kapanis)
                        degisim_pct = (pm_fiyat - son_kapanis) / son_kapanis * 100
                        sonuclar.append({
                            "sembol": sembol,
                            "pm_fiyat": round(pm_fiyat, 2),
                            "dun_kapanis": round(son_kapanis, 2),
                            "degisim_pct": round(degisim_pct, 2),
                            "kazanc_var": False,
                            "guclendirilmis": False,
                        })
                except Exception as e:
                    logger.debug(f"{sembol} pre-market veri hatası: {e}")
        return sonuclar

    def _kazanc_kontrol(self, semboller: List[str]) -> Dict[str, bool]:
        """Bugün kazanç açıklaması yapan hisseleri tespit eder."""
        kazanc_var: Dict[str, bool] = {}
        bugun = datetime.now().strftime("%Y-%m-%d")
        for sembol in semboller:
            try:
                ticker = yf.Ticker(sembol)
                cal = ticker.calendar
                if cal is not None and not cal.empty:
                    if "Earnings Date" in cal.index:
                        kazanc_tarihi = str(cal.loc["Earnings Date"].iloc[0])[:10]
                        kazanc_var[sembol] = kazanc_tarihi == bugun
            except Exception:
                pass
        return kazanc_var

    # ------------------------------------------------------------------ #
    #  Ana Tarama                                                          #
    # ------------------------------------------------------------------ #

    def tara(self, semboller: Optional[List[str]] = None) -> List[dict]:
        """
        Pre-market en çok hareket eden hisseleri bulur.
        Returns: degisim_pct'ye göre sıralı (yükselenler önce)
        """
        if semboller is None:
            semboller = TUM_EVREN

        logger.info(f"Pre-market movers taraması: {len(semboller)} sembol")

        # Pre-market değişimler
        degisimler = self._premarket_degisimler(semboller)
        logger.info(f"Pre-market veri alındı: {len(degisimler)} hisse")

        # Yalnızca anlamlı hareket edenleri filtrele (>%1 veya <%1)
        anlamli = [d for d in degisimler if abs(d["degisim_pct"]) >= 1.0]

        # Kazanç açıklaması kontrolü (en çok hareket edenler için)
        hareketli_semboller = [d["sembol"] for d in sorted(
            anlamli, key=lambda x: abs(x["degisim_pct"]), reverse=True
        )[:50]]
        kazanc_dict = self._kazanc_kontrol(hareketli_semboller)

        for d in anlamli:
            sembol = d["sembol"]
            d["kazanc_var"] = kazanc_dict.get(sembol, False)
            # Kazanç + hareket kombinasyonu = güçlendirilmiş sinyal
            if d["kazanc_var"] and abs(d["degisim_pct"]) >= 2.0:
                d["guclendirilmis"] = True

        # En çok yükselenler ve düşenler
        yukselenler = sorted(
            [d for d in anlamli if d["degisim_pct"] > 0],
            key=lambda x: x["degisim_pct"],
            reverse=True,
        )[:TOP_N]

        dusenler = sorted(
            [d for d in anlamli if d["degisim_pct"] < 0],
            key=lambda x: x["degisim_pct"],
        )[:TOP_N]

        self._movers = yukselenler + dusenler
        self._son_guncelleme = datetime.now().isoformat()

        logger.info(
            f"Pre-market movers tamamlandı: "
            f"{len(yukselenler)} yükselen, {len(dusenler)} düşen"
        )
        return self._movers

    # ------------------------------------------------------------------ #
    #  Çıktı                                                               #
    # ------------------------------------------------------------------ #

    def rapor_yaz(self, movers: Optional[List[dict]] = None) -> str:
        """Raporu premarket_raporu.txt dosyasına ekler."""
        _m = movers if movers is not None else self._movers
        yukselenler = [m for m in _m if m["degisim_pct"] > 0]
        dusenler = [m for m in _m if m["degisim_pct"] < 0]

        satirlar = [
            f"\n{'='*60}",
            f"PRE-MARKET MOVERS — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"{'='*60}",
            "",
            f"🟢 EN ÇOK YÜKSELENLER (Top {TOP_N})",
            "-" * 40,
        ]
        for m in yukselenler:
            kazanc_etiketi = " 💰KAZANÇ" if m["kazanc_var"] else ""
            guclu_etiketi = " ⚡GÜÇLÜ" if m["guclendirilmis"] else ""
            satirlar.append(
                f"  {m['sembol']:8s} {m['degisim_pct']:+.2f}%  "
                f"(PM: ${m['pm_fiyat']:.2f}, Dün: ${m['dun_kapanis']:.2f})"
                f"{kazanc_etiketi}{guclu_etiketi}"
            )

        satirlar += ["", f"🔴 EN ÇOK DÜŞENLER (Top {TOP_N})", "-" * 40]
        for m in dusenler:
            kazanc_etiketi = " 💰KAZANÇ" if m["kazanc_var"] else ""
            satirlar.append(
                f"  {m['sembol']:8s} {m['degisim_pct']:+.2f}%  "
                f"(PM: ${m['pm_fiyat']:.2f}, Dün: ${m['dun_kapanis']:.2f})"
                f"{kazanc_etiketi}"
            )
        satirlar.append("")
        icerik = "\n".join(satirlar)

        try:
            with open(CIKTI_DOSYA, "a", encoding="utf-8") as f:
                f.write(icerik)
            logger.info(f"Pre-market movers raporu eklendi: {CIKTI_DOSYA}")
        except Exception as e:
            logger.error(f"Rapor yazma hatası: {e}")

        # JSON kayıt
        try:
            with open(MOVERS_JSON, "w", encoding="utf-8") as f:
                json.dump({
                    "guncelleme": self._son_guncelleme,
                    "yukselenler": yukselenler,
                    "dusenler": dusenler,
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Movers JSON kayıt hatası: {e}")

        return icerik

    def guclendirilmis_sinyaller(self) -> List[dict]:
        """Kazanç + pre-market hareket olan güçlendirilmiş sinyalleri döner."""
        return [m for m in self._movers if m.get("guclendirilmis")]

    def yukselenler_listesi(self) -> List[str]:
        """Yükselen sembol listesini döner."""
        return [m["sembol"] for m in self._movers if m["degisim_pct"] > 0]

    def ozet(self) -> str:
        """Kısa özet metin."""
        yukselenler = [m for m in self._movers if m["degisim_pct"] > 0]
        dusenler = [m for m in self._movers if m["degisim_pct"] < 0]
        if not self._movers:
            return "Pre-market veri yok"
        satirlar = ["📈 Pre-Market Movers:"]
        for m in yukselenler[:5]:
            g = "⚡" if m.get("guclendirilmis") else ""
            satirlar.append(f"  🟢{g} {m['sembol']}: {m['degisim_pct']:+.2f}%")
        for m in dusenler[:5]:
            satirlar.append(f"  🔴 {m['sembol']}: {m['degisim_pct']:+.2f}%")
        return "\n".join(satirlar)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    movers = PremarketMovers()
    sonuclar = movers.tara()
    icerik = movers.rapor_yaz()
    print(movers.ozet())
