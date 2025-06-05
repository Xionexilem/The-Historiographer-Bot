from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)

cancel = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Отмена")],
], resize_keyboard=True)

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Поиск"), KeyboardButton(text="Помощь")],
], resize_keyboard=True)

more_info = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Демографические данные", callback_data='demographic data')],
    [InlineKeyboardButton(text="Географическая информация", callback_data='geographical information')],
    [InlineKeyboardButton(text="Профессиональная деятельность", callback_data='professional activity')],
    [InlineKeyboardButton(text="Политическая/организационная принадлежность", callback_data='political-organizational affiliation')]
    ])