# Telegram Orders

Private Telegram Bot order intake and Telegram Mini App backed by PostgreSQL.

## Architecture

- `backend/`: FastAPI, SQLAlchemy 2, Alembic, shared application services.
- `bot/`: aiogram transport; it calls the shared application service layer.
- `mini-app/`: React, TypeScript and Vite.
- `infrastructure/`: local and production deployment assets.

PostgreSQL is the source of truth. Business rules do not live in HTTP endpoints,
Telegram handlers, or React components. Customer order intake is accepted only
from a private bot chat.

The order flow includes a required delivery profile, an optional customer
comment and optional payment evidence. Administrators can open the original
product URL, follow guarded status transitions, make audited corrections, and
attach payment notes or receipt images. Status changes are delivered through
the Telegram notification outbox worker.

The `VIEWER` staff role has the same operational visibility as the administrator
but no write permissions. Mutation endpoints remain restricted to `ADMIN`, so
read-only access is enforced by the API as well as the Mini App interface.

## Local start

1. Copy `.env.example` to `.env` and replace the development secrets.
2. Run `docker compose --profile frontend up --build`.
3. Open `http://localhost:5173`; API health is at
   `http://localhost:8000/api/v1/health`.

The database has no published host port. Only the API and local frontend are
published for development.

For a real local Telegram token, run `python3 infrastructure/scripts/configure_local.py`.
The prompt is hidden, `.env` receives mode `600`, and `.env` is ignored by Git.
Never paste bot tokens into chat, issues, commits, or shell command arguments.

## Production updates

Before each deployment, follow
`docs/checkpoints.md` and `docs/frontend-publishing-checkpoint.md`. The Mini App
publishing workflow is manual and requires the real HTTPS API base URL through
the GitHub repository variable `VITE_API_BASE_URL`.

Project data belongs under `/mnt/ai`, the stack gets its own Docker network, and
existing VPN, iptables, Tailscale, Docker networks and other Compose stacks
remain untouched. Server operations are performed one command at a time.
Payment receipt images live under `/mnt/ai/data/telegram-orders/payment-proofs`
and are included in the project-specific two-disk backup process.
