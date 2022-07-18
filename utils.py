import calendar as cal
import psycopg2
import os
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from psycopg2.extras import RealDictCursor


class Calendar:
    def __init__(self, month: int = datetime.today().month, date: datetime = datetime.today()):
        self.day = date.day
        self.month = month
        self.year = date.year

    def get_month_label(self):
        return f"{cal.month_name[self.month]} {self.year}"


class Database:
    def __enter__(self):
        self.connection = psycopg2.connect(f"dbname={os.getenv('POSTGRES_DB')}"
                                           f" user={os.getenv('POSTGRES_USER')}"
                                           f" password={os.getenv('POSTGRES_PASSWD')}")
        self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        self.connection.close()


def make_calendar(source: str, month: int = 0):
    date = datetime.today()
    calendar = Calendar(month)
    keyboard = []
    # Label
    keyboard.append(
        [InlineKeyboardButton(f"{calendar.get_month_label()}", callback_data="calendar:None")]
    )
    # Weekdays
    keyboard.append(
        [
            InlineKeyboardButton(f"Mo", callback_data="calendar:None"),
            InlineKeyboardButton(f"Tu", callback_data="calendar:None"),
            InlineKeyboardButton(f"We", callback_data="calendar:None"),
            InlineKeyboardButton(f"Th", callback_data="calendar:None"),
            InlineKeyboardButton(f"Fr", callback_data="calendar:None"),
            InlineKeyboardButton(f"Sa", callback_data="calendar:None"),
            InlineKeyboardButton(f"Su", callback_data="calendar:None"),
        ]
    )
    bulk = cal.month(calendar.year, calendar.month)
    bulk = bulk.splitlines()
    bulk = bulk[2:]
    for idx, line in enumerate(bulk):
        bulk[idx] = line.split()
    while len(bulk[0]) < 7:
        bulk[0].insert(0, ' ')
    while len(bulk[4]) < 7:
        bulk[4].append(' ')
    for line in bulk:
        days = []
        for day in line:
            callback = {"type": "calendar",
                        "source": source,
                        "action": "confirm",
                        "year": calendar.year,
                        "month": calendar.month,
                        "day": calendar.day}
            days.append(
                InlineKeyboardButton(f"{day}", callback_data=f"{callback}")
            )
        keyboard.append(days)
    decrease_month = {"type": "calendar",
                      "source": source,
                      "action": "month_select",
                      "new_month": f"{calendar.month - 1}"}
    increase_month = {"type": "calendar",
                      "source": source,
                      "action": "month_select",
                      "new_month": f"{calendar.month + 1}"}
    abort = {"type": "calendar",
             "source": source,
             "action": "abort"}

    keyboard.append(
        [
            InlineKeyboardButton("⬅️", callback_data=f"{decrease_month}"),
            InlineKeyboardButton("❌", callback_data=f"{abort}"),
            InlineKeyboardButton("➡️", callback_data=f"{increase_month}"),

        ]
    )
    return InlineKeyboardMarkup(keyboard)


def get_calendar_keyboard(source: str, month: int, year: int):
    today = datetime.today()

    # Making calendar structure
    cal = get_calendar_structure(month, year)

    # Making keyboard structure
    keyboard = []
    for row in cal:
        kb_line = []
        for item in row:
            if isinstance(row, str):
                button = InlineKeyboardButton(
                    f"{row}",
                    callback_data="empty"
                )
                kb_line.append(button)
                break
            if item.isdigit():
                callback = {
                    "source": source,
                    "type": "calendar",
                    "action": "confirm",
                    "args": f"{item}-{month}-{year}"
                }
                if int(item) == today.day and today.month == month and today.year == year:
                    text = f"🎈{item}"
                elif int(item) > today.day:
                    text = f"{item}"
                else:
                    text = f"{item}"
                    callback = {
                        "source": source,
                        "type": "calendar",
                        "action": None,
                        "args": None
                    }
                button = InlineKeyboardButton(
                    text,
                    callback_data=dump_callback(callback)
                )
            else:
                button = InlineKeyboardButton(
                    item,
                    callback_data="empty"
                )
            kb_line.append(button)
        keyboard.append(kb_line)
    increase_callback = {
        "source": source,
        "type": "calendar",
        "action": "show",
        "args": f"{month+1 if month < 12 else 1}-{year if month < 12 else year+1}"
    }
    decrease_callback = {
        "source": source,
        "type": "calendar",
        "action": "show",
        "args": f"{month-1 if month > 1 else 12}-{year if month > 1 else year-1}"
    }
    abort_callback = {
        "source": source,
        "type": "calendar",
        "action": "abort",
        "args": None
    }
    keyboard.append(
        [
            InlineKeyboardButton("⬅️", callback_data=f"{dump_callback(decrease_callback)}"),
            InlineKeyboardButton("❌", callback_data=f"{dump_callback(abort_callback)}"),
            InlineKeyboardButton("➡️", callback_data=f"{dump_callback(increase_callback)}"),

        ]
    )
    return InlineKeyboardMarkup(keyboard)


def get_calendar_structure(month, year) -> list:
    calendar = cal.month(year, month).splitlines()
    calendar[0] = calendar[0].lstrip(" ")
    for idx, row in enumerate(calendar[1:]):
        calendar[idx + 1] = row.split()
    while len(calendar[2]) < 7:
        calendar[2].insert(0, " ")
    while len(calendar[-1]) < 7:
        calendar[-1].append(" ")
    return calendar


def dump_callback(callback: dict) -> [str, None]:
    if isinstance(callback, str):
        return None
    dumped_cb = ""
    for idx in callback:
        dumped_cb += f"{callback[idx]}:"
    return dumped_cb.rstrip(":")


def load_callback(dumped_cb: str) -> [dict, None]:
    data = dumped_cb.split(":")
    try:
        callback = {
            "source": data[0],
            "type": data[1],
            "action": data[2],
            "args": data[3],
        }
    except IndexError:
        print("ERROR: Missing data in callback structure. Check for SOURCE, TYPE, ACTION or ARGS.")
        return None
    return callback