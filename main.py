from aiogram import Bot, Dispatcher, executor, types
import datetime
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext

token_api = '6033695577:AAHc5EHYk59gA8fUc3zhYDNzASHwi_Nr-yA'

storage = MemoryStorage()
bot = Bot(token_api)
dp = Dispatcher(bot, storage=storage)
flag = False  # проверка создается ли запись
# запись можно создать написав любой текст после команды /new_day либо по нажают определнной кнопки (пока не реализовал)


class RecordStatesGroup(StatesGroup):
    date = State()
    text_description = State()
    voice_description = State()
    photo = State()
    emoji = State()
    places = State()


@dp.message_handler(commands='start')  # по команде /start выводиться вопрос + выбор кнопок
async def start(message: types.Message):
    kb = [
        [types.KeyboardButton(text="Просмотр записей"), types.KeyboardButton(text="Создать запись")],
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
           '/new_day - создаст новую запись\n...'
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
    await message.reply('Давай создадим новую заметку!\nСначала введи дату, на которую ты хочешь сделать запись')
    await RecordStatesGroup.date.set() # устанавливается состояние ожидания для получения даты


@dp.message_handler(state=RecordStatesGroup.date)
async def input_date(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['date'] = message.text
        # здесь и везде далее сохнаняется полученное сообщение в словарь data. потом из него можно будет в бд заливать
        # тут ещё нужно дописать проверку даты
    await message.reply('Введи описание дня текстом')
    await RecordStatesGroup.next() # устанавливается следующее состояние ожидания для получения описания дня текстом


@dp.message_handler(state=RecordStatesGroup.text_description)
async def input_text(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['text_description'] = message.text
    await message.reply('Отправь описание дня аудиосообщением')
    await RecordStatesGroup.next() # устанавливается следующее состояние ожидания для получения описания дня войсом


@dp.message_handler(content_types=['voice'], state=RecordStatesGroup.voice_description)
async def input_voice(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['audio_description'] = message.voice.file_id
    await message.reply('Отправь фотографию за этот день')
    await RecordStatesGroup.next() # устанавливается следующее состояние ожидания для получения фотографии


@dp.message_handler(content_types=['photo'], state=RecordStatesGroup.photo)
async def input_photo(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['photo'] = message.photo[0].file_id
    await message.reply('Отправь эмодзи, описывающее этот день')
    await RecordStatesGroup.next() # устанавливается следующее состояние ожидания для получения эмодзи


@dp.message_handler(state=RecordStatesGroup.emoji)
async def input_emoji(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['emoji'] = message.text
    await message.reply('Напиши адреса мест, в которых ты побывал\n(каждый адрес пиши с новой строки)')
    await RecordStatesGroup.next() # устанавливается следующее состояние ожидания для получения адресов


@dp.message_handler(state=RecordStatesGroup.places)
async def input_places(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['places'] = message.text
    await message.reply('Запись успешно создана!')
    await state.finish() # работа с состояниями завершена


@dp.message_handler()
async def first(message: types.Message):
    global flag
    if message.text not in ['Просмотр записей', "Создать запись"] and flag is False:
        await message.reply('Прости, я тебя не понимаю\nПопробуй воспользоваться командой /help или /h')
    elif flag is True:
        flag = False
        await message.reply(f'Твоя заметка создана сегодня({datetime.date.today()})!\n{message.text}')
        # тут создается запись для бд. Текст хранится в переменной message.text
    else:
        await new_day(message)


if __name__ == '__main__':
    executor.start_polling(dp)
