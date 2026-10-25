"""
Telegram-бот, який показує статус сервера за командою /status.

Встановлення:
    pip3 install python-telegram-bot psutil --break-system-packages

Запуск:
    export TELEGRAM_BOT_TOKEN="твій_токен_від_BotFather"
    python3 telegram_status_bot.py

Або, якщо змінна середовища чомусь не спрацьовує, можна передати
токен прямо аргументом:
    python3 telegram_status_bot.py твій_токен
"""

import logging
import os
import sys
import time
from datetime import datetime, timezone

import psutil
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

START_TIME = time.time()


def get_bot_token() -> str:
    """
    Дістає токен бота. Спочатку зі змінної середовища TELEGRAM_BOT_TOKEN.
    Якщо її нема — можна передати токен першим аргументом при запуску:
        python3 telegram_status_bot.py ТВІЙ_ТОКЕН
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()

    if not token and len(sys.argv) > 1:
        token = sys.argv[1].strip()
        print("[INFO] Токен взято з аргументу командного рядка.")

    if not token:
        print("[ПОМИЛКА] Токен не знайдено.")
        print("Задай його одним із способів:")
        print('  1) export TELEGRAM_BOT_TOKEN="твій_токен"')
        print("  2) python3 telegram_status_bot.py твій_токен")
        sys.exit(1)

    print(f"[INFO] Токен знайдено, довжина: {len(token)} символів.")
    return token


def format_uptime(seconds: float) -> str:
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours} год {minutes} хв {secs} с"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привіт! Я бот-монітор сервера.\n"
        "Використай /status, щоб дізнатись поточний стан сервера."
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uptime_seconds = time.time() - START_TIME

    cpu_percent = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    message = (
        "📊 *Статус сервера*\n\n"
        f"🟢 Стан: працює\n"
        f"⏱ Час роботи: {format_uptime(uptime_seconds)}\n"
        f"🖥 CPU: {cpu_percent}%\n"
        f"💾 Пам'ять: {memory.percent}%\n"
        f"💽 Диск: {disk.percent}%\n"
        f"🕒 Час перевірки: {now}"
    )

    await update.message.reply_text(message, parse_mode="Markdown")


def main() -> None:
    bot_token = get_bot_token()

    application = Application.builder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))

    logger.info("Бот запущено. Очікую команди...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
