from aiogram import Bot, Dispatcher, executor, types
import datetime as dt
from datetime import datetime
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from random import choice
import sqlite3

token_api = '6033695577:AAHc5EHYk59gA8fUc3zhYDNzASHwi_Nr-yA'

storage = MemoryStorage()
bot = Bot(token_api)
dp = Dispatcher(bot, storage=storage)
flag = False  # проверка создается ли запись
# запись можно создать написав любой текст после команды /new_day либо по нажают определнной кнопки
kb = [[types.KeyboardButton(text="Прекратить создание записи"), types.KeyboardButton(text="Пропустить")], ]
skip_keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, )
kb2 = [[types.KeyboardButton(text="Просмотр записей"), types.KeyboardButton(text="Создать запись")],
    ]
hi = ['Привет! Выбери действие!', 'Выберите действие', 'Пасхалка)']
g = choice(hi)
print(g)
keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb2,
        resize_keyboard=True,
        input_field_placeholder=g
    )


class RecordStatesGroup(StatesGroup):
    date = State()
    text_description = State()
    voice_description = State()
    photo = State()
    emoji = State()
    places = State()


@dp.message_handler(commands='start')  # по команде /start выводиться вопрос + выбор кнопок
async def start(message: types.Message):
    await message.answer("Привет, что хочешь сделать?", reply_markup=keyboard)


@dp.message_handler(commands=['help', 'h'])  # вспомогательная команда /help дает справку о всех командах бота
async def help(message: types.Message):
    text = 'Что умеет наш бот?\n/start - поможет тебе создать или посмотреть уже созданные записи\n'\
           '/new_day - создаст новую запись\nЕсли хочешь на что-то неотвечать напиши просто Пропустить!\n...'
    await message.answer(text)


# @dp.message_handler(commands=['new_day'] or types.Message.text == 'Создать запись')  # создание записи для нового дня
# async def new_day(message: types.Message):
#     global flag
#     kb = [
#         [types.KeyboardButton(text="кнопка 1"), types.KeyboardButton(text="кнопка 2")],
#     ]
#     keyboard = types.ReplyKeyboardMarkup(
#         keyboard=kb,
#         resize_keyboard=True,
#         input_field_placeholder="Напишите что-нибудь или нажмите на кнопку!"
#     )
#     text = 'Давайте создадим новую заметку!'
#     flag = True
#     await message.answer(text, reply_markup=keyboard)

@dp.message_handler(commands=['new_day'] or types.Message.text == 'Создать запись')  # создание записи для нового дня
async def new_day(message: types.Message) -> None:
    global flag
    text = 'Давай создадим новую запись!\nСначала введи дату для записи\nФормат даты ДД-ММ-ГГГГ'
    flag = True

    await message.reply(text, reply_markup=skip_keyboard)
    await RecordStatesGroup.date.set()  # устанавливается состояние ожидания для получения даты


@dp.message_handler(state=RecordStatesGroup.date)
async def input_date(message: types.Message, state: FSMContext) -> None:
    global g, keyboard
    g = choice(hi)
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb2,
        resize_keyboard=True,
        input_field_placeholder=g
    )
    async with state.proxy() as data:
        date = message.text
        stop = False
        if date == 'Прекратить создание записи':
            stop = True
        elif date == 'Пропустить':
            await message.reply('Этот пункт обязателен!')
            res = 'flag'
        else:
            try:
                res = bool(datetime.strptime(date, "%d-%m-%Y"))
            except ValueError:
                res = False
            if res:
                if datetime.strptime(str(dt.date.today()), "%Y-%m-%d") < datetime.strptime(date, "%d-%m-%Y"):
                    res = False
                else:
                    data['date'] = date
    # здесь и везде далее сохнаняется полученное сообщение в словарь data. потом из него можно будет в бд заливать
    if stop:
        await message.reply('Создание записи прекращено. Данные не сохранены', reply_markup=keyboard)
        await state.finish()
    else:
        if res == 'flag':
            pass
        elif res:
            await message.reply('Введи описание дня текстом', reply_markup=skip_keyboard)
            await RecordStatesGroup.next()  # устанавливается следующее состояние ожидания для получения описания дня текстом
        else:
            await message.reply('Введена некорректная дата\nФормат даты ДД-ММ-ГГГГ')


@dp.message_handler(state=RecordStatesGroup.text_description)
async def input_text(message: types.Message, state: FSMContext) -> None:
    if message.text == 'Прекратить создание записи':
        await message.reply('Создание записи прекращено. Данные не сохранены', reply_markup=keyboard)
        await state.finish()
    elif message.text == 'Пропустить':
        async with state.proxy() as data:
            data['text_description'] = None
        await message.reply('Отправь описание дня аудиосообщением')
        await RecordStatesGroup.next()  # устанавливается следующее состояние ожидания для получения описания дня войсом
    else:
        async with state.proxy() as data:
            data['text_description'] = message.text
        await message.reply('Отправь описание дня аудиосообщением')
        await RecordStatesGroup.next()  # устанавливается следующее состояние ожидания для получения описания дня войсом


@dp.message_handler(content_types=['any'], state=RecordStatesGroup.voice_description)
async def input_voice(message: types.Message, state: FSMContext) -> None:
    if message.voice:
        async with state.proxy() as data:
            data['audio_description'] = message.voice.file_id
        await message.reply('Отправь фотографию за этот день')
        await RecordStatesGroup.next()  # устанавливается следующее состояние ожидания для получения фотографии
    elif message.text == 'Пропустить':
        async with state.proxy() as data:
            data['audio_description'] = None
        await message.reply('Отправь фотографию за этот день')
        await RecordStatesGroup.next()  # устанавливается следующее состояние ожидания для получения фотографии
    elif message.text == 'Прекратить создание записи':
        await message.reply('Создание записи прекращено. Данные не сохранены', reply_markup=keyboard)
        await state.finish()
    else:
        await message.reply('Это не голосовое сообщение')


@dp.message_handler(content_types=['any'], state=RecordStatesGroup.photo)
async def input_photo(message: types.Message, state: FSMContext) -> None:
    if message.photo:
        async with state.proxy() as data:
            data['photo'] = message.photo[0].file_id
        await message.reply('Отправь эмодзи, описывающее этот день')
        await RecordStatesGroup.next()  # устанавливается следующее состояние ожидания для получения эмодзи
    elif message.text == 'Пропустить':
        async with state.proxy() as data:
            data['photo'] = None
        await message.reply('Отправь эмодзи, описывающее этот день')
        await RecordStatesGroup.next()  # устанавливается следующее состояние ожидания для получения эмодзи
    elif message.text == 'Прекратить создание записи':
        await message.reply('Создание записи прекращено. Данные не сохранены', reply_markup=keyboard)
        await state.finish()
    else:
        await message.reply('Это не фотография')


@dp.message_handler(state=RecordStatesGroup.emoji)
async def input_emoji(message: types.Message, state: FSMContext) -> None:
    if message.text == 'Прекратить создание записи':
        await message.reply('Создание записи прекращено. Данные не сохранены', reply_markup=keyboard)
        await state.finish()
    elif message.text == 'Пропустить':
        async with state.proxy() as data:
            data['emoji'] = None
        await message.reply('Напиши адреса мест, в которых ты побывал\n(каждый адрес пиши с новой строки)')
        await RecordStatesGroup.next()  # устанавливается следующее состояние ожидания для получения адресов
    else:
        async with state.proxy() as data:
            data['emoji'] = message.text
        await message.reply('Напиши адреса мест, в которых ты побывал\n(каждый адрес пиши с новой строки)')
        await RecordStatesGroup.next()  # устанавливается следующее состояние ожидания для получения адресов


@dp.message_handler(state=RecordStatesGroup.places)
async def input_places(message: types.Message, state: FSMContext) -> None:
    global g, keyboard
    g = choice(hi)
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb2,
        resize_keyboard=True,
        input_field_placeholder=g
    )
    if message.text == 'Прекратить создание записи':
        await message.reply('Создание записи прекращено. Данные не сохранены', reply_markup=keyboard)
        await state.finish()
    else:
        if message.text == 'Пропустить':
            places = None
        else:
            places = message.text
        async with state.proxy() as data:
            data['places'] = places
            #  здесь все записывается в базу данных
            con = sqlite3.connect('Telegram-bot.db')
            cur = con.cursor()
            cur.execute(f"INSERT INTO User_ids(user_id) VALUES({message.from_user.id});")
            cur.execute(f"""INSERT INTO Days(user_id, date) VALUES(
            (SELECT id FROM User_ids WHERE user_id = '{message.from_user.id}'),
             '{str(data['date'])}');""")
            cur.execute(f"""INSERT INTO Texts(day_id, text) VALUES(
            (SELECT id FROM Days WHERE user_id = 
            (SELECT id FROM User_ids WHERE user_id = '{message.from_user.id}') AND date = '{data['date']}'), 
            '{data['text_description']}');""")
            cur.execute(f"""INSERT INTO Voices(day_id, voice) VALUES(
            (SELECT id FROM Days WHERE user_id = 
            (SELECT id FROM User_ids WHERE user_id = '{message.from_user.id}') AND date = '{data['date']}'), 
            '{data['audio_description']}');""")
            cur.execute(f"""INSERT INTO Photos(day_id, photo) VALUES(
            (SELECT id FROM Days WHERE user_id = 
            (SELECT id FROM User_ids WHERE user_id = '{message.from_user.id}') AND date = '{data['date']}'), 
            '{data['photo']}');""")
            cur.execute(f"""INSERT INTO Emojis(day_id, emoji) VALUES(
            (SELECT id FROM Days WHERE user_id = 
            (SELECT id FROM User_ids WHERE user_id = '{message.from_user.id}') AND date = '{data['date']}'), 
            '{data['emoji']}');""")
            cur.execute(f"""INSERT INTO Places(day_id, places) VALUES(
                (SELECT id FROM Days WHERE user_id = 
                (SELECT id FROM User_ids WHERE user_id = '{message.from_user.id}') AND date = '{data['date']}'), 
                '{data['places']}');""")
            con.commit()
        await message.reply('Запись успешно создана!', reply_markup=keyboard)
        await state.finish()  # работа с состояниями завершена


@dp.message_handler()
async def first(message: types.Message, state: FSMContext):
    global flag
    if message.text not in ['Просмотр записей', "Создать запись"]:
        await message.reply('Прости, я тебя не понимаю\nПопробуй воспользоваться командой /help или /h')
    elif message.text == 'Создать запись':
        await new_day(message)
    elif message.text == 'Просмотр записей':
        pass


if __name__ == '__main__':
    executor.start_polling(dp)
