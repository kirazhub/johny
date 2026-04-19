"""
JOHNY — Portföy Yöneticisi
USD tabanlı pozisyon takibi
"""
import logging
from datetime import datetime, date
from typing import Dict, List, Optional

from johny_config import PORTFOY_PARAMETRELERI, KOMISYON
from johny_database import JohnyDatabase
from risk.position_sizer import PozisyonBoyutlandirici
from risk.limits import RiskLimitleri

logger = logging.getLogger(__name__)


class Pozisyon:
    """Tek pozisyon"""

    def __init__(
        self,
        sembol: str,
        lot: int,
        giris_fiyat: float,
        giris_tarih: str,
        strateji: str = "",
        stop_fiyat: Optional[float] = None,
        hedef_fiyat: Optional[float] = None,
    ):
        self.sembol = sembol
        self.lot = lot
        self.giris_fiyat = giris_fiyat
        self.giris_tarih = giris_tarih
        self.strateji = strateji
        self.stop_fiyat = stop_fiyat or giris_fiyat * (1 - PORTFOY_PARAMETRELERI["stop_loss_yuzdesi"])
        self.hedef_fiyat = hedef_fiyat or giris_fiyat * (1 + PORTFOY_PARAMETRELERI["take_profit_yuzdesi"])
        self.trailing_max = giris_fiyat
        self.giris_komisyon = max(lot * KOMISYON["hisse_basi"], KOMISYON["minimum"])
        self.giris_maliyet = lot * giris_fiyat + self.giris_komisyon
        self.mevcut_fiyat = giris_fiyat

    def guncelle(self, fiyat: float) -> None:
        self.mevcut_fiyat = fiyat
        if fiyat > self.trailing_max:
            self.trailing_max = fiyat

    @property
    def deger_usd(self) -> float:
        return self.lot * self.mevcut_fiyat

    @property
    def kar_zarar_usd(self) -> float:
        cikis_komisyon = max(self.lot * KOMISYON["hisse_basi"], KOMISYON["minimum"])
        return (self.mevcut_fiyat - self.giris_fiyat) * self.lot - self.giris_komisyon - cikis_komisyon

    @property
    def kar_zarar_pct(self) -> float:
        if self.giris_maliyet > 0:
            return (self.kar_zarar_usd / self.giris_maliyet) * 100
        return 0.0

    def to_dict(self) -> dict:
        return {
            "sembol": self.sembol,
            "lot": self.lot,
            "giris_fiyat": round(self.giris_fiyat, 2),
            "mevcut_fiyat": round(self.mevcut_fiyat, 2),
            "giris_tarih": self.giris_tarih,
            "strateji": self.strateji,
            "stop_fiyat": round(self.stop_fiyat, 2),
            "hedef_fiyat": round(self.hedef_fiyat, 2),
            "trailing_max": round(self.trailing_max, 2),
            "deger_usd": round(self.deger_usd, 2),
            "kar_zarar_usd": round(self.kar_zarar_usd, 2),
            "kar_zarar_pct": round(self.kar_zarar_pct, 2),
            "giris_maliyet": round(self.giris_maliyet, 2),
        }


class JohnyPortfoy:
    """Ana portföy yöneticisi"""

    def __init__(self, db: Optional[JohnyDatabase] = None):
        self.params = PORTFOY_PARAMETRELERI
        self.baslangic_sermayesi = self.params["baslangic_sermayesi"]
        self.nakit = self.baslangic_sermayesi
        self.pozisyonlar: Dict[str, Pozisyon] = {}
        self.islem_gecmisi: List[dict] = []
        self.db = db or JohnyDatabase()
        self.boyutlandirici = PozisyonBoyutlandirici()
        self.risk_limitleri = RiskLimitleri()
        self.bugun_kar_zarar = 0.0
        self._gun_baslangic_deger = self.baslangic_sermayesi
        self._bugun_tarihi = str(date.today())

    def portfoy_degeri(self) -> float:
        """Toplam portföy değeri (USD)"""
        return self.nakit + sum(p.deger_usd for p in self.pozisyonlar.values())

    def portfoy_kar_zarar(self) -> float:
        """Toplam kar/zarar (USD)"""
        return self.portfoy_degeri() - self.baslangic_sermayesi

    def portfoy_kar_zarar_pct(self) -> float:
        """Toplam kar/zarar (%)"""
        if self.baslangic_sermayesi > 0:
            return (self.portfoy_kar_zarar() / self.baslangic_sermayesi) * 100
        return 0.0

    def fiyatları_guncelle(self, fiyat_verisi: Dict[str, dict]) -> None:
        """Açık pozisyon fiyatlarını güncelle"""
        gun_str = str(date.today())
        if gun_str != self._bugun_tarihi:
            self._gun_baslangic_deger = self.portfoy_degeri()
            self._bugun_tarihi = gun_str
            self.bugun_kar_zarar = 0.0

        onceki_deger = self.portfoy_degeri()
        for sembol, poz in self.pozisyonlar.items():
            if sembol in fiyat_verisi:
                yeni_fiyat = fiyat_verisi[sembol].get("fiyat", poz.mevcut_fiyat)
                poz.guncelle(yeni_fiyat)

        self.bugun_kar_zarar = self.portfoy_degeri() - self._gun_baslangic_deger

    def al(
        self,
        sembol: str,
        fiyat: float,
        sinyal_guven: float = 0.5,
        strateji: str = "",
        atr: Optional[float] = None,
    ) -> dict:
        """Hisse al"""
        try:
            # Risk kontrolleri
            limit_kontrol = self.risk_limitleri.gunluk_kayip_kontrolu(
                self.portfoy_degeri(),
                self.baslangic_sermayesi,
                self.bugun_kar_zarar,
            )
            if not limit_kontrol["islem_yapilabilir"]:
                return {"basarili": False, "hata": f"Risk limiti: {limit_kontrol}"}

            if sembol in self.pozisyonlar:
                return {"basarili": False, "hata": f"{sembol} zaten portföyde"}

            # Pozisyon boyutu
            boyut = self.boyutlandirici.pozisyon_hesapla(
                sembol, fiyat, self.portfoy_degeri(),
                atr=atr,
                sinyal_guven=sinyal_guven,
                mevcut_pozisyon_sayisi=len(self.pozisyonlar),
            )
            if boyut.get("red"):
                return {"basarili": False, "hata": boyut["red"]}

            lot = boyut["lot"]
            maliyet = boyut["toplam_maliyet"]

            if maliyet > self.nakit:
                return {"basarili": False, "hata": f"Yetersiz nakit: ${self.nakit:.2f} < ${maliyet:.2f}"}

            # Alım gerçekleştir
            self.nakit -= maliyet
            poz = Pozisyon(
                sembol=sembol,
                lot=lot,
                giris_fiyat=fiyat,
                giris_tarih=datetime.now().isoformat(),
                strateji=strateji,
                stop_fiyat=boyut["stop_fiyat"],
                hedef_fiyat=boyut["hedef_fiyat"],
            )
            self.pozisyonlar[sembol] = poz

            islem = {
                "tarih": datetime.now().isoformat(),
                "sembol": sembol,
                "islem": "AL",
                "lot": lot,
                "fiyat": fiyat,
                "komisyon": boyut["komisyon"],
                "maliyet": maliyet,
                "strateji": strateji,
                "portfoy_degeri": self.portfoy_degeri(),
            }
            self.islem_gecmisi.append(islem)
            self.db.islem_kaydet(
                sembol=sembol,
                islem_tipi="AL",
                lot=lot,
                fiyat=fiyat,
                komisyon=boyut["komisyon"],
                neden=strateji,
                strateji=strateji,
            )
            logger.info(f"AL: {sembol} x{lot} @ ${fiyat:.2f}")
            return {"basarili": True, "islem": islem, **boyut}
        except Exception as e:
            logger.error(f"Alım hatası {sembol}: {e}")
            return {"basarili": False, "hata": str(e)}

    def sat(
        self,
        sembol: str,
        fiyat: float,
        neden: str = "Manuel",
    ) -> dict:
        """Hisse sat"""
        try:
            if sembol not in self.pozisyonlar:
                return {"basarili": False, "hata": f"{sembol} portföyde değil"}

            poz = self.pozisyonlar.pop(sembol)
            lot = poz.lot
            komisyon = max(lot * KOMISYON["hisse_basi"], KOMISYON["minimum"])
            gelir = lot * fiyat - komisyon
            kar_zarar = gelir - poz.giris_maliyet
            self.nakit += gelir

            islem = {
                "tarih": datetime.now().isoformat(),
                "sembol": sembol,
                "islem": "SAT",
                "lot": lot,
                "fiyat": fiyat,
                "giris_fiyat": poz.giris_fiyat,
                "komisyon": komisyon,
                "gelir": gelir,
                "kar_zarar": kar_zarar,
                "kar_zarar_pct": (kar_zarar / poz.giris_maliyet) * 100 if poz.giris_maliyet > 0 else 0,
                "neden": neden,
                "portfoy_degeri": self.portfoy_degeri(),
            }
            self.islem_gecmisi.append(islem)
            self.db.islem_kaydet(
                sembol=sembol,
                islem_tipi="SAT",
                lot=lot,
                fiyat=fiyat,
                komisyon=komisyon,
                kar_zarar=kar_zarar,
                neden=neden,
            )
            logger.info(f"SAT: {sembol} x{lot} @ ${fiyat:.2f} | K/Z: ${kar_zarar:.2f}")
            return {"basarili": True, "islem": islem}
        except Exception as e:
            logger.error(f"Satış hatası {sembol}: {e}")
            return {"basarili": False, "hata": str(e)}

    def stop_loss_kontrol(self, fiyat_verisi: Dict[str, dict]) -> List[dict]:
        """Tüm pozisyonlar için stop-loss kontrolü"""
        tetiklenenler: List[dict] = []
        for sembol, poz in list(self.pozisyonlar.items()):
            if sembol not in fiyat_verisi:
                continue
            fiyat = fiyat_verisi[sembol].get("fiyat", poz.mevcut_fiyat)
            kontrol = self.risk_limitleri.stop_loss_kontrolu(
                sembol, poz.giris_fiyat, fiyat, poz.trailing_max
            )
            if kontrol["cikis_gerekli"]:
                tetiklenenler.append({
                    "sembol": sembol,
                    "fiyat": fiyat,
                    "neden": kontrol["cikis_nedeni"],
                    **kontrol,
                })
        return tetiklenenler

    def pozisyon_ozeti(self) -> dict:
        """Portföy özeti"""
        poz_listesi = [p.to_dict() for p in self.pozisyonlar.values()]
        return {
            "portfoy_degeri_usd": round(self.portfoy_degeri(), 2),
            "nakit_usd": round(self.nakit, 2),
            "pozisyon_degeri_usd": round(sum(p.deger_usd for p in self.pozisyonlar.values()), 2),
            "toplam_kar_zarar_usd": round(self.portfoy_kar_zarar(), 2),
            "toplam_kar_zarar_pct": round(self.portfoy_kar_zarar_pct(), 2),
            "bugun_kar_zarar_usd": round(self.bugun_kar_zarar, 2),
            "pozisyon_sayisi": len(self.pozisyonlar),
            "pozisyonlar": poz_listesi,
            "baslangic_sermayesi": self.baslangic_sermayesi,
        }
