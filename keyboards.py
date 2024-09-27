from telebot import types

MENU = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
MENU.add(types.KeyboardButton("Встать в очередь на завтра"))

PAYMENT_SENT = types.InlineKeyboardMarkup()
PAYMENT_SENT.add(types.InlineKeyboardButton("Отправил|Sent", callback_data="payment_sent"))
