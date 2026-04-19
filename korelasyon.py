"""
JOHNY — Korelasyon Ticareti
Tetikleyici varlık hareket edince ilişkili hisseler için sinyal üretir.
Her 15 dakikada bir kontrol edilir.
"""
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import yfinance as yf

logger = logging.getLogger(__name__)

# ─── Korelasyon tanımları ─────────────────────────────────────────────────────
# Tetikleyici → ilişkili hisseler
KORELASYONLAR: Dict[str, List[str]] = {
    "BTC-USD":   ["COIN", "MSTR"],          # BTC yükselince bunlar yükselir
    "CL=F":      ["XOM", "CVX", "COP"],     # Petrol yükselince bunlar yükselir
    "DX-Y.NYB":  ["AAPL", "MSFT"],          # Dolar güçlendi → ihracatçılar zarar
    "^VIX":      ["UVXY", "SQQQ"],          # VIX yükseldi → koruma al
    "GC=F":      ["GLD", "NEM"],            # Altın yükselince
}

# Korelasyon yönü: +1 → tetikleyici ile aynı yönde, -1 → ters yönde
KORELASYON_YON: Dict[str, int] = {
    "BTC-USD":   +1,
    "CL=F":      +1,
    "DX-Y.NYB":  -1,   # Dolar güçlendi → dolar hassas ihracatçılar düşer
    "^VIX":      +1,
    "GC=F":      +1,
}

# Tetik eşiği: bu kadar hareket sinyal üretir
TETIK_PCT = 0.015   # %1.5

# Güncelleme aralığı
GUNCELLEME_SANIYE = 900  # 15 dakika


class KorelasyonTicareti:
    """
    Tetikleyici varlıkların fiyat değişimlerini izler;
    eşik aşılınca ilişkili hisseler için sinyal üretir.
    """

    def __init__(self):
        self._onceki_fiyatlar: Dict[str, float] = {}
        self._son_sinyaller: List[dict] = []
        self._son_guncelleme: float = 0.0

    # ------------------------------------------------------------------ #
    #  Tetikleyici fiyat çekme                                             #
    # ------------------------------------------------------------------ #

    def _fiyat_cek(self, sembol: str) -> Optional[float]:
        """Anlık fiyatı yfinance'den çek"""
        try:
            ticker = yf.Ticker(sembol)
            df = ticker.history(period="1d", interval="1m")
            if df is None or df.empty:
                return None
            return float(df["Close"].iloc[-1])
        except Exception as e:
            logger.debug(f"Korelasyon fiyat alınamadı {sembol}: {e}")
            return None

    def tetikleyicileri_guncelle(self) -> Dict[str, float]:
        """Tüm tetikleyicilerin güncel fiyatlarını çek"""
        fiyatlar: Dict[str, float] = {}
        for tetik in KORELASYONLAR:
            fiyat = self._fiyat_cek(tetik)
            if fiyat is not None:
                fiyatlar[tetik] = fiyat
        return fiyatlar

    # ------------------------------------------------------------------ #
    #  Değişim hesaplama                                                    #
    # ------------------------------------------------------------------ #

    def degisim_hesapla(
        self,
        tetik: str,
        yeni_fiyat: float,
    ) -> Tuple[float, float]:
        """
        Önceki fiyata göre değişimi hesapla.
        Returns: (degisim_pct, onceki_fiyat)
        """
        onceki = self._onceki_fiyatlar.get(tetik)
        if onceki is None or onceki == 0:
            self._onceki_fiyatlar[tetik] = yeni_fiyat
            return 0.0, yeni_fiyat
        degisim = (yeni_fiyat - onceki) / onceki
        return degisim, onceki

    # ------------------------------------------------------------------ #
    #  Sinyal üretme                                                        #
    # ------------------------------------------------------------------ #

    def sinyal_uret(
        self,
        mevcut_fiyatlar: Optional[Dict[str, float]] = None,
    ) -> List[dict]:
        """
        Tetikleyici harekete göre ilişkili hisse sinyalleri üret.
        Döner: [{"sembol", "sinyal", "tetik", "degisim_pct", "aciklama"}]
        """
        if mevcut_fiyatlar is None:
            mevcut_fiyatlar = self.tetikleyicileri_guncelle()

        sinyaller: List[dict] = []

        for tetik, hisseler in KORELASYONLAR.items():
            yeni_fiyat = mevcut_fiyatlar.get(tetik)
            if yeni_fiyat is None:
                continue

            degisim, onceki = self.degisim_hesapla(tetik, yeni_fiyat)
            abs_degisim = abs(degisim)

            if abs_degisim < TETIK_PCT:
                # Eşik altı — fiyatı güncelle ama sinyal üretme
                self._onceki_fiyatlar[tetik] = yeni_fiyat
                continue

            # Tetik aktif: sinyal üret
            yon = KORELASYON_YON.get(tetik, +1)
            # tetikleyici yükselince yon=+1 → hisseyi AL, yon=-1 → SAT
            if degisim > 0:
                hisse_sinyal = "AL" if yon == +1 else "SAT"
                sinyal_deger = +0.7 if yon == +1 else -0.7
            else:
                hisse_sinyal = "SAT" if yon == +1 else "AL"
                sinyal_deger = -0.7 if yon == +1 else +0.7

            # Güçlü hareket → daha güçlü sinyal
            if abs_degisim >= 0.03:
                sinyal_deger = sinyal_deger * 1.2 if sinyal_deger > 0 else sinyal_deger * 1.2
                sinyal_deger = max(-1.0, min(1.0, sinyal_deger))

            for hisse in hisseler:
                aciklama = (
                    f"Korelasyon {hisse_sinyal}: {hisse}, "
                    f"sebep: {tetik} {degisim*100:+.1f}%"
                )
                logger.info(aciklama)
                sinyaller.append({
                    "sembol": hisse,
                    "sinyal": hisse_sinyal,
                    "sinyal_deger": round(sinyal_deger, 2),
                    "tetik": tetik,
                    "tetik_fiyat": round(yeni_fiyat, 4),
                    "degisim_pct": round(degisim * 100, 2),
                    "aciklama": aciklama,
                    "zaman": datetime.now().isoformat(),
                })

            # Fiyatı güncelle (bir sonraki tik için referans)
            self._onceki_fiyatlar[tetik] = yeni_fiyat

        self._son_sinyaller = sinyaller
        return sinyaller

    # ------------------------------------------------------------------ #
    #  Periyodik güncelleme                                                 #
    # ------------------------------------------------------------------ #

    def guncelle(self, zorla: bool = False) -> List[dict]:
        """
        15 dakikada bir otomatik güncelleme.
        Döner: yeni sinyaller listesi.
        """
        simdi = time.time()
        if zorla or (simdi - self._son_guncelleme) >= GUNCELLEME_SANIYE:
            sinyaller = self.sinyal_uret()
            self._son_guncelleme = simdi
            if sinyaller:
                logger.info(
                    f"Korelasyon sinyalleri: "
                    + ", ".join(f"{s['sembol']} {s['sinyal']}" for s in sinyaller)
                )
            return sinyaller
        return []

    # ------------------------------------------------------------------ #
    #  Durum özeti                                                          #
    # ------------------------------------------------------------------ #

    def durum_ozeti(self) -> str:
        """İnsan okunabilir durum özeti"""
        if not self._onceki_fiyatlar:
            return "Korelasyon fiyatları henüz yüklenmedi"
        satirlar = ["Korelasyon İzlenen Tetikleyiciler:"]
        for tetik, fiyat in self._onceki_fiyatlar.items():
            hisseler = ", ".join(KORELASYONLAR.get(tetik, []))
            satirlar.append(f"  {tetik}: ${fiyat:.4f} → [{hisseler}]")
        return "\n".join(satirlar)
