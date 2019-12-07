import datetime
import json
import logging
import os
import time
from multiprocessing import Process

import telebot

from dropbox_service import TransferData

logging.basicConfig(filename='errors_log.log', level=logging.ERROR)

ADMIN_ID = int(os.environ.get("ADMIN_ID", None))
LERA_ID = int(os.environ.get("LERA_ID", None))

HOUR_FOR_ALERT_MESSAGE = int(os.environ.get('HOUR_FOR_ALERT_MESSAGE'))
HOUR_FOR_ALERT_MESSAGE_SECOND = int(os.environ.get('HOUR_FOR_ALERT_MESSAGE_SECOND'))

WHITE_LIST_IDS = [ADMIN_ID, LERA_ID]
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
bot = telebot.TeleBot(TOKEN_TELEGRAM)


@bot.message_handler(commands=['start'], func=lambda x: x.from_user.id in WHITE_LIST_IDS)
def send_welcome(message):
    bot.send_message(ADMIN_ID, "Start use by user: {}".format(
        message.from_user)) if message.from_user.id not in WHITE_LIST_IDS else None
    bot.reply_to(message, "send me photo, after description and only in this way")


@bot.message_handler(content_types=['photo'], func=lambda x: x.from_user.id in WHITE_LIST_IDS)
def get_photo_messages(message):
    try:
        print(f'get photo {message}')
        bot.send_message(ADMIN_ID, "Start use by user: {}".format(
            message.from_user)) if message.from_user.id not in WHITE_LIST_IDS else None
        photo_id = message.photo[-1].file_id
        file = bot.get_file(photo_id)
        downloaded_file = bot.download_file(file.file_path)
        with open(f'{datetime.datetime.now().strftime("%Y_%m_%d")}_{photo_id[:15]}.jpg', 'wb') as f:
            f.write(downloaded_file)
        drop_file = TransferData(f'{datetime.datetime.now().strftime("%Y_%m_%d")}_{photo_id[:15]}.jpg')
        drop_file.upload_file()
        print('photo uploaded on dropbox')
        os.remove(f'{datetime.datetime.now().strftime("%Y_%m_%d")}_{photo_id[:15]}.jpg')
        print('photo deleted from heroku storage')
        bot.reply_to(message, "photo saved")
    except Exception as e:
        bot.reply_to(message, f'Error {e.args}')


@bot.message_handler(content_types=["text"],
                     func=lambda x: x.text not in ['check', 'reset'] and x.from_user.id in WHITE_LIST_IDS)
def get_text_message(message):
    try:
        print(f'get text {message}')
        bot.send_message(ADMIN_ID, "Start use by user: {}".format(
            message.from_user)) if message.from_user.id not in WHITE_LIST_IDS else None
        with open(f'{datetime.datetime.now().strftime("%Y_%m_%d")}.txt', 'w') as f:
            f.write(message.text)
        drop_file = TransferData(f'{datetime.datetime.now().strftime("%Y_%m_%d")}.txt')
        drop_file.upload_file()
        print('text file uploaded to dropbox')
        os.remove(f'{datetime.datetime.now().strftime("%Y_%m_%d")}.txt')
        print('text file removed from heroku storage')
        bot.reply_to(message, "message saved")
    except Exception as e:
        bot.reply_to(message, f'Error {e.args}')


@bot.message_handler(content_types=["text"], func=lambda x: x.text == 'check' and x.from_user.id in WHITE_LIST_IDS)
def check_message(message):
    try:
        print(f'start check exists directory {datetime.datetime.now()}')
        bot.send_message(ADMIN_ID, "Start use by user: {}".format(
            message.from_user)) if message.from_user.id not in WHITE_LIST_IDS else None
        data = f'{datetime.datetime.now().strftime("%Y_%m_%d")}'
        drop_file = TransferData()
        message_check = drop_file.check_dir_data(data)
        print(f'Result of checking {message_check}')
        bot.reply_to(message, message_check)
    except Exception as e:
        bot.reply_to(message, f'Error {e.args}')


@bot.message_handler(content_types=["text"], func=lambda x: x.text == 'reset' and x.from_user.id in WHITE_LIST_IDS)
def del_today_files(message):
    try:
        print(f'start reset {datetime.datetime.now()}')
        bot.send_message(ADMIN_ID, "Start use by user: {}".format(
            message.from_user)) if message.from_user.id not in WHITE_LIST_IDS else None
        data = f'{datetime.datetime.now().strftime("%Y_%m_%d")}'
        drop_file = TransferData()
        message_reset = drop_file.delete_today_dir(data)
        print(f'finish reset with answer {message_reset}')
        bot.reply_to(message, message_reset)
    except Exception as e:
        bot.reply_to(message, f'Error {e.args}')


def send_message(*args, **kwargs):
    print('start action')
    bot.send_message(LERA_ID, "Have a Good Day and don't forget to take a photo if Anton forgets))))")
    bot.send_message(ADMIN_ID, "Don't forget to take a photo!!!")


def send_today_history(dir_name):
    print("check_history")
    old_data = dir_name.split("_")
    old_data[0] = str(int(old_data[0]) - 1)
    old_data = "_".join(old_data)
    dbx = TransferData()
    files = dbx.get_history(old_data)
    if files:
        bot.send_message(LERA_ID, f'Ваша история за {old_data}')
        bot.send_message(ADMIN_ID, f'Ваша история за {old_data}')
        for file in files:
            if json.loads(file.headers['dropbox-api-result'])['name'].endswith(".txt"):
                bot.send_message(LERA_ID, file.content.decode("utf-8"))
                bot.send_message(ADMIN_ID, file.content.decode("utf-8"))
            else:
                bot.send_photo(LERA_ID, photo=file.content)
                bot.send_photo(ADMIN_ID, photo=file.content)


def cron_send_messages(period, action):
    while True:
        if datetime.datetime.now().hour < period:
            print("calculate period_sleep")
            period_sleep = ((period - datetime.datetime.now().hour) * 60) - datetime.datetime.now().minute - (datetime.datetime.now().second / 60)
            print(f"period_sleep{period_sleep}")
            time.sleep(period_sleep * 60)
            print("end period_sleep")
        else:
            print("calculate period_sleep")
            period_sleep = ((24 + period - datetime.datetime.now().hour) * 60) - datetime.datetime.now().minute - (datetime.datetime.now().second / 60)
            print(f"period_sleep{period_sleep}")
            time.sleep(period_sleep * 60)
            print("end period_sleep")
        action(datetime.datetime.now().strftime("%Y_%m_%d"))


p1 = Process(target=cron_send_messages, args=(HOUR_FOR_ALERT_MESSAGE, send_message, ))
p1.start()

p2 = Process(target=cron_send_messages, args=(HOUR_FOR_ALERT_MESSAGE_SECOND, send_today_history, ))
p2.start()

try:
    bot.infinity_polling(none_stop=True, interval=0)
except Exception as e:
    print(e)
    logging.error('{}: {}'.format(datetime.datetime.now(), e))
