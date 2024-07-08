from datetime import datetime, timedelta


def order_date(start_date=None, stop_date=None, **sets) -> list:
    last_moment = {'hour': 23, 'minute': 59, 'second': 59, 'microsecond': 999999}
    # first_day = {'day': 1, 'hour': 0, 'minute': 0, 'second': 0, 'microsecond': 0}
    first_day = {'hour': 0, 'minute': 0, 'second': 0, 'microsecond': 0}

    if 'defu' not in sets:
        sets['defu'] = 'last_day'

    now = datetime.now()

    if start_date and stop_date:
        def date_format(date):
            return '%Y-%m-%d %H:%M:%S' if len(date) > 10 else '%Y-%m-%d'

        start_format, stop_format = date_format(start_date), date_format(stop_date)

        try:
            start_date = datetime.strptime(start_date, start_format)
        except ValueError:
            start_date = now.replace(**first_day)

        try:
            stop_date = datetime.strptime(stop_date, stop_format)
        except ValueError:
            stop_date = now.replace(**last_moment)

        if len(stop_format) < 10:  # sets['defu'][:4] == 'last' and
            stop_date = stop_date.replace(**last_moment)
    else:
        start_format = stop_format = '%Y-%m-%d'

        if sets['defu'] == 'last_day':
            start_date = now.replace(**first_day)
            stop_date = now.replace(**last_moment)
        elif sets['defu'] == 'last_24_hours':
            start_date = now - timedelta(hours=24)
            stop_date = now
        elif sets['defu'] == 'last_week':
            start_date = now.replace(**first_day) - timedelta(days=7)
            stop_date = now.replace(**last_moment)
        elif sets['defu'] == 'last_month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=1)
            stop_date = now
        elif sets['defu'] == 'last_year':
            start_date = now.replace(**first_day) - timedelta(days=365)
            stop_date = now.replace(**last_moment)
        elif sets['defu'] == 'year_end':
            start_date = now.replace(**first_day)
            stop_date = datetime(start_date.year + 1, 1, 1) - timedelta(milliseconds=1)
        else:
            start_date = now
            stop_date = now

    result = [start_date, stop_date]

    if 'strf' in sets:
        result.append(datetime.strftime(start_date, start_format))
        result.append(datetime.strftime(stop_date, stop_format))

    return result
