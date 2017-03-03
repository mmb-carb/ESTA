
from pandas.tseries.holiday import USFederalHolidayCalendar


# mapping from Python day-of-week number to a human-readable word (holidays are included)
DOW = {0: 'mon', 1: 'tuth', 2: 'tuth', 3: 'tuth', 4: 'fri', 5: 'sat', 6: 'sun', -1: 'holi'}

# definition of which months belong in which season
MONTH_2_SEASON = {1: 'w', 2: 'w', 3: 'w', 4: 's', 5: 's', 6: 's',
                  7: 's', 8: 's', 9: 's', 10: 's', 11: 'w', 12: 'w'}


def find_holidays(base_year):
    ''' Using Pandas calendar, find all 10 US Federal Holidays,
        plus California's Cesar Chavez Day (March 31).
    '''
    yr = str(base_year)
    cal = USFederalHolidayCalendar()
    holidays = cal.holidays(start=yr + '-01-01', end=yr + '-12-31').to_pydatetime()

    return [d.strftime('%m-%d') for d in holidays] + ['03-31']


def find_season(date):
    ''' Given a Python Datetime object, return the string describing if the date
        falls in either Summer or Winter.
    '''
    return MONTH_2_SEASON[date.month]
