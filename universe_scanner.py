"""
Johny — Universe Scanner
Tüm evreni tarar, en iyi fırsatları puanlar, Johny'ye bildirir
"""
import logging
import json
import os
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)

FIRSAT_DOSYASI = os.path.expanduser("~/Projects/johny/firsat_listesi.json")


def evren_tara(
    fiyat_verisi: Dict,
    teknik_veriler: Dict,
    gap_listesi: List[Dict] = None,
    rs_listesi: List[Dict] = None,
    short_squeeze_listesi: List[Dict] = None,
    kataliz_listesi: List[Dict] = None,
) -> List[Dict]:
    """
    Tüm verileri birleştir, puanla, en iyi fırsatları döndür.
    """
    puanlar = {}

    # Gap & Go puanları
    if gap_listesi:
        for g in gap_listesi:
            sembol = g.get("sembol")
            if sembol:
                puanlar.setdefault(sembol, {"puan": 0, "nedenler": []})
                gap_puan = min(g.get("gap_yuzde", 0) * 0.5, 3)
                puanlar[sembol]["puan"] += gap_puan
                puanlar[sembol]["nedenler"].append(f"Gap: %{g.get('gap_yuzde',0):.1f}")

    # Relative Strength puanları
    if rs_listesi:
        for r in rs_listesi:
            sembol = r.get("sembol")
            if sembol and r.get("rs_skoru", 0) > 1.3:
                puanlar.setdefault(sembol, {"puan": 0, "nedenler": []})
                puanlar[sembol]["puan"] += 2
                puanlar[sembol]["nedenler"].append(f"RS: {r.get('rs_skoru',0):.2f}")

    # Short Squeeze puanları
    if short_squeeze_listesi:
        for s in short_squeeze_listesi:
            sembol = s.get("sembol")
            if sembol:
                puanlar.setdefault(sembol, {"puan": 0, "nedenler": []})
                puanlar[sembol]["puan"] += 3
                puanlar[sembol]["nedenler"].append(f"Short Squeeze: %{s.get('short_float',0):.1f}")

    # Katalizör puanları
    if kataliz_listesi:
        for k in kataliz_listesi:
            sembol = k.get("sembol")
            if sembol:
                puanlar.setdefault(sembol, {"puan": 0, "nedenler": []})
                puanlar[sembol]["puan"] += k.get("puan", 1)
                puanlar[sembol]["nedenler"].append(f"Katalizör: {k.get('tur','')}")

    # Teknik analiz ekle
    for sembol, df in (teknik_veriler or {}).items():
        try:
            if df is not None and len(df) >= 20 and "RSI" in df.columns:
                rsi = float(df["RSI"].iloc[-1])
                fiyat = fiyat_verisi.get(sembol, {}).get("fiyat", 0)
                if fiyat > 0 and "MA20" in df.columns:
                    ma20 = float(df["MA20"].iloc[-1])
                    if 45 <= rsi <= 65 and fiyat > ma20:
                        puanlar.setdefault(sembol, {"puan": 0, "nedenler": []})
                        puanlar[sembol]["puan"] += 1
                        puanlar[sembol]["nedenler"].append(f"Teknik: RSI={rsi:.0f}, üst MA20")
        except:
            pass

    # Sırala ve en iyi 10'u al
    sirali = sorted(
        [{"sembol": k, "puan": round(v["puan"], 2), "nedenler": v["nedenler"]}
         for k, v in puanlar.items()],
        key=lambda x: x["puan"],
        reverse=True
    )[:10]

    # Dosyaya kaydet
    try:
        with open(FIRSAT_DOSYASI, "w", encoding="utf-8") as f:
            json.dump({
                "tarih": datetime.now().isoformat(),
                "firsatlar": sirali
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Fırsat dosyası kayıt hatası: {e}")

    if sirali:
        logger.info(f"🎯 Universe Scanner: En iyi fırsat → {sirali[0]['sembol']} ({sirali[0]['puan']:.1f} puan)")

    return sirali


def firsat_listesi_yukle() -> List[Dict]:
    """Kaydedilmiş fırsat listesini yükle"""
    try:
        if os.path.exists(FIRSAT_DOSYASI):
            with open(FIRSAT_DOSYASI, "r") as f:
                data = json.load(f)
                return data.get("firsatlar", [])
    except:
        pass
    return []
