from aiogram import Bot, Dispatcher, executor, types
import datetime

token_api = '6033695577:AAHc5EHYk59gA8fUc3zhYDNzASHwi_Nr-yA'

bot = Bot(token_api)
dp = Dispatcher(bot)
flag = False  # проверка создается ли запись
# запись можно создать написав любой текст после команды /new_day либо по нажают определнной кнопки (пока не реализовал)


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


@dp.message_handler(commands=['new_day'] or types.Message.text == 'Создать запись')  # создание записи для нового дня
async def new_day(message: types.Message):
    global flag
    kb = [
        [types.KeyboardButton(text="кнопка 1"), types.KeyboardButton(text="кнопка 2")],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Напишите что-нибудь или нажмите на кнопку!"
    )
    text = 'Давайте создадим новую заметку!'
    flag = True
    await message.answer(text, reply_markup=keyboard)


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
