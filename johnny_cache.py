#!/usr/bin/env python3
"""
Johnny Cache Helper
SQLite + Streamlit @st.cache_data ile optimize
"""
import sqlite3
import streamlit as st
import pandas as pd
from typing import List, Dict
import json

DB_PATH = "johnny.db"

class JohnnyDB:
    """Johnny Database Helper"""
    
    @staticmethod
    @st.cache_data(ttl=3600)  # 1 saat cache
    def get_all_stocks(_self, sektor: str = None):
        """Tüm hisseleri getir (cached)"""
        conn = sqlite3.connect(DB_PATH)
        
        if sektor:
            query = "SELECT * FROM hisseler WHERE sektor = ?"
            df = pd.read_sql_query(query, conn, params=(sektor,))
        else:
            query = "SELECT * FROM hisseler"
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        return df
    
    @staticmethod
    @st.cache_data(ttl=3600)
    def get_stock(_self, sembol: str):
        """Belirli hisse getir (cached)"""
        conn = sqlite3.connect(DB_PATH)
        query = "SELECT * FROM hisseler WHERE sembol = ?"
        df = pd.read_sql_query(query, conn, params=(sembol.upper(),))
        conn.close()
        
        return df.to_dict('records')[0] if not df.empty else None
    
    @staticmethod
    @st.cache_data(ttl=3600)
    def get_news(_self, sembol: str, limit: int = 10):
        """Haberler getir (cached)"""
        conn = sqlite3.connect(DB_PATH)
        query = """
            SELECT * FROM haberler 
            WHERE hisse_sembol = ? 
            ORDER BY tarih DESC 
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(sembol.upper(), limit))
        conn.close()
        
        return df
    
    @staticmethod
    @st.cache_data(ttl=3600)
    def get_top5(_self, sort_by: str = "perf_1y"):
        """Top 5 hisse (cached)"""
        conn = sqlite3.connect(DB_PATH)
        query = f"SELECT * FROM hisseler ORDER BY {sort_by} DESC LIMIT 5"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    @staticmethod
    @st.cache_data(ttl=3600)
    def get_moonshot(_self, limit: int = 20):
        """Moonshot hisseler (cached)"""
        conn = sqlite3.connect(DB_PATH)
        query = "SELECT * FROM moonshot ORDER BY kar_potansiyeli DESC LIMIT ?"
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        
        return df
    
    @staticmethod
    @st.cache_data(ttl=1800)  # 30 min cache
    def get_stats(_self):
        """İstatistikler (cached, sık değişir)"""
        conn = sqlite3.connect(DB_PATH)
        
        total_stocks = pd.read_sql_query("SELECT COUNT(*) as count FROM hisseler", conn)
        total_news = pd.read_sql_query("SELECT COUNT(*) as count FROM haberler", conn)
        total_moonshot = pd.read_sql_query("SELECT COUNT(*) as count FROM moonshot", conn)
        
        conn.close()
        
        return {
            "toplam_hisse": int(total_stocks['count'][0]),
            "toplam_haberler": int(total_news['count'][0]),
            "toplam_moonshot": int(total_moonshot['count'][0])
        }

# Singleton instance
db = JohnnyDB()

def get_db_instance():
    """Database instance al"""
    return db

@st.cache_data(ttl=3600)
def load_json_research(filepath: str):
    """JSON araştırma dosyası yükle (cached)"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Dosya yüklemesi başarısız: {e}")
        return None
