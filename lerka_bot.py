import telebot
from dropbox_service import TransferData
import os
import logging
import datetime

logging.basicConfig(filename='errors_log.log', level=logging.ERROR)

ADMIN_ID = int(os.environ.get("ADMIN_ID", None))
LERA_ID = int(os.environ.get("LERA_ID", None))

WHITE_LIST_IDS = [ADMIN_ID, LERA_ID]
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
bot = telebot.TeleBot(TOKEN_TELEGRAM)


@bot.message_handler(commands=['start'], func=lambda x: x.from_user.id in WHITE_LIST_IDS)
def send_welcome(message):
    bot.send_message(ADMIN_ID, "Start use by user: {}".format(message.from_user))
    bot.reply_to(message, "send me photo, after description and only in this way")


@bot.message_handler(content_types=['photo'], func=lambda x: x.from_user.id in WHITE_LIST_IDS)
def get_photo_messages(message):
    photo_id = message.photo[-1].file_id
    file = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file.file_path)
    with open(f'{datetime.datetime.now().strftime("%Y_%m_%d")}.jpg', 'wb') as f:
        f.write(downloaded_file)
    drop_file = TransferData(f'{datetime.datetime.now().strftime("%Y_%m_%d")}.jpg')
    drop_file.upload_file()
    os.remove(f'{datetime.datetime.now().strftime("%Y_%m_%d")}.jpg')


@bot.message_handler(content_types=["text"], func=lambda x: x.text != 'check' and x.from_user.id in WHITE_LIST_IDS)
def get_text_message(message):
    with open(f'{datetime.datetime.now().strftime("%Y_%m_%d")}.txt', 'w') as f:
        f.write(message.text)
    drop_file = TransferData(f'{datetime.datetime.now().strftime("%Y_%m_%d")}.txt')
    drop_file.upload_file()
    os.remove(f'{datetime.datetime.now().strftime("%Y_%m_%d")}.txt')


@bot.message_handler(content_types=["text"], func=lambda x: x.text == 'check' and x.from_user.id in WHITE_LIST_IDS)
def check_message(message):
    data = f'{datetime.datetime.now().strftime("%Y_%m_%d")}'
    drop_file = TransferData()
    message_check = drop_file.check_dir_data(data)
    bot.reply_to(message, message_check)


try:
    bot.infinity_polling(none_stop=True, interval=0)
except Exception as e:
    print(e)
    logging.error('{}: {}'.format(datetime.datetime.now(), e))
    raise e
