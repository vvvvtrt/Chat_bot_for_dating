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
import json
import asyncio

lock = asyncio.Lock()

# устанавливаем уровень логирования
logging.basicConfig(level=logging.INFO)

# создаем экземпляр бота
bot = Bot(token=token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

reg_user = {}
queue_search = {"Подготовка к сессии": {}, "Поиск по интересам": [], "Поиск по родному городу": [],
                "Поиск компании для прогулки": []}
in_queue = {}


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    db = sqlite3.connect("user.db")
    sql = db.cursor()

    sql.execute("""CREATE TABLE IF NOT EXISTS user (
                                               Id BIGINT,
                                               faculty TEXT,
                                               directions TEXT,
                                               degree TEXT,
                                               course INT,
                                               name TEXT,
                                               city TEXT,
                                               hobby TEXT,
                                               tg_id TEXT,
                                               last_meeting BIGINT
                                           )""")

    db.commit()

    sql.execute("SELECT * FROM user WHERE Id=?", (int(message.chat.id),))
    data = sql.fetchone()

    if data == None:
        reg_user[message.chat.id] = {}

        buttons = []
        for i in arr_faculty:
            buttons.append(KeyboardButton(text=i))
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(*buttons)

        await message.reply(
            'Привет! \nДанный бот поможет завести тебе новые знакомства, провести хорошо время или подготовится к экзаменам')
        await bot.send_message(message.chat.id, 'Выбри свой факультет:', reply_markup=keyboard)
    else:
        await menuSearch(message)

    sql.close()
    db.close()


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

    elif message.text in arr_search:
        if message.chat.id not in in_queue:
            if message.text == arr_search[0]:
                db = sqlite3.connect("user.db")
                sql = db.cursor()

                sql.execute(f"SELECT * FROM user WHERE id = {int(message.chat.id)}")
                data = sql.fetchone()

                in_queue[message.chat.id] = list(data) + [0]

                if data[2] in queue_search[message.text]:
                    async with lock:
                        for i in queue_search[message.text][data[2]]:
                            if i[1] == data[2] and i[2] == data[3] and i[3] == data[4]:
                                await bot.send_message(message.chat.id,
                                                       f"""Мы нашли Вам человека с которым вы можете подготовится к сессии, напишите: @{i[4]}""",
                                                       reply_markup=types.ReplyKeyboardRemove())
                                await bot.send_message(i[0],
                                                       f"""Мы нашли Вам человека с которым вы можете подготовится к сессии, напишите: @{data[8]}""",
                                                       reply_markup=types.ReplyKeyboardRemove())

                                del in_queue[i[0]]
                                queue_search[message.text][data[2]].remove(i)
                                del in_queue[message.chat.id]
                                return

                        queue_search[message.text][data[2]] = [[message.chat.id, data[2], data[3], data[4], data[8]]]
                        keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton(text="Отмена"))
                        await bot.send_message(message.chat.id, 'Вы добавлены в очередь', reply_markup=keyboard)

                else:
                    async with lock:
                        queue_search[message.text][data[2]] = [[message.chat.id, data[2], data[3], data[4], data[8]]]
                        keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton(text="Отмена"))
                        await bot.send_message(message.chat.id, 'Вы добавлены в очередь', reply_markup=keyboard)


            elif message.text == arr_search[2]:
                db = sqlite3.connect("user.db")
                sql = db.cursor()

                sql.execute(f"SELECT * FROM user WHERE id = {int(message.chat.id)}")
                data = sql.fetchone()
                in_queue[message.chat.id] = list(data) + [2]

                async with lock:
                    for i in queue_search[arr_search[2]]:
                        if i[1].lower() in data[6].lower() or data[6].lower() in i[1].lower():
                            await bot.send_message(message.chat.id,
                                                   f"""Мы нашли Вам человека из Вашего города, напишите: @{i[2]}""",
                                                   reply_markup=types.ReplyKeyboardRemove())
                            await bot.send_message(i[0],
                                                   f"""Мы нашли Вам человека из Вашего города, напишите: @{data[8]}""",
                                                   reply_markup=types.ReplyKeyboardRemove())

                            del in_queue[i[0]]
                            queue_search[message.text].remove(i)
                            del in_queue[message.chat.id]
                            return

                    queue_search[message.text].append([message.chat.id, data[6], data[8]])
                    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton(text="Отмена"))
                    await bot.send_message(message.chat.id, 'Вы добавлены в очередь', reply_markup=keyboard)

        else:
            await bot.send_message(message.chat.id, 'Вы уже в очереди')


    elif message.text == "Отмена":
        async with lock:
            if message.chat.id in in_queue:
                if in_queue[message.chat.id][-1] == 0:
                    for i in queue_search[arr_search[0]]:
                        if i[0] == message.chat.id:
                            queue_search[arr_search[0]].remove(i)
                            del in_queue[message.chat.id]
                            await bot.send_message(message.chat.id, 'Вы удалены из очереди',
                                                   reply_markup=types.ReplyKeyboardRemove())
                            return
                if in_queue[message.chat.id][-1] == 2:
                    for i in queue_search[arr_search[2]]:
                        if i[0] == message.chat.id:
                            queue_search[arr_search[2]].remove(i)
                            del in_queue[message.chat.id]
                            await bot.send_message(message.chat.id, 'Вы удалены из очереди',
                                                   reply_markup=types.ReplyKeyboardRemove())
                            return
            else:
                await bot.send_message(message.chat.id, 'Вас нет в очереди', reply_markup=types.ReplyKeyboardRemove())



    elif message.text == "✅Готово✅":
        if "hobby" not in reg_user[message.chat.id]:
            await bot.send_message(message.chat.id, 'Выбери свои интересы')
        else:
            await endRegistration(message)
            reply_markup = types.ReplyKeyboardRemove()
            await bot.send_message(message.chat.id, 'Вы успешно зарегестрировались', reply_markup=reply_markup)
            await menuSearch(message)


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


async def endRegistration(message):
    db = sqlite3.connect("user.db")
    sql = db.cursor()

    sql.execute("""CREATE TABLE IF NOT EXISTS user (
                                            Id BIGINT,
                                            faculty TEXT,
                                            directions TEXT,
                                            degree TEXT,
                                            course INT,
                                            name TEXT,
                                            city TEXT,
                                            hobby TEXT,
                                            tg_id TEXT,
                                            last_meeting BIGINT
                                        )""")

    sql.execute('INSERT INTO user VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (int(message.chat.id), reg_user[message.chat.id]["faculty"],
                 reg_user[message.chat.id]["directions"], reg_user[message.chat.id]["degree"],
                 reg_user[message.chat.id]["year"], reg_user[message.chat.id]["name"],
                 reg_user[message.chat.id]["city"], json.dumps(reg_user[message.chat.id]["hobby"]),
                 message.from_user.username, 0))

    db.commit()
    sql.close()
    db.close()


async def readSQL():
    db = sqlite3.connect("user.db")
    sql = db.cursor()

    sql.execute("""CREATE TABLE IF NOT EXISTS user (
                                                Id BIGINT,
                                                faculty TEXT,
                                                directions TEXT,
                                                degree TEXT,
                                                course INT,
                                                name TEXT,
                                                city TEXT,
                                                hobby TEXT,
                                                tg_id TEXT,
                                                last_meeting BIGINT
                                            )""")

    sql.execute('SELECT * FROM user')
    data = sql.fetchall()

    for row in data:
        print(row)
        deserialized_array = json.loads(row[7])
        print(deserialized_array)

    sql.close()
    db.close()


async def menuSearch(message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for i in arr_search:
        keyboard.add(KeyboardButton(text=i))

    await bot.send_message(message.chat.id, 'Выберите, с какой целью ищите', reply_markup=keyboard)


# запускаем бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
