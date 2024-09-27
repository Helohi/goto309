from telebot.async_telebot import AsyncTeleBot
from telebot.states import State, StatesGroup
from telebot.storage import StateMemoryStorage
from telebot import types, asyncio_filters

import keyboards
import text
import asyncio

state_storage = StateMemoryStorage()
bot = AsyncTeleBot("7785842674:AAERrK0DXfluKLLGshkX0xd6jCxUnUxqE1M", state_storage=state_storage)
main_admin = 5701980281


class MyStates(StatesGroup):
    waiting_name = State()
    waiting_phone_number = State()
    waiting_payment = State()
    on_moderation = State()


@bot.message_handler(commands=['cancel'])
async def delete_state(message: types.Message):
    await bot.delete_state(message.from_user.id)
    await bot.send_message(message.chat.id, "Cancel. Lets start from beginning? /start\n\nОтмена. Начнем сначала? "
                                            "/start")


@bot.message_handler(commands=['id'])
async def sending_id(message: types.Message):
    await bot.reply_to(message, str(message.from_user.id))


@bot.message_handler(state="*", commands=['help', 'start'])
async def send_please_cancel(message: types.Message):
    await bot.reply_to(message, "Please first /cancel current order!\n\nПожалуйста, сначала /cancel (отмените) "
                                "текущую операцию")


@bot.message_handler(commands=['help', 'start'])
async def send_welcome(message: types.Message):
    await bot.send_message(message.chat.id, text.INTRO, reply_markup=keyboards.MENU)


@bot.message_handler(func=lambda message: message.text.lower() == "встать в очередь на завтра")
async def start_registration(message: types.Message):
    await bot.send_message(message.chat.id, "Пожалуйста, отправьте свои имя и фамилию")
    await bot.set_state(message.from_user.id, MyStates.waiting_name)


@bot.message_handler(state=MyStates.waiting_name, func=lambda message: True)
async def getting_name_and_last_name(message: types.Message):
    await bot.send_message(main_admin, f"{message.from_user.id} or {message.from_user.username}: {message.text}")
    await bot.send_message(message.chat.id, "Получил. А теперь отправь свой номер телефона")
    await bot.set_state(message.from_user.id, MyStates.waiting_phone_number)


@bot.message_handler(state=MyStates.waiting_name)
async def getting_phone_number(message: types.Message):
    if message.text.startswith("+7") and " " not in message.text:
        await bot.send_message(main_admin, f"{message.from_user.id} or {message.from_user.username}: {message.text}")
        await bot.send_message(message.chat.id, "Получил! Осталось только отправить 1000р на номер +79770338324",
                               reply_markup=keyboards.PAYMENT_SENT)
        await bot.set_state(message.from_user.id, MyStates.waiting_payment)
    else:
        await bot.reply_to(message, 'Можно использовать только российский номер и без пробелов. (+79210347595)')


@bot.callback_query_handler(func=lambda message: message.text == "payment_sent", state=MyStates.waiting_payment)
async def registering_order(message: types.Message):
    await bot.send_message(message.chat.id, "На этом все. Мы проверим вашу оплату и завтра утром отправим ваш номер в "
                                            "очереди")
    await bot.send_message(main_admin, f"{message.from_user.id} or {message.from_user.username}: Оплату подтвердил")
    await bot.delete_state(message.from_user.id)


@bot.message_handler(func=lambda message: True)
async def show_error_message(message: types.Message):
    await bot.send_message(message.chat.id, text.MISUNDERSTANDING, reply_markup=keyboards.MENU)


def main():
    print("[SETTING UP]")
    bot.add_custom_filter(asyncio_filters.StateFilter(bot))
    print("[START]")
    asyncio.run(bot.polling())
    print("[FINISH]")


if __name__ == '__main__':
    main()
