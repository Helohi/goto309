from typing import Union

from telebot import types

MENU = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
MENU.add(types.KeyboardButton("Встать в очередь на завтра"))

PAYMENT_SENT = types.InlineKeyboardMarkup()
PAYMENT_SENT.add(types.InlineKeyboardButton("Отправил|Sent", callback_data="payment_sent"))


def generate_inline_for_accepted_payments(customer_telegram_id: Union[int, str]):
    customer_telegram_id = str(customer_telegram_id)
    PAYMENT_ACCEPTED = types.InlineKeyboardMarkup()
    PAYMENT_ACCEPTED.add(types.InlineKeyboardButton("Подтвердить перевод",
                                                    callback_data=f"PAYMENTACCEPTED {customer_telegram_id}"))
    return PAYMENT_ACCEPTED
