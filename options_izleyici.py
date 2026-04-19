"""
JOHNY — Unusual Options Activity İzleyici
Her saat çalışır (yfinance options chain kullanarak).
- call_volume > call_open_interest * 2 → olağandışı hacim
- Toplam call premium > $500K → büyük call alımı
- Bu hisseler için +2 sinyal puanı
- Sonuçlar log'a yazılır ve sinyal olarak döner
"""
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional

import yfinance as yf

from johny_config import TUM_EVREN

logger = logging.getLogger("options_izleyici")

# Eşikler
UNUSUAL_HACIM_KATSAYI = 2.0         # call_volume > call_OI * 2
BUYUK_PREMIUM_USD = 500_000         # $500K+ premium
SINYAL_BONUS = 0.20                  # +0.20 sinyal değeri ekle
BATCH_BOYUTU = 10                    # Aynı anda kaç sembol
MAX_SEMBOL = 100                     # Taranacak maksimum sembol (rate limiting)


class OptionsIzleyici:
    """
    Olağandışı options aktivitesini tespit eder.
    Büyük call alımları kurumsal ilgiyi gösterir.
    """

    def __init__(self):
        self._sonuclar: List[dict] = []
        self._son_guncelleme: Optional[str] = None

    # ------------------------------------------------------------------ #
    #  Veri Çekme                                                          #
    # ------------------------------------------------------------------ #

    def _options_analiz(self, sembol: str) -> Optional[dict]:
        """
        Bir sembol için options chain analizi yapar.
        Returns: analiz sonucu veya None
        """
        try:
            ticker = yf.Ticker(sembol)
            # Mevcut opsion tarihleri
            tarihler = ticker.options
            if not tarihler:
                return None

            # En yakın 2 opsiyon tarihini al
            kontrol_tarihleri = tarihler[:2]

            toplam_call_hacim = 0
            toplam_call_oi = 0
            toplam_put_hacim = 0
            toplam_put_oi = 0
            tahmini_call_premium = 0.0
            fiyat_bilgi = ticker.fast_info
            hisse_fiyat = getattr(fiyat_bilgi, "last_price", 0.0) or 0.0

            for tarih in kontrol_tarihleri:
                try:
                    chain = ticker.option_chain(tarih)
                    calls = chain.calls
                    puts = chain.puts

                    if calls is not None and not calls.empty:
                        toplam_call_hacim += int(calls["volume"].fillna(0).sum())
                        toplam_call_oi += int(calls["openInterest"].fillna(0).sum())
                        # Premium tahmini: hacim * (ask+bid)/2 * 100 lot
                        if "ask" in calls.columns and "bid" in calls.columns:
                            orta = ((calls["ask"].fillna(0) + calls["bid"].fillna(0)) / 2)
                            tahmini_call_premium += float(
                                (calls["volume"].fillna(0) * orta * 100).sum()
                            )

                    if puts is not None and not puts.empty:
                        toplam_put_hacim += int(puts["volume"].fillna(0).sum())
                        toplam_put_oi += int(puts["openInterest"].fillna(0).sum())
                except Exception:
                    pass

            if toplam_call_hacim == 0 and toplam_put_hacim == 0:
                return None

            # Olağandışılık tespiti
            olagan_disi = False
            buyuk_call = False

            if toplam_call_oi > 0 and toplam_call_hacim > toplam_call_oi * UNUSUAL_HACIM_KATSAYI:
                olagan_disi = True

            if tahmini_call_premium >= BUYUK_PREMIUM_USD:
                buyuk_call = True

            if not olagan_disi and not buyuk_call:
                return None

            # Put/Call oranı
            pc_orani = toplam_put_hacim / toplam_call_hacim if toplam_call_hacim > 0 else 0.0

            sinyal_deger = SINYAL_BONUS if (olagan_disi or buyuk_call) else 0.0

            return {
                "sembol": sembol,
                "call_hacim": toplam_call_hacim,
                "call_oi": toplam_call_oi,
                "put_hacim": toplam_put_hacim,
                "put_oi": toplam_put_oi,
                "tahmini_call_premium_usd": int(tahmini_call_premium),
                "pc_orani": round(pc_orani, 2),
                "olagan_disi_hacim": olagan_disi,
                "buyuk_call_alimi": buyuk_call,
                "sinyal_deger": sinyal_deger,
                "guncelleme": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.debug(f"{sembol} options hatası: {e}")
            return None

    # ------------------------------------------------------------------ #
    #  Ana Tarama                                                          #
    # ------------------------------------------------------------------ #

    def tara(self, semboller: Optional[List[str]] = None) -> List[dict]:
        """
        Sembollerin options aktivitesini tarar.
        Rate limiting nedeniyle MAX_SEMBOL ile sınırlıdır.
        Returns: sinyal bulunan hisseler listesi
        """
        if semboller is None:
            semboller = TUM_EVREN

        # Rate limiting: çok fazla sembol taramamak için sınırla
        taranacak = semboller[:MAX_SEMBOL]
        logger.info(f"Options taraması başlıyor: {len(taranacak)} sembol")

        sonuclar: List[dict] = []
        for i, sembol in enumerate(taranacak):
            sonuc = self._options_analiz(sembol)
            if sonuc:
                sonuclar.append(sonuc)
                logger.info(
                    f"[Options] {sembol}: Call Hacim={sonuc['call_hacim']:,} "
                    f"Premium=${sonuc['tahmini_call_premium_usd']:,} "
                    f"Olağandışı={sonuc['olagan_disi_hacim']} "
                    f"BüyükCall={sonuc['buyuk_call_alimi']}"
                )
            if (i + 1) % BATCH_BOYUTU == 0:
                time.sleep(1.0)  # Rate limiting: her 10 sembolde bir bekle

        self._sonuclar = sonuclar
        self._son_guncelleme = datetime.now().isoformat()
        logger.info(f"Options tarama tamamlandı: {len(sonuclar)} olağandışı aktivite")
        return sonuclar

    # ------------------------------------------------------------------ #
    #  Çıktı                                                               #
    # ------------------------------------------------------------------ #

    def sinyal_bonuslari(self) -> Dict[str, float]:
        """
        johny_main.py entegrasyonu için {sembol: sinyal_bonus} döner.
        Bu değerleri mevcut sinyallere ekle.
        """
        return {s["sembol"]: s["sinyal_deger"] for s in self._sonuclar}

    def ozet(self) -> str:
        """Kısa özet metin."""
        if not self._sonuclar:
            return "📊 Options İzleyici: olağandışı aktivite yok"
        satirlar = [f"📊 Olağandışı Options Aktivitesi: {len(self._sonuclar)} hisse"]
        for s in self._sonuclar[:5]:
            tip = "🐳 BÜYÜK CALL" if s["buyuk_call_alimi"] else "📈 UNUSUAL"
            satirlar.append(
                f"  {tip} {s['sembol']}: "
                f"Call {s['call_hacim']:,} | "
                f"Premium ${s['tahmini_call_premium_usd']:,} | "
                f"P/C {s['pc_orani']:.2f}"
            )
        return "\n".join(satirlar)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    izleyici = OptionsIzleyici()
    sonuclar = izleyici.tara()
    print(izleyici.ozet())
