import os
from aiogram import Dispatcher, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import CommandStart, Command, Filter, StateFilter
from aiogram.fsm.state import default_state
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from dotenv import load_dotenv
from requests import *
import datetime
import sqlite3

load_dotenv()

bot = Bot(os.getenv('BOT_TOKEN'))

dp = Dispatcher()

admins = os.getenv('ADMINS').split(', ')

admin = os.getenv('ADMIN')

card = os.getenv('CARD')


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

plans = {1: 199, 3:499, 6:899, 12:1499}
    
class States(StatesGroup):
    
    summ = State()
    pay_receipt = State()

@dp.message(Command(commands='admin'))
async def commands(message:Message):
    if str(message.from_user.id) in admins:
        await message.answer('---ADMIN_PANEL---\n\n' \
        f'Баланс бота: {bot_balance}\n' \
        f'Всего юзеров: {amount_of_users}\n',
        reply_markup=admin_panel)
    

@dp.message(StateFilter(default_state))
async def start(message:Message):
    
    buttons = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Оформить подписку', callback_data="sub", style='success')],
                                                    [InlineKeyboardButton(text='Управление подпиской', callback_data="settings", style='primary')],
                                                    [InlineKeyboardButton(text='Пополнить баланс', callback_data="top_up_balance")]])
    await message.answer('Меню', reply_markup=buttons)
    await add_user(message.from_user.id, message.from_user.username)


@dp.callback_query()
async def callbacks(callback:CallbackQuery, state:FSMContext):
    data = callback.data
    user = callback.from_user
    if data == 'sub':
        buttons = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f'1 мес•{plans[1]}₽', callback_data='sub_1')],
                                                        [InlineKeyboardButton(text=f'3 мес•{plans[3]}₽ ({round(plans[3]/3)}₽/мес)', callback_data='sub_3')],
                                                        [InlineKeyboardButton(text=f'6 мес•{plans[6]}₽ ({round(plans[6]/6)}₽/мес)', callback_data='sub_6')],
                                                        [InlineKeyboardButton(text=f'12 мес•{plans[12]}₽ ({round(plans[12]/12)}₽/мес)', callback_data='sub_12')],
                                                        [InlineKeyboardButton(text='Назад', callback_data='menu')]])
        await callback.message.edit_text("⚡️ Вы покупаете подписку на FISH VPN.\n\n• Подходит для обхода всех блокировок", reply_markup=buttons)
    elif data.startswith("sub_"):
        plan = int(data.replace('sub_',''))
        buttons = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f'Оплатить {plans[plan]}₽', callback_data=f'buy_sub_{plan}')],
                                                        [InlineKeyboardButton(text='Назад', callback_data=f'sub{plan}')]])
        text = f'''⚡️ Оформление подписки FISH VPN

💳 Стоимость: {plans[plan]} ₽
📅 Действует до: ???

Что входит:
✅ Безлимит на обычные локации
✅ Мобильный трафик: ??? ГБ/месяц
✅ Устройств в подписке: ???

🔔 Мы заранее напомним, когда подписка будет подходить к концу.'''
        
        await callback.message.edit_text(text=text,reply_markup=buttons)
    elif data.startswith('buy_sub_'):
        plan = int(data.replace('buy_sub_',''))
        if await get_user_balance(user.id) > plans[plan]:
            await add_sub(tg_id=user.id, plan=plan)
            await callback.message.edit_text(text='Покупка прошла успешно', reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Вернутся в меню', callback_data='menu')]]))
        else:
            await callback.message.edit_text(text='На вашем счете недостаточно средств чтобы оплатить, пополните пожалуста баланс', reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Пополнить баланс', callback_data='top_up_balance')]]))
    elif data == 'top_up_balance':
        buttons = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Карта РФ', callback_data='rf_card')]])
        await callback.message.edit_text(text='Выберите способ пополнения', reply_markup=buttons)
    elif data == "rf_card":
        await state.set_state(States.summ)
        await callback.message.edit_text(text='Введи сумму пополнения:')

    elif data == 'menu':
        buttons = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Оформить подписку', callback_data="sub", style='success')],
                                                    [InlineKeyboardButton(text='Управление подпиской', callback_data="settings", style='primary')]])
        await callback.message.edit_text('Меню', reply_markup=buttons)
        await add_user(user.id, user.username)

    elif str(user.id) in admins:
        if data =='statistic':
            await callback.message.edit_text('statistic', reply_markup=admin_return_button)
        elif data == 'admin_return':
            await callback.message.edit_text('---ADMIN_PANEL---\n\n' \
            f'Баланс бота: {bot_balance}\n' \
            f'Всего юзеров: {amount_of_users}\n',
            reply_markup=admin_panel)
        elif data.startswith("accept_"):
            _, summ, id = data.split('_')
            await callback.message.delete()
            summ = int(summ)
            id = int(id)
            await bot.send_message(chat_id=id, text=f'Ваш баланс пополнен на {summ}₽')
            await add_balance(tg_id=id, summ=summ)
        elif data.startswith('decline_'):
            id = data.split('_')[1]
            await bot.send_message(chat_id=id, text=f'Заявка на пополнение баланса отклонена, для дополнительной информации обратитесь к {admin}')

@dp.message(States.summ)
async def rf_card(message: Message, state: FSMContext):
    await state.update_data(summ=int(message.text))
    await message.answer(text=f'Переведите на карту <code>{card}</code> {message.text}₽, после пришлите чек об оплате',parse_mode='HTML')
    await state.set_state(States.pay_receipt)
    # await state.update_data(summ=int(message.text))


@dp.message(States.pay_receipt, F.photo)
async def receive_receipt(message: Message, state: FSMContext):
    photo = message.photo[-1].file_id
    data = await state.get_data()
    summ = data.get('summ')
    buttons = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Принять', callback_data=f'accept_{summ}_{message.from_user.id}', style='success')],
                                                    [InlineKeyboardButton(text='Отклонить', callback_data=f'decline_{message.from_user.id}', style="danger")]])
    for admin in admins:
        await bot.send_photo(chat_id=int(admin), photo=photo, caption=f'''
Чек от @{message.from_user.username}
id <code>{message.from_user.id}</code>
Сумма {summ}₽''', 
parse_mode='html',
reply_markup=buttons)
    await message.answer("Чек отправлен на проверку. Ожидайте.")


if __name__ == '__main__':
    print('bot active')
    dp.run_polling(bot)
    print('bot stopped')