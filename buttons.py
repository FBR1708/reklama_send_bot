from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

keyboard = ReplyKeyboardMarkup(resize_keyboard=True,
                               keyboard=[[KeyboardButton(text='Reklama yaratish'),
                                          KeyboardButton(text='Reklama o\'chirish')],
                                         [KeyboardButton(text='Reklamani guruhlarga jo\'natish')]])
