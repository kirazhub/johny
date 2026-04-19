"""
Johny — Canlı ABD Borsa Haber İzleyici
Her 5 dakikada S&P 500 / NASDAQ haberlerini çeker
"""
import logging
import time
import requests
import sqlite3
from datetime import datetime
from xml.etree import ElementTree as ET
from typing import List, Optional

logger = logging.getLogger("johny_haberler")

HISSE_ANAHTAR = {
    "AAPL": ["Apple", "AAPL", "iPhone", "Tim Cook"],
    "MSFT": ["Microsoft", "MSFT", "Azure", "Satya Nadella"],
    "NVDA": ["Nvidia", "NVDA", "GPU", "Jensen Huang"],
    "GOOGL": ["Google", "Alphabet", "GOOGL"],
    "AMZN": ["Amazon", "AMZN", "AWS"],
    "META": ["Meta", "Facebook", "Instagram", "Zuckerberg"],
    "TSLA": ["Tesla", "TSLA", "Elon Musk"],
    "JPM": ["JPMorgan", "JPM"],
    "BAC": ["Bank of America", "BAC"],
    "XOM": ["ExxonMobil", "Exxon", "XOM"],
    "WMT": ["Walmart", "WMT"],
    "COST": ["Costco", "COST"],
    "NFLX": ["Netflix", "NFLX"],
    "AMD": ["AMD", "Advanced Micro"],
}

HABER_KAYNAKLARI = [
    # Yahoo Finance
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US",
    # Google News - Genel piyasa
    "https://news.google.com/rss/search?q=S%26P500+stocks+market&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=NASDAQ+tech+stocks+earnings&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Fed+interest+rate+stocks+2026&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Wall+Street+market+today&hl=en&gl=US&ceid=US:en",
    # NTV Ekonomi (Turkiye kokenli ABD haberleri)
    "https://news.google.com/rss/search?q=NTV+Wall+Street+economy&hl=en&gl=US&ceid=US:en",
    # Bloomberg
    "https://news.google.com/rss/search?q=Bloomberg+stocks+earnings+Fed&hl=en&gl=US&ceid=US:en",
    # Reuters
    "https://news.google.com/rss/search?q=Reuters+stocks+market+economy&hl=en&gl=US&ceid=US:en",
    # CNBC
    "https://news.google.com/rss/search?q=CNBC+market+stocks+today&hl=en&gl=US&ceid=US:en",
    # Kazanc aciklamalari
    "https://news.google.com/rss/search?q=earnings+report+beat+miss+2026&hl=en&gl=US&ceid=US:en",
]


def hisse_eslestir(baslik: str) -> Optional[str]:
    baslik_lower = baslik.lower()
    for sembol, kelimeler in HISSE_ANAHTAR.items():
        for k in kelimeler:
            if k.lower() in baslik_lower:
                return sembol
    return None


def haber_cek(kaynak: str) -> List[dict]:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
        r = requests.get(kaynak, headers=headers, timeout=10)
        if r.status_code != 200:
            return []
        root = ET.fromstring(r.content)
        haberler = []
        for item in root.findall(".//item"):
            baslik = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            pub_date = item.findtext("pubDate", "")
            tarih = datetime.now().strftime("%Y-%m-%d %H:%M")
            if pub_date:
                try:
                    from email.utils import parsedate_to_datetime
                    tarih = parsedate_to_datetime(pub_date).strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            if baslik and link:
                haberler.append({"baslik": baslik, "url": link, "tarih": tarih,
                                  "hisse": hisse_eslestir(baslik)})
        return haberler
    except Exception as e:
        logger.debug(f"Haber hatası: {e}")
        return []


def haberleri_db_kaydet(haberler: List[dict], db_path: str = "johny_data.db"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS us_haberler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            baslik TEXT,
            url TEXT UNIQUE,
            tarih TEXT,
            hisse TEXT,
            okundu INTEGER DEFAULT 0
        )
    """)
    eklendi = 0
    for h in haberler:
        try:
            c.execute(
                "INSERT OR IGNORE INTO us_haberler (baslik, url, tarih, hisse) VALUES (?,?,?,?)",
                (h["baslik"], h["url"], h["tarih"], h.get("hisse"))
            )
            if c.rowcount > 0:
                eklendi += 1
        except:
            pass
    conn.commit()
    conn.close()
    return eklendi


def haber_turu_calistir(db_path: str = "johny_data.db"):
    tum_haberler = []
    for kaynak in HABER_KAYNAKLARI:
        haberler = haber_cek(kaynak)
        tum_haberler.extend(haberler)
        time.sleep(0.5)

    eklendi = haberleri_db_kaydet(tum_haberler, db_path)
    if eklendi > 0:
        logger.info(f"📰 {eklendi} yeni ABD haberi eklendi")
        hisseli = [h for h in tum_haberler if h.get("hisse")]
        for h in hisseli[:5]:
            logger.info(f"  📌 {h['hisse']}: {h['baslik'][:60]}")
    return eklendi
