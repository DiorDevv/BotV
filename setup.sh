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
touch fallback_log.jsonl
mkdir -p logs tmp

# 5. Qurish va ishga tushirish -------------------------------------------------
info "Docker konteyner qurilmoqda va ishga tushirilmoqda..."
docker compose up -d --build

info "Tayyor! Bot fonda ishlamoqda (restart: always)."
echo "    Loglarni ko'rish:      docker compose logs -f"
echo "    To'xtatish:            docker compose down"
echo "    Qayta ishga tushirish: docker compose restart"
