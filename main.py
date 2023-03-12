from aiogram import Bot, Dispatcher, executor, types

token_api = '6033695577:AAHc5EHYk59gA8fUc3zhYDNzASHwi_Nr-yA'

bot = Bot(token_api)
dp = Dispatcher(bot)


@dp.message_handler(commands='start')
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
    # await message.delete()


@dp.message_handler(commands=['help', 'h'])
async def help(message: types.Message):
    text = 'Что умеет наш бот?\n/start - поможет тебе создать или посмотреть уже созданные записи\n/...'
    await message.answer(text)


@dp.message_handler()
async def first(message: types.Message):
    if message.text not in ['Просмотр записей', "Создать запись"]:
        await message.reply('Прости, я тебя не понимаю\nПопробуй воспользоваться командой /help или /h')
    else:
        await message.answer('Я тебя услышал!')


if __name__ == '__main__':
    executor.start_polling(dp)
