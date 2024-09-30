import json

from telebot import TeleBot
from telebot import types

from realtime_database import RealtimeDatabase
from security.config import TELEGRAM_BOT_API

import keyboards
import text
import asyncio

from states import States

bot = TeleBot(TELEGRAM_BOT_API)
main_admin = 5701980281  # who gets the money
admins = [1301200391]
database = RealtimeDatabase()


@bot.message_handler(commands=['cancel'])
def delete_state(message: types.Message):
    bot.delete_state(message.from_user.id)
    bot.send_message(message.chat.id, "Cancel. Lets start from beginning? /start\n\nОтмена. Начнем сначала? "
                                      "/start")
    database.set_user_state(str(message.from_user.id), States.no_state, auto_add_to_database=True,
                            telegram_nick=message.from_user.username)


@bot.message_handler(commands=['id'])
def sending_id(message: types.Message):
    bot.reply_to(message, str(message.from_user.id))


@bot.message_handler(func=lambda message: database.get_user_state(str(message.from_user.id), auto_add_to_database=True,
                                                                  telegram_nick=message.from_user.username) != States.
                     no_state,
                     commands=['help', 'start'])
def send_please_cancel(message: types.Message):
    bot.reply_to(message, "Please first /cancel current order!\n\nПожалуйста, сначала /cancel (отмените) "
                          "текущую операцию")


@bot.message_handler(commands=['help', 'start'])
def send_welcome(message: types.Message):
    if message.from_user.id in admins + [main_admin]:
        bot.send_message(message.from_user.id, text.HELP_FOR_ADMINS)
    bot.send_message(message.chat.id, text.INTRO, reply_markup=keyboards.MENU)


@bot.message_handler(func=lambda message: message.text.lower() == "встать в очередь на завтра")
def start_registration(message: types.Message):
    if database.get_user_state(message.from_user.id) == States.no_state:
        bot.send_message(message.chat.id, "Пожалуйста, отправьте свои имя и фамилию")
        database.set_user_state(str(message.from_user.id), States.waiting_name, True, message.from_user.username)
    else:
        bot.reply_to(message, "Please first /cancel current order!\n\nПожалуйста, сначала /cancel (отмените) "
                              "текущую операцию")


@bot.message_handler(func=lambda message: database.get_user_state(message.from_user.id) == States.waiting_name)
def getting_name_and_last_name(message: types.Message):
    for admin in admins + [main_admin]:
        bot.send_message(admin, f"{message.from_user.id} or @{message.from_user.username}: {message.text}")
    bot.send_message(message.chat.id, "Получил. А теперь отправь свой номер телефона")
    database.update_user(str(message.from_user.id), full_name=message.text)
    database.set_user_state(str(message.from_user.id), States.waiting_phone_number, True, message.from_user.username)


@bot.message_handler(func=lambda message: database.get_user_state(message.from_user.id) == States.waiting_phone_number)
def getting_phone_number(message: types.Message):
    if message.text.startswith("+7") and " " not in message.text:
        for admin in admins + [main_admin]:
            bot.send_message(admin, f"{message.from_user.id} or @{message.from_user.username}: {message.text}")
        bot.send_message(message.chat.id,
                         "Получил! Осталось только отправить 500р на номер +79770338324 или на карту 2202208337539663",
                         reply_markup=keyboards.PAYMENT_SENT)
        database.set_user_state(str(message.from_user.id), States.waiting_payment)
        database.update_user(message.from_user.id, phone_number=message.text)
    else:
        bot.reply_to(message, 'Можно использовать только российский номер и без пробелов. (+79770338324)')


@bot.callback_query_handler(func=lambda callback: callback.data == "payment_sent")
def registering_order(callback: types.CallbackQuery):
    bot.send_message(callback.message.chat.id, "На этом все. Мы проверим вашу оплату и завтра утром отправим "
                                               "ваш номер в очереди (+ фото листка)")
    for admin in admins:
        bot.send_message(admin, f"{callback.from_user.id} or @{callback.from_user.username}: Отправил оплату")
    bot.send_message(main_admin, f"{callback.from_user.id} or @{callback.from_user.username}: "
                                 f"Отправил оплату", reply_markup=keyboards.
                     generate_inline_for_accepted_payments(str(callback.from_user.id)))
    database.set_user_state(callback.from_user.id, States.no_state)
    bot.delete_message(callback.message.chat.id, callback.message.message_id)


# ONLY FOR ADMINS👇

@bot.message_handler(commands=['show'], func=lambda message: message.from_user.id in admins + [main_admin])
def show_user_data_to_admin(message: types.Message):
    lst_of_args = message.text.split()
    if len(lst_of_args) < 2:
        bot.reply_to(message, "/show {user_id}. Например: /show 1212312312")
    bot.reply_to(message, json.dumps(database.get_user_data(lst_of_args[1]), indent=4, ensure_ascii=False))


@bot.callback_query_handler(func=lambda callback: "PAYMENTACCEPTED" in callback.data
                                                  and callback.from_user.id == main_admin)
def send_customer_payment_approval(callback: types.CallbackQuery):
    lst_of_args = callback.data.split()
    customer_id = lst_of_args[1]
    database.add_order_to_user(customer_id)
    for admin in admins + [main_admin]:
        bot.send_message(admin, f"Главный подтвердил оплату от {customer_id}. Не забудьте завтра листок и ручку")


@bot.message_handler(func=lambda message: message.from_user.id in admins + [main_admin], content_types=['photo'])
def send_media_to_customer(message: types.Message):
    customer_id = message.caption.split()[1]
    bot.send_photo(customer_id, message.photo[0].file_id, f"\n\nЕсли есть вопросы вы можете написать: "
                                                          f"@{message.from_user.username}")
    bot.reply_to(message, "sent|отправлено")


@bot.message_handler(func=lambda message: message.from_user.id in admins + [main_admin], commands=['send'])
def send_reply_to_customer(message: types.Message):
    lst_of_args = message.text.split()
    if len(lst_of_args) < 2:
        return bot.reply_to(message, "Что бы использовать /send вам нужно написать </send *user_id* *message*>.\n"
                                     "Например: /send 123123123 Ваш номер в очереди 1")
    text_to_send = " ".join(lst_of_args[2:])
    bot.send_message(lst_of_args[1], text_to_send + f"\n\nЕсли есть вопросы вы можете написать: "
                                                    f"@{message.from_user.username}")
    bot.reply_to(message, "sent|отправлено")


@bot.message_handler(func=lambda message: True)
def show_error_message(message: types.Message):
    bot.send_message(message.chat.id, text.MISUNDERSTANDING, reply_markup=keyboards.MENU)


def main():
    print("[SETTING UP]")
    print("[START]")
    bot.polling()
    print("[FINISH]")


if __name__ == '__main__':
    main()
