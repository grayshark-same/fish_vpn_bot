import os
from aiogram import Dispatcher, Bot, F
from aiogram.filters import CommandStart, Command, Filter
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from dotenv import load_dotenv

load_dotenv()

bot = Bot(os.getenv('BOT_TOKEN'))

dp = Dispatcher()

admins = os.getenv('ADMINS').split(', ')




bot_balance = 0
amount_of_users = 0
admin_panel = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Статистика', callback_data='statistic', style='success')],
                                                    [InlineKeyboardButton(text='Рассылка', callback_data='newsletter', style='danger')]])

return_button = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Назад', callback_data='return')]])
class Admin(Filter):
    def __init__(self, id: str) -> None:
        self.id = id

    async def __call__(self, message: Message) -> bool:
        return str(message.from_user.id) in admins

@dp.message(Admin)
async def admin_commands(message:Message):
    # if str(message.from_user.id) in admins:
    if Command(commands='admin'):
        await message.answer('---ADMIN_PANEL---\n\n' \
        f'Баланс бота: {bot_balance}\n' \
        f'Всего юзеров: {amount_of_users}\n',
        reply_markup=admin_panel)
    else:
        print(admins)
        print(message.from_user.id)

    
@dp.callback_query(Admin)
async def admin_callbacks(callback: CallbackQuery):
    data = callback.data
    if data =='statistic':
        await callback.message.edit_text('statistic', reply_markup=return_button)
    elif data == 'return':
        await callback.message.edit_text('---ADMIN_PANEL---\n\n' \
        f'Баланс бота: {bot_balance}\n' \
        f'Всего юзеров: {amount_of_users}\n',
        reply_markup=admin_panel)

    



if __name__ == '__main__':
    print('bot active')
    dp.run_polling(bot)
    print('bot stopped')