"""
JOHNY — US Stock Market Trading Agent
Konfigürasyon Dosyası
"""
from typing import Dict, List, Optional
import os

# ─── Versiyon ───────────────────────────────────────────────────────────────
VERSIYON = "1.0.0"
AGENT_ADI = "JOHNY"
ACIKLAMA = "US Stock Market Simülasyon Ajanı"

# ─── ABD Piyasası Sembolleri ─────────────────────────────────────────────────
US_SEMBOLLER: List[str] = [
    # Mega Cap Tech
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA",
    # Finance
    "JPM", "BAC", "GS", "MS", "WFC", "V", "MA",
    # Healthcare
    "UNH", "JNJ", "PFE", "ABBV", "MRK",
    # Energy
    "XOM", "CVX", "COP", "OXY",
    # Consumer
    "WMT", "COST", "HD", "MCD", "NKE", "SBUX",
    # Industrial
    "CAT", "BA", "GE", "HON", "RTX",
    # Semiconductors
    "AMD", "INTC", "QCOM", "AVGO", "MU",
    # Growth/ARK-style
    "PLTR", "COIN", "HOOD", "SOFI", "RBLX",
    # ETFs
    "SPY", "QQQ", "IWM",
]

# ─── Sektör Grupları ─────────────────────────────────────────────────────────
SEKTOR_GRUPLARI: Dict[str, List[str]] = {
    "Teknoloji": ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"],
    "Finans": ["JPM", "BAC", "GS", "MS", "WFC", "V", "MA"],
    "Sağlık": ["UNH", "JNJ", "PFE", "ABBV", "MRK"],
    "Enerji": ["XOM", "CVX", "COP", "OXY"],
    "Tüketim": ["WMT", "COST", "HD", "MCD", "NKE", "SBUX"],
    "Sanayi": ["CAT", "BA", "GE", "HON", "RTX"],
    "Yarı İletkenler": ["AMD", "INTC", "QCOM", "AVGO", "MU"],
    "Büyüme": ["PLTR", "COIN", "HOOD", "SOFI", "RBLX"],
    "ETF": ["SPY", "QQQ", "IWM"],
}

# ─── Piyasa Saatleri (EST) ───────────────────────────────────────────────────
PIYASA_SAATLERI = {
    "premarket_acilis": "04:00",
    "piyasa_acilis": "09:30",
    "piyasa_kapanis": "16:00",
    "sonrasi_kapanis": "20:00",
    "timezone": "America/New_York",
}

# ─── İstanbul'dan EST Farkı ──────────────────────────────────────────────────
ISTANBUL_EST_FARK = -7  # İstanbul = EST + 7 (yaz) veya EST + 8 (kış)

# ─── Portföy Parametreleri ───────────────────────────────────────────────────
PORTFOY_PARAMETRELERI = {
    "baslangic_sermayesi": 3000.0,       # USD
    "max_pozisyon_yuzdesi": 0.25,         # %25 max per position ($3k portföy için yeterli)
    "stop_loss_yuzdesi": 0.04,            # %3 stop-loss
    "take_profit_yuzdesi": 0.025,  # Hızlı kar al          # %5 take-profit
    "trailing_stop_yuzdesi": 0.02,        # %2 trailing stop
    "max_pozisyon_sayisi": 20,
    "gunluk_kayip_limiti": 0.03,          # %3 daily loss limit
    "portfoy_stop_yuzdesi": 0.10,         # %10 portfolio stop
}

# ─── Komisyon (Garanti Yatırım — ABD Hisseleri) ─────────────────────────────
KOMISYON = {
    "oran": 0.0025,             # %0.25 alım veya satım başına
    "minimum_usd": 1.50,        # Minimum $1.50 komisyon
    "maksimum_oran": 0.01,      # Maximum %1 tavan
    "sec_vergisi": 0.0000278,   # SEC düzenleyici vergisi (satışta)
    "finra_taf": 0.000119,      # FINRA TAF (satışta, max $5.95)
    "toplam_oran": 0.003,       # Tahmini toplam maliyet ~%0.30
}
# Kayma (slippage) — ABD piyasası likit, düşük kayma
KAYMA_ORANI = 0.0005  # %0.05 kayma

# ─── Teknik Gösterge Parametreleri ──────────────────────────────────────────
# Son güncelleme: 2026-04-19 08:02:05 (otomatik optimizasyon)
# RSI en iyi getiri: 66.04% | MACD: 11.03% | MA: 21.36%
TEKNIK_PARAMETRELER = {
    "rsi_periyot": 10,
    "rsi_asiri_alim": 75,
    "rsi_asiri_satim": 30,
    "macd_hizli": 8,
    "macd_yavas": 21,
    "macd_sinyal": 5,
    "bb_periyot": 20,
    "bb_std": 2.0,
    "ema_kisa": 50,
    "ema_orta": 21,
    "ema_uzun": 200,
    "ema_cok_uzun": 200,
    "hacim_ma_periyot": 20,
    "atr_periyot": 14,
}
# ─── Strateji Ağırlıkları ────────────────────────────────────────────────────
STRATEJI_AGIRLIKLARI = {
    "momentum": 0.25,
    "mean_reversion": 0.20,
    "breakout": 0.20,
    "news_sentiment": 0.20,
    "sector_rotation": 0.15,
}

# ─── Backtest Parametreleri ──────────────────────────────────────────────────
BACKTEST_PARAMETRELERI = {
    "donem": "2y",                        # 2 yıl
    "benchmark": "SPY",
    "baslangic_sermayesi": 3000.0,
}

# ─── Veri Kaynakları ─────────────────────────────────────────────────────────
VERI_KAYNAKLARI = {
    "fear_greed_api": "https://api.alternative.me/fng/?limit=30",
    "usdtry_sembol": "USDTRY=X",
    "sp500_benchmark": "^GSPC",
}

# ─── Haber Anahtar Kelimeleri (İngilizce) ───────────────────────────────────
POZITIF_HABERLER = [
    "beat", "beats", "exceeds", "record", "surge", "rally", "gain",
    "upgrade", "buy", "outperform", "strong", "growth", "revenue",
    "FDA approval", "merger", "acquisition", "buyback", "dividend",
    "earnings beat", "guidance raised", "analyst upgrade",
]

NEGATIF_HABERLER = [
    "miss", "misses", "disappoints", "decline", "fall", "drop",
    "downgrade", "sell", "underperform", "weak", "loss", "lawsuit",
    "FDA rejection", "investigation", "recall", "guidance cut",
    "earnings miss", "analyst downgrade", "layoff", "bankruptcy",
]

# ─── Telegram Ayarları ───────────────────────────────────────────────────────
TELEGRAM_TOKEN: Optional[str] = os.getenv("JOHNY_TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID: Optional[str] = os.getenv("JOHNY_TELEGRAM_CHAT_ID", "")

# ─── Dashboard Ayarları ──────────────────────────────────────────────────────
DASHBOARD_PORT = 8503
DASHBOARD_HOST = "0.0.0.0"
DASHBOARD_TITLE = "🇺🇸 JOHNY — US Markets Simülasyon"

# ─── Veri Güncelleme Aralıkları (saniye) ────────────────────────────────────
GUNCELLEME_ARALIGI = {
    "fiyat": 30,
    "haber": 1800,  # 30 dakika
    "teknik": 60,
    "portfoy": 10,
}

# ─── Kayıt Dosyaları ─────────────────────────────────────────────────────────
DB_DOSYASI = "johny_data.db"
LOG_DOSYASI = "johny.log"

# ─── Loglama Seviyesi ────────────────────────────────────────────────────────
LOG_SEVIYESI = "INFO"

# ─── Sektör Renkleri (Dashboard) ─────────────────────────────────────────────
SEKTOR_RENKLERI: Dict[str, str] = {
    "Teknoloji": "#1f77b4",
    "Finans": "#2ca02c",
    "Sağlık": "#d62728",
    "Enerji": "#ff7f0e",
    "Tüketim": "#9467bd",
    "Sanayi": "#8c564b",
    "Yarı İletkenler": "#e377c2",
    "Büyüme": "#7f7f7f",
    "ETF": "#bcbd22",
}

# ─── Sinyal Eşikleri ────────────────────────────────────────────────────────
SINYAL_ESLIKLERI = {
    "guclu_al": 0.70,
    "al": 0.55,
    "notr": 0.45,
    "sat": 0.35,
    "guclu_sat": 0.20,
}

# ─── Hisse → Sektör Haritası (her hissenin sektörü) ─────────────────────────
HISSE_SEKTOR_HARITASI: Dict[str, str] = {}
for _sektor, _semboller in SEKTOR_GRUPLARI.items():
    for _s in _semboller:
        HISSE_SEKTOR_HARITASI[_s] = _sektor

# ─── Korelasyon Çiftleri ─────────────────────────────────────────────────────
KORELASYON_CIFTLERI: Dict[str, List[str]] = {
    "BTC-USD":    ["COIN", "MSTR"],          # BTC yükselince bunlar yükselir
    "CL=F":       ["XOM", "CVX", "COP"],     # Petrol yükselince bunlar yükselir
    "DX-Y.NYB":   ["AAPL", "MSFT"],          # Dolar güçlendi → ihracatçılar zarar
    "^VIX":       ["UVXY", "SQQQ"],          # VIX yükseldi → koruma al
    "GC=F":       ["GLD", "NEM"],            # Altın yükselince
}

# Korelasyon yönü: +1 → tetikleyici yükselince hisse de yükselir, -1 → ters
KORELASYON_YON: Dict[str, int] = {
    "BTC-USD":   +1,
    "CL=F":      +1,
    "DX-Y.NYB":  -1,
    "^VIX":      +1,
    "GC=F":      +1,
}

# Korelasyon tetik eşiği: %1.5 hareket sinyal üretir
KORELASYON_TETIK_PCT = 0.015

# ─── Dinamik Stop-Loss Ayarları ──────────────────────────────────────────────
DINAMIK_STOP_LOSS: Dict[str, float] = {
    "normal":          0.03,   # %3 — normal gün
    "kazanc_oncesi":   0.02,   # %2 — kazanç açıklaması öncesi (dar stop)
    "yuksek_volatil":  0.04,   # %4 — ATR ortalama üstünde
    "makro_kritik":    0.02,   # %2 — FOMC/CPI/NFP günü
}

# ATR yüzdesinin kaç katı "yüksek volatilite" sayılır
ATR_YUKSEK_KATMANI = 1.5  # ATR > ortalama ATR × 1.5 ise yüksek volatilite

# ─── Max Drawdown Koruyucu ───────────────────────────────────────────────────
MAX_DRAWDOWN_PCT = 0.08          # -%8 → tüm pozisyonları kapat
MAX_DRAWDOWN_BEKLEME_SAAT = 24   # Kapatma sonrası 24 saat bekle

# ─── Makro Risk Ayarları ─────────────────────────────────────────────────────
MAKRO_RISK_AYARLARI: Dict[str, float] = {
    "kritik_gun_max_pozisyon_pct": 0.04,   # Kritik günde max %4 pozisyon
    "kritik_oncesi_kucultme":      0.5,    # 1 gün önce pozisyonu yarıya indir
}

# ─── Pre-market Önemli Hareket Eşiği ────────────────────────────────────────
PREMARKET_ESIK = 0.02  # %2
PREMARKET_RAPOR_DOSYA = "premarket_raporu.txt"
MAKRO_TAKVIM_DOSYA = "makro_takvim.json"

# ─── ABD Hisse Piyasası Tatil Günleri (2024-2025) ───────────────────────────
PIYASA_TATILLERI = [
    "2024-01-01", "2024-01-15", "2024-02-19", "2024-03-29",
    "2024-05-27", "2024-06-19", "2024-07-04", "2024-09-02",
    "2024-11-28", "2024-12-25",
    "2025-01-01", "2025-01-20", "2025-02-17", "2025-04-18",
    "2025-05-26", "2025-06-19", "2025-07-04", "2025-09-01",
    "2025-11-27", "2025-12-25",
]

# ─── Small/Mid Cap Ek Evren (~370 hisse) ─────────────────────────────────────
# S&P 500 ve Russell 1000'den ek semboller (US_SEMBOLLER'e ek olarak)
SMALL_MID_CAP_EVREN: List[str] = [
    # Teknoloji & Yazılım (S&P 500 + Mid Cap)
    "NFLX", "ADBE", "CRM", "CSCO", "INTU", "NOW", "WDAY", "VEEV",
    "SNOW", "CRWD", "DDOG", "ZS", "NET", "OKTA", "TWLO", "HUBS",
    "TEAM", "MDB", "ANSS", "CDNS", "SNPS", "ADSK", "PAYC", "PCTY",
    "GTLB", "ZI", "BILL", "SPOT", "ROKU", "ZM", "DOCU", "DOCN",
    "U", "APP", "TTD", "PTON", "ETSY", "W", "CHWY", "CVNA",
    "IBM", "ORCL", "NTAP", "DELL", "HPE", "HPQ", "STX", "WDC",
    "PSTG", "NTNX", "VRSN", "CTSH", "FFIV", "AKAM", "EPAM", "GLOB",
    # Finans (S&P 500 + Mid Cap)
    "BRK-B", "BLK", "CB", "AXP", "USB", "PNC", "COF", "SCHW",
    "CME", "ICE", "NDAQ", "CBOE", "SPGI", "MCO", "ALLY",
    "AIG", "MET", "PRU", "AFL", "TRV", "ALL", "HIG",
    "BX", "KKR", "APO", "ARES",
    "FITB", "KEY", "RF", "HBAN", "CFG", "MTB", "WAL", "ZION",
    "SLM", "NAVI", "CACC",
    # Sağlık & İlaç (S&P 500 + Mid Cap)
    "LLY", "AMGN", "GILD", "BMY", "REGN", "VRTX", "BIIB", "MRNA",
    "ISRG", "SYK", "MDT", "EW", "ZTS", "IDXX", "BSX", "BDX",
    "DXCM", "PODD", "TMO", "DHR", "A", "MCK", "CVS", "CI",
    "HUM", "ELV", "CNC", "MOH", "WBA", "NVAX", "BNTX",
    "BEAM", "EDIT", "CRSP", "ACAD", "IQV", "HOLX", "CRL",
    # Tüketim (S&P 500 + Mid Cap)
    "PG", "KO", "PEP", "CL", "EL", "ULTA", "LULU", "TGT",
    "DG", "DLTR", "CMG", "DPZ", "YUM", "BKNG", "MAR", "HLT",
    "EXPE", "ABNB", "DASH", "UBER", "LYFT", "DIS", "CMCSA",
    "RCL", "CCL", "NCLH", "LVS", "MGM", "WYNN",
    "TSCO", "ORLY", "AZO", "KHC", "MDLZ", "K", "GIS", "HRL", "TAP",
    "TJX", "ROST", "BJ", "M", "BBY",
    "AAL", "UAL", "DAL", "LUV", "JBLU",
    # Sanayi (S&P 500 + Mid Cap)
    "DE", "LMT", "NOC", "GD", "UPS", "FDX", "CSX", "NSC", "UNP",
    "EMR", "ETN", "PH", "ROK", "IR", "OTIS", "CARR", "TT", "FAST",
    "GWW", "ITW", "MMM", "DOV", "PWR", "HUBB", "URI",
    "XPO", "CHRW", "EXPD", "JBHT", "SAIA", "ODFL",
    "HWM", "TDG", "TXT", "LHX", "LDOS", "SAIC", "BAH",
    # Enerji
    "SLB", "HAL", "BKR", "MPC", "PSX", "VLO", "HES", "DVN",
    "FANG", "APA", "EQT", "RRC", "AR", "SWN", "CIVI", "MTDR",
    "ENPH", "SEDG", "FSLR", "RUN",
    "PLUG", "FCEL", "BLNK", "CHPT", "EVGO", "GNRC",
    # Yarı İletkenler Ek
    "AMAT", "LRCX", "KLAC", "MRVL", "ON", "SWKS", "QRVO",
    "ADI", "MPWR", "WOLF", "AEHR", "TER", "ONTO", "ACLS", "FORM",
    "MCHP", "SLAB",
    # Telecom & Medya
    "T", "VZ", "TMUS", "CHTR", "WBD", "FOXA",
    # Kamu Hizmetleri & Gayrimenkul
    "SO", "DUK", "D", "AEP", "EXC", "SRE", "XEL", "PCG",
    "CCI", "AMT", "PLD", "EQIX", "PSA", "O", "VICI", "SPG",
    "NNN", "STAG", "ARE", "EQR", "AVB",
    "WM", "RSG", "CTAS", "PAYX",
    # Hammadde & Kimya
    "LIN", "APD", "NEM", "FCX", "ALB", "MOS", "CF",
    "STLD", "NUE", "CLF", "AA", "X",
    "SHW", "PPG", "ECL", "IFF", "RPM",
    "WRK", "PKG", "IP",
    # Büyüme / Mid Cap Tech
    "MSTR", "SMCI", "ASTS", "IONQ", "RKLB", "SOUN", "AI",
    "BMBL", "MTCH", "APPS",
    # Fintech / Kripto İlişkili
    "AFRM", "UPST", "LC",
    "MARA", "RIOT", "CLSK",
    # EV & Temiz Enerji
    "NIO", "LI", "XPEV", "RIVN", "LCID", "F", "GM",
    # Küçük Kap Favoriler
    "GME", "AMC", "SPCE",
    "OPEN", "Z", "RDFN", "HIMS", "CLOV",
    "DKNG", "PENN", "CZR",
    # Sektör ETF'leri (tarama için)
    "GLD", "SLV", "GDX", "TLT", "HYG",
    "XLF", "XLK", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU",
    "ARKK", "BITO", "UVXY", "SQQQ", "TQQQ",
]

# Toplam Evren (~430 hisse, çiftler kaldırılır)
TUM_EVREN: List[str] = list(dict.fromkeys(US_SEMBOLLER + SMALL_MID_CAP_EVREN))

# ─── Piyasa Değeri Kademeli Pozisyon Boyutları ────────────────────────────────
PIYASA_DEGERI_KADEMELERI: Dict[str, dict] = {
    "buyuk_kap": {
        "min_piyasa_degeri_usd": 10_000_000_000,  # $10B+
        "max_pozisyon_pct": 0.08,
        "stop_loss_pct": 0.03,
        "aciklama": "Büyük kap ($10B+)",
    },
    "orta_kap": {
        "min_piyasa_degeri_usd": 2_000_000_000,   # $2B-$10B
        "max_pozisyon_pct": 0.06,
        "stop_loss_pct": 0.025,
        "aciklama": "Orta kap ($2B-$10B)",
    },
    "kucuk_kap": {
        "min_piyasa_degeri_usd": 0,               # <$2B
        "max_pozisyon_pct": 0.04,
        "stop_loss_pct": 0.02,
        "aciklama": "Küçük kap (<$2B)",
    },
}

# Momentum Scalp Parametreleri
MOMENTUM_SCALP_PARAMETRELERI: Dict[str, object] = {
    "interval": "15m",
    "rsi_esik": 60,
    "rsi_periyot": 14,
    "hacim_katsayi": 2.0,
    "ma_periyot": 20,
    "hedef_pct": 0.03,
    "stop_pct": 0.015,
    "max_sure_saat": 2,
    "max_pozisyon_pct": 0.03,
    "gap_bonus_puan": 0.10,
}

# ─── Yeni Çıktı Dosyaları ────────────────────────────────────────────────────
GAP_GO_LISTESI_DOSYA = "gap_go_listesi.json"
RS_LISTESI_DOSYA = "rs_listesi.json"
SHORT_SQUEEZE_DOSYA = "short_squeeze_listesi.json"
KATALIZOR_LISTESI_DOSYA = "katalizor_listesi.json"
FIRSAT_LISTESI_DOSYA = "firsat_listesi.json"

# Gap & Go eşikleri
GAP_GUCLU_PCT = 3.0        # %3 → GÜÇLÜ AL
GAP_COK_GUCLU_PCT = 5.0    # %5 → ÇOK GÜÇLÜ AL
GAP_HACIM_KATSAYI = 3.0    # 3x hacim
GAP_SHORT_PCT = -3.0       # %-3 → SHORT fikri

# Relative Strength eşikleri
RS_GUCLU_ESIK = 1.5        # SPY'dan 1.5x daha iyi → AL adayı
RS_ZAYIF_ESIK = 0.5        # SPY'dan 0.5x kötü → dikkat
RS_MOMENTUM_ESIK = 1.2     # 5 günde sürekli > 1.2 → GÜÇLÜ MOMENTUM
RS_MOMENTUM_GUN = 5        # Momentum için kontrol edilen gün sayısı

# Short Squeeze eşikleri
SHORT_FLOAT_ESIK = 0.20    # %20 üzeri short float
SHORT_HACIM_ARTIS = 0.50   # 5 günde %50 hacim artışı
