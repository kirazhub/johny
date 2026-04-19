"""
JOHNY — Telegram Bildirim Modülü
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TelegramBildirici:
    """Telegram bot bildirimleri"""

    def __init__(self, token: str = "", chat_id: str = ""):
        self.token = token
        self.chat_id = chat_id
        self._aktif = bool(token and chat_id)

    def mesaj_gonder(self, mesaj: str, parse_mode: str = "HTML") -> bool:
        """Telegram mesajı gönder"""
        if not self._aktif:
            logger.debug(f"Telegram kapalı: {mesaj[:50]}")
            return False
        try:
            import requests
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": mesaj,
                "parse_mode": parse_mode,
            }
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                return True
            logger.warning(f"Telegram gönderme hatası: {resp.status_code}")
            return False
        except Exception as e:
            logger.error(f"Telegram hatası: {e}")
            return False

    def al_bildirimi(
        self,
        sembol: str,
        lot: int,
        fiyat: float,
        strateji: str,
        portfoy_degeri: float,
    ) -> bool:
        """Alım bildirimi"""
        mesaj = (
            f"🟢 <b>JOHNY — AL SİNYALİ</b>\n"
            f"📊 Sembol: <b>{sembol}</b>\n"
            f"📦 Lot: {lot}\n"
            f"💵 Fiyat: ${fiyat:.2f}\n"
            f"🧠 Strateji: {strateji}\n"
            f"💰 Portföy: ${portfoy_degeri:,.2f}"
        )
        return self.mesaj_gonder(mesaj)

    def sat_bildirimi(
        self,
        sembol: str,
        lot: int,
        fiyat: float,
        kar_zarar: float,
        neden: str,
        portfoy_degeri: float,
    ) -> bool:
        """Satış bildirimi"""
        emoji = "🟢" if kar_zarar >= 0 else "🔴"
        mesaj = (
            f"{emoji} <b>JOHNY — SAT</b>\n"
            f"📊 Sembol: <b>{sembol}</b>\n"
            f"📦 Lot: {lot}\n"
            f"💵 Fiyat: ${fiyat:.2f}\n"
            f"📈 K/Z: ${kar_zarar:+.2f}\n"
            f"📌 Neden: {neden}\n"
            f"💰 Portföy: ${portfoy_degeri:,.2f}"
        )
        return self.mesaj_gonder(mesaj)

    def gunluk_ozet_gonder(self, ozet: dict) -> bool:
        """Günlük özet bildirimi"""
        portfoy = ozet.get("portfoy_degeri_usd", 0)
        kar = ozet.get("bugun_kar_zarar_usd", 0)
        toplam_kar = ozet.get("toplam_kar_zarar_usd", 0)
        pozisyon = ozet.get("pozisyon_sayisi", 0)
        emoji = "📈" if kar >= 0 else "📉"
        mesaj = (
            f"🇺🇸 <b>JOHNY — Günlük Özet</b>\n"
            f"{emoji} Bugün: <b>${kar:+.2f}</b>\n"
            f"💰 Portföy: ${portfoy:,.2f}\n"
            f"📊 Toplam K/Z: ${toplam_kar:+.2f}\n"
            f"📁 Açık Pozisyon: {pozisyon}"
        )
        return self.mesaj_gonder(mesaj)

    def uyari_gonder(self, baslik: str, mesaj_icerik: str) -> bool:
        """Uyarı bildirimi"""
        mesaj = f"⚠️ <b>JOHNY UYARI</b>\n<b>{baslik}</b>\n{mesaj_icerik}"
        return self.mesaj_gonder(mesaj)

    def risk_uyarisi(self, risk_skoru: float, seviye: str) -> bool:
        """Risk uyarısı"""
        mesaj = (
            f"🚨 <b>JOHNY — Risk Uyarısı</b>\n"
            f"⚠️ Risk Skoru: <b>{risk_skoru:.1f}/100</b>\n"
            f"🔴 Seviye: <b>{seviye}</b>"
        )
        return self.mesaj_gonder(mesaj)
