import datetime as dt


def aware_datetime():
    return dt.datetime.now().astimezone()


def naive_datetime():
    return dt.datetime.now()


def utc_datetime():
    return dt.datetime.utcnow()
