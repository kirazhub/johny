"""
JOHNY — Alpaca WebSocket ile Anlık Veri
Ücretsiz Alpaca paper trading hesabı ile gerçek zamanlı fiyatlar
"""
import logging
import threading
import time
from datetime import datetime
from typing import Dict, Optional, Callable

logger = logging.getLogger(__name__)


class AlpacaFetcher:
    """
    Alpaca Markets REST + WebSocket ile anlık fiyat verisi.
    
    Kurulum:
    1. https://alpaca.markets adresine git
    2. Ücretsiz hesap aç
    3. Paper Trading → API Keys → Key ve Secret al
    4. johny_config.py'ye ALPACA_KEY ve ALPACA_SECRET ekle
    """

    def __init__(self, api_key: str, api_secret: str, paper: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://paper-api.alpaca.markets" if paper else "https://api.alpaca.markets"
        self.data_url = "https://data.alpaca.markets"
        
        # Anlık fiyat cache
        self._fiyatlar: Dict[str, dict] = {}
        self._lock = threading.Lock()
        self._ws_aktif = False
        self._callback: Optional[Callable] = None

        try:
            import alpaca_trade_api as tradeapi
            self.api = tradeapi.REST(api_key, api_secret, self.base_url)
            self._alpaca_kurulu = True
            logger.info("Alpaca API bağlantısı kuruldu")
        except ImportError:
            self._alpaca_kurulu = False
            logger.warning("alpaca-trade-api kurulu değil, REST fallback kullanılıyor")

    def anlık_fiyat_cek(self, semboller: list) -> Dict[str, dict]:
        """REST ile anlık fiyat çek (WebSocket yerine basit alternatif)"""
        import requests

        headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret,
        }

        sonuclar = {}
        # Batch olarak çek
        sembol_str = ",".join(semboller[:50])
        try:
            url = f"{self.data_url}/v2/stocks/quotes/latest?symbols={sembol_str}"
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json().get("quotes", {})
                for sembol, q in data.items():
                    sonuclar[sembol] = {
                        "fiyat": q.get("ap", 0) or q.get("bp", 0),  # ask veya bid
                        "zaman": q.get("t", ""),
                        "kaynak": "alpaca_realtime",
                    }
            else:
                logger.warning(f"Alpaca quotes hatası: {r.status_code}")
        except Exception as e:
            logger.error(f"Alpaca anlık fiyat hatası: {e}")

        return sonuclar

    def bars_cek(self, sembol: str, limit: int = 100, timeframe: str = "1Min") -> list:
        """Son N bar'ı çek (1 dakikalık mum verileri)"""
        import requests

        headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret,
        }

        try:
            url = f"{self.data_url}/v2/stocks/{sembol}/bars?timeframe={timeframe}&limit={limit}&feed=iex"
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                return r.json().get("bars", [])
        except Exception as e:
            logger.error(f"Alpaca bars hatası {sembol}: {e}")

        return []

    def hesap_bilgisi(self) -> dict:
        """Paper hesap bakiyesi"""
        import requests
        headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret,
        }
        try:
            r = requests.get(f"{self.base_url}/v2/account", headers=headers, timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            logger.error(f"Alpaca hesap hatası: {e}")
        return {}
