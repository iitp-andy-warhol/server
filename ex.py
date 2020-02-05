from datetime import datetime


def now():
    """
    Get datetime as string like '0000-00-00 00:00:00'
    :return: string
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"'{now}'"

print(now())
