#!/usr/bin/env bash
# HR Filtrlash Boti - bitta buyruq bilan o'rnatish va ishga tushirish.
#
#   ./setup.sh
#
# Docker yo'q bo'lsa o'rnatadi (Ubuntu/Debian, sudo talab qilinadi), .env va
# credentials.json uchun joy tayyorlaydi, keyin docker compose orqali botni
# ishga tushiradi.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

info()  { printf '\033[1;34m==>\033[0m %s\n' "$1"; }
warn()  { printf '\033[1;33m!!\033[0m %s\n' "$1"; }
error() { printf '\033[1;31mXATOLIK:\033[0m %s\n' "$1" >&2; }

# 1. Docker va Docker Compose plaginini tekshirish / o'rnatish -------------
if ! command -v docker &>/dev/null; then
    info "Docker topilmadi, o'rnatilmoqda (get.docker.com skripti orqali, sudo kerak)..."
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker "$USER" || true
    warn "Docker o'rnatildi. 'docker' buyrug'ini sudo'siz ishlatish uchun tizimga qayta kiring"
    warn "(logout/login) yoki joriy terminalda 'newgrp docker' buyrug'ini bajaring, so'ng"
    warn "./setup.sh ni qaytadan ishga tushiring."
    exit 0
fi

if ! docker compose version &>/dev/null; then
    error "'docker compose' plagini topilmadi. Docker Engine'ni yangilang yoki"
    error "docker-compose-plugin paketini o'rnating: sudo apt install docker-compose-plugin"
    exit 1
fi

# 2. .env faylini tayyorlash -------------------------------------------------
if [ ! -f .env ]; then
    cp .env.example .env
    warn ".env fayli .env.example asosida yaratildi."
    warn "BOT_TOKEN va boshqa sozlamalarni to'ldirib, ./setup.sh ni qaytadan ishga tushiring."
    exit 0
fi

if ! grep -qE '^BOT_TOKEN=.+' .env; then
    error ".env faylida BOT_TOKEN bo'sh. Botni ishga tushirishdan oldin to'ldiring."
    exit 1
fi

# 3. credentials.json - bo'lmasa bo'sh joy egallovchi (bind mount uchun) ----
if [ ! -f credentials.json ]; then
    echo '{}' > credentials.json
    warn "credentials.json topilmadi - bo'sh joy egallovchi fayl yaratildi."
    warn "Google Sheets/Drive integratsiyasi haqiqiy Service Account kaliti qo'yilmaguncha ishlamaydi"
    warn "(bot baribir ishga tushadi, ma'lumotlar vaqtincha fallback_log.jsonl'ga yoziladi)."
fi

# 4. Kerakli fayl/papkalar ----------------------------------------------------
mkdir -p logs data
# Eski versiyadagi fallback_log.jsonl bo'lsa, yangi joyiga ko'chiramiz
if [ -f fallback_log.jsonl ] && [ ! -s data/fallback_log.jsonl ]; then
    mv fallback_log.jsonl data/fallback_log.jsonl
    info "fallback_log.jsonl data/ papkasiga ko'chirildi."
fi

# Konteyner ichida bot UID 1000 foydalanuvchisi sifatida ishlaydi - u logs/, data/
# ga yoza olishi va credentials.json'ni o'qiy olishi kerak.
BOT_UID=1000
if [ "$(stat -c %u logs)" != "$BOT_UID" ] || [ "$(stat -c %u data)" != "$BOT_UID" ] \
    || [ "$(stat -c %u credentials.json)" != "$BOT_UID" ]; then
    if [ "$(id -u)" = "0" ]; then
        chown -R "$BOT_UID:$BOT_UID" logs data credentials.json
    else
        sudo chown -R "$BOT_UID:$BOT_UID" logs data credentials.json
    fi
fi

# 5. Qurish va ishga tushirish -------------------------------------------------
info "Docker konteyner qurilmoqda va ishga tushirilmoqda..."
docker compose up -d --build

info "Tayyor! Bot fonda ishlamoqda (restart: always)."
echo "    Loglarni ko'rish:      docker compose logs -f"
echo "    To'xtatish:            docker compose down"
echo "    Qayta ishga tushirish: docker compose restart"
