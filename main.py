import sqlite3
from sqlite3 import Connection
from typing import Any, Optional
from datetime import datetime, date, time
from dataclasses import dataclass, asdict

shift_lables = ["_id", "text", "alarmTime", "alarm", "alarmOneDayBefore", "color", "textColor", "sequentialCode", "textSize", "alarmTime2", "alarm2", "alarmTwoDayBefore", "sound1", "sound2", "abbreviation", "startTime1", "endTime1", "startTime2", "endTime2", "splitShift", "performAction", "hourlyEarnings", "extraHourlyEarnings", "restTime", "shiftTime", "calculatedManualShiftDuration"]


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
    sound1: str
    sound2: str
    abbreviation: str
    startTime1: time
    endTime1: time
    startTime2: time
    endTime2: time
    splitShift: bool
    performAction: str
    hourlyEarnings: float
    extraHourlyEarnings: float
    restTime: float
    shiftTime: float
    calculatedManualShiftDuration: float

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

    for day in calendar:
        # Turn SQL date into a datetime.date object
        date_str = str(day[0])  # Format is YYYYMMDD
        date_object = datetime.strptime(date_str, "%Y%m%d").date()

        # Get shift type and note of day
        shift_type: int | None = day[1]
        note: str | None = day[2]

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


""" Only contains language code """
# query_2 = "SELECT * FROM android_metadata"
# android_metadata = db.execute(query_2)
# print(f"android_metadata: {android_metadata.fetchall()}")

""" Mostly a bunch of None's, only fecha has the date and notas has the note with html tags and nota1 as shift type"""
# query_2 = "SELECT * FROM dias"
# dias = db.execute(query_2)
# print(f"dias: {dias.fetchall()}")

""" Only shows name of calendar """
# query_2 = "SELECT * FROM nombreCalendario"
# nombreCalendario = db.execute(query_2)
# print(f"nombreCalendario: {nombreCalendario.fetchall()}")

""" No clue """
# query_2 = "SELECT * FROM patrones"
# patrones = db.execute(query_2)
# print(f"patrones: {patrones.fetchall()}")

""" Also no clue """
# query_2 = "SELECT * FROM contenidoPatron"
# contenidoPatron = db.execute(query_2)
# print(f"contenidoPatron: {contenidoPatron.fetchall()}")

""" Holidays or something, but it doesn't return anything by default """
# query_2 = "SELECT * FROM festivos"
# festivos = db.execute(query_2)
# print(f"festivos: {festivos.fetchall()}")


def main():
    # Open .Shifter file
    db = sqlite3.connect("Testing.Shifter")
    table_names: list[tuple[str]] = fetch_tables(db)

    # Check if table format is correct
    if not (tuple('tablaTurnos') in table_names) and (tuple('dias') in table_names):
        raise ValueError("File isn't a valid .Shifter file")

    # Get information of shift types
    shift_types: dict[int, Shift] = fetch_shift_types(db)

    # Get all days and their corresponding shift_type and notes
    calendar: list[Day] = fetch_calendar(db)

    combined_calendar = combine_calendar_and_shifts(calendar, shift_types)
    print(combined_calendar)

    db.close()


if __name__ == "__main__":
    main()
