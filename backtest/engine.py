"""
JOHNY — Backtest Engine
2 yıllık US market simülasyonu
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import yfinance as yf

from johny_config import (
    US_SEMBOLLER, BACKTEST_PARAMETRELERI, KOMISYON, PORTFOY_PARAMETRELERI
)
from backtest.metrics import BacktestMetrikleri

logger = logging.getLogger(__name__)


class BacktestEngine:
    """Gerçekçi komisyonlu backtest motoru"""

    def __init__(self):
        self.params = BACKTEST_PARAMETRELERI
        self.komisyon = KOMISYON
        self.pf_params = PORTFOY_PARAMETRELERI
        self.metrik_hesaplayici = BacktestMetrikleri()

    def backtest_calistir(
        self,
        semboller: Optional[List[str]] = None,
        strateji_sinyal_fn=None,
        ilerleme_fn=None,
    ) -> dict:
        """Tam backtest çalıştır"""
        try:
            if semboller is None:
                semboller = US_SEMBOLLER[:20]  # İlk 20 sembol

            sermaye = self.params["baslangic_sermayesi"]
            nakit = sermaye
            portfoy: Dict[str, dict] = {}
            islemler: List[dict] = []
            portfoy_serisi: List[dict] = []

            # Veri çek
            logger.info("Backtest verisi çekiliyor...")
            if ilerleme_fn:
                ilerleme_fn("Veri çekiliyor...", 10)

            fiyat_verisi: Dict[str, pd.DataFrame] = {}
            for i, sembol in enumerate(semboller):
                try:
                    ticker = yf.Ticker(sembol)
                    df = ticker.history(period=self.params["donem"])
                    if not df.empty:
                        fiyat_verisi[sembol] = df
                except Exception as e:
                    logger.warning(f"Backtest veri hatası {sembol}: {e}")

            if not fiyat_verisi:
                return {"hata": "Veri çekilemedi"}

            # Benchmark
            benchmark_sembol = self.params["benchmark"]
            benchmark_df = fiyat_verisi.get(benchmark_sembol)
            if benchmark_df is None:
                try:
                    ticker = yf.Ticker(benchmark_sembol)
                    benchmark_df = ticker.history(period=self.params["donem"])
                except Exception:
                    pass

            # Ortak tarih aralığı
            tum_tarihler = set()
            for df in fiyat_verisi.values():
                tum_tarihler.update(df.index.date)
            tarihler = sorted(list(tum_tarihler))

            if ilerleme_fn:
                ilerleme_fn(f"{len(tarihler)} gün işleniyor...", 20)

            # Günlük simülasyon
            for i, tarih in enumerate(tarihler):
                if i < 50:  # İlk 50 gün teknik gösterge warm-up
                    continue

                if ilerleme_fn and i % 50 == 0:
                    pct = 20 + int(i / len(tarihler) * 60)
                    ilerleme_fn(f"Gün {i}/{len(tarihler)} işleniyor...", pct)

                gunun_fiyatlari = {}
                for sembol, df in fiyat_verisi.items():
                    idx = df.index.date
                    mask = idx == tarih
                    if mask.any():
                        satir = df[mask].iloc[-1]
                        gunun_fiyatlari[sembol] = {
                            "open": float(satir.get("Open", satir["Close"])),
                            "close": float(satir["Close"]),
                            "high": float(satir.get("High", satir["Close"])),
                            "low": float(satir.get("Low", satir["Close"])),
                            "volume": float(satir.get("Volume", 0)),
                        }

                # Stop-loss kontrolü
                cikis_listesi = []
                for sembol, poz in portfoy.items():
                    if sembol not in gunun_fiyatlari:
                        continue
                    fiyat = gunun_fiyatlari[sembol]["close"]
                    giris = poz["giris_fiyat"]
                    lot = poz["lot"]
                    degisim = (fiyat - giris) / giris if giris > 0 else 0

                    # Max fiyat takibi
                    if fiyat > poz.get("max_fiyat", giris):
                        poz["max_fiyat"] = fiyat

                    stop_pct = self.pf_params["stop_loss_yuzdesi"]
                    tp_pct = self.pf_params["take_profit_yuzdesi"]
                    trailing_pct = self.pf_params["trailing_stop_yuzdesi"]
                    trailing_stop = poz.get("max_fiyat", giris) * (1 - trailing_pct)

                    if fiyat <= giris * (1 - stop_pct):
                        cikis_listesi.append((sembol, fiyat, "Stop-Loss"))
                    elif fiyat >= giris * (1 + tp_pct):
                        cikis_listesi.append((sembol, fiyat, "Take-Profit"))
                    elif fiyat <= trailing_stop and fiyat < giris * (1 + 0.01):
                        cikis_listesi.append((sembol, fiyat, "Trailing Stop"))

                for sembol, fiyat, neden in cikis_listesi:
                    poz = portfoy.pop(sembol)
                    lot = poz["lot"]
                    komisyon = max(lot * self.komisyon["hisse_basi"], self.komisyon["minimum"])
                    gelir = lot * fiyat - komisyon
                    nakit += gelir
                    kar_zarar = gelir - poz["giris_maliyet"]
                    islemler.append({
                        "tarih": str(tarih),
                        "sembol": sembol,
                        "islem": "SAT",
                        "lot": lot,
                        "fiyat": fiyat,
                        "komisyon": komisyon,
                        "kar_zarar": kar_zarar,
                        "neden": neden,
                    })

                # Sinyal üret ve al
                if strateji_sinyal_fn and len(portfoy) < self.pf_params["max_pozisyon_sayisi"]:
                    for sembol in semboller:
                        if sembol in portfoy or sembol not in gunun_fiyatlari:
                            continue
                        df_slice = fiyat_verisi[sembol]
                        mask = pd.Series(df_slice.index.date) <= tarih
                        df_slice = df_slice[mask.values]
                        if len(df_slice) < 50:
                            continue
                        try:
                            sinyal = strateji_sinyal_fn(sembol, df_slice)
                            if sinyal and sinyal.get("birlesik_sinyal", 0) > 0.5:
                                fiyat = gunun_fiyatlari[sembol]["open"]
                                max_poz = nakit * self.pf_params["max_pozisyon_yuzdesi"]
                                lot = int(max_poz / fiyat) if fiyat > 0 else 0
                                if lot > 0:
                                    komisyon = max(lot * self.komisyon["hisse_basi"], self.komisyon["minimum"])
                                    maliyet = lot * fiyat + komisyon
                                    if maliyet <= nakit:
                                        nakit -= maliyet
                                        portfoy[sembol] = {
                                            "lot": lot,
                                            "giris_fiyat": fiyat,
                                            "giris_maliyet": maliyet,
                                            "max_fiyat": fiyat,
                                            "tarih": str(tarih),
                                        }
                                        islemler.append({
                                            "tarih": str(tarih),
                                            "sembol": sembol,
                                            "islem": "AL",
                                            "lot": lot,
                                            "fiyat": fiyat,
                                            "komisyon": komisyon,
                                            "kar_zarar": 0,
                                            "neden": "Sinyal",
                                        })
                        except Exception:
                            pass

                # Portföy değeri
                portfoy_degeri = nakit
                for sembol, poz in portfoy.items():
                    if sembol in gunun_fiyatlari:
                        portfoy_degeri += poz["lot"] * gunun_fiyatlari[sembol]["close"]

                portfoy_serisi.append({
                    "tarih": str(tarih),
                    "deger": portfoy_degeri,
                    "nakit": nakit,
                    "pozisyon_sayisi": len(portfoy),
                })

            if ilerleme_fn:
                ilerleme_fn("Metrikler hesaplanıyor...", 90)

            # Sonuç metrikleri
            if len(portfoy_serisi) < 2:
                return {"hata": "Yetersiz veri"}

            portfoy_df = pd.DataFrame(portfoy_serisi)
            portfoy_df.index = pd.to_datetime(portfoy_df["tarih"])
            portfoy_val_serisi = portfoy_df["deger"]

            bm_val_serisi = None
            if benchmark_df is not None and not benchmark_df.empty:
                # Benchmark normalize
                bm_norm = benchmark_df["Close"] / benchmark_df["Close"].iloc[0] * sermaye
                bm_val_serisi = bm_norm

            metrikler = self.metrik_hesaplayici.tam_metrik_hesapla(portfoy_val_serisi, bm_val_serisi)
            rolling_sharpe = self.metrik_hesaplayici.rolling_sharpe(portfoy_val_serisi)
            drawdown = self.metrik_hesaplayici.drawdown_serisi(portfoy_val_serisi)

            if ilerleme_fn:
                ilerleme_fn("Backtest tamamlandı!", 100)

            return {
                "metrikler": metrikler,
                "portfoy_serisi": portfoy_df.to_dict("records"),
                "islemler": islemler,
                "rolling_sharpe": rolling_sharpe.to_dict() if not rolling_sharpe.empty else {},
                "drawdown": drawdown.to_dict() if not drawdown.empty else {},
                "benchmark_serisi": bm_val_serisi.to_dict() if bm_val_serisi is not None else {},
                "toplam_islem": len(islemler),
                "kazanma_orani": self._kazanma_orani_hesapla(islemler),
            }

        except Exception as e:
            logger.error(f"Backtest motor hatası: {e}")
            return {"hata": str(e)}

    def _kazanma_orani_hesapla(self, islemler: List[dict]) -> float:
        """İşlem bazlı kazanma oranı"""
        satislar = [i for i in islemler if i["islem"] == "SAT"]
        if not satislar:
            return 0.0
        kazananlar = sum(1 for i in satislar if i["kar_zarar"] > 0)
        return round(kazananlar / len(satislar) * 100, 2)

    def hizli_backtest(
        self,
        sembol: str,
        sinyal_fn=None,
        donem: str = "1y",
    ) -> dict:
        """Tek sembol için hızlı backtest"""
        try:
            ticker = yf.Ticker(sembol)
            df = ticker.history(period=donem)
            if df.empty or len(df) < 50:
                return {}

            sermaye = 1000.0
            nakit = sermaye
            pozisyon: Optional[dict] = None
            portfoy_serisi = [sermaye]
            stop_pct = self.pf_params["stop_loss_yuzdesi"]
            tp_pct = self.pf_params["take_profit_yuzdesi"]

            for i in range(50, len(df)):
                fiyat = float(df["Close"].iloc[i])
                df_slice = df.iloc[:i]

                if pozisyon:
                    giris = pozisyon["giris"]
                    lot = pozisyon["lot"]
                    if fiyat <= giris * (1 - stop_pct) or fiyat >= giris * (1 + tp_pct):
                        komisyon = max(lot * self.komisyon["hisse_basi"], self.komisyon["minimum"])
                        nakit += lot * fiyat - komisyon
                        pozisyon = None
                else:
                    if sinyal_fn:
                        s = sinyal_fn(sembol, df_slice)
                        if s and s.get("birlesik_sinyal", 0) > 0.5:
                            lot = int(nakit * 0.95 / fiyat)
                            if lot > 0:
                                komisyon = max(lot * self.komisyon["hisse_basi"], self.komisyon["minimum"])
                                nakit -= lot * fiyat + komisyon
                                pozisyon = {"giris": fiyat, "lot": lot}

                poz_deger = pozisyon["lot"] * fiyat if pozisyon else 0
                portfoy_serisi.append(nakit + poz_deger)

            final_deger = portfoy_serisi[-1]
            return {
                "sembol": sembol,
                "baslangic": sermaye,
                "son_deger": final_deger,
                "getiri_pct": round((final_deger - sermaye) / sermaye * 100, 2),
            }
        except Exception as e:
            logger.error(f"Hızlı backtest hatası {sembol}: {e}")
            return {}
