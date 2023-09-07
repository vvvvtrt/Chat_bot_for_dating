import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram import executor
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
from data import *

# устанавливаем уровень логирования
logging.basicConfig(level=logging.INFO)

# создаем экземпляр бота
bot = Bot(token=token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

reg_user = {}


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    db = sqlite3.connect("user.db")
    sql = db.cursor()

    sql.execute("""CREATE TABLE IF NOT EXISTS movie (
                                        Id BIGINT,
                                        faculty TEXT,
                                        directions TEXT,
                                        degree TEXT,
                                        course INT,
                                        name TEXT,
                                        сity TEXT,
                                        tg_id TEXT,
                                        last_meeting BIGINT
                                    )""")

    db.commit()

    sql.execute("SELECT * FROM movie WHERE Id=?", (int(message.chat.id),))
    data = sql.fetchone()

    if data == None:
        reg_user[message.chat.id] = {}

        buttons = []
        for i in arr_faculty:
            buttons.append(KeyboardButton(text=i))
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(*buttons)

        await message.reply('Привет! \nДанный бот поможет завести тебе новые знакомства, провести хорошо время или подготовится к экзаменам')
        await bot.send_message(message.chat.id, 'Выбри свой факультет:', reply_markup=keyboard)

# Обработчик нажатия кнопки
@dp.callback_query_handler(text='button_clicked')
async def button_clicked(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Текст, который выдает бот.')

@dp.message_handler(content_types=["text"])
async def text(message):
    list_val = []
    for i in [values for values in arr_directions.values()]:
        for j in i:
            list_val.append(j)

    list_hobby = []
    for i in [values for values in arr_hobby.values()]:
        for j in i:
            list_hobby.append(j)

    if message.text in arr_faculty:
        reg_user[message.chat.id]["faculty"] = message.text
        await directions(message)

    elif message.text in list_val:
        reg_user[message.chat.id]["directions"] = message.text

        buttons = []
        for i in arr_degree:
            buttons.append(KeyboardButton(text=i))
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(*buttons)

        await bot.send_message(message.chat.id, 'Выбри степень:', reply_markup=keyboard)

    elif message.text in arr_degree:
        reg_user[message.chat.id]["degree"] = message.text

        buttons = []
        for i in arr_degree[message.text]:
            buttons.append(KeyboardButton(text=i))
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(*buttons)

        await bot.send_message(message.chat.id, 'Введите свой курс', reply_markup=keyboard)

    elif message.text in ["1", "2", "3", "4", "5"]:
        reg_user[message.chat.id]["year"] = message.text

        reply_markup = types.ReplyKeyboardRemove()
        await bot.send_message(message.chat.id, 'Введите свой родной город', reply_markup=reply_markup)

    elif message.text in arr_hobby:
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        for i in list(arr_hobby[message.text]) + ["↩️Назад↩️"]:
            keyboard.add(KeyboardButton(text=i))

        await bot.send_message(message.chat.id, 'Выбери свои интересы', reply_markup=keyboard)

    elif message.text in list_hobby:
        if "hobby" not in reg_user[message.chat.id]:
            reg_user[message.chat.id]["hobby"] = [message.text]
        else:
            reg_user[message.chat.id]["hobby"].append(message.text)

        await bot.send_message(message.chat.id, '✅' + message.text)

    elif message.text == "✅Готово✅":
        if "hobby" not in reg_user[message.chat.id]:
            await bot.send_message(message.chat.id, 'Выбери свои интересы')
        else:
            print(reg_user)

    elif message.text == "↩️Назад↩️":
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        for i in list(arr_hobby) + ["✅Готово✅"]:
            keyboard.add(KeyboardButton(text=i))

        await bot.send_message(message.chat.id, 'Выбери свои интересы', reply_markup=keyboard)

    elif message.chat.id in reg_user:
        if "year" in reg_user[message.chat.id] and "city" not in reg_user[message.chat.id]:
            reg_user[message.chat.id]["city"] = message.text
            reply_markup = types.ReplyKeyboardRemove()
            await bot.send_message(message.chat.id, 'Введите свое имя и фамилию', reply_markup=reply_markup)

        elif "city" in reg_user[message.chat.id] and "name" not in reg_user[message.chat.id]:
            reg_user[message.chat.id]["name"] = message.text

            keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
            for i in list(arr_hobby) + ["✅Готово✅"]:
                keyboard.add(KeyboardButton(text=i))

            await bot.send_message(message.chat.id, 'Выбери свои интересы', reply_markup=keyboard)



async def directions(message):
    buttons = []
    for i in arr_directions[message.text]:
        buttons.append(KeyboardButton(text=i))
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(*buttons)

    await bot.send_message(message.chat.id, 'Выбри специальноть:', reply_markup=keyboard)

# запускаем бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)