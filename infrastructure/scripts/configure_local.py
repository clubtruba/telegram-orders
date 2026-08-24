from getpass import getpass
from pathlib import Path
import re

TOKEN_RE = re.compile(r"^\d{8,12}:[A-Za-z0-9_-]{30,}$")


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    example_path = root / ".env.example"
    env_path = root / ".env"
    token = getpass("Новый Telegram Bot Token (ввод скрыт): ").strip()
    if not TOKEN_RE.fullmatch(token):
        raise SystemExit("Некорректный формат токена; .env не изменён")
    source = env_path.read_text() if env_path.exists() else example_path.read_text()
    lines = source.splitlines()
    replaced = False
    for index, line in enumerate(lines):
        if line.startswith("TELEGRAM_BOT_TOKEN="):
            lines[index] = f"TELEGRAM_BOT_TOKEN={token}"
            replaced = True
            break
    if not replaced:
        lines.append(f"TELEGRAM_BOT_TOKEN={token}")
    env_path.write_text("\n".join(lines) + "\n")
    env_path.chmod(0o600)
    print(f"Готово: секрет сохранён в {env_path} с правами 600")


if __name__ == "__main__":
    main()
