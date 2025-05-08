import logging
import time
import telebot
from datetime import datetime

# Загружаем конфиг
import json
with open("config.json") as f:
    config = json.load(f)

TOKEN = config["telegram_token"]
CHAT_ID = config["chat_id"]
bot = telebot.TeleBot(TOKEN)

logging.basicConfig(level=logging.INFO)

def send_reminders():
    now = datetime.now()
    current_time = now.strftime("%H:%M")

    if current_time == "07:45":
        bot.send_message(CHAT_ID, "Доброе утро ☀️ Не забудь взвеситься и записать время сна/пробуждения.")
    elif current_time == "21:00":
        bot.send_message(CHAT_ID, "Вечерний пинг 🌙 Не забудь записать настроение и витамины.")

if __name__ == "__main__":
    while True:
        send_reminders()
        time.sleep(60)
