#!/usr/bin/env bash
set -euo pipefail

target_dir=/mnt/ai/compose/telegram-orders
target_file="$target_dir/.env"

if ! mountpoint -q /mnt/ai; then
  echo "ERROR: /mnt/ai is not mounted" >&2
  exit 1
fi

if [[ -e "$target_file" ]]; then
  echo "ERROR: $target_file already exists; refusing to overwrite it" >&2
  exit 1
fi

read -rsp "Telegram bot token: " telegram_orders_bot_token
echo
if [[ ! "$telegram_orders_bot_token" =~ ^[0-9]+:[A-Za-z0-9_-]{30,}$ ]]; then
  echo "ERROR: invalid Telegram bot token format" >&2
  exit 1
fi

umask 077
mkdir -p "$target_dir"
postgres_password="$(openssl rand -hex 32)"
app_secret="$(openssl rand -hex 32)"

cat >"$target_file" <<EOF
APP_ENV=production
APP_SECRET=$app_secret
POSTGRES_DB=telegram_orders
POSTGRES_USER=telegram_orders
POSTGRES_PASSWORD=$postgres_password
DATABASE_URL=postgresql+asyncpg://telegram_orders:$postgres_password@db:5432/telegram_orders
TELEGRAM_BOT_TOKEN=$telegram_orders_bot_token
TELEGRAM_ADMIN_IDS=252246696
TELEGRAM_INIT_DATA_MAX_AGE_SECONDS=3600
CORS_ORIGINS=https://orders.papamio.es
EOF

unset telegram_orders_bot_token postgres_password app_secret
chmod 600 "$target_file"
echo "Created $target_file with mode 600"
