"""Telegram-бот учня.

Уся логіка бота — у функції handle_update(): вона отримує одне повідомлення
від Telegram (словник) і повертає текст відповіді. Решта файла лише доставляє
повідомлення туди й назад. Тому бота можна перевірити без Telegram:
    python3 try_bot.py "/start"

Заняття 02 — /start, /help і відповідь на текст.
"""
import json
import os
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

import yaml

import env  # noqa: F401  — читає ~/app/.env

BASE = Path(__file__).parent
CFG = yaml.safe_load((BASE / "project.yaml").read_text(encoding="utf-8"))
PRODUCT = CFG["product"]["name"]
TOKEN = os.environ.get("BOT_TOKEN", "")


# ── Telegram Bot API: звичайні HTTP-запити з JSON ──────────────────
def tg(method, **params):
    """Виклик методу Telegram: tg("sendMessage", chat_id=1, text="Привіт")."""
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    data = json.dumps(params).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=40) as resp:
        return json.loads(resp.read().decode("utf-8"))


def now():
    return datetime.now().isoformat(timespec="seconds")


# ── логіка бота ─────────────────────────────────────────────────────
HELP = ("Що я вмію:\n"
        "/start — привітання\n"
        "/help — ця підказка\n"
        "будь-який інший текст — повторю його")
def handle_update(update):
    """Одне повідомлення від Telegram → текст відповіді (або None)."""
    msg = update.get("message") or {}
    text = (msg.get("text") or "").strip()
    sender = msg.get("from") or {}
    if not text:
        return None
    name = sender.get("first_name") or "друже"
    
    if text.startswith("/start"):
        return (f"Привіт, {name}! Я бот проєкту «{PRODUCT}». "
                "Скоро я знатиму багато про космос, а поки вчуся. Напиши /help.")
    if text.startswith("/help"):
        return HELP
    if text.startswith("/"):
        return "Не знаю такої команди. Напиши /help."
    return f"Ти написав: {text}"

# ── доставка: long polling ──────────────────────────────────────────
STATE = Path.home() / "data" / "bot_state.json"


def get_state(key, default=""):
    try:
        return json.loads(STATE.read_text(encoding="utf-8")).get(key, default)
    except (OSError, ValueError):
        return default


def set_state(key, value):
    """Записує одне значення у ~/data/bot_state.json. Спершу у тимчасовий
    файл, потім підміною: якщо процес уб'ють посеред запису, старий стан цілий."""
    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    state[key] = value
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, STATE)


def poll_forever(stop):
    """Питає Telegram «чи є нові повідомлення?» і відповідає на кожне.

    offset зберігаємо у файлі: якщо службу вбили посеред роботи, після
    перезапуску бот продовжить з того самого місця й не відповість двічі."""
    offset = int(get_state("offset", 0) or 0)
    while not stop.is_set():
        set_state("last_poll", now())
        try:
            data = tg("getUpdates", offset=offset, timeout=25)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            print(f"{now()} Telegram недоступний: {e}", flush=True)
            stop.wait(10)
            continue
        for update in data.get("result", []):
            offset = update["update_id"] + 1
            set_state("offset", offset)
            try:
                reply = handle_update(update)
            except Exception as e:                    # помилка в логіці не валить бота
                print(f"{now()} помилка обробки: {e!r}", flush=True)
                reply = "Ой, щось пішло не так. Спробуй ще раз."
            chat = (update.get("message") or {}).get("chat", {}).get("id")
            if reply and chat:
                try:
                    tg("sendMessage", chat_id=chat, text=reply)
                except (urllib.error.URLError, OSError) as e:
                    print(f"{now()} не вдалося надіслати: {e}", flush=True)


def start_polling():
    """Запускає polling у фоновому потоці. Повертає подію для зупинки або None."""
    if not TOKEN or os.environ.get("BOT_POLLING", "1") == "0":
        return None
    stop = threading.Event()
    threading.Thread(target=poll_forever, args=(stop,), daemon=True, name="bot").start()
    return stop
