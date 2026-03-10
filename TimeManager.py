from datetime import datetime

# created time conversion functions to simplify it in actual code

def ConvertToNormal(date_string):
    date_object = datetime.strptime(date_string.replace(", ", "-").replace(",", "-"), "%Y-%m-%d-%H-%M")

    return str(date_object)

def CovertFromNormal(date_string):
    """Convert normal datetime string to tuple format (year, month, day, hour, minute)"""
    date_object = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
    return str((date_object.year, date_object.month, date_object.day, date_object.hour, date_object.minute))

def TupleNow():
    now = datetime.now()
    return str((now.year, now.month, now.day, now.hour, now.minute))

def NormalNow():
    now = datetime.now()
    return str(now.strftime("%Y-%m-%d %H:%M:%S"))

if __name__ == "__main__":
    # example use
    print(TupleNow())
    print(NormalNow())

    print(ConvertToNormal("2025, 12, 27, 0, 20"))
    print(CovertFromNormal("2025-12-27 00:20:00"))
