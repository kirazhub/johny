"""
JOHNY — Pozisyon Boyutlandırıcı
USD-bazlı Kelly + Fixed risk
"""
import logging
from typing import Optional

from johny_config import PORTFOY_PARAMETRELERI, KOMISYON

logger = logging.getLogger(__name__)


class PozisyonBoyutlandirici:
    """USD tabanlı pozisyon boyutlandırma"""

    def __init__(self):
        self.params = PORTFOY_PARAMETRELERI
        self.komisyon = KOMISYON

    def pozisyon_hesapla(
        self,
        sembol: str,
        fiyat: float,
        portfoy_degeri: float,
        atr: Optional[float] = None,
        sinyal_guven: float = 0.5,
        mevcut_pozisyon_sayisi: int = 0,
    ) -> dict:
        """Optimal pozisyon büyüklüğünü hesapla"""
        try:
            max_pozisyon = self.params["max_pozisyon_sayisi"]
            max_pct = self.params["max_pozisyon_yuzdesi"]
            stop_pct = self.params["stop_loss_yuzdesi"]

            # Maksimum pozisyon sayısı kontrolü
            if mevcut_pozisyon_sayisi >= max_pozisyon:
                return {
                    "sembol": sembol,
                    "lot": 0,
                    "deger_usd": 0.0,
                    "red": "Maksimum pozisyon sayısına ulaşıldı",
                }

            # Temel pozisyon büyüklüğü
            max_deger = portfoy_degeri * max_pct
            if fiyat <= 0:
                return {"sembol": sembol, "lot": 0, "deger_usd": 0.0, "red": "Geçersiz fiyat"}

            # ATR bazlı dinamik pozisyon yüzdesi: min(%8, 0.2% / ATR%)
            # Formül: volatilite arttıkça pozisyon küçülür
            if atr and atr > 0 and fiyat > 0:
                atr_yuzde = atr / fiyat
                dinamik_pct = min(max_pct, 0.002 / atr_yuzde) if atr_yuzde > 0 else max_pct
                # Sinyal güvenini de dahil et (Kelly benzeri)
                efektif_pct = dinamik_pct * sinyal_guven
                efektif_pct = min(efektif_pct, max_pct)
            else:
                # ATR yoksa sabit maksimum × güven
                efektif_pct = max_pct * sinyal_guven
                atr_yuzde = None

            hedef_deger = portfoy_degeri * efektif_pct
            lot = hedef_deger / fiyat

            # Maksimum değer kontrolü
            lot = max(0, lot)
            deger = lot * fiyat
            if deger > max_deger:
                lot = max_deger / fiyat

            # Komisyon dahil maliyet
            komisyon = self._komisyon_hesapla(int(lot))
            toplam_maliyet = lot * fiyat + komisyon

            # Portföy değerine göre son kontrol
            if toplam_maliyet > portfoy_degeri * max_pct:
                lot = (portfoy_degeri * max_pct - komisyon) / fiyat

            # Fractional lot destekle (ABD piyasası fract. shares)
            lot = round(lot, 4)  # 4 decimal hassasiyet
            lot = max(0, lot)
            if lot < 0.001:
                return {
                    "sembol": sembol,
                    "lot": 0,
                    "deger_usd": 0.0,
                    "red": "Yetersiz sermaye veya fiyat çok yüksek",
                }

            komisyon_final = self._komisyon_hesapla(lot)
            return {
                "sembol": sembol,
                "lot": lot,
                "fiyat": fiyat,
                "deger_usd": lot * fiyat,
                "komisyon": komisyon_final,
                "toplam_maliyet": lot * fiyat + komisyon_final,
                "portfoy_yuzdesi": (lot * fiyat / portfoy_degeri) * 100,
                "stop_fiyat": fiyat * (1 - stop_pct),
                "hedef_fiyat": fiyat * (1 + self.params["take_profit_yuzdesi"]),
                "trailing_stop": fiyat * (1 - self.params["trailing_stop_yuzdesi"]),
                "atr_yuzde": round(atr_yuzde * 100, 2) if atr_yuzde is not None else None,
                "dinamik_pct": round(efektif_pct * 100, 2),
                "red": None,
            }
        except Exception as e:
            logger.error(f"Pozisyon hesaplama hatası {sembol}: {e}")
            return {"sembol": sembol, "lot": 0, "deger_usd": 0.0, "red": str(e)}

    def _komisyon_hesapla(self, lot: int) -> float:
        """Interactive Brokers tarzı komisyon hesapla"""
        komisyon = lot * self.komisyon["hisse_basi"]
        return max(komisyon, self.komisyon["minimum"])

    def cikis_komisyonu_hesapla(self, lot: int) -> float:
        return self._komisyon_hesapla(lot)

    def toplam_komisyon(self, lot: int) -> float:
        """Giriş + çıkış komisyonu"""
        return self._komisyon_hesapla(lot) * 2
