import sqlite3
from sqlite3 import Connection
from typing import Any, Optional
from datetime import datetime, date, time, timedelta
from dataclasses import dataclass, asdict
import ics
import re
from tzlocal import get_localzone

shift_lables = ["_id", "text", "alarmTime", "alarm", "alarmOneDayBefore", "color", "textColor", "sequentialCode", "textSize", "alarmTime2", "alarm2", "alarmTwoDayBefore", "sound1", "sound2", "abbreviation", "startTime1", "endTime1", "startTime2", "endTime2", "splitShift", "performAction", "hourlyEarnings", "extraHourlyEarnings", "restTime", "shiftTime", "calculatedManualShiftDuration"]

local_tz = get_localzone()


@dataclass
class Shift():
    _id: int
    text: str
    alarmTime: time
    alarm: bool
    alarmOneDayBefore: bool
    color: str
    textColor: str
    sequentialCode: int
    textSize: float
    alarmTime2: time
    alarm2: bool
    alarmTwoDayBefore: bool
    sound1: Optional[str]
    sound2: Optional[str]
    abbreviation: str
    startTime1: time
    endTime1: time
    startTime2: time
    endTime2: time
    splitShift: bool
    performAction: Optional[str]
    hourlyEarnings: Optional[float]
    extraHourlyEarnings: Optional[float]
    restTime: Optional[float]
    shiftTime: Optional[str]
    calculatedManualShiftDuration: Optional[float]

    @classmethod
    def from_dict(cls, shift: dict[str, Any]):
        # Turn boolean integers into actual python booleans
        boolean_labels = ["alarm", "alarmOneDayBefore", "alarm2", "alarmTwoDayBefore", "splitShift"]
        for label in boolean_labels:
            if shift.get(label, 0) == 0:
                shift[label] = False
            else:
                shift[label] = True

        # Turn color 32 bit integers into hex color codes
        color_labels = ["color", "textColor"]
        for label in color_labels:
            color_int = shift.get(label)
            if color_int:
                blue = color_int & 0xff
                green = (color_int >> 8) & 0xff
                red = (color_int >> 16) & 0xff

                color_hex = ('#%02x%02x%02x' % (red, green, blue))
                shift[label] = color_hex

        # Turn time string into datetime.time object
        time_labels = ["alarmTime", "alarmTime2", "startTime1", "endTime1", "startTime2", "endTime2"]
        for label in time_labels:
            time_value = shift.get(label)
            if time_value:
                datetime_object = datetime.strptime(time_value, '%H:%M').time()
                shift[label] = datetime_object
        return cls(**shift)


@dataclass
class DayWithShift(Shift):
    date: date
    note: str | None


@dataclass
class Day():
    date: date
    shift_id: Optional[int]
    note: Optional[str]


def fetch_tables(database: Connection) -> list[tuple[str]]:
    """Find all tables in database and return them as a list"""
    query = "SELECT name FROM sqlite_schema WHERE type = 'table'"
    tables = database.execute(query).fetchall()
    return tables


def fetch_shift_types(database: Connection) -> dict[int, Shift]:
    """Fetch different types of shift and format them as a dict of _id and Shift object"""

    # Fetch all shift types from database
    query = "SELECT * FROM tablaTurnos"
    sql_shifts: list[tuple[Any]] = database.execute(query).fetchall()

    # Pair every shift value with a label from shift_labels
    dict_shifts: list = [dict(zip(shift_lables, shift)) for shift in sql_shifts]

    # Turn every shift into a Shift object
    shifts: dict[int, Shift] = {}
    for shift in dict_shifts:
        shift_object = Shift.from_dict(shift)
        shifts[shift_object._id] = shift_object

    return shifts


def fetch_calendar(database: Connection) -> list[Any]:
    """Fetch all notes from database and return them"""

    # Fetch dates, shifts, and notes from table containing the dates
    query = "SELECT fecha, turno1, notas FROM dias"
    calendar: list[tuple[int, int | None, str | None]] = database.execute(query).fetchall()

    formatted_calendar: list[Day] = []

    for calendar_day in calendar:
        # Turn SQL date into a datetime.date object
        try:
            insane_date_str = str(calendar_day[0])  # Format is YYYYMMDD, but the month is apperantly in integers, so january is 00, this has wasted 2 hours of my life (╯°□°)╯︵ ┻━┻
            year = insane_date_str[:4]
            month = int(insane_date_str[4:6]) + 1
            month_str = f"{month:02d}"
            day = insane_date_str[6:]

            sane_date_str = f"{year}{month_str}{day}"

            date_object = datetime.strptime(sane_date_str, "%Y%m%d").date()
        except ValueError:
            continue

        # Get shift type and note of day
        shift_type: int | None = calendar_day[1]
        note: str | None = calendar_day[2]

        # Unformated notes look like this: <p dir="ltr">TEXT_HERE</p>
        # To parse this into normal text a regex match is used
        if note:
            note = re.findall(r'>(.*?)<', note)[0]

        # Add formatted day to list as a Day object
        formatted_calendar.append(Day(date_object, shift_type, note))

    return formatted_calendar


def combine_calendar_and_shifts(days: list[Day], shifts: dict[int, Shift]) -> list[Day | DayWithShift]:
    """Combine calendar entries with details about shifts"""
    combined_calendar: list[Day | DayWithShift] = []

    for day in days:
        shift_id = day.shift_id
        if shift_id:
            shift: Shift = shifts[shift_id]
            shift_day = DayWithShift(date=day.date, note=day.note, **asdict(shift))
            combined_calendar.append(shift_day)
        else:
            combined_calendar.append(day)

    return combined_calendar


def add_ics_event(calendar: ics.Calendar, name: str, start_date: date, start_time: time = time(0, 0), end_time=None, all_day=False, abreviation=None, second_part=False):
    event = ics.Event()

    event.name = name
    event.begin = datetime.combine(start_date, start_time).replace(tzinfo=None).replace(tzinfo=local_tz)

    if all_day:
        event.make_all_day()
        event.uid = f"note-{start_date.strftime('%Y-%m-%d')}-{name[:10].replace(' ', '')}"
    elif end_time:
        end_date = start_date if not (second_part or (start_time > end_time)) else start_date + timedelta(days=1)
        event.end = datetime.combine(end_date, end_time).replace(tzinfo=local_tz)
        event.uid = f"{abreviation if abreviation else 'shift'}-{start_date.strftime('%Y-%m-%d')}-{start_time.strftime('%H%M')}"
    else:
        print("ERROR: no end time found")

    calendar.events.add(event)
    global event_amount
    event_amount += 1


def shifts_to_ics(shifts: list[Day | DayWithShift]):
    ics_calendar = ics.Calendar()

    for day in shifts:
        if isinstance(day, DayWithShift):
            if day.startTime1 == day.endTime1:
                add_ics_event(ics_calendar, day.text, day.date, abreviation=day.abbreviation, all_day=True)
            else:
                add_ics_event(ics_calendar, day.text, day.date, start_time=day.startTime1, end_time=day.endTime1, abreviation=day.abbreviation)
                if day.splitShift:
                    add_ics_event(ics_calendar, day.text, day.date, start_time=day.startTime2, end_time=day.endTime2, abreviation=f"{day.abbreviation}-2", second_part=True)
        if day.note:
            add_ics_event(ics_calendar, day.note, day.date, all_day=True)

    with open('output_calendar.ics', 'w') as f:
        f.write(ics_calendar.serialize())


def main():
    global event_amount
    event_amount = 0
    # Open .Shifter file
    # db = sqlite3.connect("Testing.Shifter")
    db = sqlite3.connect("Cargill.Shifter")
    table_names: list[tuple[str]] = fetch_tables(db)

    # Check if table format is correct
    table_name_list = [row[0] for row in table_names]
    if ('tablaTurnos' not in table_name_list) or ('dias' not in table_name_list):
        raise ValueError("File isn't a valid .Shifter file")

    # Get information of shift types
    shift_types: dict[int, Shift] = fetch_shift_types(db)

    # Get all days and their corresponding shift_type and notes
    calendar: list[Day] = fetch_calendar(db)

    # Add shift details to the calendar items
    combined_calendar = combine_calendar_and_shifts(calendar, shift_types)

    shifts_to_ics(combined_calendar)
    print(event_amount)

    db.close()


if __name__ == "__main__":
    main()
