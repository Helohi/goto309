import json

from telebot.async_telebot import AsyncTeleBot
from telebot import types

from realtime_database import RealtimeDatabase
from security.config import TELEGRAM_BOT_API

import keyboards
import text
import asyncio

from states import States

bot = AsyncTeleBot(TELEGRAM_BOT_API)
main_admin = 5701980281  # who gets the money
admins = [1301200391]
database = RealtimeDatabase()


@bot.message_handler(commands=['cancel'])
async def delete_state(message: types.Message):
    await bot.delete_state(message.from_user.id)
    await bot.send_message(message.chat.id, "Cancel. Lets start from beginning? /start\n\nОтмена. Начнем сначала? "
                                            "/start")
    database.set_user_state(str(message.from_user.id), States.no_state, auto_add_to_database=True,
                            telegram_nick=message.from_user.username)


@bot.message_handler(commands=['id'])
async def sending_id(message: types.Message):
    await bot.reply_to(message, str(message.from_user.id))


@bot.message_handler(func=lambda message: database.get_user_state(str(message.from_user.id), auto_add_to_database=True,
                                                                  telegram_nick=message.from_user.username) != States.
                     no_state,
                     commands=['help', 'start'])
async def send_please_cancel(message: types.Message):
    await bot.reply_to(message, "Please first /cancel current order!\n\nПожалуйста, сначала /cancel (отмените) "
                                "текущую операцию")


@bot.message_handler(commands=['help', 'start'])
async def send_welcome(message: types.Message):
    if message.from_user.id in admins + [main_admin]:
        await bot.send_message(message.from_user.id, text.HELP_FOR_ADMINS)
    await bot.send_message(message.chat.id, text.INTRO, reply_markup=keyboards.MENU)


@bot.message_handler(func=lambda message: message.text.lower() == "встать в очередь на завтра")
async def start_registration(message: types.Message):
    if database.get_user_state(message.from_user.id) == States.no_state:
        await bot.send_message(message.chat.id, "Пожалуйста, отправьте свои имя и фамилию")
        database.set_user_state(str(message.from_user.id), States.waiting_name, True, message.from_user.username)
    else:
        await bot.reply_to(message, "Please first /cancel current order!\n\nПожалуйста, сначала /cancel (отмените) "
                                    "текущую операцию")


@bot.message_handler(func=lambda message: database.get_user_state(message.from_user.id) == States.waiting_name)
async def getting_name_and_last_name(message: types.Message):
    for admin in admins + [main_admin]:
        await bot.send_message(admin, f"{message.from_user.id} or @{message.from_user.username}: {message.text}")
    await bot.send_message(message.chat.id, "Получил. А теперь отправь свой номер телефона")
    database.update_user(str(message.from_user.id), full_name=message.text)
    database.set_user_state(str(message.from_user.id), States.waiting_phone_number, True, message.from_user.username)


@bot.message_handler(func=lambda message: database.get_user_state(message.from_user.id) == States.waiting_phone_number)
async def getting_phone_number(message: types.Message):
    if message.text.startswith("+7") and " " not in message.text:
        for admin in admins + [main_admin]:
            await bot.send_message(admin, f"{message.from_user.id} or @{message.from_user.username}: {message.text}")
        await bot.send_message(message.chat.id,
                               "Получил! Осталось только отправить 500р на номер +79770338324 или на карту ",
                               reply_markup=keyboards.PAYMENT_SENT)
        database.set_user_state(str(message.from_user.id), States.waiting_payment)
        database.update_user(message.from_user.id, phone_number=message.text)
    else:
        await bot.reply_to(message, 'Можно использовать только российский номер и без пробелов. (+79770338324)')


@bot.callback_query_handler(func=lambda callback: callback.data == "payment_sent")
async def registering_order(callback: types.CallbackQuery):
    await bot.send_message(callback.message.chat.id, "На этом все. Мы проверим вашу оплату и завтра утром отправим "
                                                     "ваш номер в очереди (+ фото листка)")
    for admin in admins:
        await bot.send_message(admin, f"{callback.from_user.id} or @{callback.from_user.username}: Отправил оплату")
    await bot.send_message(main_admin, f"{callback.from_user.id} or @{callback.from_user.username}: "
                                       f"Отправил оплату", reply_markup=keyboards.
                           generate_inline_for_accepted_payments(str(callback.from_user.id)))
    database.set_user_state(callback.from_user.id, States.no_state)
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)


# ONLY FOR ADMINS👇

@bot.message_handler(commands=['show'], func=lambda message: message.from_user.id in admins + [main_admin])
async def show_user_data_to_admin(message: types.Message):
    lst_of_args = message.text.split()
    if len(lst_of_args) < 2:
        await bot.reply_to(message, "/show {user_id}. Например: /show 1212312312")
    await bot.reply_to(message, json.dumps(database.get_user_data(lst_of_args[1]), indent=4, ensure_ascii=False))


@bot.callback_query_handler(func=lambda callback: "PAYMENTACCEPTED" in callback.data
                                                  and callback.from_user.id == main_admin)
async def send_customer_payment_approval(callback: types.CallbackQuery):
    lst_of_args = callback.data.split()
    customer_id = lst_of_args[1]
    database.add_order_to_user(customer_id)
    for admin in admins + [main_admin]:
        await bot.send_message(admin, f"Главный подтвердил оплату от {customer_id}. Не забудьте завтра листок и ручку")


@bot.message_handler(func=lambda message: message.from_user.id in admins + [main_admin], content_types=['photo'])
async def send_media_to_customer(message: types.Message):
    customer_id = message.caption.split()[1]
    await bot.send_photo(customer_id, message.photo[0].file_id, f"\n\nЕсли есть вопросы вы можете написать: "
                                                                f"@{message.from_user.username}")
    await bot.reply_to(message, "sent|отправлено")


@bot.message_handler(func=lambda message: message.from_user.id in admins + [main_admin], commands=['send'])
async def send_reply_to_customer(message: types.Message):
    lst_of_args = message.text.split()
    if len(lst_of_args) < 2:
        return await bot.reply_to(message, "Что бы использовать /send вам нужно написать </send *user_id* *message*>.\n"
                                           "Например: /send 123123123 Ваш номер в очереди 1")
    text_to_send = " ".join(lst_of_args[2:])
    await bot.send_message(lst_of_args[1], text_to_send + f"\n\nЕсли есть вопросы вы можете написать: "
                                                          f"@{message.from_user.username}")
    await bot.reply_to(message, "sent|отправлено")


@bot.message_handler(func=lambda message: True)
async def show_error_message(message: types.Message):
    await bot.send_message(message.chat.id, text.MISUNDERSTANDING, reply_markup=keyboards.MENU)


def main():
    print("[SETTING UP]")
    print("[START]")
    asyncio.run(bot.polling())
    print("[FINISH]")


if __name__ == '__main__':
    main()
