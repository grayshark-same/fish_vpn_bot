import os
import datetime
from aiogram import Dispatcher, Bot, F
from aiogram.types import FSInputFile
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
    newsletter_text = State()
    newsletter_photo = State()
    newsletter_buttons = State()

# @dp.message(F.photo)
# async def get_file_id(message: Message):
#     print(message.photo[-1].file_id)

async def edit_or_answer(callback: CallbackQuery, text: str, reply_markup=None, parse_mode='HTML'):
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
    else:
        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)


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
        "<b><tg-emoji emoji-id='5206376793778437124'>🌊</tg-emoji> Fish VPN</b> – Стабильный, защищенный и анонимный VPN.\n\n"
        "<b>🇷🇺 Белые списки \n• 🇸🇪 Швеция \n• 🇳🇱 Нидерланды \n• 🇪🇪 Эстония\n"
        "• 🇫🇮 Финляндия \n• 🇺🇸 США \n• 🇱🇻 Латвия \n• 🇩🇪 Германия\n"
        "• 🇬🇧 Великобритания \n• 🇫🇷 Франция \n• 🇰🇿 Казахстан \n• 🇧🇾 Беларусь</b>\n\n"
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
    photo = FSInputFile('menu.png')
    if isinstance(target, CallbackQuery):
        if target.message.photo:
            await target.message.edit_caption(caption=text, reply_markup=buttons, parse_mode='HTML')
        else:
            await target.message.delete()
            await target.message.answer_photo(photo=photo, caption=text, reply_markup=buttons, parse_mode='HTML')
    else:
        await target.answer_photo(photo=photo, caption=text, reply_markup=buttons, parse_mode='HTML')



@dp.message(Command('start'))
async def start_handler(message: Message):
    await send_main_menu(message, message.from_user.id, message.from_user.username)




@dp.message(Command('admin'))
async def admin_command(message: Message):
    if str(message.from_user.id) in admins:
        count = await get_users_count()
        total_profit = 0
        todays_purchases = 0
        todays_profit = 0
        bot_balance = 0
        await message.answer(
            f'''---------ADMIN_PANEL---------
            
<tg-emoji emoji-id="5258204546391351475">💰</tg-emoji><b>Баланс бота</b>: <code>{bot_balance}</code>
<tg-emoji emoji-id="5890848474563352982">🪙</tg-emoji>Всего заработано: <code>{total_profit}</code>

<tg-emoji emoji-id="6032594876506312598">👥</tg-emoji>Всего юзеров: {count}
<tg-emoji emoji-id="5902206159095339799">🤑</tg-emoji>Прибыль сегодня: <code>{todays_profit}</code>
            ''',
            reply_markup=admin_panel, parse_mode='html'
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
        await edit_or_answer(callback, text, reply_markup=buttons)

    elif data == 'connect':
        text = "📍Главное меню » <tg-emoji emoji-id='6032742198179532882'>⚙️</tg-emoji> Управление подпиской » 🔗 <b>Подключиться к VPN</b>\n\nВыберите устройство:"
        buttons = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Android', callback_data='connect_android', icon_custom_emoji_id='6030400221232501136'),
             InlineKeyboardButton(text='iOS', callback_data='connect_ios', icon_custom_emoji_id='5775870512127283512')],
            [InlineKeyboardButton(text='🖥 Windows', callback_data='connect_windows'),
             InlineKeyboardButton(text='💻 MacOS', callback_data='connect_macos')],
            [back_btn('settings')[0]]
        ])
        await edit_or_answer(callback, text, reply_markup=buttons)

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
        await edit_or_answer(callback, text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

    elif data.startswith('activate_'):
        await callback.answer("Функция в разработке", show_alert=True)

    elif data.endswith('_sbp'):
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
        await edit_or_answer(callback, text, reply_markup=buttons)

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
        await edit_or_answer(callback, text, reply_markup=buttons)

    elif data.startswith('pay_'):
        parts = data.split('_')
        plan, method = int(parts[1]), parts[2]
        if method == 'crypto':
            await callback.answer("Оплата криптой в разработке", show_alert=True)
        else:
            await state.update_data(plan=plan, summ=plans[plan])
            await state.set_state(States.pay_receipt)
            await edit_or_answer(
                callback,
                f"Переведите <b>{plans[plan]}₽</b> на карту <code>{card}</code>\n\nПосле оплаты отправьте фото чека.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[back_btn(f'plan_{plan}')])
            )

    elif data == 'support':
        text = (
            f"📍Главное меню » <b><tg-emoji emoji-id='6030329749409108167'>💬</tg-emoji> Поддержка</b>\n\n"
            f"Скопируйте ваш ID и отправьте в поддержку с описанием проблемы.\n\n"
            f"📋 Ваш ID: <blockquote>{user.id}</blockquote>"
        )
        buttons = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Поддержка', url=f'https://t.me/{admin.lstrip("@")}', icon_custom_emoji_id='6030329749409108167')],
            [back_menu_btn()[0]]
        ])
        await edit_or_answer(callback, text, reply_markup=buttons)

    elif data == 'about':
        text = ('''📍Главное меню » <tg-emoji emoji-id="6032594876506312598">👥</tg-emoji><b>Что это?</b>

<tg-emoji emoji-id="5920515922505765329">⚡️</tg-emoji>Молниеносная скорость:
<blockquote>• До 25 Гбит/с — смотрите 4K без задержек
• 13+ Серверов — стабильное соединение
• VLESS + Reality — современный протокол</blockquote>

<tg-emoji emoji-id="6039729023343400390">🔨</tg-emoji><b>Максимальная защита:</b>
<blockquote>• Никаких логов — ваша приватность под защитой
• Умное шифрование — ваши данные в безопасности
• Защита от утечек — полная анонимность</blockquote>

<tg-emoji emoji-id="5890925363067886150">✨</tg-emoji><b>Почему выбирают нас:</b>
<blockquote>• Никакой рекламы — чистый интернет
• Настройка за 1 минуту — всё просто 
• Поддержка 24/7 — всегда на связи
• Пробный период — попробуйте бесплатно
• Доступная цена — качество без переплат</blockquote>'''
        )
        await edit_or_answer(
            callback,
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Политика Конфиденциальности', icon_custom_emoji_id="6037397706505195857", url='https://telegra.ph/Politika-konfidencialnosti-servisa-Fish-VPN-05-03')],
                                                               [InlineKeyboardButton(text='Пользовательское соглашение', icon_custom_emoji_id="6039422865189638057", url='https://telegra.ph/Polzovatelskoe-soglashenie-servisa-Fish-VPN-05-03')],
                                                               [back_menu_btn()[0]]])
        )

    elif str(user.id) in admins:
        if data == 'statistic':
            await callback.message.edit_text('statistic', reply_markup=admin_return_button)
        elif data == 'admin_return':
            count = await get_users_count()
            total_profit = 0
            todays_purchases = 0
            todays_profit = 0
            bot_balance = 0
            await callback.message.edit_text(
                f'''---------ADMIN_PANEL---------

<tg-emoji emoji-id="5258204546391351475">💰</tg-emoji><b>Баланс бота</b>: <code>{bot_balance}</code>
<tg-emoji emoji-id="5890848474563352982">🪙</tg-emoji>Всего заработано: <code>{total_profit}</code>

<tg-emoji emoji-id="6032594876506312598">👥</tg-emoji>Всего юзеров: {count}
<tg-emoji emoji-id="5902206159095339799">🤑</tg-emoji>Прибыль сегодня: <code>{todays_profit}</code>''',
                reply_markup=admin_panel
            )
        elif data.startswith('accept_'):
            _, plan, uid = data.split('_')
            plan, uid = int(plan), int(uid)
            print(uid)
            try:
                await callback.message.delete()
            except:
                pass
            await add_sub(tg_id=uid, plan=plan)
            await add_report(money=plans[plan])
            await bot.send_message(chat_id=uid, text=f'✅ Подписка на {plan_names[plan]} активирована!')
        elif data.startswith('decline_'):
            uid = int(data.split('_')[1])
            await callback.message.delete()
            await bot.send_message(chat_id=uid, text=f'❌ Чек отклонён. Обратитесь в поддержку: @{admin.lstrip("@")}')
        elif data == 'newsletter':
            await state.set_state(States.newsletter_text)
            await callback.message.answer('✍️ Введите текст рассылки:')
        elif data == 'nl_skip_photo':
            await state.set_state(States.newsletter_buttons)
            await callback.message.answer(
                '🔗 Введите кнопки в формате:\n<code>Текст кнопки | https://ссылка</code>\n\nКаждая кнопка с новой строки. Или нажмите «Пропустить».',
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Пропустить', callback_data='nl_skip_buttons')]])
            )
        elif data == 'nl_skip_buttons':
            fsm_data = await state.get_data()
            await _send_newsletter_preview(callback.message, fsm_data)
        elif data == 'nl_confirm':
            fsm_data = await state.get_data()
            await state.clear()
            await callback.message.edit_text('📤 Рассылка запущена...')
            count = await _do_newsletter(fsm_data)
            await callback.message.edit_text(f'✅ Рассылка отправлена {count} пользователям.')
        elif data == 'nl_cancel':
            await state.clear()
            await callback.message.edit_text('❌ Рассылка отменена.')



async def _parse_buttons(text: str) -> list:
    rows = []
    for line in text.strip().splitlines():
        if '|' in line:
            label, url = line.split('|', 1)
            rows.append([InlineKeyboardButton(text=label.strip(), url=url.strip())])
    return rows


async def _send_newsletter_preview(message: Message, fsm_data: dict):
    text = fsm_data.get('nl_text', '')
    photo = fsm_data.get('nl_photo')
    buttons_text = fsm_data.get('nl_buttons', '')
    rows = await _parse_buttons(buttons_text) if buttons_text else []
    rows.append([
        InlineKeyboardButton(text='✅ Отправить', callback_data='nl_confirm'),
        InlineKeyboardButton(text='❌ Отмена', callback_data='nl_cancel')
    ])
    markup = InlineKeyboardMarkup(inline_keyboard=rows)
    await message.answer('👁 <b>Предпросмотр:</b>', parse_mode='HTML')
    if photo:
        await message.answer_photo(photo=photo, caption=text, parse_mode='HTML', reply_markup=markup)
    else:
        await message.answer(text, parse_mode='HTML', reply_markup=markup)


async def _do_newsletter(fsm_data: dict) -> int:
    text = fsm_data.get('nl_text', '')
    photo = fsm_data.get('nl_photo')
    buttons_text = fsm_data.get('nl_buttons', '')
    rows = await _parse_buttons(buttons_text) if buttons_text else []
    markup = InlineKeyboardMarkup(inline_keyboard=rows) if rows else None

    with sqlite3.connect('users.db') as db:
        cur = db.cursor()
        cur.execute("SELECT tg_id FROM users")
        user_ids = [row[0] for row in cur.fetchall()]

    count = 0
    for uid in user_ids:
        try:
            if photo:
                await bot.send_photo(chat_id=uid, photo=photo, caption=text, parse_mode='HTML', reply_markup=markup)
            else:
                await bot.send_message(chat_id=uid, text=text, parse_mode='HTML', reply_markup=markup)
            count += 1
        except:
            pass
    return count


@dp.message(States.newsletter_text)
async def newsletter_get_text(message: Message, state: FSMContext):
    await state.update_data(nl_text=message.text or message.caption or '')
    await state.set_state(States.newsletter_photo)
    await message.answer(
        '🖼 Прикрепите фото или нажмите «Пропустить»:',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Пропустить', callback_data='nl_skip_photo')]])
    )


@dp.message(States.newsletter_photo, F.photo)
async def newsletter_get_photo(message: Message, state: FSMContext):
    await state.update_data(nl_photo=message.photo[-1].file_id)
    await state.set_state(States.newsletter_buttons)
    await message.answer(
        '🔗 Введите кнопки в формате:\n<code>Текст кнопки | https://ссылка</code>\n\nКаждая кнопка с новой строки. Или нажмите «Пропустить».',
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Пропустить', callback_data='nl_skip_buttons')]])
    )


@dp.message(States.newsletter_buttons)
async def newsletter_get_buttons(message: Message, state: FSMContext):
    await state.update_data(nl_buttons=message.text)
    fsm_data = await state.get_data()
    await _send_newsletter_preview(message, fsm_data)


@dp.message(States.pay_receipt, F.photo)
async def receive_receipt(message: Message, state: FSMContext):
    photo = message.photo[-1].file_id
    fsm_data = await state.get_data()
    plan = fsm_data.get('plan')
    summ = fsm_data.get('summ')

    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Принять', callback_data=f'accept_{plan}_{message.from_user.id}', style='success')],
        [InlineKeyboardButton(text='Отклонить', callback_data=f'decline_{message.from_user.id}', style='danger')]
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
