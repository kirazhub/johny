"""
JOHNY — Risk Limitleri
Günlük kayıp, portföy stop, dinamik stop-loss,
max drawdown -%8 koruması (24 saat bekleme).
"""
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional

from johny_config import (
    PORTFOY_PARAMETRELERI,
    DINAMIK_STOP_LOSS,
    ATR_YUKSEK_KATMANI,
    MAX_DRAWDOWN_PCT,
    MAX_DRAWDOWN_BEKLEME_SAAT,
)

logger = logging.getLogger(__name__)


class RiskLimitleri:
    """Risk limiti yönetimi"""

    def __init__(self):
        self.params = PORTFOY_PARAMETRELERI
        self._gunluk_kar_zarar: Dict[str, float] = {}
        self._gunluk_islem_sayisi: Dict[str, int] = {}

        # Max drawdown koruyucu
        self._max_drawdown_tetiklendi: bool = False
        self._max_drawdown_zaman: Optional[datetime] = None
        self._pik_portfoy_degeri: float = self.params["baslangic_sermayesi"]

    # ------------------------------------------------------------------ #
    #  Günlük kayıp kontrolü                                               #
    # ------------------------------------------------------------------ #

    def gunluk_kayip_kontrolu(
        self,
        portfoy_degeri: float,
        baslangic_degeri: float,
        bugun_zarar: float,
    ) -> dict:
        """Günlük kayıp limiti kontrolü"""
        gunluk_limit = self.params["gunluk_kayip_limiti"]
        portfoy_stop = self.params["portfoy_stop_yuzdesi"]
        baslanggic_sermaye = self.params["baslangic_sermayesi"]

        gunluk_kayip_pct = bugun_zarar / portfoy_degeri if portfoy_degeri > 0 else 0
        portfoy_kayip_pct = (portfoy_degeri - baslanggic_sermaye) / baslanggic_sermaye

        # Max drawdown kontrolü
        if self._max_drawdown_tetiklendi and self._max_drawdown_zaman:
            bekleme_bitti = (
                datetime.now() - self._max_drawdown_zaman
            ).total_seconds() / 3600 >= MAX_DRAWDOWN_BEKLEME_SAAT
            if not bekleme_bitti:
                kalan_saat = MAX_DRAWDOWN_BEKLEME_SAAT - (
                    datetime.now() - self._max_drawdown_zaman
                ).total_seconds() / 3600
                return {
                    "gunluk_kayip_pct": round(gunluk_kayip_pct * 100, 2),
                    "gunluk_limit_pct": gunluk_limit * 100,
                    "gunluk_limit_asimi": True,
                    "portfoy_kayip_pct": round(portfoy_kayip_pct * 100, 2),
                    "portfoy_stop_asimi": True,
                    "islem_yapilabilir": False,
                    "neden": f"Max drawdown bekleme: {kalan_saat:.1f} saat kaldı",
                }
            else:
                # Bekleme bitti, kilidi kaldır
                self._max_drawdown_tetiklendi = False
                logger.info("Max drawdown bekleme süresi doldu, işlem kilidi kaldırıldı")

        return {
            "gunluk_kayip_pct": round(gunluk_kayip_pct * 100, 2),
            "gunluk_limit_pct": gunluk_limit * 100,
            "gunluk_limit_asimi": abs(gunluk_kayip_pct) >= gunluk_limit,
            "portfoy_kayip_pct": round(portfoy_kayip_pct * 100, 2),
            "portfoy_stop_asimi": portfoy_kayip_pct <= -portfoy_stop,
            "islem_yapilabilir": (
                abs(gunluk_kayip_pct) < gunluk_limit and
                portfoy_kayip_pct > -portfoy_stop
            ),
        }

    # ------------------------------------------------------------------ #
    #  Max Drawdown -%8 koruması                                           #
    # ------------------------------------------------------------------ #

    def max_drawdown_kontrol(self, portfoy_degeri: float) -> dict:
        """
        Portföy tepe değerinden -%8 düşüşü tespit et.
        Tetiklenirse tüm pozisyonlar kapatılmalı, 24 saat beklenmeli.
        """
        # Pik güncelle
        if portfoy_degeri > self._pik_portfoy_degeri:
            self._pik_portfoy_degeri = portfoy_degeri

        drawdown = 0.0
        if self._pik_portfoy_degeri > 0:
            drawdown = (portfoy_degeri - self._pik_portfoy_degeri) / self._pik_portfoy_degeri

        tetiklendi = drawdown <= -MAX_DRAWDOWN_PCT

        if tetiklendi and not self._max_drawdown_tetiklendi:
            self._max_drawdown_tetiklendi = True
            self._max_drawdown_zaman = datetime.now()
            logger.warning(
                f"MAX DRAWDOWN TETİKLENDİ: {drawdown*100:.1f}% "
                f"(pik: ${self._pik_portfoy_degeri:.2f}, şimdi: ${portfoy_degeri:.2f}) "
                f"— TÜM POZİSYONLAR KAPATILIYOR, 24 saat bekleniyor"
            )

        return {
            "drawdown_pct": round(drawdown * 100, 2),
            "pik_deger": round(self._pik_portfoy_degeri, 2),
            "esik_pct": MAX_DRAWDOWN_PCT * 100,
            "tetiklendi": tetiklendi,
            "tum_pozisyonlari_kapat": tetiklendi,
            "kilitli_mi": self._max_drawdown_tetiklendi,
        }

    # ------------------------------------------------------------------ #
    #  Dinamik stop-loss                                                    #
    # ------------------------------------------------------------------ #

    def dinamik_stop_loss_hesapla(
        self,
        giris_fiyat: float,
        atr: Optional[float] = None,
        ortalama_atr: Optional[float] = None,
        kazanc_oncesi: bool = False,
        makro_kritik_gun: bool = False,
    ) -> dict:
        """
        Piyasa koşuluna göre dinamik stop-loss yüzdesi ve fiyatı hesapla.

        Öncelik sırası:
        1. Makro kritik gün  → %2 (dar)
        2. Kazanç öncesi    → %2 (dar)
        3. Yüksek volatilite → %4 (geniş)
        4. Normal            → %3
        """
        if makro_kritik_gun:
            stop_pct = DINAMIK_STOP_LOSS["makro_kritik"]
            durum = "MAKRO_KRİTİK"
        elif kazanc_oncesi:
            stop_pct = DINAMIK_STOP_LOSS["kazanc_oncesi"]
            durum = "KAZANÇ_ÖNCESİ"
        elif atr is not None and ortalama_atr is not None and ortalama_atr > 0:
            # ATR ortalamanın 1.5 katından büyükse yüksek volatilite
            if atr > ortalama_atr * ATR_YUKSEK_KATMANI:
                stop_pct = DINAMIK_STOP_LOSS["yuksek_volatil"]
                durum = "YÜKSEK_VOLATİLİTE"
            else:
                stop_pct = DINAMIK_STOP_LOSS["normal"]
                durum = "NORMAL"
        else:
            stop_pct = DINAMIK_STOP_LOSS["normal"]
            durum = "NORMAL"

        stop_fiyat = giris_fiyat * (1 - stop_pct) if giris_fiyat > 0 else 0.0

        return {
            "stop_pct": stop_pct,
            "stop_fiyat": round(stop_fiyat, 2),
            "durum": durum,
            "aciklama": f"Stop-loss: %{stop_pct*100:.0f} ({durum})",
        }

    # ------------------------------------------------------------------ #
    #  Stop-loss kontrolü (dinamik destekli)                               #
    # ------------------------------------------------------------------ #

    def stop_loss_kontrolu(
        self,
        sembol: str,
        giris_fiyat: float,
        mevcut_fiyat: float,
        trailing_max: Optional[float] = None,
        stop_pct_override: Optional[float] = None,
    ) -> dict:
        """Stop-loss ve trailing stop kontrolü"""
        # Dinamik veya varsayılan stop yüzdesi
        stop_pct = stop_pct_override if stop_pct_override is not None else self.params["stop_loss_yuzdesi"]
        trailing_pct = self.params["trailing_stop_yuzdesi"]
        tp_pct = self.params["take_profit_yuzdesi"]

        degisim = (mevcut_fiyat - giris_fiyat) / giris_fiyat if giris_fiyat > 0 else 0
        stop_fiyat = giris_fiyat * (1 - stop_pct)
        tp_fiyat = giris_fiyat * (1 + tp_pct)

        # Trailing stop
        trailing_tetik = False
        trailing_stop_fiyat = None
        if trailing_max and trailing_max > giris_fiyat:
            trailing_stop_fiyat = trailing_max * (1 - trailing_pct)
            trailing_tetik = mevcut_fiyat <= trailing_stop_fiyat

        return {
            "sembol": sembol,
            "degisim_pct": round(degisim * 100, 2),
            "stop_fiyat": round(stop_fiyat, 2),
            "tp_fiyat": round(tp_fiyat, 2),
            "stop_tetik": mevcut_fiyat <= stop_fiyat,
            "tp_tetik": mevcut_fiyat >= tp_fiyat,
            "trailing_stop_fiyat": trailing_stop_fiyat,
            "trailing_tetik": trailing_tetik,
            "cikis_gerekli": mevcut_fiyat <= stop_fiyat or trailing_tetik or mevcut_fiyat >= tp_fiyat,
            "cikis_nedeni": (
                "Stop-Loss" if mevcut_fiyat <= stop_fiyat else
                "Take-Profit" if mevcut_fiyat >= tp_fiyat else
                "Trailing Stop" if trailing_tetik else
                None
            ),
        }

    # ------------------------------------------------------------------ #
    #  Pozisyon büyüklük kontrolü                                          #
    # ------------------------------------------------------------------ #

    def max_pozisyon_kontrolu(
        self,
        mevcut_pozisyon_sayisi: int,
        portfoy_degeri: float,
        yeni_pozisyon_degeri: float,
    ) -> dict:
        """Maksimum pozisyon kontrolü"""
        max_poz_sayisi = self.params["max_pozisyon_sayisi"]
        max_poz_pct = self.params["max_pozisyon_yuzdesi"]

        poz_pct = yeni_pozisyon_degeri / portfoy_degeri if portfoy_degeri > 0 else 0
        return {
            "mevcut_pozisyon": mevcut_pozisyon_sayisi,
            "max_pozisyon": max_poz_sayisi,
            "pozisyon_sayisi_ok": mevcut_pozisyon_sayisi < max_poz_sayisi,
            "pozisyon_boyutu_ok": poz_pct <= max_poz_pct,
            "kabul_edilebilir": (
                mevcut_pozisyon_sayisi < max_poz_sayisi and
                poz_pct <= max_poz_pct
            ),
        }

    # ------------------------------------------------------------------ #
    #  Genel risk skoru                                                     #
    # ------------------------------------------------------------------ #

    def risk_skoru_hesapla(
        self,
        portfoy_degeri: float,
        baslangic_sermaye: float,
        bugun_zarar: float,
        pozisyon_sayisi: int,
        portfoy_beta: float = 1.0,
    ) -> dict:
        """Genel risk skoru (0-100)"""
        kayip_pct = abs(bugun_zarar / portfoy_degeri) if portfoy_degeri > 0 else 0
        portfoy_kayip = (baslangic_sermaye - portfoy_degeri) / baslangic_sermaye if baslangic_sermaye > 0 else 0

        # Bileşenler
        kayip_skor = min(kayip_pct / self.params["gunluk_kayip_limiti"] * 40, 40)
        portfoy_skor = min(max(portfoy_kayip, 0) / self.params["portfoy_stop_yuzdesi"] * 30, 30)
        pozisyon_skor = (pozisyon_sayisi / self.params["max_pozisyon_sayisi"]) * 15
        beta_skor = min((portfoy_beta - 1) * 10, 15) if portfoy_beta > 1 else 0

        toplam = kayip_skor + portfoy_skor + pozisyon_skor + beta_skor
        return {
            "risk_skoru": round(toplam, 1),
            "seviye": "Kritik" if toplam > 75 else "Yüksek" if toplam > 50 else "Orta" if toplam > 25 else "Düşük",
            "bilesenler": {
                "gunluk_kayip": round(kayip_skor, 1),
                "portfoy_kayip": round(portfoy_skor, 1),
                "pozisyon_yogunlugu": round(pozisyon_skor, 1),
                "beta_riski": round(beta_skor, 1),
            },
        }
