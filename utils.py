from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import calendar as cal


class Calendar:
    def __init__(self, month: int = datetime.today().month, date: datetime = datetime.today()):
        self.day = date.day
        self.month = month
        self.year = date.year

    def get_month_label(self):
        return f"{cal.month_name[self.month]} {self.year}"


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


def get_calendar_keyboard(month: int, year: int) -> InlineKeyboardMarkup:
    pass