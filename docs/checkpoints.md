# Implementation checkpoints

## CP0 — local bootstrap (current)

- Repository structure and executable local stack.
- No production-server changes.
- No real Telegram token required for API/frontend development.

## CP1 — domain and database

- Complete v1.1 schema and migrations.
- State-transition rules, ownership checks, transactions, idempotency,
  notification outbox and audit tests.
- Local backup and restore drill.

## CP2 — interfaces and local E2E

- Private-chat-only bot intake.
- Admin and Customer Mini App flows with verified Telegram init data.
- Local end-to-end and security tests.

## CP3 — production readiness review

- Review secrets, image versions, resource limits and rollback.
- Confirm `/mnt/ai` mount guard and bind-mount paths.
- Confirm independent backup target and tested restore.
- Explicit user approval is required before production changes.

Prepared production assets live in `infrastructure/production`. The API is
bound only to `127.0.0.1:8000`; its public HTTPS endpoint will be provided by
Tailscale Funnel at `https://alex-server.tail684c35.ts.net`.

The project-specific backup timer creates a PostgreSQL custom-format dump under
`/mnt/ai/backups/telegram-orders/postgres` and copies it to the physically
separate `/mnt/archive_hdd_serv/telegram-orders/postgres` mount. It keeps 7 days
locally and 30 days on the backup disk. Installation and a restore drill remain
mandatory deployment checkpoints.

## Confirmed production facts

- Ubuntu 24.04.4 LTS; Docker 29.7.2; Compose 5.4.0.
- `/mnt/ai` is ext4 on UUID `d60a9a69-35a0-40f2-82e6-23c43c3c29b4` and has
  systemd unit `mnt-ai.mount`.
- Repository: `/mnt/ai/repos/telegram-orders`.
- Compose config: `/mnt/ai/compose/telegram-orders`.
- Persistent data: `/mnt/ai/data/telegram-orders`.
- Local dumps: `/mnt/ai/backups/telegram-orders`; a separate mechanism must
  copy project backups to a different physical backup disk.
- Docker root is `/srv/docker`.
- The project must not join `ai-net` or any existing stack network.
- PostgreSQL has no host port; Bot uses outbound long polling.
- Do not change VPN/Amnezia, iptables, Tailscale, routing, SSH, libvirt, other
  Compose stacks or the shared `compose@.service` template.
- Future server work follows one-command-at-a-time operation.
