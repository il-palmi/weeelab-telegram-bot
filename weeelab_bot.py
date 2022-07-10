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
import test
import pytz
import os
import utils
import telegram
from datetime import datetime
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, filters, CallbackQueryHandler, CallbackContext, MessageHandler


load_dotenv(".env")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

DEFAULT_MESSAGES = json.load(open("default_messages.json"))

WEBAPP = {
    "CALENDARz": telegram.WebAppInfo("https://python-telegram-bot.org/static/webappbot"),
    "CALENDAR": telegram.WebAppInfo("https://expented.github.io/tgdtp/"),
    "TARALLO": telegram.WebAppInfo("https://tarallo.weeeopen.it/"),
}

'''
default_callback_structure = {
    "source": "command source",
    "type": "type of response",
    "action": "user action",
    "args": "arguments"
}
'''


# Commands handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=DEFAULT_MESSAGES["start"],
                                   parse_mode='HTML')


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

    connection = psycopg2.connect("dbname=weeelab user=weeelab-bot password=asd")
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM log WHERE date_trunc('day', date_in) = date_trunc('day', (SELECT MAX(date_in) FROM log));")
    message = compose_message(cursor.fetchall())
    callback = {
        "source": "log",
        "type": "calendar",
        "action": "show_calendar",
        "args": None
    }
    keyboard = [
        [
            InlineKeyboardButton("Select date",
                                 callback_data=f""
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


async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = json.loads(update.effective_message.web_app_data.data)
    print(data)
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        text=f"You selected the color with the HEX value <code>{data['hex']}</code>. The "
             f"corresponding RGB value is <code>{tuple(data['rgb'].values())}</code>."
    )


async def inline_buttons_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    button_data = dict(update.callback_query.data)
    await query.answer()
    if button_data["source"] == "None":
        return
    elif button_data["source"] == "log":
        await calendar(query, button_data)


async def calendar(query: telegram.CallbackQuery, button_data: dict):
    if button_data["action"] == 'show_select':
        # show calendar in chat
        date = datetime.today()
        keyboard = test.get_calendar_keyboard(
            source=button_data["source"],
            month=date.month,
            year=date.year
        )
        await query.edit_message_reply_markup()
    elif button_data["action"] == 'confirm':
        # show new log for date
        pass
    elif button_data["action"] == 'change_month':
        # change calendar
        pass


if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()

    # Command handlers
    application.add_handlers([
        CommandHandler("start", start),
        CommandHandler("log", log),
    ])

    # Message handlers
    application.add_handlers([
        MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data),
        CallbackQueryHandler(inline_buttons_callback)
    ])

    application.run_polling()
