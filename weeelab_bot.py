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

import logging
import json
import psycopg2
import datetime

import pytz
from psycopg2.extras import RealDictCursor
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler


TOKEN = "2067550678:AAHMlWnjmfwoicfQmDTqysmeJr5NcJ9uMdU"
DEFAULT_MESSAGES = json.load(open("default_messages.json"))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=DEFAULT_MESSAGES["start"],
                                   parse_mode='HTML')

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    def compose_message(fetch: list) -> str:
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
        latest_log: datetime.datetime = cursor.fetchall()[0]["latest"]
        latest_log = latest_log.replace(tzinfo=pytz.UTC)
        latest_log = latest_log.astimezone(pytz.timezone("Europe/Rome"))
        message += f"\nLatest log update: {latest_log.strftime('%d-%m-%Y %H:%M')}"
        return message

    try:
        args = update.message.text.split(" ", 1)[1]
    except:
        args = None
    connection = psycopg2.connect("dbname=weeelab user=weeelab-bot password=asd")
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    if not args:
        cursor.execute("SELECT * FROM log WHERE date_trunc('day', date_in) = date_trunc('day', (SELECT MAX(date_in) FROM log));")
        message = compose_message(cursor.fetchall())
    elif len(args.split()) > 1:
        message = DEFAULT_MESSAGES["log_format_error"]
    else:
        cursor.execute(
            f"SELECT * FROM log WHERE date_trunc('day', date_in) = {datetime.datetime.now().date()}")
        message = compose_message(cursor.fetchall())

    sender = context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=f"{message}",
                                   parse_mode='HTML')
    cursor.close()
    connection.close()
    await sender


if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()
    start_handler = CommandHandler("start", start)
    # log_handler = CommandHandler("log", log)
    application.add_handler(start_handler)
    application.add_handler(CommandHandler("log", log))
    application.run_polling()
