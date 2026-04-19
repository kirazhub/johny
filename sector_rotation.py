"""
JOHNY — Makro Tabanlı Sektör Rotasyonu
Google News RSS ile Fed/enflasyon/istihdam haberlerini izler,
sektör ağırlıklarını makro olaylara göre ayarlar.
"""
import logging
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# ─── Makro haber → sektör sinyal kuralları ────────────────────────────────────
# Değer: pozitif = o sektörü al, negatif = sat
_KURAL_HARITASI: List[Tuple[List[str], Dict[str, float]]] = [
    # Fed faiz kararları
    (
        ["fed raised", "fed hikes", "rate hike", "interest rate increase",
         "fomc raised", "fed raised rates", "tightening"],
        {"Finans": +0.7, "Teknoloji": -0.5, "Büyüme": -0.6, "Gayrimenkul": -0.7},
    ),
    (
        ["fed cut", "fed cuts", "rate cut", "interest rate decrease",
         "fomc cut", "fed lowered", "easing", "pivot"],
        {"Teknoloji": +0.6, "Büyüme": +0.7, "Gayrimenkul": +0.6, "Finans": -0.3},
    ),
    # Enflasyon
    (
        ["inflation rose", "inflation higher", "cpi higher", "cpi beat",
         "prices surged", "hot inflation", "inflation above"],
        {"Enerji": +0.6, "Tüketim": -0.5, "Teknoloji": -0.4},
    ),
    (
        ["inflation fell", "inflation lower", "cpi lower", "cpi miss",
         "deflation", "prices declined", "cooling inflation"],
        {"Teknoloji": +0.5, "Tüketim": +0.3, "Enerji": -0.3},
    ),
    # İstihdam / NFP
    (
        ["jobs added", "nfp beat", "strong jobs", "unemployment fell",
         "payrolls beat", "labor market strong", "hiring surged"],
        {"Tüketim": +0.5, "Finans": +0.4, "Sanayi": +0.3},
    ),
    (
        ["jobs lost", "nfp miss", "unemployment rose", "layoffs",
         "payrolls miss", "weak jobs", "jobless claims rose"],
        {"Sağlık": +0.4, "Savunma": +0.3, "Tüketim": -0.4},
    ),
    # Risk-off / VIX yüksek
    (
        ["risk off", "market selloff", "recession fears", "vix spike",
         "flight to safety", "market crash", "bear market"],
        {"Savunma": +0.7, "Sağlık": +0.6, "Teknoloji": -0.6, "Büyüme": -0.7},
    ),
    # AI / Tech haberleri
    (
        ["ai breakthrough", "artificial intelligence", "chatgpt", "nvidia earnings",
         "tech rally", "semiconductor boom", "chip demand"],
        {"Teknoloji": +0.7, "Yarı İletkenler": +0.8, "Büyüme": +0.4},
    ),
    # Petrol / Enerji
    (
        ["oil surge", "crude higher", "opec cut", "energy crisis",
         "oil rally", "brent higher", "wti higher"],
        {"Enerji": +0.7, "Tüketim": -0.3},
    ),
    (
        ["oil drop", "crude lower", "opec increase", "oil glut",
         "energy lower", "oil selloff"],
        {"Enerji": -0.6, "Tüketim": +0.2},
    ),
    # Çin/küresel büyüme
    (
        ["china growth", "global recovery", "gdp beat", "economic expansion"],
        {"Sanayi": +0.5, "Enerji": +0.3, "Teknoloji": +0.3},
    ),
    (
        ["china slowdown", "global recession", "gdp miss", "contraction"],
        {"Sağlık": +0.4, "Savunma": +0.4, "Sanayi": -0.5},
    ),
]

# Sektör → ETF / temsili semboller
SEKTOR_ETF: Dict[str, List[str]] = {
    "Teknoloji":       ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"],
    "Finans":          ["JPM", "BAC", "GS", "MS", "WFC", "V", "MA"],
    "Sağlık":          ["UNH", "JNJ", "PFE", "ABBV", "MRK"],
    "Enerji":          ["XOM", "CVX", "COP", "OXY"],
    "Tüketim":         ["WMT", "COST", "HD", "MCD", "NKE", "SBUX"],
    "Sanayi":          ["CAT", "BA", "GE", "HON", "RTX"],
    "Yarı İletkenler": ["AMD", "INTC", "QCOM", "AVGO", "MU"],
    "Büyüme":          ["PLTR", "COIN", "HOOD", "SOFI", "RBLX"],
    "Savunma":         ["RTX", "LMT", "NOC", "GD"],
    "Gayrimenkul":     ["AMT", "PLD", "EQIX"],
}


class MacroSektorRotasyonu:
    """
    Her saat Google News RSS'i tarar,
    makro haberlerden sektör ağırlıklarını hesaplar.
    """

    def __init__(self):
        self._sektor_agirliklari: Dict[str, float] = {}
        self._son_haberler: List[dict] = []
        self._son_guncelleme: float = 0.0
        self._cache_ttl = 3600.0  # 1 saat

    # ------------------------------------------------------------------ #
    #  Haber çekme                                                         #
    # ------------------------------------------------------------------ #

    def haber_cek(self, limit: int = 50) -> List[dict]:
        """Google News RSS'den ABD makro/piyasa haberlerini çek"""
        haberler: List[dict] = []
        urls = [
            "https://news.google.com/rss/search?q=federal+reserve+interest+rate&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=inflation+CPI+economy&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=jobs+report+NFP+employment&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=stock+market+nasdaq+sp500&hl=en-US&gl=US&ceid=US:en",
        ]
        try:
            import feedparser
        except ImportError:
            logger.warning("feedparser kurulu değil, haber çekilemiyor")
            return []

        for url in urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:limit // len(urls)]:
                    baslik = getattr(entry, "title", "")
                    haberler.append({
                        "baslik": baslik.lower(),
                        "link":   getattr(entry, "link", ""),
                        "tarih":  getattr(entry, "published", ""),
                    })
            except Exception as e:
                logger.debug(f"RSS çekilemedi {url}: {e}")

        self._son_haberler = haberler
        return haberler

    # ------------------------------------------------------------------ #
    #  Kural eşleme                                                        #
    # ------------------------------------------------------------------ #

    def _haber_kural_esle(self, baslik: str) -> Dict[str, float]:
        """Tek bir haber başlığı için sektör sinyalleri döner"""
        sinyaller: Dict[str, float] = {}
        for anahtar_kelimeler, sektor_sinyalleri in _KURAL_HARITASI:
            if any(kw in baslik for kw in anahtar_kelimeler):
                for sektor, sinyal in sektor_sinyalleri.items():
                    if sektor not in sinyaller:
                        sinyaller[sektor] = 0.0
                    sinyaller[sektor] += sinyal
        return sinyaller

    # ------------------------------------------------------------------ #
    #  Sektör ağırlıkları                                                  #
    # ------------------------------------------------------------------ #

    def sektor_agirliklari_hesapla(
        self,
        haberler: Optional[List[dict]] = None,
    ) -> Dict[str, float]:
        """
        Haberlere göre sektör ağırlıklarını hesapla.
        Döner: {sektör: sinyal} — pozitif = al, negatif = sat
        """
        if haberler is None:
            haberler = self._son_haberler or self.haber_cek()

        sektor_skor: Dict[str, float] = {}
        for haber in haberler:
            sinyaller = self._haber_kural_esle(haber["baslik"])
            for sektor, sinyal in sinyaller.items():
                sektor_skor[sektor] = sektor_skor.get(sektor, 0.0) + sinyal

        # -1.0 ile +1.0 arasında normalize et
        if sektor_skor:
            maks = max(abs(v) for v in sektor_skor.values()) or 1.0
            sektor_skor = {s: round(v / maks, 3) for s, v in sektor_skor.items()}

        self._sektor_agirliklari = sektor_skor
        return sektor_skor

    # ------------------------------------------------------------------ #
    #  Hisse bazlı sinyal                                                  #
    # ------------------------------------------------------------------ #

    def hisse_sinyal_al(self, sembol: str) -> Tuple[float, str]:
        """
        Tek bir hisse için sektör rotasyon sinyali döner.
        Returns: (sinyal -1.0..+1.0, açıklama)
        """
        from johny_config import HISSE_SEKTOR_HARITASI
        sektor = HISSE_SEKTOR_HARITASI.get(sembol, "")
        if not sektor:
            # Alternatif: SEKTOR_ETF üzerinden ara
            for s, semboller in SEKTOR_ETF.items():
                if sembol in semboller:
                    sektor = s
                    break

        if not sektor:
            return 0.0, "Sektör bulunamadı"

        if not self._sektor_agirliklari:
            return 0.0, "Sektör ağırlıkları henüz hesaplanmadı"

        sinyal = self._sektor_agirliklari.get(sektor, 0.0)
        if sinyal > 0.3:
            aciklama = f"Sektör Rotasyon AL: {sektor} ({sinyal:+.2f})"
        elif sinyal < -0.3:
            aciklama = f"Sektör Rotasyon SAT: {sektor} ({sinyal:+.2f})"
        else:
            aciklama = f"Sektör Rotasyon Nötr: {sektor} ({sinyal:+.2f})"
        return sinyal, aciklama

    # ------------------------------------------------------------------ #
    #  Güncelleme döngüsü                                                  #
    # ------------------------------------------------------------------ #

    def guncelle(self, zorla: bool = False) -> Dict[str, float]:
        """
        Cache süresi dolmuşsa haberleri güncelle ve ağırlıkları yeniden hesapla.
        """
        simdi = time.time()
        if zorla or (simdi - self._son_guncelleme) >= self._cache_ttl:
            haberler = self.haber_cek()
            agirlıklar = self.sektor_agirliklari_hesapla(haberler)
            self._son_guncelleme = simdi
            logger.info(
                f"Sektör rotasyon güncellendi: "
                + ", ".join(f"{s}:{v:+.2f}" for s, v in agirlıklar.items() if abs(v) > 0.2)
            )
            return agirlıklar
        return self._sektor_agirliklari

    # ------------------------------------------------------------------ #
    #  Önemli haber özeti                                                  #
    # ------------------------------------------------------------------ #

    def makro_ozet(self) -> str:
        """İnsan okunabilir makro özet"""
        if not self._sektor_agirliklari:
            return "Makro sektör verisi yok"
        satirlar = []
        for sektor, sinyal in sorted(
            self._sektor_agirliklari.items(), key=lambda x: -abs(x[1])
        ):
            if abs(sinyal) >= 0.2:
                yon = "▲" if sinyal > 0 else "▼"
                satirlar.append(f"  {yon} {sektor}: {sinyal:+.2f}")
        return "Makro Sektör Rotasyonu:\n" + ("\n".join(satirlar) or "  Tüm sektörler nötr")
