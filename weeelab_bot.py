#!/usr/bin/env python
# coding:utf-8

"""
WEEELAB_BOT - Telegram bot.
Author: WEEE Open Team
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import json
import psycopg2
import pytz
import os
import utils
import telegram
from datetime import datetime
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, filters, CallbackQueryHandler,\
    CallbackContext, MessageHandler


load_dotenv(".env")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

DEFAULT_MESSAGES = json.load(open("default_messages.json"))

WEBAPP = {
    "CALENDARz": telegram.WebAppInfo("https://python-telegram-bot.org/static/webappbot"),
    "CALENDAR": telegram.WebAppInfo("https://expented.github.io/tgdtp/"),
    "TARALLO": telegram.WebAppInfo("https://tarallo.weeeopen.it/"),
}

application = (
    ApplicationBuilder()
    .token(TOKEN)
    .arbitrary_callback_data(True)
    .build()
)

'''
default_callback_structure = {
    "source": "command source",
    "type": "type of response",
    "action": "user action",
    "args": "arguments"
}
'''


# Decorators
def command_handler(command):
    def decorator(func):
        handler = CommandHandler(command, func)
        application.add_handler(handler)
        return func
    return decorator


def callback_query_handler(callback: str):
    def decorator(func):
        handler = CallbackQueryHandler(func, pattern=callback)
        application.add_handler(handler)
        return func
    return decorator


# Commands handlers
@command_handler("start")
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=DEFAULT_MESSAGES["start"],
                                   parse_mode='HTML')


@command_handler("log")
async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    def compose_message(fetch: list) -> str:
        if not fetch:
            message = DEFAULT_MESSAGES["log_empty"]
            return message
        date = fetch[0]["date_in"]
        message = f"<b>{date.date().strftime('%A %d-%m-%Y')}</b>\n\n"
        for row in fetch:
            message += f"<i>{row['username']}</i>"
            if row['duration']:
                seconds = row["duration"].total_seconds()
                hours, remainder = divmod(seconds, 60 * 60)
                minutes = int(remainder / 60)
                message += f" [{str(int(hours)).zfill(2)}:{str(minutes).zfill(2)}]"
                message += f": {row['description']}\n"
            else:
                message += ": inlab right now.\n"
        cursor.execute("SELECT MAX(GREATEST(date_in, date_out)) as latest FROM log;")
        # noinspection PyTypeChecker
        latest_log: datetime = cursor.fetchall()[0]["latest"]
        latest_log = latest_log.replace(tzinfo=pytz.UTC)
        latest_log = latest_log.astimezone(pytz.timezone("Europe/Rome"))
        message += f"\nLatest log update: {latest_log.strftime('%d-%m-%Y %H:%M')}\n"
        return message

    connection = psycopg2.connect("dbname=weeelab user=weeelab_bot password=asd")
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM log WHERE date_trunc('day', date_in) = date_trunc('day', (SELECT MAX(date_in) FROM log));")
    message = compose_message(cursor.fetchall())
    callback = {
        "source": "log",
        "type": "calendar",
        "action": "show",
        "args": None
    }
    keyboard = [
        [
            InlineKeyboardButton("Select date",
                                 callback_data=utils.dump_callback(callback)
                                 )
         ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    sender = update.message.reply_text(text=message,
                                       parse_mode="HTML",
                                       reply_markup=reply_markup)
    cursor.close()
    connection.close()
    await sender


@command_handler("test")
async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("asda", callback_data="asd")]]
    keyboard = InlineKeyboardMarkup(keyboard)
    sender = update.message.reply_text(text="lool",
                                       parse_mode="HTML",
                                       reply_markup=keyboard)
    await sender


# Web app things
async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = json.loads(update.effective_message.web_app_data.data)
    print(data)
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        text=f"You selected the color with the HEX value <code>{data['hex']}</code>. The "
             f"corresponding RGB value is <code>{tuple(data['rgb'].values())}</code>."
    )


# Callbacks
async def inline_buttons_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    button_data = utils.load_callback(update.callback_query.data)
    if not button_data:
        return
    await query.answer()
    if button_data["source"] == "None":
        return
    elif button_data["source"] == "log":
        await calendar(query, button_data)


@callback_query_handler("asd")
async def lol(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("asd")


async def calendar(query: telegram.CallbackQuery, button_data: dict):
    if button_data["action"] == 'show':
        # show calendar in chat
        if button_data["args"] != 'None':
            date = button_data["args"].split("-")
            month = int(date[0])
            year = int(date[1])
        else:
            date = datetime.today()
            month = date.month
            year = date.year
        keyboard = utils.get_calendar_keyboard(
            source=button_data["source"],
            month=month,
            year=year
        )
        await query.edit_message_reply_markup(reply_markup=keyboard)
    elif button_data["action"] == 'confirm':
        pass
    elif button_data["action"] == 'abort':
        await query.edit_message_text(query.message.text)


# Main
if __name__ == "__main__":
    application.run_polling()
