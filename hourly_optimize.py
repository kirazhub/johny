"""
JOHNY — Saatlik Optimizasyon Script'i
Cron tarafından çalıştırılır. Telegram'a HİÇBİR ŞEY göndermez.
"""
import sys
import os
import logging
from datetime import datetime, timezone
import time
import json
from typing import Optional

# Proje dizinine ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import yfinance as yf

from johny_config import (
    US_SEMBOLLER, TEKNIK_PARAMETRELER, BACKTEST_PARAMETRELERI,
    POZITIF_HABERLER, NEGATIF_HABERLER, SEKTOR_GRUPLARI
)

# Logging — sadece dosyaya, Telegram YOK
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

LOG_DOSYASI = os.path.expanduser("~/Projects/johny/kontrol_log.txt")
ZAMAN_DAMGASI = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ─── Yardımcı ────────────────────────────────────────────────────────────────

def log_yaz(satir: str):
    print(satir)  # stdout


def hesapla_rsi(close: pd.Series, periyot: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_g = gain.ewm(com=periyot - 1, adjust=False).mean()
    avg_l = loss.ewm(com=periyot - 1, adjust=False).mean()
    rs = avg_g / (avg_l + 1e-10)
    return 100 - (100 / (1 + rs))


def hesapla_macd(close: pd.Series, hizli: int, yavas: int, sinyal: int):
    ema_h = close.ewm(span=hizli, adjust=False).mean()
    ema_y = close.ewm(span=yavas, adjust=False).mean()
    macd_line = ema_h - ema_y
    signal_line = macd_line.ewm(span=sinyal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def hesapla_ema(close: pd.Series, periyot: int) -> pd.Series:
    return close.ewm(span=periyot, adjust=False).mean()


# ─── 1. VERİ GÜNCELLEME ──────────────────────────────────────────────────────

def veri_guncelle(semboller: list) -> dict:
    """50 hissenin güncel verilerini yfinance ile çek"""
    sonuclar = {}
    basarili = 0
    hatali = 0

    # Toplu çekme — daha hızlı
    try:
        tickers = " ".join(semboller)
        data = yf.download(
            tickers,
            period="2y",
            interval="1d",
            group_by="ticker",
            auto_adjust=True,
            progress=False,
            threads=True,
        )

        for sembol in semboller:
            try:
                if len(semboller) == 1:
                    df = data
                else:
                    df = data[sembol] if sembol in data.columns.get_level_values(0) else None

                if df is None or (hasattr(df, 'empty') and df.empty):
                    hatali += 1
                    continue

                df = df.dropna()
                if len(df) < 30:
                    hatali += 1
                    continue

                son_fiyat = float(df["Close"].iloc[-1])
                onceki = float(df["Close"].iloc[-2]) if len(df) > 1 else son_fiyat
                degisim_pct = ((son_fiyat - onceki) / onceki * 100) if onceki > 0 else 0

                # Teknik göstergeler
                rsi = hesapla_rsi(df["Close"], 14)
                macd_line, signal_line, histogram = hesapla_macd(df["Close"], 12, 26, 9)
                ema20 = hesapla_ema(df["Close"], 20)
                ema50 = hesapla_ema(df["Close"], 50)

                son_rsi = float(rsi.iloc[-1]) if not rsi.empty else 50.0
                son_macd = float(macd_line.iloc[-1]) if not macd_line.empty else 0.0
                son_signal = float(signal_line.iloc[-1]) if not signal_line.empty else 0.0
                son_histogram = float(histogram.iloc[-1]) if not histogram.empty else 0.0
                son_ema20 = float(ema20.iloc[-1]) if not ema20.empty else son_fiyat
                son_ema50 = float(ema50.iloc[-1]) if not ema50.empty else son_fiyat

                # Trend durumu
                trend = "YUKARI" if son_ema20 > son_ema50 else "ASAGI"
                macd_durumu = "POZITIF" if son_histogram > 0 else "NEGATIF"

                hacim_ort = float(df["Volume"].tail(20).mean()) if "Volume" in df.columns else 0
                son_hacim = float(df["Volume"].iloc[-1]) if "Volume" in df.columns else 0
                hacim_orani = son_hacim / hacim_ort if hacim_ort > 0 else 1.0

                sonuclar[sembol] = {
                    "fiyat": round(son_fiyat, 2),
                    "degisim_pct": round(degisim_pct, 2),
                    "rsi": round(son_rsi, 1),
                    "macd": round(son_macd, 4),
                    "macd_signal": round(son_signal, 4),
                    "macd_histogram": round(son_histogram, 4),
                    "ema20": round(son_ema20, 2),
                    "ema50": round(son_ema50, 2),
                    "trend": trend,
                    "macd_durumu": macd_durumu,
                    "hacim_orani": round(hacim_orani, 2),
                    "veri_gunleri": len(df),
                    "df": df,  # backtest için sakla
                }
                basarili += 1
            except Exception as e:
                hatali += 1
    except Exception as e:
        log_yaz(f"[HATA] Toplu veri çekme: {e}")
        # Tek tek dene
        for sembol in semboller[:10]:
            try:
                ticker = yf.Ticker(sembol)
                df = ticker.history(period="6mo", interval="1d")
                df = df.dropna()
                if len(df) >= 30:
                    sonuclar[sembol] = {"fiyat": float(df["Close"].iloc[-1]), "df": df}
                    basarili += 1
            except Exception:
                hatali += 1

    return {"veriler": sonuclar, "basarili": basarili, "hatali": hatali}


# ─── 2. BACKTEST & OPTİMİZASYON ─────────────────────────────────────────────

def rsi_backtest(df: pd.DataFrame, periyot: int, aa: int, asat: int) -> float:
    """RSI stratejisi — toplam getiri % döndür"""
    try:
        close = df["Close"]
        if len(close) < periyot + 10:
            return -999.0
        rsi = hesapla_rsi(close, periyot)
        pozisyon = 0
        nakit = 1000.0
        hisse = 0.0
        for i in range(periyot, len(close)):
            fiyat = float(close.iloc[i])
            r = float(rsi.iloc[i])
            if r < asat and pozisyon == 0 and nakit > fiyat:
                hisse = nakit / fiyat
                nakit = 0.0
                pozisyon = 1
            elif r > aa and pozisyon == 1:
                nakit = hisse * fiyat
                hisse = 0.0
                pozisyon = 0
        son_deger = nakit + hisse * float(close.iloc[-1])
        return round((son_deger - 1000.0) / 1000.0 * 100, 2)
    except Exception:
        return -999.0


def macd_backtest(df: pd.DataFrame, hizli: int, yavas: int, sinyal: int) -> float:
    """MACD stratejisi — toplam getiri % döndür"""
    try:
        close = df["Close"]
        if len(close) < yavas + 20:
            return -999.0
        macd_line, signal_line, _ = hesapla_macd(close, hizli, yavas, sinyal)
        pozisyon = 0
        nakit = 1000.0
        hisse = 0.0
        for i in range(yavas, len(close)):
            fiyat = float(close.iloc[i])
            m = float(macd_line.iloc[i])
            s = float(signal_line.iloc[i])
            m_prev = float(macd_line.iloc[i - 1])
            s_prev = float(signal_line.iloc[i - 1])
            # Golden cross
            if m_prev < s_prev and m > s and pozisyon == 0 and nakit > fiyat:
                hisse = nakit / fiyat
                nakit = 0.0
                pozisyon = 1
            # Death cross
            elif m_prev > s_prev and m < s and pozisyon == 1:
                nakit = hisse * fiyat
                hisse = 0.0
                pozisyon = 0
        son_deger = nakit + hisse * float(close.iloc[-1])
        return round((son_deger - 1000.0) / 1000.0 * 100, 2)
    except Exception:
        return -999.0


def ma_backtest(df: pd.DataFrame, kisa: int, uzun: int) -> float:
    """MA crossover stratejisi — toplam getiri % döndür"""
    try:
        close = df["Close"]
        if len(close) < uzun + 10:
            return -999.0
        ema_k = hesapla_ema(close, kisa)
        ema_u = hesapla_ema(close, uzun)
        pozisyon = 0
        nakit = 1000.0
        hisse = 0.0
        for i in range(uzun, len(close)):
            fiyat = float(close.iloc[i])
            k = float(ema_k.iloc[i])
            u = float(ema_u.iloc[i])
            k_p = float(ema_k.iloc[i - 1])
            u_p = float(ema_u.iloc[i - 1])
            if k_p < u_p and k > u and pozisyon == 0 and nakit > fiyat:
                hisse = nakit / fiyat
                nakit = 0.0
                pozisyon = 1
            elif k_p > u_p and k < u and pozisyon == 1:
                nakit = hisse * fiyat
                hisse = 0.0
                pozisyon = 0
        son_deger = nakit + hisse * float(close.iloc[-1])
        return round((son_deger - 1000.0) / 1000.0 * 100, 2)
    except Exception:
        return -999.0


def hesapla_max_drawdown(deger_serisi: list) -> float:
    """Verilen sermaye serisinden maksimum drawdown % hesapla"""
    if len(deger_serisi) < 2:
        return 0.0
    tepe = deger_serisi[0]
    max_dd = 0.0
    for deger in deger_serisi:
        if deger > tepe:
            tepe = deger
        dd = (tepe - deger) / tepe if tepe > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    return round(max_dd * 100, 2)


def rsi_backtest_detayli(df: pd.DataFrame, periyot: int, aa: int, asat: int) -> dict:
    """RSI backtest — getiri + max drawdown döndür"""
    try:
        close = df["Close"]
        if len(close) < periyot + 10:
            return {"getiri": -999.0, "max_dd": 0.0}
        rsi = hesapla_rsi(close, periyot)
        pozisyon = 0
        nakit = 1000.0
        hisse = 0.0
        sermaye_serisi = [nakit]
        for i in range(periyot, len(close)):
            fiyat = float(close.iloc[i])
            r = float(rsi.iloc[i])
            if r < asat and pozisyon == 0 and nakit > fiyat:
                hisse = nakit / fiyat
                nakit = 0.0
                pozisyon = 1
            elif r > aa and pozisyon == 1:
                nakit = hisse * fiyat
                hisse = 0.0
                pozisyon = 0
            sermaye_serisi.append(nakit + hisse * fiyat)
        son_deger = nakit + hisse * float(close.iloc[-1])
        getiri = round((son_deger - 1000.0) / 1000.0 * 100, 2)
        return {"getiri": getiri, "max_dd": hesapla_max_drawdown(sermaye_serisi)}
    except Exception:
        return {"getiri": -999.0, "max_dd": 0.0}


def backtest_sonuc_kaydet(sonuclar: dict, dosya_adi: Optional[str] = None) -> str:
    """Backtest sonuçlarını backtest/ klasörüne JSON olarak kaydet"""
    import json
    backtest_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backtest")
    os.makedirs(backtest_dir, exist_ok=True)
    if dosya_adi is None:
        zaman = datetime.now().strftime("%Y%m%d_%H%M%S")
        dosya_adi = f"optimize_{zaman}.json"
    yol = os.path.join(backtest_dir, dosya_adi)
    # Son N dosyayı tut (50'den fazlaysa eskilerini sil)
    mevcut = sorted([
        f for f in os.listdir(backtest_dir)
        if f.startswith("optimize_") and f.endswith(".json")
    ])
    if len(mevcut) >= 50:
        for eski in mevcut[:len(mevcut) - 49]:
            try:
                os.remove(os.path.join(backtest_dir, eski))
            except Exception:
                pass
    try:
        with open(yol, "w", encoding="utf-8") as f:
            json.dump(sonuclar, f, ensure_ascii=False, indent=2, default=str)
        return yol
    except Exception as e:
        return f"HATA: {e}"


def optimizasyon_calistir(veriler: dict) -> dict:
    """SPY benchmark üzerinde grid search"""
    # SPY üzerinde optimize et (benchmark)
    spy_df = veriler.get("SPY", {}).get("df")
    qqq_df = veriler.get("QQQ", {}).get("df")
    nvda_df = veriler.get("NVDA", {}).get("df")

    # Referans hisseler — likit ve volatil olanlar
    test_sembolleri = ["SPY", "QQQ", "NVDA", "AAPL", "MSFT"]
    test_dfs = [veriler.get(s, {}).get("df") for s in test_sembolleri]
    test_dfs = [df for df in test_dfs if df is not None]

    if not test_dfs:
        return {"hata": "Yeterli veri yok"}

    # RSI Grid Search
    rsi_params = [(10, 65, 25), (10, 70, 25), (10, 70, 30), (10, 75, 30),
                  (14, 65, 25), (14, 65, 30), (14, 70, 25), (14, 70, 30), (14, 70, 35),
                  (14, 75, 25), (14, 75, 30), (21, 65, 25), (21, 70, 30), (21, 75, 35)]

    rsi_en_iyi = {"params": None, "ort_getiri": -999.0, "ort_max_dd": 0.0}
    rsi_sonuclar = []
    for (periyot, aa, asat) in rsi_params:
        getiriler = []
        drawdownlar = []
        for df in test_dfs:
            sonuc = rsi_backtest_detayli(df, periyot, aa, asat)
            if sonuc["getiri"] > -999:
                getiriler.append(sonuc["getiri"])
                drawdownlar.append(sonuc["max_dd"])
        if getiriler:
            ort = round(sum(getiriler) / len(getiriler), 2)
            ort_dd = round(sum(drawdownlar) / len(drawdownlar), 2) if drawdownlar else 0.0
            rsi_sonuclar.append({
                "params": {"periyot": periyot, "aa": aa, "asat": asat},
                "ort_getiri": ort,
                "ort_max_dd": ort_dd,
            })
            if ort > rsi_en_iyi["ort_getiri"]:
                rsi_en_iyi = {
                    "params": {"periyot": periyot, "aa": aa, "asat": asat},
                    "ort_getiri": ort,
                    "ort_max_dd": ort_dd,
                }

    rsi_sonuclar.sort(key=lambda x: x["ort_getiri"], reverse=True)

    # MACD Grid Search
    macd_params = [(8, 21, 5), (10, 22, 7), (12, 26, 9), (12, 26, 7), (8, 17, 9),
                   (10, 26, 9), (12, 30, 9), (15, 30, 10)]

    macd_en_iyi = {"params": None, "ort_getiri": -999.0}
    macd_sonuclar = []
    for (h, y, s) in macd_params:
        getiriler = []
        for df in test_dfs:
            g = macd_backtest(df, h, y, s)
            if g > -999:
                getiriler.append(g)
        if getiriler:
            ort = round(sum(getiriler) / len(getiriler), 2)
            macd_sonuclar.append({"params": {"hizli": h, "yavas": y, "sinyal": s}, "ort_getiri": ort})
            if ort > macd_en_iyi["ort_getiri"]:
                macd_en_iyi = {"params": {"hizli": h, "yavas": y, "sinyal": s}, "ort_getiri": ort}

    macd_sonuclar.sort(key=lambda x: x["ort_getiri"], reverse=True)

    # MA Crossover Grid Search
    ma_params = [(9, 21), (9, 50), (10, 30), (20, 50), (20, 100), (21, 55), (50, 200)]
    ma_en_iyi = {"params": None, "ort_getiri": -999.0}
    ma_sonuclar = []
    for (k, u) in ma_params:
        getiriler = []
        for df in test_dfs:
            g = ma_backtest(df, k, u)
            if g > -999:
                getiriler.append(g)
        if getiriler:
            ort = round(sum(getiriler) / len(getiriler), 2)
            ma_sonuclar.append({"params": {"kisa": k, "uzun": u}, "ort_getiri": ort})
            if ort > ma_en_iyi["ort_getiri"]:
                ma_en_iyi = {"params": {"kisa": k, "uzun": u}, "ort_getiri": ort}

    ma_sonuclar.sort(key=lambda x: x["ort_getiri"], reverse=True)

    return {
        "rsi": {"en_iyi": rsi_en_iyi, "top5": rsi_sonuclar[:5]},
        "macd": {"en_iyi": macd_en_iyi, "top5": macd_sonuclar[:5]},
        "ma": {"en_iyi": ma_en_iyi, "top5": ma_sonuclar[:5]},
        "test_sembolleri": test_sembolleri,
    }


# ─── 3. HABER TARAMA ─────────────────────────────────────────────────────────

def haber_tara() -> dict:
    """Yahoo Finance üzerinden ABD/global haberleri tara"""
    onemli_haberler = []
    pozitif_sayac = 0
    negatif_sayac = 0
    notr_sayac = 0

    izleme_sembolleri = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "TSLA", "JPM", "AMZN"]
    macro_keywords = ["fed", "federal reserve", "inflation", "cpi", "ppi", "interest rate",
                      "earnings", "gdp", "unemployment", "fomc", "powell", "treasury",
                      "tariff", "trade war", "recession", "soft landing", "rate cut", "rate hike",
                      "q1 earnings", "q2 earnings", "guidance", "revenue beat", "eps beat"]

    tum_haberler = []
    for sembol in izleme_sembolleri:
        try:
            ticker = yf.Ticker(sembol)
            news = ticker.news or []
            for item in news[:8]:
                baslik = item.get("title", "")
                if baslik:
                    tum_haberler.append({
                        "sembol": sembol,
                        "baslik": baslik,
                        "kaynak": item.get("publisher", "Yahoo"),
                        "zaman": item.get("providerPublishTime", 0),
                        "link": item.get("link", ""),
                    })
        except Exception:
            pass
        time.sleep(0.2)

    # Tekrarlanan haberleri temizle
    gorulen_basliklar = set()
    tekil_haberler = []
    for h in tum_haberler:
        baslik_kisa = h["baslik"][:60].lower()
        if baslik_kisa not in gorulen_basliklar:
            gorulen_basliklar.add(baslik_kisa)
            tekil_haberler.append(h)

    # Analiz
    for h in tekil_haberler:
        baslik_lower = h["baslik"].lower()
        sinyal_skoru = 0

        for kw in POZITIF_HABERLER:
            if kw.lower() in baslik_lower:
                sinyal_skoru += 1
        for kw in NEGATIF_HABERLER:
            if kw.lower() in baslik_lower:
                sinyal_skoru -= 1

        # Macro kontrol
        is_macro = any(kw in baslik_lower for kw in macro_keywords)
        onem = "YUKSEK" if is_macro or abs(sinyal_skoru) >= 2 else "NORMAL"

        h["sinyal"] = "POZITIF" if sinyal_skoru > 0 else "NEGATIF" if sinyal_skoru < 0 else "NOTR"
        h["sinyal_skoru"] = sinyal_skoru
        h["macro"] = is_macro
        h["onem"] = onem

        if sinyal_skoru > 0:
            pozitif_sayac += 1
        elif sinyal_skoru < 0:
            negatif_sayac += 1
        else:
            notr_sayac += 1

        if onem == "YUKSEK":
            onemli_haberler.append(h)

    # Zaman sırala
    tekil_haberler.sort(key=lambda x: x.get("zaman", 0), reverse=True)
    onemli_haberler.sort(key=lambda x: x.get("zaman", 0), reverse=True)

    toplam = len(tekil_haberler)
    sentiment_skoru = (pozitif_sayac - negatif_sayac) / max(toplam, 1) * 100

    return {
        "toplam_haber": toplam,
        "pozitif": pozitif_sayac,
        "negatif": negatif_sayac,
        "notr": notr_sayac,
        "sentiment_skoru": round(sentiment_skoru, 1),
        "piyasa_duygu": "BULLISH" if sentiment_skoru > 10 else "BEARISH" if sentiment_skoru < -10 else "NOTR",
        "onemli_haberler": onemli_haberler[:10],
        "son_haberler": tekil_haberler[:15],
    }


# ─── 4. CONFIG GÜNCELLEME ────────────────────────────────────────────────────

def config_guncelle(opt_sonuclari: dict):
    """johny_config.py'deki TEKNIK_PARAMETRELER'i güncelle"""
    config_path = os.path.expanduser("~/Projects/johny/johny_config.py")

    rsi_en_iyi = opt_sonuclari.get("rsi", {}).get("en_iyi", {})
    macd_en_iyi = opt_sonuclari.get("macd", {}).get("en_iyi", {})
    ma_en_iyi = opt_sonuclari.get("ma", {}).get("en_iyi", {})

    if not rsi_en_iyi.get("params") or not macd_en_iyi.get("params") or not ma_en_iyi.get("params"):
        return False, "Optimizasyon sonuçları eksik"

    rsi_p = rsi_en_iyi["params"]
    macd_p = macd_en_iyi["params"]
    ma_p = ma_en_iyi["params"]

    yeni_teknik = f'''# ─── Teknik Gösterge Parametreleri ──────────────────────────────────────────
# Son güncelleme: {ZAMAN_DAMGASI} (otomatik optimizasyon)
# RSI en iyi getiri: {rsi_en_iyi["ort_getiri"]}% | MACD: {macd_en_iyi["ort_getiri"]}% | MA: {ma_en_iyi["ort_getiri"]}%
TEKNIK_PARAMETRELER = {{
    "rsi_periyot": {rsi_p["periyot"]},
    "rsi_asiri_alim": {rsi_p["aa"]},
    "rsi_asiri_satim": {rsi_p["asat"]},
    "macd_hizli": {macd_p["hizli"]},
    "macd_yavas": {macd_p["yavas"]},
    "macd_sinyal": {macd_p["sinyal"]},
    "bb_periyot": 20,
    "bb_std": 2.0,
    "ema_kisa": {ma_p["kisa"]},
    "ema_orta": 21,
    "ema_uzun": {ma_p["uzun"]},
    "ema_cok_uzun": 200,
    "hacim_ma_periyot": 20,
    "atr_periyot": 14,
}}'''

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            icerik = f.read()

        # Mevcut TEKNIK_PARAMETRELER bloğunu değiştir
        import re
        # Yorum satırından dict kapanışına kadar
        pattern = r"# ─── Teknik Gösterge Parametreleri.*?^}\s*$"
        yeni_icerik = re.sub(pattern, yeni_teknik, icerik, flags=re.DOTALL | re.MULTILINE)

        if yeni_icerik == icerik:
            # Pattern bulunamadı, dict'i doğrudan değiştir
            pattern2 = r"TEKNIK_PARAMETRELER\s*=\s*\{[^}]*\}"
            yeni_icerik = re.sub(pattern2, yeni_teknik, icerik, flags=re.DOTALL)

        with open(config_path, "w", encoding="utf-8") as f:
            f.write(yeni_icerik)

        return True, "Config başarıyla güncellendi"
    except Exception as e:
        return False, f"Config güncelleme hatası: {e}"


# ─── 5. PIYASA ÖZET ──────────────────────────────────────────────────────────

def piyasa_ozet_olustur(veriler: dict) -> dict:
    """Tüm hisseler için piyasa özeti"""
    if not veriler:
        return {}

    tum_degisimler = [v["degisim_pct"] for v in veriler.values() if "degisim_pct" in v]
    yukselenler = [s for s, v in veriler.items() if v.get("degisim_pct", 0) > 0]
    dusenler = [s for s, v in veriler.items() if v.get("degisim_pct", 0) < 0]

    # RSI aşırı alım/satım
    asiri_alim = [(s, round(v["rsi"], 1)) for s, v in veriler.items()
                  if v.get("rsi", 50) >= 70]
    asiri_satim = [(s, round(v["rsi"], 1)) for s, v in veriler.items()
                   if v.get("rsi", 50) <= 30]

    # MACD pozitif/negatif
    macd_pozitif = [s for s, v in veriler.items() if v.get("macd_durumu") == "POZITIF"]

    # En güçlü/zayıf
    siralanan = sorted(veriler.items(), key=lambda x: x[1].get("degisim_pct", 0), reverse=True)
    en_guclu = siralanan[:5]
    en_zayif = siralanan[-5:]

    # Sektörel performans
    sektor_performans = {}
    for sektor, semboller in SEKTOR_GRUPLARI.items():
        sektor_degisimler = [veriler[s]["degisim_pct"] for s in semboller if s in veriler and "degisim_pct" in veriler[s]]
        if sektor_degisimler:
            sektor_performans[sektor] = round(sum(sektor_degisimler) / len(sektor_degisimler), 2)

    ort_degisim = round(sum(tum_degisimler) / len(tum_degisimler), 2) if tum_degisimler else 0

    return {
        "toplam_sembol": len(veriler),
        "yukselenler": len(yukselenler),
        "dusenler": len(dusenler),
        "ort_degisim_pct": ort_degisim,
        "asiri_alim": asiri_alim,
        "asiri_satim": asiri_satim,
        "macd_pozitif_sayisi": len(macd_pozitif),
        "en_guclu": [(s, round(v.get("degisim_pct", 0), 2)) for s, v in en_guclu],
        "en_zayif": [(s, round(v.get("degisim_pct", 0), 2)) for s, v in en_zayif],
        "sektor_performans": sektor_performans,
    }


# ─── ANA FONKSİYON ───────────────────────────────────────────────────────────

def main():
    baslangic = time.time()
    log_satirlari = []

    def satir(s=""):
        log_satirlari.append(s)

    satir("=" * 70)
    satir(f"JOHNY — SAATLİK OPTİMİZASYON RAPORU")
    satir(f"Tarih/Saat (İstanbul): {ZAMAN_DAMGASI}")
    satir(f"Çalıştırma: Otomatik Cron")
    satir("=" * 70)

    # 1. Veri güncelleme
    satir("")
    satir("─── 1. VERİ GÜNCELLEME ─────────────────────────────────────────────")
    veri_basla = time.time()
    veri_sonucu = veri_guncelle(US_SEMBOLLER)
    veriler = veri_sonucu["veriler"]
    veri_sure = round(time.time() - veri_basla, 1)

    satir(f"  Sembol sayısı: {len(US_SEMBOLLER)}")
    satir(f"  Başarılı: {veri_sonucu['basarili']} | Hatalı: {veri_sonucu['hatali']}")
    satir(f"  Süre: {veri_sure}s")

    # Piyasa özeti
    ozet = piyasa_ozet_olustur(veriler)
    if ozet:
        satir(f"  Yükselenler: {ozet['yukselenler']} | Düşenler: {ozet['dusenler']}")
        satir(f"  Ort. Değişim: {ozet['ort_degisim_pct']:+.2f}%")

        if ozet.get("en_guclu"):
            satir(f"  En Güçlü 5: " + " | ".join([f"{s}({d:+.1f}%)" for s, d in ozet["en_guclu"]]))
        if ozet.get("en_zayif"):
            satir(f"  En Zayıf 5: " + " | ".join([f"{s}({d:+.1f}%)" for s, d in ozet["en_zayif"]]))

        if ozet.get("asiri_alim"):
            satir(f"  RSI Aşırı Alım (≥70): " + " ".join([f"{s}({r})" for s, r in ozet["asiri_alim"][:6]]))
        if ozet.get("asiri_satim"):
            satir(f"  RSI Aşırı Satım (≤30): " + " ".join([f"{s}({r})" for s, r in ozet["asiri_satim"][:6]]))

        satir(f"  MACD Pozitif: {ozet['macd_pozitif_sayisi']} hisse")

        if ozet.get("sektor_performans"):
            satir("  Sektörel Performans:")
            for sektor, perf in sorted(ozet["sektor_performans"].items(), key=lambda x: x[1], reverse=True):
                bar = "▲" if perf > 0 else "▼"
                satir(f"    {bar} {sektor:<20} {perf:+.2f}%")

        # Bireysel hisse detayı (önemli olanlar)
        satir("")
        satir("  Temel Göstergeler (Seçili Hisseler):")
        kritik_semboller = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "META", "JPM"]
        satir(f"  {'Sembol':<8} {'Fiyat':>8} {'Değ%':>7} {'RSI':>6} {'MACD':>10} {'Trend':>7}")
        satir(f"  {'-'*55}")
        for s in kritik_semboller:
            if s in veriler:
                v = veriler[s]
                satir(f"  {s:<8} {v['fiyat']:>8.2f} {v.get('degisim_pct', 0):>+7.2f}% {v.get('rsi', 0):>6.1f} {v.get('macd_histogram', 0):>+10.4f} {v.get('trend', '?'):>7}")

    # 2. Backtest & Optimizasyon
    satir("")
    satir("─── 2. BACKTEST & OPTİMİZASYON ────────────────────────────────────")
    opt_basla = time.time()

    opt_sonuclari = {}
    if len(veriler) >= 3:
        opt_sonuclari = optimizasyon_calistir(veriler)
        opt_sure = round(time.time() - opt_basla, 1)
        satir(f"  Test sembolleri: {', '.join(opt_sonuclari.get('test_sembolleri', []))}")
        satir(f"  Süre: {opt_sure}s")

        # RSI Sonuçları
        if opt_sonuclari.get("rsi", {}).get("en_iyi", {}).get("params"):
            rsi = opt_sonuclari["rsi"]
            p = rsi["en_iyi"]["params"]
            satir(f"")
        satir(f"  RSI En İyi Parametreler:")
        if opt_sonuclari.get("rsi", {}).get("top5"):
            for i, r in enumerate(opt_sonuclari["rsi"]["top5"], 1):
                p = r["params"]
                marker = "★" if i == 1 else " "
                satir(f"    {marker} #{i} Periyot:{p['periyot']} AA:{p['aa']} AS:{p['asat']} → Getiri: {r['ort_getiri']:+.2f}%")

        satir(f"")
        satir(f"  MACD En İyi Parametreler:")
        if opt_sonuclari.get("macd", {}).get("top5"):
            for i, r in enumerate(opt_sonuclari["macd"]["top5"], 1):
                p = r["params"]
                marker = "★" if i == 1 else " "
                satir(f"    {marker} #{i} H:{p['hizli']} Y:{p['yavas']} S:{p['sinyal']} → Getiri: {r['ort_getiri']:+.2f}%")

        satir(f"")
        satir(f"  MA Crossover En İyi Parametreler:")
        if opt_sonuclari.get("ma", {}).get("top5"):
            for i, r in enumerate(opt_sonuclari["ma"]["top5"], 1):
                p = r["params"]
                marker = "★" if i == 1 else " "
                satir(f"    {marker} #{i} Kısa:{p['kisa']} Uzun:{p['uzun']} → Getiri: {r['ort_getiri']:+.2f}%")

        # Config güncelleme
        satir("")
        basari, mesaj = config_guncelle(opt_sonuclari)
        satir(f"  johny_config.py → {'✓ ' + mesaj if basari else '✗ ' + mesaj}")

        # Backtest sonuçlarını kaydet
        backtest_kayit = {
            "zaman": ZAMAN_DAMGASI,
            "optimizasyon": opt_sonuclari,
            "piyasa_ozeti": ozet if 'ozet' in dir() else {},
        }
        kayit_yolu = backtest_sonuc_kaydet(backtest_kayit)
        satir(f"  Backtest kayıt → {kayit_yolu}")

        # Özet
        rsi_g = opt_sonuclari.get("rsi", {}).get("en_iyi", {}).get("ort_getiri", 0)
        macd_g = opt_sonuclari.get("macd", {}).get("en_iyi", {}).get("ort_getiri", 0)
        ma_g = opt_sonuclari.get("ma", {}).get("en_iyi", {}).get("ort_getiri", 0)
        en_iyi_strateji = max([("RSI", rsi_g), ("MACD", macd_g), ("MA", ma_g)], key=lambda x: x[1])
        satir(f"  En İyi Strateji: {en_iyi_strateji[0]} ({en_iyi_strateji[1]:+.2f}%)")
    else:
        satir(f"  [UYARI] Yeterli veri yok, optimizasyon atlandı (mevcut: {len(veriler)})")

    # 3. Haber Tarama
    satir("")
    satir("─── 3. HABER TARAMA ────────────────────────────────────────────────")
    haber_basla = time.time()
    haber_sonucu = haber_tara()
    haber_sure = round(time.time() - haber_basla, 1)

    satir(f"  Toplam haber: {haber_sonucu['toplam_haber']} | Süre: {haber_sure}s")
    satir(f"  Sentiment → Pozitif: {haber_sonucu['pozitif']} | Negatif: {haber_sonucu['negatif']} | Nötr: {haber_sonucu['notr']}")
    satir(f"  Piyasa Duygu: {haber_sonucu['piyasa_duygu']} (Skor: {haber_sonucu['sentiment_skoru']:+.1f})")

    if haber_sonucu.get("onemli_haberler"):
        satir(f"")
        satir(f"  ⚡ Önemli/Macro Haberler ({len(haber_sonucu['onemli_haberler'])} adet):")
        for h in haber_sonucu["onemli_haberler"][:8]:
            durum = "+" if h["sinyal"] == "POZITIF" else "-" if h["sinyal"] == "NEGATIF" else "~"
            macro_tag = "[MACRO] " if h.get("macro") else ""
            satir(f"    [{durum}] {macro_tag}{h['baslik'][:80]}")
            satir(f"        Kaynak: {h['kaynak']} | İlgili: {h['sembol']}")

    satir("")
    satir(f"  Son Haberler ({min(len(haber_sonucu['son_haberler']), 10)} adet):")
    for h in haber_sonucu.get("son_haberler", [])[:10]:
        durum = "+" if h["sinyal"] == "POZITIF" else "-" if h["sinyal"] == "NEGATIF" else "~"
        satir(f"    [{durum}] {h['baslik'][:75]}")

    # Özet & Süre
    toplam_sure = round(time.time() - baslangic, 1)
    satir("")
    satir("─── ÖZET ───────────────────────────────────────────────────────────")
    satir(f"  Toplam süre: {toplam_sure}s")
    satir(f"  Veri: ✓ ({veri_sonucu['basarili']}/{len(US_SEMBOLLER)} sembol)")
    if opt_sonuclari:
        satir(f"  Backtest: ✓ (RSI/MACD/MA grid search tamamlandı)")
    satir(f"  Haberler: ✓ ({haber_sonucu['toplam_haber']} haber, {haber_sonucu['piyasa_duygu']})")
    satir(f"  Config: {'✓ Güncellendi' if opt_sonuclari else '— Atlandı'}")
    satir(f"  Telegram: ✗ (Devre dışı — sadece dosyaya log)")
    satir("")
    satir(f"  Durum: TAMAMLANDI ✓")
    satir("=" * 70)

    # Dosyaya yaz — başa ekle (en son log en üstte)
    try:
        mevcut = ""
        if os.path.exists(LOG_DOSYASI):
            with open(LOG_DOSYASI, "r", encoding="utf-8") as f:
                mevcut = f.read()
            # Çok büyürse son 50 bloğu tut
            bloklar = mevcut.split("=" * 70)
            if len(bloklar) > 100:
                mevcut = ("=" * 70).join(bloklar[-50:])

        yeni_log = "\n".join(log_satirlari) + "\n\n"
        with open(LOG_DOSYASI, "w", encoding="utf-8") as f:
            f.write(yeni_log + mevcut)

        print(f"[OK] Log yazıldı: {LOG_DOSYASI}")
    except Exception as e:
        print(f"[HATA] Log yazma hatası: {e}")


if __name__ == "__main__":
    main()
