"""
JOHNY — Kazanç Takvimi İzleyici
Yahoo Finance üzerinden yaklaşan kazanç açıklamalarını izler.
Portföydeki hisseler için 3 gün öncesinden uyarı verir,
kazanç öncesi pozisyon azaltma önerir.
"""
import logging
from datetime import datetime, date, timedelta
from typing import Optional, List

import yfinance as yf

logger = logging.getLogger(__name__)


class KazancTakvimi:
    """
    Portföydeki hisseler için yaklaşan kazanç açıklamalarını takip eder.

    Kullanım:
        izleyici = KazancTakvimi(portfoy_sembolleri=["AAPL", "MSFT"])
        uyarilar = izleyici.kontrol_et()
    """

    UYARI_GUN_ESIGI = 3       # Kazançtan kaç gün önce uyar
    POZISYON_AZALT_PCT = 0.50  # Kazanç öncesi pozisyonu bu oranda azalt

    def __init__(
        self,
        portfoy_sembolleri: Optional[List[str]] = None,
        uyari_gun: int = UYARI_GUN_ESIGI,
    ):
        self.portfoy_sembolleri = portfoy_sembolleri or []
        self.uyari_gun = uyari_gun
        self._cache: dict = {}          # sembol → kazanç tarihi
        self._cache_gun: Optional[date] = None

    # ─── Ana metot ───────────────────────────────────────────────────────────

    def kontrol_et(
        self,
        portfoy_sembolleri: Optional[List[str]] = None,
    ) -> dict:
        """
        Portföydeki tüm hisseler için kazanç tarihi kontrolü yap.

        Returns
        -------
        dict
            acil_uyarilar   : 0-3 gün içinde kazanç olan hisseler
            yaklasan        : 4-14 gün içinde kazanç olan hisseler
            pozisyon_azalt  : acil_uyarılar listesi (pozisyon azaltma önerisi)
            tum_kazanclar   : tüm tarihler
        """
        semboller = portfoy_sembolleri or self.portfoy_sembolleri
        if not semboller:
            return {"acil_uyarilar": [], "yaklasan": [], "pozisyon_azalt": [], "tum_kazanclar": {}}

        bugun = date.today()

        # Günlük cache yenile
        if self._cache_gun != bugun:
            self._cache = {}
            self._cache_gun = bugun

        tum_kazanclar: dict = {}
        acil_uyarilar: list = []
        yaklasan: list = []

        for sembol in semboller:
            kazanc = self._kazanc_tarihi_al(sembol)
            if kazanc is None:
                continue
            tum_kazanclar[sembol] = str(kazanc)
            gun_kaldi = (kazanc - bugun).days
            if 0 <= gun_kaldi <= self.uyari_gun:
                bilgi = {
                    "sembol": sembol,
                    "kazanc_tarihi": str(kazanc),
                    "gun_kaldi": gun_kaldi,
                    "oneri": "POZİSYON AZALT" if gun_kaldi <= self.uyari_gun else "İZLE",
                }
                acil_uyarilar.append(bilgi)
                logger.warning(
                    f"KAZANÇ UYARISI: {sembol} — {gun_kaldi} gün kaldı ({kazanc})"
                )
            elif 0 < gun_kaldi <= 14:
                yaklasan.append({
                    "sembol": sembol,
                    "kazanc_tarihi": str(kazanc),
                    "gun_kaldi": gun_kaldi,
                    "oneri": "İZLE",
                })

        # Tarihe göre sırala
        acil_uyarilar.sort(key=lambda x: x["gun_kaldi"])
        yaklasan.sort(key=lambda x: x["gun_kaldi"])

        return {
            "acil_uyarilar": acil_uyarilar,
            "yaklasan": yaklasan,
            "pozisyon_azalt": acil_uyarilar,  # Kazanç öncesi azalt
            "tum_kazanclar": tum_kazanclar,
            "kontrol_tarihi": str(bugun),
        }

    def kazanc_var_mi(self, sembol: str, gun: int = 3) -> bool:
        """Sembolün önümüzdeki N gün içinde kazanç açıklaması var mı?"""
        tarih = self._kazanc_tarihi_al(sembol)
        if tarih is None:
            return False
        gun_kaldi = (tarih - date.today()).days
        return 0 <= gun_kaldi <= gun

    def pozisyon_azalt_faktoru(self, sembol: str) -> float:
        """
        Kazanç yakınsa azaltma faktörü döndür (0.0 = hepsini sat, 1.0 = değiştirme).
        Kazanç 0-1 gün → %50 azalt (faktör 0.5)
        Kazanç 2-3 gün → %25 azalt (faktör 0.75)
        """
        tarih = self._kazanc_tarihi_al(sembol)
        if tarih is None:
            return 1.0
        gun_kaldi = (tarih - date.today()).days
        if gun_kaldi < 0:
            return 1.0  # Geçti
        if gun_kaldi <= 1:
            return 1.0 - self.POZISYON_AZALT_PCT  # %50 tut
        if gun_kaldi <= self.uyari_gun:
            return 0.75  # %25 azalt
        return 1.0

    # ─── Yardımcı ────────────────────────────────────────────────────────────

    def _kazanc_tarihi_al(self, sembol: str) -> Optional[date]:
        """Yahoo Finance'den en yakın kazanç tarihini çek (cache'li)."""
        if sembol in self._cache:
            return self._cache[sembol]

        try:
            ticker = yf.Ticker(sembol)

            # 1. calendar tablosundan dene
            cal = getattr(ticker, "calendar", None)
            if cal is not None:
                if isinstance(cal, dict):
                    kazanc_raw = cal.get("Earnings Date")
                    if kazanc_raw:
                        if isinstance(kazanc_raw, list) and kazanc_raw:
                            kazanc_raw = kazanc_raw[0]
                        tarih = self._tarihe_donustur(kazanc_raw)
                        if tarih and tarih >= date.today():
                            self._cache[sembol] = tarih
                            return tarih
                elif hasattr(cal, "columns"):
                    # DataFrame
                    if "Earnings Date" in cal.columns:
                        vals = cal["Earnings Date"].dropna()
                        if not vals.empty:
                            tarih = self._tarihe_donustur(vals.iloc[0])
                            if tarih and tarih >= date.today():
                                self._cache[sembol] = tarih
                                return tarih

            # 2. earnings_dates tablosundan dene
            ed = getattr(ticker, "earnings_dates", None)
            if ed is not None and hasattr(ed, "index") and not ed.empty:
                bugun = date.today()
                gelecek = [
                    idx.date() for idx in ed.index
                    if hasattr(idx, "date") and idx.date() >= bugun
                ]
                if gelecek:
                    tarih = min(gelecek)
                    self._cache[sembol] = tarih
                    return tarih

            self._cache[sembol] = None
        except Exception as e:
            logger.debug(f"Kazanç tarihi alınamadı {sembol}: {e}")
            self._cache[sembol] = None

        return None

    @staticmethod
    def _tarihe_donustur(deger) -> Optional[date]:
        """Çeşitli formatlardaki tarihi date nesnesine dönüştür."""
        if deger is None:
            return None
        if isinstance(deger, date) and not isinstance(deger, datetime):
            return deger
        if isinstance(deger, datetime):
            return deger.date()
        if hasattr(deger, "date"):
            return deger.date()
        try:
            return datetime.fromisoformat(str(deger)[:10]).date()
        except Exception:
            return None

    # ─── Sembol listesi yönetimi ─────────────────────────────────────────────

    def sembol_ekle(self, sembol: str) -> None:
        if sembol not in self.portfoy_sembolleri:
            self.portfoy_sembolleri.append(sembol)
            self._cache.pop(sembol, None)

    def sembol_cikar(self, sembol: str) -> None:
        if sembol in self.portfoy_sembolleri:
            self.portfoy_sembolleri.remove(sembol)
        self._cache.pop(sembol, None)

    def sembolleri_guncelle(self, semboller: List[str]) -> None:
        """Portföy değişince sembol listesini güncelle."""
        self.portfoy_sembolleri = list(semboller)
        self._cache = {}


# ─── Singleton ───────────────────────────────────────────────────────────────

_kazanc_izleyici: Optional[KazancTakvimi] = None


def get_kazanc_izleyici(semboller: Optional[List[str]] = None) -> KazancTakvimi:
    """Global singleton döndür."""
    global _kazanc_izleyici
    if _kazanc_izleyici is None:
        _kazanc_izleyici = KazancTakvimi(portfoy_sembolleri=semboller or [])
    elif semboller is not None:
        _kazanc_izleyici.sembolleri_guncelle(semboller)
    return _kazanc_izleyici


# ─── CLI testi ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    test_semboller = (
        sys.argv[1:] if len(sys.argv) > 1
        else ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA",
              "JPM", "AMD", "COIN"]
    )

    print(f"\n=== JOHNY — Kazanç Takvimi ({date.today()}) ===")
    print(f"  Kontrol edilen hisseler: {', '.join(test_semboller)}\n")

    izleyici = KazancTakvimi(portfoy_sembolleri=test_semboller, uyari_gun=3)
    sonuc = izleyici.kontrol_et()

    if sonuc["acil_uyarilar"]:
        print("  ⚠️  ACİL UYARILAR (≤3 gün):")
        for u in sonuc["acil_uyarilar"]:
            print(f"    [{u['gun_kaldi']} gün] {u['sembol']} → {u['kazanc_tarihi']}  | {u['oneri']}")
    else:
        print("  ✓  Önümüzdeki 3 gün içinde kazanç yok.")

    if sonuc["yaklasan"]:
        print("\n  Yaklaşan Kazançlar (4-14 gün):")
        for u in sonuc["yaklasan"]:
            print(f"    [{u['gun_kaldi']} gün] {u['sembol']} → {u['kazanc_tarihi']}")

    if sonuc["tum_kazanclar"]:
        print("\n  Tüm Tarihler:")
        for s, t in sorted(sonuc["tum_kazanclar"].items()):
            print(f"    {s:<8} {t}")
    else:
        print("\n  Kazanç tarihi bulunamadı.")
