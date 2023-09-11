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
from PIL import Image, ImageDraw, ImageFont
import openai

lock = asyncio.Lock()

# устанавливаем уровень логирования
logging.basicConfig(level=logging.INFO)

# создаем экземпляр бота
bot = Bot(token=token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
openai.api_key = token_ai

reg_user = {}
queue_search = {"Подготовка к сессии": {}, "Поиск по интересам": [], "Поиск по родному городу": [],
                "Поиск компании для прогулки": []}
in_queue = {}


@dp.message_handler(commands=['start', 'menu'])
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
        await bot.send_message(message.chat.id, 'Выберите свой факультет:', reply_markup=keyboard)
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

    list_varia = []
    for i in [values for values in arr_varia.values()]:
        for j in i:
            list_varia.append(j)

    if message.text in arr_faculty:
        reg_user[message.chat.id]["faculty"] = message.text
        await directions(message)

    elif message.text in list_val:
        reg_user[message.chat.id]["directions"] = message.text

        buttons = []
        for i in arr_degree:
            buttons.append(KeyboardButton(text=i))
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(*buttons)

        await bot.send_message(message.chat.id, 'Выберите ступень:', reply_markup=keyboard)

    elif message.text in arr_degree:
        reg_user[message.chat.id]["degree"] = message.text

        buttons = []
        for i in arr_degree[message.text]:
            buttons.append(KeyboardButton(text=i))
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(*buttons)

        await bot.send_message(message.chat.id, 'Выберите свой курс', reply_markup=keyboard)

    elif message.text in ["1", "2", "3", "4", "5"]:
        reg_user[message.chat.id]["year"] = message.text

        reply_markup = types.ReplyKeyboardRemove()
        await bot.send_message(message.chat.id, 'Введите свой родной город', reply_markup=reply_markup)

    elif message.text in arr_hobby:
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        for i in list(arr_hobby[message.text]) + ["↩️Назад↩️"]:
            keyboard.add(KeyboardButton(text=i))

        await bot.send_message(message.chat.id, 'Выберите свои интересы', reply_markup=keyboard)

    elif message.text in list_hobby + list_varia:
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
                        await bot.send_message(message.chat.id, 'Идет поиск')
                        for i in queue_search[message.text][data[2]]:
                            if i[1] == data[2] and i[2] == data[3] and i[3] == data[4]:
                                response = openai.ChatCompletion.create(
                                    model="gpt-3.5-turbo",
                                    messages=[
                                        {"role": "user",
                                         "content": f"Как начать диолог коротко в социальных сетях используя в каждом знакмстве только 1 интерес, и выведи не более 5 пунктов для начала диалога, если у нас общие интересы: подготовка к сессии"}
                                    ]
                                )

                                text_ai = response['choices'][0]['message']['content']

                                photo = open(f'profile/{i[0]}.jpeg', 'rb')
                                await bot.send_photo(message.chat.id, photo,
                                                     f"""Мы нашли Вам человека с которым вы можете подготовится к сессии\nСовет от искуственного интелекта, как начать диалог:\n {text_ai}\nнапишите: @{i[4]}""",
                                                     reply_markup=types.ReplyKeyboardRemove())
                                await bot.send_message(message.chat.id, 'Чтобы вернутся в меню: /menu')
                                photo.close()
                                photo = open(f'profile/{message.chat.id}.jpeg', 'rb')
                                await bot.send_photo(i[0], photo,
                                                     f"""Мы нашли Вам человека с которым вы можете подготовится к сессии\nСовет от искуственного интелекта, как начать диалог:\n {text_ai}\nнапишите: @{data[8]}""",
                                                     reply_markup=types.ReplyKeyboardRemove())
                                photo.close()
                                await bot.send_message(i[0], 'Чтобы вернутся в меню: /menu')
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

            elif message.text == arr_search[1]:
                db = sqlite3.connect("user.db")
                sql = db.cursor()

                sql.execute(f"SELECT * FROM user WHERE id = {int(message.chat.id)}")
                data = sql.fetchone()
                in_queue[message.chat.id] = list(data) + [1]

                async with lock:
                    await bot.send_message(message.chat.id, 'Идет поиск')
                    arr = set(json.loads(data[7]))
                    arr_similarity = []
                    sum_similarity = 0
                    for i in queue_search[arr_search[1]]:
                        if len(set(i[1]) & arr) > sum_similarity:
                            arr_similarity = i
                            sum_similarity = len(set(i[1]) & arr)

                    if sum_similarity:
                        response = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "user",
                                 "content": f"Как начать диолог коротко в социальных сетях используя в каждом знакмстве только 1 интерес, и выведи не более 5 пунктов для начала диалога, если у нас общие интересы: {', '.join(list(set(arr_similarity[1]) & arr))}"}
                            ]
                        )


                        text_ai = response['choices'][0]['message']['content']

                        photo = open(f'profile/{arr_similarity[0]}.jpeg', 'rb')
                        await bot.send_photo(message.chat.id, photo,
                                             f"""Мы нашли Вам человека с похожими интересами.\n\nОбщие интересы:\n {', '.join(list(set(arr_similarity[1]) & arr))}\n\nСовет от искуственного интелекта, как начать диалог:\n {text_ai}\nнапишите: @{arr_similarity[2]}""",
                                             reply_markup=types.ReplyKeyboardRemove())
                        await bot.send_message(message.chat.id, 'Чтобы вернутся в меню: /menu')
                        photo.close()
                        photo = open(f'profile/{message.chat.id}.jpeg', 'rb')
                        await bot.send_photo(arr_similarity[0], photo,
                                             f"""Мы нашли Вам человека с похожими интересами.\n\nОбщие интересы:\n {", ".join(list(set(arr_similarity[1]) & arr))}\n\nСовет от искуственного интелекта, как начать диалог:\n {text_ai}\nнапишите: @{data[8]}""",
                                             reply_markup=types.ReplyKeyboardRemove())
                        await bot.send_message(arr_similarity[0], 'Чтобы вернутся в меню: /menu')
                        photo.close()

                        del in_queue[arr_similarity[0]]
                        queue_search[message.text].remove(arr_similarity)
                        del in_queue[message.chat.id]
                        return

                    else:
                        queue_search[message.text].append([message.chat.id, json.loads(data[7]), data[8]])
                        keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton(text="Отмена"))
                        await bot.send_message(message.chat.id, 'Вы добавлены в очередь', reply_markup=keyboard)




            elif message.text == arr_search[2]:
                db = sqlite3.connect("user.db")
                sql = db.cursor()

                sql.execute(f"SELECT * FROM user WHERE id = {int(message.chat.id)}")
                data = sql.fetchone()
                in_queue[message.chat.id] = list(data) + [2]

                async with lock:
                    await bot.send_message(message.chat.id, 'Идет поиск')
                    for i in queue_search[arr_search[2]]:
                        if i[1].lower() in data[6].lower() or data[6].lower() in i[1].lower():
                            response = openai.ChatCompletion.create(
                                model="gpt-3.5-turbo",
                                messages=[
                                    {"role": "user",
                                     "content": f"Как начать диолог коротко в социальных сетях используя в каждом знакмстве только 1 интерес, и выведи не более 5 пунктов для начала диалога, если у нас общие интересы: родной город {i[1]}"}
                                ]
                            )

                            text_ai = response['choices'][0]['message']['content']

                            photo = open(f'profile/{i[0]}.jpeg', 'rb')
                            await bot.send_photo(message.chat.id, photo,
                                                 f"""Мы нашли Вам человека из Вашего родного города\nСовет от искуственного интелекта, как начать диалог:\n {text_ai}\n напишите: @{i[2]}""",
                                                 reply_markup=types.ReplyKeyboardRemove())
                            await bot.send_message(message.chat.id, 'Чтобы вернутся в меню: /menu')
                            photo.close()
                            photo = open(f'profile/{message.chat.id}.jpeg', 'rb')
                            await bot.send_photo(i[0], photo,
                                                 f"""Мы нашли Вам человека из Вашего родного города\nСовет от искуственного интелекта, как начать диалог:\n {text_ai}\n напишите: @{data[8]}""",
                                                 reply_markup=types.ReplyKeyboardRemove())
                            await bot.send_message(i[0], 'Чтобы вернутся в меню: /menu')

                            photo.close()
                            del in_queue[i[0]]
                            queue_search[message.text].remove(i)
                            del in_queue[message.chat.id]
                            return

                    queue_search[message.text].append([message.chat.id, data[6], data[8]])
                    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton(text="Отмена"))
                    await bot.send_message(message.chat.id, 'Вы добавлены в очередь', reply_markup=keyboard)

            elif message.text == arr_search[3]:
                keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
                for i in arr_place:
                    keyboard.add(KeyboardButton(text=i))
                keyboard.add(KeyboardButton(text="Отмена"))
                await bot.send_message(message.chat.id, 'Выберите место для отдыха', reply_markup=keyboard)

        else:
            keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton(text="Отмена"))
            await bot.send_message(message.chat.id, 'Вы уже в очереди', reply_markup=keyboard)

    elif message.text in arr_place:
        db = sqlite3.connect("user.db")
        sql = db.cursor()

        sql.execute(f"SELECT * FROM user WHERE id = {int(message.chat.id)}")
        data = sql.fetchone()

        async with lock:
            if message.chat.id not in in_queue:
                in_queue[message.chat.id] = list(data) + [3]
                await bot.send_message(message.chat.id, 'Идет поиск')

                for i in queue_search[arr_search[3]]:
                    if i[1] == message.text:
                        response = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "user",
                                 "content": f"Как начать диолог коротко в социальных сетях используя в каждом знакмстве только 1 интерес, и выведи не более 5 пунктов для начала диалога, если у нас общие интересы: сходить в {message.text}"}
                            ]
                        )

                        text_ai = response['choices'][0]['message']['content']

                        photo = open(f'profile/{i[0]}.jpeg', 'rb')
                        await bot.send_photo(message.chat.id, photo,
                                             f"""Мы нашли Вам человека, который тоже хочет сходить в {message.text}\nСовет от искуственного интелекта, как начать диалог:\n {text_ai}\nнапишите: @{i[2]}""",
                                             reply_markup=types.ReplyKeyboardRemove())
                        await bot.send_message(message.chat.id, 'Чтобы вернутся в меню: /menu')
                        photo.close()
                        photo = open(f'profile/{message.chat.id}.jpeg', 'rb')
                        await bot.send_photo(i[0], photo,
                                             f"""Мы нашли Вам человека, который тоже хочет сходить в {message.text}\nСовет от искуственного интелекта, как начать диалог:\n {text_ai}\nнапишите: @{data[8]}""",
                                             reply_markup=types.ReplyKeyboardRemove())
                        await bot.send_message(i[0], 'Чтобы вернутся в меню: /menu')

                        photo.close()
                        del in_queue[i[0]]
                        queue_search[arr_search[3]].remove(i)
                        del in_queue[message.chat.id]
                        return
                print(queue_search, arr_search[3])
                queue_search[arr_search[3]].append([message.chat.id, message.text, data[8]])
                keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton(text="Отмена"))
                await bot.send_message(message.chat.id, 'Вы добавлены в очередь', reply_markup=keyboard)
            else:
                keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton(text="Отмена"))
                await bot.send_message(message.chat.id, 'Вы уже в очереди', reply_markup=keyboard)


    elif message.text == "Отмена":
        async with lock:
            if message.chat.id in in_queue:
                if in_queue[message.chat.id][-1] == 0:
                    for i in queue_search[arr_search[0]][in_queue[message.chat.id][2]]:
                        if i[0] == message.chat.id:
                            queue_search[arr_search[0]][in_queue[message.chat.id][2]].remove(i)
                            del in_queue[message.chat.id]

                elif in_queue[message.chat.id][-1] == 1:
                    for i in queue_search[arr_search[1]]:
                        if i[0] == message.chat.id:
                            queue_search[arr_search[1]].remove(i)
                            del in_queue[message.chat.id]

                elif in_queue[message.chat.id][-1] == 2:
                    for i in queue_search[arr_search[2]]:
                        if i[0] == message.chat.id:
                            queue_search[arr_search[2]].remove(i)
                            del in_queue[message.chat.id]

                elif in_queue[message.chat.id][-1] == 3:
                    for i in queue_search[arr_search[3]]:
                        if i[0] == message.chat.id:
                            queue_search[arr_search[3]].remove(i)
                            del in_queue[message.chat.id]

                print(queue_search, in_queue)
                await bot.send_message(message.chat.id, 'Вы удалены из очереди',
                                       reply_markup=types.ReplyKeyboardRemove())
                await menuSearch(message)

            else:
                await bot.send_message(message.chat.id, 'Вас нет в очереди', reply_markup=types.ReplyKeyboardRemove())
                await menuSearch(message)



    elif message.text == "✅Готово✅":
        if "hobby" not in reg_user[message.chat.id]:
            await bot.send_message(message.chat.id, 'Выбери свои интересы')
        else:
            await endRegistration(message)
            reply_markup = types.ReplyKeyboardRemove()
            await imageGeneration(message)

            photo = open(f'profile/{message.chat.id}.jpeg', 'rb')
            await bot.send_photo(message.chat.id, photo, 'Вы успешно зарегестрировались', reply_markup=reply_markup)
            photo.close()

            await menuSearch(message)
            async with lock:
                del reg_user[message.chat.id]


    elif message.text == "↩️Назад↩️":
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        for i in list(arr_hobby) + ["⭐️Разное⭐️", "✅Готово✅"]:
            keyboard.add(KeyboardButton(text=i))

        await bot.send_message(message.chat.id, 'Выбери свои интересы', reply_markup=keyboard)

    elif message.text == "⭐️Разное⭐️":
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        for i in list(arr_varia) + ["↩️Назад↩️"]:
            keyboard.add(KeyboardButton(text=i))

        await bot.send_message(message.chat.id, 'Выбери свои интересы', reply_markup=keyboard)

    elif message.text in list(arr_varia):
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        for i in arr_varia[message.text] + ["↩️Назад↩️"]:
            keyboard.add(KeyboardButton(text=i))

        if message.text == list(arr_varia)[2]:
            media_group = [types.InputMediaPhoto(media=open(image_path, 'rb')) for image_path in
                           ["hobby/Мем 1.jpg", "hobby/Мем 2.jpg", "hobby/Мем 3.jpg", "hobby/Мем 4.jpg"]]
            await bot.send_media_group(chat_id=message.chat.id, media=media_group)

        await bot.send_message(message.chat.id, 'Выбери свои интересы', reply_markup=keyboard)

    elif message.chat.id in reg_user:
        if "year" in reg_user[message.chat.id] and "city" not in reg_user[message.chat.id]:
            reg_user[message.chat.id]["city"] = message.text
            reply_markup = types.ReplyKeyboardRemove()
            await bot.send_message(message.chat.id, 'Введите свое имя', reply_markup=reply_markup)

        elif "city" in reg_user[message.chat.id] and "name" not in reg_user[message.chat.id]:
            reg_user[message.chat.id]["name"] = message.text

            keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
            for i in list(arr_hobby) + ["⭐️Разное⭐️", "✅Готово✅"]:
                keyboard.add(KeyboardButton(text=i))

            await bot.send_message(message.chat.id, 'Выбери свои интересы', reply_markup=keyboard)


async def directions(message):
    buttons = []
    for i in arr_directions[message.text]:
        buttons.append(KeyboardButton(text=i))
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(*buttons)

    await bot.send_message(message.chat.id, 'Выберите специальность:', reply_markup=keyboard)


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

    await bot.send_message(message.chat.id, 'Выберите, с какой целью ищете', reply_markup=keyboard)


async def imageGeneration(message):
    im = Image.open('img/пустое.png')
    font = ImageFont.truetype('font/Molot.otf', size=150)
    draw_text = ImageDraw.Draw(im)
    draw_text.text(
        (50, 25),
        reg_user[message.chat.id]["name"] + "-" * 100,
        font=font,
        fill='#1C0606')

    font = ImageFont.truetype('font/CandaraBold.ttf', size=88)
    arr_cords = [(800, 300), (800, 370), (870, 520), (790, 600)]
    arr_names = [reg_user[message.chat.id]["faculty"], reg_user[message.chat.id]["directions"],
                 reg_user[message.chat.id]["year"], "КУРС"]
    for i in range(4):
        draw_text = ImageDraw.Draw(im)
        draw_text.text(
            arr_cords[i],
            arr_names[i],
            font=font,
            fill='#1C0606')

    arr_cord = [(52, 230), (52, 489), (52, 746), (450, 230), (450, 487), (450, 744)]
    arr_hobby = reg_user[message.chat.id]["hobby"]
    print(arr_hobby)
    for i in range(min(6, len(arr_hobby))):
        watermark = Image.open(f'hobby/{arr_hobby[i]}.jpg')
        out = watermark.resize((300, 200))
        im.paste(out, arr_cord[i])

    im = im.convert('RGB')

    im.save(f"profile/{message.chat.id}.jpeg")



# запускаем бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
