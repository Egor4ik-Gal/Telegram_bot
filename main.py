from aiogram import Bot, Dispatcher, executor, types
import datetime as dt
from datetime import datetime
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
import sqlite3

token_api = '6033695577:AAHc5EHYk59gA8fUc3zhYDNzASHwi_Nr-yA'

storage = MemoryStorage()
bot = Bot(token_api)
dp = Dispatcher(bot, storage=storage)
flag = False  # проверка создается ли запись
# запись можно создать написав любой текст после команды /new_day либо по нажают определнной кнопки
kb = [[types.KeyboardButton(text="Прекратить создание записи"), types.KeyboardButton(text="Пропустить")], ]
skip_keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, )


class RecordStatesGroup(StatesGroup):
    date = State()
    text_description = State()
    voice_description = State()
    photo = State()
    emoji = State()
    places = State()


class ViewingStatesGroup(StatesGroup):
    ask_date = State()


@dp.message_handler(commands='start')  # по команде /start выводиться вопрос + выбор кнопок
async def start(message: types.Message):
    kb = [[types.KeyboardButton(text="Просмотр записей"), types.KeyboardButton(text="Создать запись")],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )
    await message.answer("Привет, что хочешь сделать?", reply_markup=keyboard)


@dp.message_handler(commands=['help', 'h'])  # вспомогательная команда /help дает справку о всех командах бота
async def help(message: types.Message):
    text = 'Что умеет наш бот?\n/start - поможет тебе создать или посмотреть уже созданные записи\n'\
           '/new_day - создаст новую запись\nЕсли хочешь на что-то неотвечать напиши просто Пропустить!\n...'
    await message.answer(text)


@dp.message_handler(commands=['new_day'] or types.Message.text == 'Создать запись')  # создание записи для нового дня
async def new_day(message: types.Message) -> None:
    global flag
    text = 'Давай создадим новую запись!\nСначала введи дату для записи\nФормат даты ДД-ММ-ГГГГ'
    flag = True

    await message.reply(text, reply_markup=skip_keyboard)
    await RecordStatesGroup.date.set()  # устанавливается состояние ожидания для получения даты


@dp.message_handler(state=RecordStatesGroup.date)
async def input_date(message: types.Message, state: FSMContext) -> None:
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
        await message.reply('Создание записи прекращено. Данные не сохранены')
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
        await message.reply('Создание записи прекращено. Данные не сохранены')
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
        await message.reply('Создание записи прекращено. Данные не сохранены')
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
        await message.reply('Создание записи прекращено. Данные не сохранены')
        await state.finish()
    else:
        await message.reply('Это не фотография')


@dp.message_handler(state=RecordStatesGroup.emoji)
async def input_emoji(message: types.Message, state: FSMContext) -> None:
    if message.text == 'Прекратить создание записи':
        await message.reply('Создание записи прекращено. Данные не сохранены')
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
    if message.text == 'Прекратить создание записи':
        await message.reply('Создание записи прекращено. Данные не сохранены')
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
        kb = [[types.KeyboardButton(text="Просмотр записей"), types.KeyboardButton(text="Создать запись")],
              ]
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True,
            input_field_placeholder="Выберите действие"
        )
        await message.reply('Запись успешно создана!', reply_markup=keyboard)
        await state.finish()  # работа с состояниями завершена


@dp.message_handler(commands=['viewing'] or types.Message.text == 'Просмотр записей')  # создание записи для нового дня
async def viewing(message: types.Message) -> None:
    dates = [] # здесь нужен список дат которые есть в БД
    dates_str = ''
    for date in dates:
        dates_str += date + '\n'
    if dates:
        text = f'Есть записи на такие даты:\n{dates_str}'
        await message.reply(text)
        await ViewingStatesGroup.ask_date.set()  # устанавливается состояние ожидания для получения даты
    else:
        await message.reply('Пока нет ни одной записи')


@dp.message_handler(state=ViewingStatesGroup.ask_date)
async def ask_date(message: types.Message, state: FSMContext) -> None:
    date = message.text
    try:
        res = bool(datetime.strptime(date, "%d-%m-%Y"))
    except ValueError:
        res = False
    if res:
        if datetime.strptime(str(dt.date.today()), "%Y-%m-%d") < datetime.strptime(date, "%d-%m-%Y"):
            res = False
    if res:
        проверка_на_то_что_дата_есть_в_бд = False
        # в if  надо написать проверку есть ли дата в БД
        if проверка_на_то_что_дата_есть_в_бд:
            text = '' # в эту переменную записать то, что есть в БД на эту дату в разделе текст
            voice = '' # в эту переменную записать то, что есть в БД на эту дату в разделе голосовое сообщение
            photo = '' # в эту переменную записать то, что есть в БД на эту дату в разделе фото
            emoji = '' # в эту переменную записать то, что есть в БД на эту дату в разделе эмодзи
            place = '' # в эту переменную записать то, что есть в БД на эту дату в разделе места
        else:
            await message.reply('На эту дату нет записи. Попробуй другую')
    else:
        await message.reply('Введена некорректная дата\nФормат даты ДД-ММ-ГГГГ')

@dp.message_handler()
async def first(message: types.Message, state: FSMContext):
    global flag
    if message.text not in ['Просмотр записей', "Создать запись"]:
        await message.reply('Прости, я тебя не понимаю\nПопробуй воспользоваться командой /help или /h')
    elif message.text == 'Создать запись':
        await new_day(message)
    elif message.text == 'Просмотр записей':
        await viewing(message)


if __name__ == '__main__':
    executor.start_polling(dp)
