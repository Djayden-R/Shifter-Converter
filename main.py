import sqlite3
from sqlite3 import Connection
from typing import Any
from datetime import datetime

shift_lables = ["_id", "text", "alarmTime", "alarm", "alarmOneDayBefore", "color", "textColor", "sequentialCode", "textSize", "alarmTime2", "alarm2", "alarmTwoDayBefore", "sound1", "sound2", "abbreviation", "startTime1", "endTime1", "startTime2", "endTime2", "splitShift", "performAction", "hourlyEarnings", "extraHourlyEarnings", "restTime", "shiftTime", "calculatedManualShiftDuration"]

def fetch_tables(database: Connection) -> list[tuple[str]]:
    """Find all tables in database and return them as a list"""
    query = "SELECT name FROM sqlite_schema WHERE type = 'table'"
    tables = database.execute(query).fetchall()
    return tables

def fetch_shifts(database: Connection):
    """Fetch all shifts from the database and format them as a standardized dictionary"""
    query = "SELECT * FROM tablaTurnos"
    shifts: list[tuple[Any]] = database.execute(query).fetchall()
    dict_shifts = [dict(zip(shift_lables, shift)) for shift in shifts]

    # Standardize values of shifts
    for shift in dict_shifts:
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
                blue =  color_int & 0xff
                green = (color_int >> 8) & 0xff
                red = (color_int >> 16) & 0xff

                color_hex = ('#%02x%02x%02x' % (red, green, blue))
                shift[label] = color_hex

        # Turn time string into datetime object
        time_labels = ["alarmTime", "alarmTime2", "startTime1", "endTime1",  "startTime2", "endTime2"]
        for label in time_labels:
            time_value = shift.get(label)
            if time_value:
                datetime_object = datetime.strptime(time_value, '%H:%M')
                shift[label] = datetime_object
        
    print(dict_shifts)

# query_2 = "SELECT * FROM android_metadata"
# android_metadata = db.execute(query_2)
# print(f"android_metadata: {android_metadata.fetchall()}")

# query_2 = "SELECT * FROM dias"
# dias = db.execute(query_2)
# print(f"dias: {dias.fetchall()}")

# query_2 = "SELECT * FROM nombreCalendario"
# nombreCalendario = db.execute(query_2)
# print(f"nombreCalendario: {nombreCalendario.fetchall()}")

# query_2 = "SELECT * FROM patrones"
# patrones = db.execute(query_2)
# print(f"patrones: {patrones.fetchall()}")

# query_2 = "SELECT * FROM contenidoPatron"
# contenidoPatron = db.execute(query_2)
# print(f"contenidoPatron: {contenidoPatron.fetchall()}")

# query_2 = "SELECT * FROM festivos"
# festivos = db.execute(query_2)
# print(f"festivos: {festivos.fetchall()}")

def main():
    db = sqlite3.connect("Testing.Shifter")
    # tables = fetch_tables(db)
    # print(tables)
    fetch_shifts(db)

    db.close()

if __name__ == "__main__":
    main()
