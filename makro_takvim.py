"""
JOHNY — Makro Ekonomik Takvim
FOMC, CPI, NFP, GDP gibi kritik etkinlikleri takip eder.
- Kritik veri 1 gün önce: pozisyon büyüklüğünü yarıya indir
- Kritik veri günü: sadece teknik sinyallere göre trade yap
"""
import json
import logging
import os
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Takvim dosyası
_DIZIN = os.path.dirname(os.path.abspath(__file__))
TAKVIM_DOSYA = os.path.join(_DIZIN, "makro_takvim.json")

# Etkinlik tipleri ve önem dereceleri (0-3)
ETKINLIK_ONEM: Dict[str, int] = {
    "FOMC": 3,   # En kritik: Fed faiz kararı
    "CPI":  2,   # Çok önemli: Enflasyon
    "NFP":  2,   # Çok önemli: İstihdam
    "GDP":  2,   # Önemli: Büyüme verisi
    "PCE":  2,   # Önemli: Fed'in tercih ettiği enflasyon göstergesi
    "PPI":  1,   # Orta: Üretici fiyatları
    "ISM":  1,   # Orta: İmalat endeksi
}


class MakroTakvim:
    """
    Makro ekonomik etkinlik takipçisi.
    JSON dosyasından etkinlikleri yükler, kritik günleri bildirir.
    """

    def __init__(self, takvim_dosya: Optional[str] = None):
        self.takvim_dosya = takvim_dosya or TAKVIM_DOSYA
        self._etkinlikler: List[dict] = []
        self._yukle()

    # ------------------------------------------------------------------ #
    #  JSON yükleme / kaydetme                                             #
    # ------------------------------------------------------------------ #

    def _yukle(self) -> None:
        """Takvim dosyasını yükle"""
        try:
            with open(self.takvim_dosya, "r", encoding="utf-8") as f:
                veri = json.load(f)
            self._etkinlikler = veri.get("etkinlikler", [])
            logger.info(f"Makro takvim yüklendi: {len(self._etkinlikler)} etkinlik")
        except FileNotFoundError:
            logger.warning(f"Makro takvim dosyası bulunamadı: {self.takvim_dosya}")
            self._etkinlikler = []
        except Exception as e:
            logger.error(f"Makro takvim yükleme hatası: {e}")
            self._etkinlikler = []

    def kaydet(self, etkinlikler: Optional[List[dict]] = None) -> None:
        """Etkinlikleri JSON dosyasına kaydet"""
        veri = {
            "son_guncelleme": str(date.today()),
            "aciklama": "JOHNY Makro Ekonomik Takvim — FOMC, CPI, NFP, GDP",
            "etkinlikler": etkinlikler or self._etkinlikler,
        }
        try:
            with open(self.takvim_dosya, "w", encoding="utf-8") as f:
                json.dump(veri, f, ensure_ascii=False, indent=2)
            logger.info("Makro takvim kaydedildi")
        except Exception as e:
            logger.error(f"Makro takvim kayıt hatası: {e}")

    # ------------------------------------------------------------------ #
    #  Sorgu yöntemleri                                                     #
    # ------------------------------------------------------------------ #

    def bugun_kritik_mi(self) -> Tuple[bool, List[dict]]:
        """
        Bugün kritik makro etkinlik var mı?
        Returns: (kritik_mi, etkinlik_listesi)
        """
        bugun_str = str(date.today())
        kritikler = [
            e for e in self._etkinlikler
            if e.get("tarih") == bugun_str
        ]
        return bool(kritikler), kritikler

    def yarin_kritik_mi(self) -> Tuple[bool, List[dict]]:
        """
        Yarın kritik makro etkinlik var mı? (Bugün pozisyon küçült)
        Returns: (kritik_mi, etkinlik_listesi)
        """
        yarin_str = str(date.today() + timedelta(days=1))
        kritikler = [
            e for e in self._etkinlikler
            if e.get("tarih") == yarin_str
        ]
        return bool(kritikler), kritikler

    def yaklasan_etkinlikler(self, gun_esik: int = 7) -> List[dict]:
        """
        Belirtilen gün içinde olan etkinlikleri listele.
        """
        bugun = date.today()
        sonuclar = []
        for etkinlik in self._etkinlikler:
            try:
                tarih = date.fromisoformat(etkinlik["tarih"])
                gun_kala = (tarih - bugun).days
                if 0 <= gun_kala <= gun_esik:
                    sonuclar.append({**etkinlik, "gun_kala": gun_kala})
            except (ValueError, KeyError):
                pass
        sonuclar.sort(key=lambda x: x["gun_kala"])
        return sonuclar

    def etkinlik_onem_al(self, etkinlik: dict) -> int:
        """Etkinliğin önem derecesini döner (0-3)"""
        return ETKINLIK_ONEM.get(etkinlik.get("tip", ""), 1)

    # ------------------------------------------------------------------ #
    #  Risk kararları                                                       #
    # ------------------------------------------------------------------ #

    def risk_ayari_al(self) -> dict:
        """
        Bugünün makro durumuna göre risk ayarını döner.
        {
            "durum": "NORMAL" | "KRITIK_ONCESI" | "KRITIK_GUN",
            "pozisyon_carpani": 1.0 | 0.5 | 0.5,
            "stop_loss_carpani": 1.0 | 1.0 | 0.67,  (daha dar stop)
            "mesaj": str
        }
        """
        bugun_kritik, bugun_etkinlikler = self.bugun_kritik_mi()
        yarin_kritik, yarin_etkinlikler = self.yarin_kritik_mi()

        if bugun_kritik:
            isimler = ", ".join(e.get("aciklama", e.get("tip", "?")) for e in bugun_etkinlikler)
            return {
                "durum": "KRITIK_GUN",
                "pozisyon_carpani": 0.5,         # Küçük pozisyon
                "stop_loss_carpani": 0.67,        # %3 yerine %2 stop → 0.02/0.03 ≈ 0.67
                "sadece_teknik": True,            # Makro sinyali yok, sadece teknik
                "mesaj": f"Kritik makro gün: {isimler} — küçük pozisyon, dar stop",
            }

        if yarin_kritik:
            isimler = ", ".join(e.get("aciklama", e.get("tip", "?")) for e in yarin_etkinlikler)
            return {
                "durum": "KRITIK_ONCESI",
                "pozisyon_carpani": 0.5,          # Yarıya indir
                "stop_loss_carpani": 1.0,
                "sadece_teknik": False,
                "mesaj": f"Kritik makro yarın: {isimler} — pozisyon yarıya indirildi",
            }

        return {
            "durum": "NORMAL",
            "pozisyon_carpani": 1.0,
            "stop_loss_carpani": 1.0,
            "sadece_teknik": False,
            "mesaj": "Normal gün",
        }

    # ------------------------------------------------------------------ #
    #  Özet / Raporlama                                                     #
    # ------------------------------------------------------------------ #

    def ozet(self) -> str:
        """Önümüzdeki 7 günlük etkinliklerin özeti"""
        etkinlikler = self.yaklasan_etkinlikler(gun_esik=7)
        if not etkinlikler:
            return "Önümüzdeki 7 günde kritik makro etkinlik yok"

        satirlar = ["Yaklaşan Makro Etkinlikler:"]
        for e in etkinlikler:
            gun_kala = e.get("gun_kala", "?")
            tip = e.get("tip", "")
            aciklama = e.get("aciklama", "")
            tarih = e.get("tarih", "")
            onem = "!!!" if ETKINLIK_ONEM.get(tip, 0) >= 2 else "!"
            satirlar.append(f"  {onem} {tarih} ({gun_kala} gün) — {tip}: {aciklama}")

        return "\n".join(satirlar)

    def etkinlik_ekle(self, tarih: str, tip: str, aciklama: str) -> None:
        """Yeni etkinlik ekle ve kaydet"""
        self._etkinlikler.append({
            "tarih": tarih,
            "tip": tip,
            "aciklama": aciklama,
        })
        self._etkinlikler.sort(key=lambda x: x.get("tarih", ""))
        self.kaydet()
