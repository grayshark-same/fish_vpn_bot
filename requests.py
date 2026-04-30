import sqlite3
import os
from aiogram import Dispatcher, Bot, F
from aiogram.filters import CommandStart, Command, Filter
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

async def add_user(tg_id: int, username: str):
    with sqlite3.connect('users.db') as db:
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
        user = cur.fetchone()
        print(user)
        if not user:
            cur.execute("INSERT INTO users (tg_id, username) VALUES(?, ?)",(tg_id, username))
