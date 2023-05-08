import re
from datetime import date, datetime, time, timedelta
from decimal import Decimal, DecimalException

from dateutil import parser
from dateutil.parser import ParserError

duration_rgx1 = re.compile(
    r'(-)?(\d+) (?:days?, )?(\d{1,2}):(\d{2}):(\d{2})(?:\.(\d+))?',
    re.IGNORECASE
)
duration_rgx2 = re.compile(
    r'(-)?P(\d+)DT(\d{2})H(\d{2})M(\d{2})(?:\.(\d+))?S',
    re.IGNORECASE
)


def try_convert(primitive, value, raise_on_error=True):
    try:
        return CONVERTERS[primitive](value)
    except (ValueError, TypeError, KeyError, ParserError, DecimalException) as err:
        if raise_on_error:
            raise ValueError(str(err)) from err
        return value


def str_to_timedelta(value):
    try:
        return timedelta(seconds=float(value))
    except ValueError:
        mtch = duration_rgx1.match(value) or duration_rgx2.match(value)
        if mtch:
            sign, days, hours, minutes, seconds, microseconds = mtch.groups()
            return (-1 if sign else 1) * timedelta(
                days=int(days),
                hours=int(hours),
                minutes=int(minutes),
                seconds=int(seconds),
                microseconds=int(microseconds or 0)
            )
        raise


def str_to_decimal(value):
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str) and value:
        return Decimal(value)
    raise ValueError('Invalid decimal value')


CONVERTERS = {
    date: lambda value: parser.parse(value).date(),
    datetime: lambda value: parser.parse(value),
    time: lambda value: parser.parse(value).time(),
    timedelta: str_to_timedelta,
    Decimal: str_to_decimal
}
