#!/usr/bin/env bash
set -euo pipefail

repo_dir=/mnt/ai/repos/telegram-orders
compose_file="$repo_dir/infrastructure/production/docker-compose.yml"
env_file=/mnt/ai/compose/telegram-orders/.env
archive_dir=/mnt/archive_hdd_serv/telegram-orders/postgres
restore_db="telegram_orders_restore_drill_$$"

mountpoint -q /mnt/ai || { echo "ERROR: /mnt/ai is not mounted" >&2; exit 1; }
mountpoint -q /mnt/archive_hdd_serv || { echo "ERROR: backup disk is not mounted" >&2; exit 1; }

dump_file="$(find "$archive_dir" -maxdepth 1 -type f -name 'telegram-orders-*.dump' -printf '%T@ %p\n' | sort -nr | head -n1 | cut -d' ' -f2-)"
test -n "$dump_file" && test -s "$dump_file" || { echo "ERROR: no backup dump found" >&2; exit 1; }

compose=(docker compose --env-file "$env_file" -f "$compose_file")
cleanup() {
  "${compose[@]}" exec -T db dropdb -U telegram_orders --if-exists "$restore_db" >/dev/null 2>&1 || true
}
trap cleanup EXIT

"${compose[@]}" exec -T db createdb -U telegram_orders "$restore_db"
"${compose[@]}" exec -T db pg_restore -U telegram_orders -d "$restore_db" --exit-on-error <"$dump_file"

migration="$("${compose[@]}" exec -T db psql -U telegram_orders -d "$restore_db" -Atqc 'SELECT version_num FROM alembic_version')"
table_count="$("${compose[@]}" exec -T db psql -U telegram_orders -d "$restore_db" -Atqc "SELECT count(*) FROM pg_tables WHERE schemaname = 'public'")"

test "$migration" = "0004_finance" || { echo "ERROR: unexpected migration: $migration" >&2; exit 1; }
test "$table_count" -ge 10 || { echo "ERROR: too few restored tables: $table_count" >&2; exit 1; }

echo "Restore drill passed: migration=$migration tables=$table_count source=$(basename "$dump_file")"
