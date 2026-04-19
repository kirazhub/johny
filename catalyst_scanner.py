"""
Johny — Catalyst Scanner
FDA onayları, birleşmeler, büyük sözleşmeler — hisse fırlatıcı haberler
"""
import logging
import requests
import sqlite3
import os
from datetime import datetime
from xml.etree import ElementTree as ET
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

KATALIZ_KELIMELER = {
    "FDA": ["FDA approval", "FDA approved", "FDA grants", "NDA approval", "BLA approval"],
    "BIRLESME": ["merger", "acquisition", "takeover", "buyout", "deal announced"],
    "SOZLESME": ["contract awarded", "contract won", "major contract", "partnership agreement"],
    "KAZANC": ["earnings beat", "revenue beat", "raised guidance", "record revenue"],
    "BUYUME": ["expansion", "new product", "product launch", "market entry"],
}

KATALIZ_PUANLARI = {
    "FDA": 5,
    "BIRLESME": 4,
    "SOZLESME": 3,
    "KAZANC": 3,
    "BUYUME": 2,
}

RSS_KAYNAKLAR = [
    "https://news.google.com/rss/search?q=FDA+approval+stock&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=merger+acquisition+deal+2026&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=earnings+beat+revenue+record&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=major+contract+awarded+stock&hl=en&gl=US&ceid=US:en",
]

DB_PATH = os.path.expanduser("~/Projects/johny/johny_data.db")


def haber_cek(url: str) -> List[dict]:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return []
        root = ET.fromstring(r.content)
        haberler = []
        for item in root.findall(".//item"):
            baslik = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            if baslik and link:
                haberler.append({"baslik": baslik, "url": link})
        return haberler
    except:
        return []


def kataliz_turu_bul(baslik: str) -> Optional[str]:
    baslik_lower = baslik.lower()
    for tur, kelimeler in KATALIZ_KELIMELER.items():
        for kelime in kelimeler:
            if kelime.lower() in baslik_lower:
                return tur
    return None


def sembol_bul(baslik: str, semboller: List[str]) -> Optional[str]:
    for s in semboller:
        if s in baslik.upper():
            return s
    return None


def katalizor_tara(semboller: List[str]) -> List[Dict]:
    tum_haberler = []
    for kaynak in RSS_KAYNAKLAR:
        haberler = haber_cek(kaynak)
        for h in haberler:
            tur = kataliz_turu_bul(h["baslik"])
            if tur:
                sembol = sembol_bul(h["baslik"], semboller)
                puan = KATALIZ_PUANLARI.get(tur, 1)
                tum_haberler.append({
                    "sembol": sembol,
                    "tur": tur,
                    "baslik": h["baslik"][:200],
                    "url": h["url"],
                    "puan": puan,
                    "tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
                })

    # DB'ye kaydet
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS katalizorler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sembol TEXT, tur TEXT, baslik TEXT,
            url TEXT UNIQUE, puan INTEGER, tarih TEXT
        )""")
        for h in tum_haberler:
            try:
                c.execute("INSERT OR IGNORE INTO katalizorler (sembol,tur,baslik,url,puan,tarih) VALUES (?,?,?,?,?,?)",
                    (h["sembol"], h["tur"], h["baslik"], h["url"], h["puan"], h["tarih"]))
            except:
                pass
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Katalizör DB hatası: {e}")

    logger.info(f"📡 Katalizör tarama: {len(tum_haberler)} haber, {sum(1 for h in tum_haberler if h['sembol'])} hisse eşleşmesi")
    return tum_haberler


def sembol_katalizor_puani(sembol: str) -> int:
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT SUM(puan) FROM katalizorler WHERE sembol=? AND tarih >= date('now', '-1 day')", (sembol,))
        r = c.fetchone()
        conn.close()
        return int(r[0] or 0)
    except:
        return 0
