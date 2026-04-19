#!/usr/bin/env bash
# JOHNY — US Markets Dashboard Başlatıcı
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔══════════════════════════════════════════╗"
echo "║       🇺🇸 JOHNY — US Markets Agent        ║"
echo "║       NYSE + NASDAQ Simülasyon            ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Python 3.9+ kontrolü
PYTHON_CMD=""
for cmd in python3.9 python3.10 python3.11 python3.12 python3 python; do
    if command -v "$cmd" &>/dev/null; then
        VER=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
        MAJOR=$(echo "$VER" | cut -d. -f1)
        MINOR=$(echo "$VER" | cut -d. -f2)
        if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 9 ]; then
            PYTHON_CMD="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ Python 3.9+ bulunamadı!"
    exit 1
fi
echo "✅ Python: $($PYTHON_CMD --version)"

# Virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Virtual environment oluşturuluyor..."
    "$PYTHON_CMD" -m venv .venv
fi

source .venv/bin/activate

# Bağımlılıklar
echo "📥 Bağımlılıklar kontrol ediliyor..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Ortam değişkenleri (opsiyonel)
if [ -f ".env" ]; then
    echo "🔐 .env yükleniyor..."
    export $(grep -v '^#' .env | xargs)
fi

echo ""
echo "🚀 JOHNY Dashboard başlatılıyor..."
echo "🌐 http://localhost:8511"
echo ""

# Streamlit dashboard
streamlit run johny_dashboard.py \
    --server.port 8511 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false \
    --theme.base dark \
    --theme.backgroundColor "#0a0e1a" \
    --theme.primaryColor "#4a9eff" \
    --theme.secondaryBackgroundColor "#111827" \
    --theme.textColor "#e8eaf0"
