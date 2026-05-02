import os
import datetime
from aiogram import Dispatcher, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State, default_state
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from dotenv import load_dotenv
from requests import *
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
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            devices INTEGER DEFAULT 0,
            end_of_sub TIMESTAMP
        )
    ''')
with sqlite3.connect('reports.db') as db:
    cursor = db.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS reports_for_day (
                        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP UNIQUE,
                        money INTEGER,
                        transactions INTEGER,
                        users INTEGER
                   )''')

bot_balance = 0
plans = {1: 199, 3: 499, 6: 899, 12: 1499}
plan_days_map = {1: 30, 3: 90, 6: 180, 12: 360}
plan_names = {1: '1 месяц', 3: '3 месяца', 6: '6 месяцев', 12: '⚡️12 месяцев'}

admin_panel = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Статистика', callback_data='statistic')],
    [InlineKeyboardButton(text='Рассылка', callback_data='newsletter')]
])
admin_return_button = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Назад', callback_data='admin_return')]
])


class States(StatesGroup):
    pay_receipt = State()


def back_menu_btn():
    return [InlineKeyboardButton(text='« Главное Меню', callback_data='menu')]


def back_btn(cb):
    return [InlineKeyboardButton(text='« Назад', callback_data=cb)]


async def send_main_menu(target, user_id, username=None):
    await add_user(user_id, username)
    is_active, end_date = await get_user_sub(user_id)
    status = "активна ✅" if is_active else "не активна ❌"
    date_str = end_date.strftime("%d.%m.%Y") if end_date else "—"
    balance = await get_user_balance(user_id)

    text = (
        "<b><tg-emoji emoji-id='5206376793778437124'>🌊</tg-emoji> Fish VPN</b> – Стабильный, защищённый VPN.\n\n"
        "<b>🇷🇺 Белые списки | 🇸🇪 Швеция | 🇳🇱 Нидерланды | 🇪🇪 Эстония\n"
        "🇫🇮 Финляндия | 🇺🇸 США | 🇱🇻 Латвия | 🇩🇪 Германия\n"
        "🇬🇧 Великобритания | 🇫🇷 Франция | 🇰🇿 Казахстан | 🇧🇾 Беларусь</b>\n\n"
        f"<blockquote>📌 Ваша подписка:\n"
        f"Статус: <code>{status}</code>\n"
        f"Действует до: <code>{date_str}</code>\n"
        f"Лимит устройств: <code>1</code></blockquote>\n"
        # f"Ваш баланс: <code>{balance}</code></blockquote>"
        
    )
    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Управление подпиской', callback_data='settings', icon_custom_emoji_id='6032742198179532882')],
        [InlineKeyboardButton(text='Продлить', callback_data='extend', icon_custom_emoji_id='5769126056262898415'),
         InlineKeyboardButton(text='Поддержка', callback_data='support', icon_custom_emoji_id='6030329749409108167')],
        [InlineKeyboardButton(text='Что это?', callback_data='about', icon_custom_emoji_id='6032594876506312598')]
    ])
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=buttons, parse_mode='HTML')
    else:
        await target.answer(text, reply_markup=buttons, parse_mode='HTML')



@dp.message(Command('start'))
async def start_handler(message: Message):
    await send_main_menu(message, message.from_user.id, message.from_user.username)




@dp.message(Command('admin'))
async def admin_command(message: Message):
    if str(message.from_user.id) in admins:
        count = await get_users_count()
        total_profit = None
        todays_purchases = None
        todays_profit = None
        await message.answer(
            f'''---------ADMIN_PANEL---------
            
Баланс бота: {bot_balance}
Всего заработано: {total_profit}

Всего юзеров: {count}
Покупок сегодня: {todays_purchases}
Прибыль сегодня: {todays_profit}
            ''',
            reply_markup=admin_panel
        ),
        



@dp.callback_query()
async def callbacks(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    user = callback.from_user

    if data == 'menu':
        await send_main_menu(callback, user.id, user.username)

    elif data == 'settings':
        text = (
            "📍Главное меню » <tg-emoji emoji-id='6032742198179532882'>⚙️</tg-emoji> <b>Управление подпиской</b>\n\n"
            "🔗 <b>Подключение</b> — выберите платформу, затем автонастройку Happ.\n\n"
            "📱 <b>Мои устройства</b> — список привязанных устройств.\n\n"
            "📋 <b>Универсальная ссылка</b> — строка подписки для вставки в Happ и другие клиенты."
        )
        buttons = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='🔗 Подключиться к VPN', callback_data='connect')],
            [InlineKeyboardButton(text='📱 Мои устройства', callback_data='devices')],
            [InlineKeyboardButton(text='📋 Универсальная ссылка', callback_data='universal_link')],
            [back_menu_btn()[0]]
        ])
        await callback.message.edit_text(text, reply_markup=buttons, parse_mode='HTML')

    elif data == 'connect':
        text = "📍Главное меню » <tg-emoji emoji-id='6032742198179532882'>⚙️</tg-emoji> Управление подпиской » 🔗 <b>Подключиться к VPN</b>\n\nВыберите устройство:"
        buttons = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Android', callback_data='connect_android', icon_custom_emoji_id='6030400221232501136'),
             InlineKeyboardButton(text='iOS', callback_data='connect_ios', icon_custom_emoji_id='5775870512127283512')],
            [InlineKeyboardButton(text='🖥 Windows', callback_data='connect_windows'),
             InlineKeyboardButton(text='💻 MacOS', callback_data='connect_macos')],
            [back_btn('settings')[0]]
        ])
        await callback.message.edit_text(text, reply_markup=buttons, parse_mode='HTML')

    elif data.startswith('connect_'):
        platform = data.replace('connect_', '')
        info = {
            'android': ("<tg-emoji emoji-id='6030400221232501136'>🤖</tg-emoji> Android", 'https://play.google.com/store/apps/details?id=com.happproxy'),
            'ios':     ("<tg-emoji emoji-id='5775870512127283512'>🍏</tg-emoji> iOS",     'https://apps.apple.com/us/app/happ-proxy-utility/id6504287215'),
            'windows': ('🖥 Windows',  'https://www.happ.su/main/ru'),
            'macos':   ('💻 MacOS',   'https://apps.apple.com/us/app/happ-proxy-utility/id6504287215'),
        }
        name, download_url = info[platform]
        text = (
            f"📍Главное меню » <tg-emoji emoji-id='6032742198179532882'>⚙️</tg-emoji> Управление подпиской » 🔗 Подключиться к VPN » <b>{name}</b>\n\n"
            "1. Нажмите «📥 Скачать приложение» и установите программу.\n\n"
            "2. Нажмите «🔗 Активировать VPN-профиль», чтобы добавить подключение.\n\n"
            "3. Готово! Выберите локацию и подключитесь!"
        )
        rows = []
        if download_url:
            rows.append([InlineKeyboardButton(text='📥 Скачать приложение', url=download_url)])
        rows.append([InlineKeyboardButton(text='🔗 Активировать VPN-профиль', callback_data=f'activate_{platform}')])
        rows.append([back_btn('connect')[0]])
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows), parse_mode='HTML')

    elif data.startswith('activate_'):
        await callback.answer("Функция в разработке", show_alert=True)

    elif data == 'devices':
        await callback.answer("Функция в разработке", show_alert=True)

    elif data == 'universal_link':
        await callback.answer("Функция в разработке", show_alert=True)

    elif data == 'extend':
        _, end_date = await get_user_sub(user.id)
        days_left = max((end_date - datetime.datetime.now()).days, 0) if end_date else 0
        text = (
            f"📍Главное меню » <b><tg-emoji emoji-id='5258204546391351475'>👛</tg-emoji> Продлить</b>\n\n"
            f"<blockquote>⏳ До окончания подписки: {days_left} дней\n"
            f"📱 Количество устройств: 3</blockquote>\n\n"
            f"💳 <b>Выберите тариф</b>:"
        )
        buttons = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f'1 месяц — {plans[1]}₽', callback_data='plan_1')],
            [InlineKeyboardButton(text=f'3 месяца — {plans[3]}₽ ({round(plans[3]/3)}₽/мес)', callback_data='plan_3')],
            [InlineKeyboardButton(text=f'6 месяцев — {plans[6]}₽ ({round(plans[6]/6)}₽/мес)', callback_data='plan_6')],
            [InlineKeyboardButton(text=f'⚡️12 месяцев — {plans[12]}₽ ({round(plans[12]/12)}₽/мес)', callback_data='plan_12')],
            [back_menu_btn()[0]]
        ])
        await callback.message.edit_text(text, reply_markup=buttons, parse_mode='HTML')

    elif data.startswith('plan_'):
        plan = int(data.replace('plan_', ''))
        text = (
            f"📍Главное меню » <tg-emoji emoji-id='5258204546391351475'>👛</tg-emoji> Продлить » <b>{plan_names[plan]}</b>\n\n"
            f"<blockquote>⏱️ {plan_days_map[plan]} дней • 3 устройства\n"
            f"💰 Сумма: {plans[plan]}₽</blockquote>\n"
        )
        buttons = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='СБП', callback_data=f'pay_{plan}_sbp', icon_custom_emoji_id='5425008221330880308')],
            [InlineKeyboardButton(text='Карта', callback_data=f'pay_{plan}_card', icon_custom_emoji_id='5312057711091813718'),
             InlineKeyboardButton(text='Крипта', callback_data=f'pay_{plan}_crypto', icon_custom_emoji_id='5195308461193182892')],
            [back_btn('extend')[0]]
        ])
        await callback.message.edit_text(text, reply_markup=buttons, parse_mode='HTML')

    elif data.startswith('pay_'):
        parts = data.split('_')
        plan, method = int(parts[1]), parts[2]
        if method == 'crypto':
            await callback.answer("Оплата криптой в разработке", show_alert=True)
        else:
            await state.update_data(plan=plan, summ=plans[plan])
            await state.set_state(States.pay_receipt)
            await callback.message.edit_text(
                f"Переведите <b>{plans[plan]}₽</b> на карту <code>{card}</code>\n\n"
                f"После оплаты отправьте фото чека.",
                parse_mode='HTML'
            )

    elif data == 'support':
        text = (
            f"📍Главное меню » <b>💬 Поддержка</b>\n\n"
            f"Скопируйте ваш ID и отправьте в поддержку с описанием проблемы.\n\n"
            f"📋 Ваш ID: <code>{user.id}</code>"
        )
        buttons = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='💬 Поддержка', url=f'https://t.me/{admin.lstrip("@")}')],
            [back_menu_btn()[0]]
        ])
        await callback.message.edit_text(text, reply_markup=buttons, parse_mode='HTML')

    elif data == 'about':
        text = (
            "📍Главное меню » <b>👥 Что это?</b>\n\n"
            "⚡️ <b>Молниеносная скорость:</b>\n"
            "• До 25 Гбит/с — смотрите 4K без задержек\n"
            "• 13+ Серверов — стабильное соединение\n"
            "• VLESS + Reality — современный протокол\n\n"
            "🛡️ <b>Максимальная защита:</b>\n"
            "• Никаких логов — ваша приватность под защитой\n"
            "• Умное шифрование — ваши данные в безопасности\n"
            "• Защита от утечек — полная анонимность\n\n"
            "✨ <b>Почему выбирают нас:</b>\n"
            "• Никакой рекламы — чистый интернет\n"
            "• Настройка за 1 минуту — всё просто\n"
            "• Поддержка 24/7 — всегда на связи\n"
            "• Пробный период — попробуйте бесплатно\n"
            "• Доступная цена — качество без переплат"
        )
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[back_menu_btn()[0]]]),
            parse_mode='HTML'
        )

    elif str(user.id) in admins:
        if data == 'statistic':
            await callback.message.edit_text('statistic', reply_markup=admin_return_button)
        elif data == 'admin_return':
            count = await get_users_count()
            total_profit = None
            todays_purchases = None
            todays_profit = None
            await callback.message.edit_text(
                f'''---------ADMIN_PANEL---------
                
    Баланс бота: {bot_balance}
    Всего заработано: {total_profit}

    Всего юзеров: {count}
    Покупок сегодня: {todays_purchases}
    Прибыль сегодня: {todays_profit}
                ''',
                reply_markup=admin_panel
            )
        elif data.startswith('accept_'):
            _, plan, uid = data.split('_')
            plan, uid = int(plan), int(uid)
            await callback.message.delete()
            await add_sub(tg_id=uid, plan=plan)
            await bot.send_message(chat_id=uid, text=f'✅ Подписка на {plan_names[plan]} активирована!')
        elif data.startswith('decline_'):
            uid = int(data.split('_')[1])
            await callback.message.delete()
            await bot.send_message(chat_id=uid, text=f'❌ Чек отклонён. Обратитесь в поддержку: @{admin.lstrip("@")}')



@dp.message(States.pay_receipt, F.photo)
async def receive_receipt(message: Message, state: FSMContext):
    photo = message.photo[-1].file_id
    fsm_data = await state.get_data()
    plan = fsm_data.get('plan')
    summ = fsm_data.get('summ')

    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✅ Принять', callback_data=f'accept_{plan}_{message.from_user.id}', style='success')],
        [InlineKeyboardButton(text='❌ Отклонить', callback_data=f'decline_{message.from_user.id}', style='danger')]
    ])
    for admin_id in admins:
        await bot.send_photo(
            chat_id=int(admin_id),
            photo=photo,
            caption=(f'Чек от @{message.from_user.username}\n'
                     f'ID: <code>{message.from_user.id}</code>\n'
                     f'План: {plan_names[plan]} — {summ}₽'),
            parse_mode='HTML',
            reply_markup=buttons
        )
    await state.clear()
    await message.answer("✅ Чек отправлен на проверку. Ожидайте активации.")


if __name__ == '__main__':
    print('bot active')
    dp.run_polling(bot)
    print('bot stopped')
