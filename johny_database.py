"""
JOHNY — Veritabanı Modülü
SQLite tabanlı işlem ve portföy kaydı
"""
import json
import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

from johny_config import DB_DOSYASI

logger = logging.getLogger(__name__)


class JohnyDatabase:
    """SQLite veritabanı yönetimi"""

    def __init__(self, db_dosyasi: str = DB_DOSYASI):
        self.db_dosyasi = db_dosyasi
        self._baglanti_olustur()
        self._tablolari_olustur()

    def _baglanti_olustur(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_dosyasi)

    def _tablolari_olustur(self) -> None:
        """Tabloları oluştur"""
        try:
            with self._baglanti_olustur() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS islemler (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tarih TEXT NOT NULL,
                        sembol TEXT NOT NULL,
                        islem_tipi TEXT NOT NULL,
                        lot INTEGER NOT NULL,
                        fiyat REAL NOT NULL,
                        komisyon REAL NOT NULL,
                        kar_zarar REAL DEFAULT 0,
                        neden TEXT,
                        strateji TEXT,
                        meta TEXT
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS portfoy_snapshot (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tarih TEXT NOT NULL,
                        portfoy_degeri REAL NOT NULL,
                        nakit REAL NOT NULL,
                        pozisyon_sayisi INTEGER NOT NULL,
                        gunluk_kar_zarar REAL DEFAULT 0,
                        toplam_kar_zarar REAL DEFAULT 0,
                        meta TEXT
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sinyaller (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tarih TEXT NOT NULL,
                        sembol TEXT NOT NULL,
                        sinyal REAL NOT NULL,
                        tavsiye TEXT,
                        strateji_detay TEXT,
                        uyguland_mi INTEGER DEFAULT 0
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ayarlar (
                        anahtar TEXT PRIMARY KEY,
                        deger TEXT NOT NULL,
                        guncelleme TEXT
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Tablo oluşturma hatası: {e}")

    def islem_kaydet(
        self,
        sembol: str,
        islem_tipi: str,
        lot: int,
        fiyat: float,
        komisyon: float,
        kar_zarar: float = 0.0,
        neden: str = "",
        strateji: str = "",
        meta: Optional[dict] = None,
    ) -> Optional[int]:
        """İşlem kaydet"""
        try:
            with self._baglanti_olustur() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO islemler
                    (tarih, sembol, islem_tipi, lot, fiyat, komisyon, kar_zarar, neden, strateji, meta)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    sembol, islem_tipi, lot, fiyat, komisyon,
                    kar_zarar, neden, strateji,
                    json.dumps(meta) if meta else None
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"İşlem kaydetme hatası: {e}")
            return None

    def portfoy_snapshot_kaydet(
        self,
        portfoy_degeri: float,
        nakit: float,
        pozisyon_sayisi: int,
        gunluk_kar_zarar: float = 0.0,
        toplam_kar_zarar: float = 0.0,
        meta: Optional[dict] = None,
    ) -> None:
        """Portföy snapshot kaydet"""
        try:
            with self._baglanti_olustur() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO portfoy_snapshot
                    (tarih, portfoy_degeri, nakit, pozisyon_sayisi, gunluk_kar_zarar, toplam_kar_zarar, meta)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    portfoy_degeri, nakit, pozisyon_sayisi,
                    gunluk_kar_zarar, toplam_kar_zarar,
                    json.dumps(meta) if meta else None
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Snapshot kaydetme hatası: {e}")

    def sinyal_kaydet(
        self,
        sembol: str,
        sinyal: float,
        tavsiye: str,
        strateji_detay: Optional[dict] = None,
    ) -> None:
        """Sinyal kaydet"""
        try:
            with self._baglanti_olustur() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sinyaller (tarih, sembol, sinyal, tavsiye, strateji_detay)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    sembol, sinyal, tavsiye,
                    json.dumps(strateji_detay) if strateji_detay else None
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Sinyal kaydetme hatası: {e}")

    def islemleri_al(self, limit: int = 100, sembol: Optional[str] = None) -> List[dict]:
        """İşlem geçmişini al"""
        try:
            with self._baglanti_olustur() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                if sembol:
                    cursor.execute(
                        "SELECT * FROM islemler WHERE sembol=? ORDER BY tarih DESC LIMIT ?",
                        (sembol, limit)
                    )
                else:
                    cursor.execute(
                        "SELECT * FROM islemler ORDER BY tarih DESC LIMIT ?",
                        (limit,)
                    )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"İşlem getirme hatası: {e}")
            return []

    def portfoy_gecmisi_al(self, limit: int = 252) -> List[dict]:
        """Portföy geçmişi"""
        try:
            with self._baglanti_olustur() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM portfoy_snapshot ORDER BY tarih DESC LIMIT ?",
                    (limit,)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Portföy geçmişi hatası: {e}")
            return []

    def ayar_kaydet(self, anahtar: str, deger) -> None:
        """Ayar kaydet"""
        try:
            with self._baglanti_olustur() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO ayarlar (anahtar, deger, guncelleme)
                    VALUES (?, ?, ?)
                """, (anahtar, json.dumps(deger), datetime.now().isoformat()))
                conn.commit()
        except Exception as e:
            logger.error(f"Ayar kaydetme hatası: {e}")

    def ayar_al(self, anahtar: str, varsayilan=None):
        """Ayar al"""
        try:
            with self._baglanti_olustur() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT deger FROM ayarlar WHERE anahtar=?", (anahtar,))
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
                return varsayilan
        except Exception:
            return varsayilan

    def istatistikleri_al(self) -> dict:
        """Genel istatistikler"""
        try:
            with self._baglanti_olustur() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM islemler")
                toplam_islem = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM islemler WHERE islem_tipi='SAT' AND kar_zarar > 0")
                kazanilan = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM islemler WHERE islem_tipi='SAT' AND kar_zarar < 0")
                kaybedilen = cursor.fetchone()[0]
                cursor.execute("SELECT SUM(kar_zarar) FROM islemler")
                toplam_kz = cursor.fetchone()[0] or 0.0
                cursor.execute("SELECT SUM(komisyon) FROM islemler")
                toplam_komisyon = cursor.fetchone()[0] or 0.0
                return {
                    "toplam_islem": toplam_islem,
                    "kazanilan": kazanilan,
                    "kaybedilen": kaybedilen,
                    "toplam_kar_zarar": round(float(toplam_kz), 2),
                    "toplam_komisyon": round(float(toplam_komisyon), 2),
                    "kazanma_orani": round(kazanilan / (kazanilan + kaybedilen) * 100, 2) if (kazanilan + kaybedilen) > 0 else 0,
                }
        except Exception as e:
            logger.error(f"İstatistik hatası: {e}")
            return {}
