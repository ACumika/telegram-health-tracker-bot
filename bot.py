import logging
import time
from datetime import datetime
import telebot
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import threading
#from sheets import log_data

# Загружаем конфиг
with open("config.json") as f:
    config = json.load(f)

TOKEN = config["telegram_token"]
CHAT_ID = config["chat_id"]
bot = telebot.TeleBot(TOKEN)

# Включение логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка подключения
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gspread.authorize(creds)

# Подключение к таблице
sheet = client.open_by_key("1oWuqBtspBuDIJkyPd1cRSzwtMk2v1YYYtYNPsf1e5Xg")  # вставь свой ID таблицы
worksheet = sheet.worksheet("Данные")  # имя листа

# Словарь соответствия колонок
column_map = {
        "Вес": 2,
        "Сон с": 5,
        "Пробуждение": 4,
        "Настроение": 16
    }

# Команда /ping
@bot.message_handler(commands=['ping'])
def send_ping(message):
    bot.reply_to(message, "Понял, пингую тебя!")
    
# Запись данных
def log_data(column, value, yesterday = False):
    today = datetime.today().strftime("%d.%m.%Y")
    print(today)
    all_data = worksheet.get_all_records()
    print(all_data)
    dates = [row['Дата'] for row in all_data]
    print(dates)

    if today in dates:
        print("использую текущую дату")
        if yesterday == True:
            row_number = dates.index(today) + 1  # строка в таблице за прошлый день
        else:
            row_number = dates.index(today) + 2  # строка в таблице
    else:
        print("делаю новую дату")
        row_number = len(all_data) + 2
        worksheet.update_cell(row_number, 1, today)

    if column in column_map:
        worksheet.update_cell(row_number, column_map[column], value)

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Бот запущен и работает!")
    
def get_data():
    all_data = worksheet.get_all_records()
    dates = [row['Дата'] for row in all_data]
    weight = [row['Вес'] for row in all_data]
    return [all_data, dates, weight]

def add_data():
    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        today = datetime.today().strftime("%d.%m.%Y")

        print("иду брать дату в адд_дата")
        data = get_data()
        if today not in data[1]:
            row_number = len(data[0]) + 2
            worksheet.update_cell(row_number, 1, today)
        time.sleep(3600)


# Напоминания по времени
def send_reminders_weight():
    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        today = datetime.today().strftime("%d.%m.%Y")
        
        if current_time == "07:45":
            print("иду брать дату в весе до напоминаний")
            data = get_data()
            if today in data[1]:
                row_number = data[1].index(today) + 2
                while len(data[2])<len(data[1]) or data[2][len(data[2])-1] == '':
                    bot.send_message(CHAT_ID, "Доброе утро ☀️ Не забудь взвеситься и записать вес. Используй формат: /weight 72.5")
                    time.sleep(60*5)
                    print("иду брать дату в весе после напоминаний")
                    data = get_data()
        time.sleep(60)

def send_reminders_sleep():
    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        today = datetime.today().strftime("%d.%m.%Y")

        if current_time == "7:45":
            print("иду брать дату в сне до напоминаний")
            data = get_data()
            if today in data[1]:
                row_number = data[1].index(today) + 2
                while len(data[4])<len(data[1]) or data[4][len(data[4])-1] == '':
                    bot.send_message(CHAT_ID, "Доброе утро ☀️ записать время сна/пробуждения. Формат: /sleep 00:30 07:30")
                    time.sleep(60*5)
                    print("иду брать дату в сне после напоминаний")
                    data = get_data()
        time.sleep(60)

@bot.message_handler(commands=['weight'])
def handle_weight(message):
    print("зашел в функцию веса")
    try:
        weight = message.text.split()[1]
        print("ща буду log функцию дергать")
        log_data("Вес", weight)
        bot.reply_to(message, f"Вес {weight} кг записан.")
    except:
        bot.reply_to(message, "Используй формат: /weight 72.5")

@bot.message_handler(commands=['sleep'])
def handle_sleep(message):
    try:
        sleep_from, wake_up = message.text.split()[1:3]
        log_data("Сон с", sleep_from, yesterday = True)
        log_data("Пробуждение", wake_up)
        bot.reply_to(message, f"Сон с {sleep_from} до {wake_up} записан.")
    except:
        bot.reply_to(message, "Формат: /sleep 00:30 07:30")

@bot.message_handler(commands=['mood'])
def handle_mood(message):
    mood = " ".join(message.text.split()[1:])
    log_data("Настроение", mood)
    bot.reply_to(message, f"Настроение записано: {mood}")

# Запускаем бота и напоминания в цикле
if __name__ == "__main__":
    while True:
        try:
            add_data_func = threading.Thread(target=add_data, daemon=True)
            send_reminders_weight_func = threading.Thread(target=send_reminders_weight, daemon=True)
            send_reminders_sleep_func = threading.Thread(target=send_reminders_sleep, daemon=True)
            add_data_func.start()
            send_reminders_weight_func.start()
            send_reminders_sleep_func.start()
            bot.infinity_polling(none_stop=True, timeout=60)
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            time.sleep(15)
