import sqlite3
import os
from aiogram import Dispatcher, Bot, F
from aiogram.filters import CommandStart, Command, Filter
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
import datetime


async def add_user(tg_id: int, username: str):
    with sqlite3.connect('users.db') as db:
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
        user = cur.fetchone()
        # print(user)
        if not user:
            cur.execute("INSERT INTO users (tg_id, username) VALUES(?, ?)",(tg_id, username))

async def add_sub(tg_id: int, plan: int):
    plan_days = {1: 30, 3: 90, 6: 180, 12: 365}
    with sqlite3.connect('users.db') as db:
        cur = db.cursor()
        cur.execute("SELECT end_of_sub FROM users WHERE tg_id = ?", (tg_id,))
        row = cur.fetchone()
        end_date = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S") if row and row[0] else None
        if not end_date or end_date < datetime.datetime.now():
            end_date = datetime.datetime.now()
        end_date += datetime.timedelta(days=plan_days[plan])
        cur.execute("UPDATE users SET end_of_sub = ? WHERE tg_id = ?", (end_date.strftime("%Y-%m-%d %H:%M:%S"), tg_id))

async def get_user_balance(tg_id: int):
    with sqlite3.connect('users.db') as db:
        cur = db.cursor()
        cur.execute("SELECT balance FROM users WHERE tg_id = ?", (tg_id,))
        balance = cur.fetchone()
        if balance[0] > 0:
            print(balance[0])
            return int(balance[0])
        return 0

async def add_balance(tg_id: int, summ: int):
    with sqlite3.connect('users.db') as db:
        cur = db.cursor()
        cur.execute("UPDATE users SET balance = balance + ? WHERE tg_id = ?", (summ, tg_id))

async def get_user_end_date(tg_id: int):
    with sqlite3.connect('users.db') as db:
        cur = db.cursor()
        cur.execute("SELECT end_of_sub FROM users WHERE tg_id = ?", (tg_id,))
        end_date = cur.fetchone()
        print(end_date)
        return end_date
    
