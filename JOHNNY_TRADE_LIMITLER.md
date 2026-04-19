# 🛑 JOHNNY'NİN TRADE LİMİTLERİ

**Güncelleme Tarihi:** 20 Nisan 2026, 02:49 GMT+3

---

## 📊 GÜNLÜK SINIRLAMA

### Günlük Kayıp Sınırı (Daily Loss Limit)

| Kısıtlama | Değer |
|-----------|-------|
| **Günlük Kayıp Limiti** | **-%3** |
| **Başlangıç Portföyü** | 20.000 USD |
| **Güvenli Kayıp Seviyesi** | 600 USD |
| **Tetikleyici** | Günde -600 USD zarar |
| **Sonuç** | Tüm trading durur |

**Açıklama:**
- Günün herhangi bir saatinde portföy -%3 kaybederse
- Johnny otomatik olarak **trading yapamaz**
- Kaybı başka hisse ile kapsama girişimi yapılmaz
- Ertesi günü yeniden başlar

---

## 💰 POZİSYON SINIRLARı

### Maximum Position Size

| Kısıtlama | Değer |
|-----------|-------|
| **Max Per Position** | **25%** |
| **Başlangıç Portföyü** | 20.000 USD |
| **Max Per Hisse** | 5.000 USD |

**Örnek:**
- AAPL'e max 5.000 USD
- MSFT'e max 5.000 USD
- Toplam 4 hisse = 20.000 USD (limitte)

**Daha Fazla Almaya Kalkarsa:**
- Sistem ENGELLER ve error verir
- "Position size exceeded" hatası
- Hiçbir işlem yapılmaz

---

### Maksimum Position Sayısı

| Kısıtlama | Değer |
|-----------|-------|
| **Max Açık Pozisyon** | **20** |
| **Güncel Portföy** | 59 hisse takibi |
| **Aktif Trading** | Max 20 aynı anda |

**Mantığı:**
- 59 hisse var ama
- Herhangi bir zamanda max 20 pozisyon
- Diğerleri "watched" statüsü (yalnızca takip)

---

## 🎯 STOP-LOSS SINIRLARı

### Otomatik Kapatma Kuralları

| Kural | Trigger | İşlem |
|-------|---------|-------|
| **Position Stop-Loss** | -4% (entry fiyatından) | Otomatik SAT |
| **Trailing Stop** | -2% (en yüksek fiyatından) | Otomatik SAT |
| **Portfolio Stop-Loss** | -10% (total) | TÜM POZİSYON SAT |
| **Daily Loss Limit** | -%3 (günlük) | TRADİNG DURAĞI |

**Örnek Senaryo:**

```
HOOD'u 100'den aldı:
- Position SL: 96'da otomatik sat
- (100'ün -%4'ü)

HOOD en yüksek 120'ye çıktı:
- Trailing SL: 117.6'da otomatik sat
- (120'nin -%2'si)

Portföy 18.000'e düşerse (20K'dan -%10):
- TÜM POZİSYONLAR kapatılır
- Derhal likidite sağlanır

Günün herhangi bir saatinde -600 USD zarar:
- Johnny trading yapamaz
- Yalnızca monitoring
- Ertesi gün reset
```

---

## 📈 TAKE-PROFIT LİMİTLERİ

### Kâr Alma Seviyeleri

| Seviye | Trigger | İşlem |
|--------|---------|-------|
| **Take-Profit 1** | +2.5% (entry fiyatından) | 1/3 SAT |
| **Take-Profit 2** | +5% | 1/3 Daha SAT |
| **Take-Profit 3** | +10%+ | GERİSİ SAT |

**Örnek:**

```
HOOD'u 100'den 1000 USD aldı:

TP1: 102.5'e çıkınca (+2.5%)
- 333 USD sat (1/3)
- Geriye: 666 USD kalır

TP2: 105'e çıkınca (+5%)
- 333 USD daha sat (1/3)
- Geriye: 333 USD kalır

TP3: 110'a çıkınca (+10%)
- Son 333 USD sat
- Pozisyon kapatılır
```

---

## ⏰ TRADE SAATLERI SINIRLARı

### Likit Saatler (Johnny Aktif)

| Zaman (EST) | Durum |
|-------------|-------|
| **09:30 - 16:00** | ✅ AKTIF (Normal hours) |
| **04:00 - 09:30** | ⚠️ PRE-MARKET (Düşük likidite) |
| **16:00 - 20:00** | ⚠️ AFTER-HOURS (Düşük likidite) |
| **20:00 - 04:00** | ❌ KAPALIT (Johnny uyur) |

**Johnny'nin Stratejisi:**
- Normal hours: Agresif alım/satım
- Pre/After-hours: Yalnızca monitoring
- Kapalı saatler: Pause

---

## 📊 GUNLUK SINIRLAR (ÖZET)

```
╔════════════════════════════════════════╗
║       JOHNNY'NİN GÜNLÜK LİMİTLERİ     ║
╠════════════════════════════════════════╣
║                                        ║
║ 1. Günlük Kayıp Sınırı: -%3 (-600$)  ║
║    → Tetiklenirse: Trading duraği    ║
║                                        ║
║ 2. Position Size: Max 25% (5.000$)    ║
║    → Aşarsa: Sistem ENGELLER         ║
║                                        ║
║ 3. Açık Pozisyon: Max 20             ║
║    → Fazlası: Watched statüsü        ║
║                                        ║
║ 4. Portfolio Stop: -10% (2.000$)      ║
║    → Tetiklenirse: TÜM SAT           ║
║                                        ║
║ 5. Position SL: -4% per hisse         ║
║    → Otomatik kapalı              ║
║                                        ║
║ 6. Trade Saatleri: 09:30-16:00 EST   ║
║    → Kapalı saatler: Yalnız izle     ║
║                                        ║
╚════════════════════════════════════════╝
```

---

## 🚨 LİMİT AŞILIRSA NE OLUR?

### Senaryo 1: Günlük -%3 Limiti
```
Sabah açılırken portföy: 20.000 USD
Hisse düşüyor, -600 USD kaybı
Johnny'nin günlük sınırı ulaşıyor:

❌ SONUÇ:
- Johnny trading yapamaz
- Yalnız monitoring (verileri okur)
- Market kapadı mı? Ertesi aç reset
```

### Senaryo 2: Position Size %25'i Aş
```
Johnny AAPL'e 4.500 USD girmiş
AAPL spike yapıyor, +10% kazanç
Johnny kazancı "tahta ekle" düşüncesiyle
AAPL'ye 2.000 USD daha almak istiyor:

❌ SONUÇ:
- Sistem ENGELLER
- "Position size exceeded" hatası
- İşlem yapılmaz
- Hiçbir kayıp olmaz
```

### Senaryo 3: Portfolio -%10 Ulaş
```
Pazar çöküşü, tüm hisseler düşüyor:
- AAPL: -8%
- MSFT: -9%
- AMD: -10%
- ...
Portföy: 18.000 USD (20K'dan -%10)

❌ SONUÇ:
- TÜM POZİSYONLAR otomatik KAPATILIR
- Derhal likidite sağlanır
- Cash olur: ~18.000 USD
- Risk DURUYOR
- Yeni strateji planlanır
```

---

## ✅ JOHNNY'NİN SORUMLU BORSA DÖNEMİ

**Johnny Risk-Aware:**
- ✅ Günlük kayıp koruması
- ✅ Position size sınırlaması
- ✅ Otomatik stop-losses
- ✅ Portfolio circuit-breaker
- ✅ Trade hour restrictions

**Felsefe:**
> "Agresif büyüme, ama controlled risk"

---

## 📋 KONTROL LİSTESİ

Johnny her sabah:
- [ ] Önceki günün kayıp/kazancını kontrol et
- [ ] Günlük sınır reset kontrolü
- [ ] 20 position limiti kontrol
- [ ] Stop-loss seviyeleri doğrulama
- [ ] Trade saatleri kontrol (EST)
- [ ] Market haberleri taraması

---

**Patron, Johnny'nin bütün sınırları tanımlanmış ve implement edilmiş!** 🛡️

Agresif ama kontrollü — tam senin için! 🎯
