import os
from aiogram import Dispatcher, Bot, F
from aiogram.filters import CommandStart, Command, Filter
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from dotenv import load_dotenv
from requests import *
import sqlite3

load_dotenv()

bot = Bot(os.getenv('BOT_TOKEN'))

dp = Dispatcher()

admins = os.getenv('ADMINS').split(', ')


with sqlite3.connect('users.db') as db:
    cursor = db.cursor()

    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        tg_id INTEGER UNIQUE NOT NULL,
                        username TEXT,
                        balance REAL DEFAULT 0.0,
                        join_date TIMESTAMP  DEFAULT CURRENT_TIMESTAMP,
                        end_of_sub TIMESTAMP
                        )
                    ''')



bot_balance = 0
amount_of_users = 0
admin_panel = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Статистика', callback_data='statistic', style='success')],
                                                    [InlineKeyboardButton(text='Рассылка', callback_data='newsletter', style='danger')]])

admin_return_button = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Назад', callback_data='admin_return')]])


class Admin(Filter):
    def __init__(self, id: str) -> None:
        self.id = id

    async def __call__(self, message: Message) -> bool:
        return str(message.from_user.id) in admins
    

@dp.message(Command(commands='admin'), Admin)
async def commands(message:Message):
    await message.answer('---ADMIN_PANEL---\n\n' \
    f'Баланс бота: {bot_balance}\n' \
    f'Всего юзеров: {amount_of_users}\n',
    reply_markup=admin_panel)
    

@dp.message()
async def start(message:Message):
    if Command(commands='start'):
        await message.answer('Меню:')
        await add_user(message.from_user.id, message.from_user.username)

@dp.callback_query(Admin)
async def admin_callbacks(callback: CallbackQuery):
    data = callback.data
    if data =='statistic':
        await callback.message.edit_text('statistic', reply_markup=admin_return_button)
    elif data == 'admin_return':
        await callback.message.edit_text('---ADMIN_PANEL---\n\n' \
        f'Баланс бота: {bot_balance}\n' \
        f'Всего юзеров: {amount_of_users}\n',
        reply_markup=admin_panel)

    



if __name__ == '__main__':
    print('bot active')
    dp.run_polling(bot)
    print('bot stopped')