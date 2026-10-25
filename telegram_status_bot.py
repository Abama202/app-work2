"""
Telegram-бот, який показує статус сервера за командою /status.

Встановлення:
    pip install python-telegram-bot psutil

Запуск:
    export TELEGRAM_BOT_TOKEN="твій_токен_від_BotFather"
    python telegram_status_bot.py
"""

import logging
import os
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

# Час старту бота — потрібен для розрахунку uptime
START_TIME = time.time()

# Токен бота беремо зі змінної середовища (безпечніше, ніж хардкодити в коді)
BOT_TOKEN = os.environ.get("8738288755:AAHNspFPbNrJgszYrJYxpKdSNvho29d1a8A")


def format_uptime(seconds: float) -> str:
    """Перетворює секунди у формат 'X год Y хв Z с'."""
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
    """Обробник команди /status — збирає дані про сервер і надсилає у чат."""
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
    if not BOT_TOKEN:
        raise RuntimeError(
            "Не знайдено токен! Встанови змінну середовища TELEGRAM_BOT_TOKEN."
        )

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))

    logger.info("Бот запущено. Очікую команди...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
