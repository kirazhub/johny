#!/usr/bin/env python3
"""
Johnny FastAPI Server
SQLite Database ile hisse verilerini serve et
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import json
from datetime import datetime
import os

app = FastAPI(title="Johnny API", version="1.0.0")

# CORS izin ver
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "johnny.db"

def get_db():
    """Database bağlantısı al"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ===== ENDPOINTS =====

@app.get("/")
def read_root():
    """API'nin sağlık kontrolü"""
    return {
        "status": "🚀 Johnny API Çalışıyor",
        "version": "1.0.0",
        "endpoints": [
            "/api/hisseler",
            "/api/hisseler/{sembol}",
            "/api/haberler/{sembol}",
            "/api/moonshot",
            "/api/top5",
            "/api/sentiment/{sentiment}"
        ]
    }

@app.get("/api/hisseler")
def get_all_stocks(sektor: str = None, sentiment: str = None, limit: int = 100):
    """Tüm hisseleri getir (filtreleme seçeneği ile)"""
    try:
        conn = get_db()
        query = "SELECT * FROM hisseler"
        params = []
        
        if sektor:
            query += " WHERE sektor = ?"
            params.append(sektor)
        
        if sentiment:
            if sektor:
                query += " AND sentiment = ?"
            else:
                query += " WHERE sentiment = ?"
            params.append(sentiment)
        
        query += f" LIMIT {limit}"
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/hisseler/{sembol}")
def get_stock(sembol: str):
    """Belirli bir hisse getir"""
    try:
        conn = get_db()
        cursor = conn.execute(
            "SELECT * FROM hisseler WHERE sembol = ?",
            (sembol.upper(),)
        )
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Hisse bulunamadı: {sembol}")
        
        return dict(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/haberler/{sembol}")
def get_news(sembol: str, limit: int = 10):
    """Hisse haberleri getir"""
    try:
        conn = get_db()
        cursor = conn.execute(
            "SELECT * FROM haberler WHERE hisse_sembol = ? ORDER BY tarih DESC LIMIT ?",
            (sembol.upper(), limit)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/moonshot")
def get_moonshot(limit: int = 20):
    """3 aylık moonshot hisseler"""
    try:
        conn = get_db()
        cursor = conn.execute(
            "SELECT * FROM moonshot ORDER BY kar_potansiyeli DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/top5")
def get_top5(sort_by: str = "perf_1y"):
    """Top 5 hisse"""
    try:
        conn = get_db()
        valid_sorts = ["perf_1y", "perf_6m", "perf_3m", "sentiment"]
        
        if sort_by not in valid_sorts:
            sort_by = "perf_1y"
        
        query = f"SELECT * FROM hisseler ORDER BY {sort_by} DESC LIMIT 5"
        cursor = conn.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sentiment/{sentiment}")
def get_by_sentiment(sentiment: str, limit: int = 20):
    """Sentiment'e göre hisseler filtrele"""
    try:
        conn = get_db()
        cursor = conn.execute(
            "SELECT * FROM hisseler WHERE sentiment = ? LIMIT ?",
            (sentiment.upper(), limit)
        )
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            raise HTTPException(status_code=404, detail=f"Sentiment bulunamadı: {sentiment}")
        
        return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
def get_stats():
    """Database istatistikleri"""
    try:
        conn = get_db()
        
        stats = {
            "toplam_hisse": conn.execute("SELECT COUNT(*) FROM hisseler").fetchone()[0],
            "toplam_haberler": conn.execute("SELECT COUNT(*) FROM haberler").fetchone()[0],
            "toplam_moonshot": conn.execute("SELECT COUNT(*) FROM moonshot").fetchone()[0],
            "sektorler": [row[0] for row in conn.execute("SELECT DISTINCT sektor FROM hisseler")],
            "sentimentler": [row[0] for row in conn.execute("SELECT DISTINCT sentiment FROM hisseler")],
            "son_guncelleme": datetime.now().isoformat()
        }
        
        conn.close()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("🚀 Johnny API başlatılıyor...")
    print("📍 http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
