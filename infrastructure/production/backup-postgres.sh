#!/usr/bin/env bash
set -euo pipefail

repo_dir=/mnt/ai/repos/telegram-orders
compose_file="$repo_dir/infrastructure/production/docker-compose.yml"
env_file=/mnt/ai/compose/telegram-orders/.env
local_dir=/mnt/ai/backups/telegram-orders/postgres
archive_mount=/mnt/archive_hdd_serv
archive_dir="$archive_mount/telegram-orders/postgres"
proof_source=/mnt/ai/data/telegram-orders/payment-proofs
local_proof_dir=/mnt/ai/backups/telegram-orders/payment-proofs
archive_proof_dir="$archive_mount/telegram-orders/payment-proofs"
lock_file=/run/lock/telegram-orders-backup.lock

exec 9>"$lock_file"
flock -n 9 || { echo "Another Telegram Orders backup is running" >&2; exit 1; }

mountpoint -q /mnt/ai || { echo "ERROR: /mnt/ai is not mounted" >&2; exit 1; }
mountpoint -q "$archive_mount" || { echo "ERROR: $archive_mount is not mounted" >&2; exit 1; }
test -r "$env_file" || { echo "ERROR: $env_file is not readable" >&2; exit 1; }

install -d -m 700 "$local_dir" "$archive_dir" "$proof_source" "$local_proof_dir" "$archive_proof_dir"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
temporary="$local_dir/.telegram-orders-$timestamp.dump.tmp"
dump_file="$local_dir/telegram-orders-$timestamp.dump"
proof_archive="$local_proof_dir/payment-proofs-$timestamp.tar.gz"

cleanup() { rm -f "$temporary"; }
trap cleanup EXIT

docker compose --env-file "$env_file" -f "$compose_file" exec -T db \
  pg_dump -U telegram_orders -d telegram_orders --format=custom >"$temporary"
test -s "$temporary"
mv "$temporary" "$dump_file"
sha256sum "$dump_file" >"$dump_file.sha256"

rsync -a --partial "$dump_file" "$dump_file.sha256" "$archive_dir/"
tar -C "$proof_source" -czf "$proof_archive" .
sha256sum "$proof_archive" >"$proof_archive.sha256"
rsync -a --partial "$proof_archive" "$proof_archive.sha256" "$archive_proof_dir/"
find "$local_dir" -maxdepth 1 -type f -name 'telegram-orders-*.dump*' -mtime +7 -delete
find "$archive_dir" -maxdepth 1 -type f -name 'telegram-orders-*.dump*' -mtime +30 -delete
find "$local_proof_dir" -maxdepth 1 -type f -name 'payment-proofs-*.tar.gz*' -mtime +7 -delete
find "$archive_proof_dir" -maxdepth 1 -type f -name 'payment-proofs-*.tar.gz*' -mtime +30 -delete

echo "Backup completed: $dump_file and $proof_archive"
