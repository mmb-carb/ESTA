
from pandas.tseries.holiday import USFederalHolidayCalendar
import numpy as np


# mapping from Python day-of-week number to a human-readable word (holidays are included)
DOW = {0: 'mon', 1: 'tuth', 2: 'tuth', 3: 'tuth', 4: 'fri', 5: 'sat', 6: 'sun', -1: 'holi'}


def find_holidays(base_year):
    ''' Using Pandas calendar, find all 10 US Federal Holidays,
        plus California's Cesar Chavez Day (March 31).
    '''
    yr = str(base_year)
    cal = USFederalHolidayCalendar()
    holidays = cal.holidays(start=yr + '-01-01', end=yr + '-12-31').to_pydatetime()
    holidays = np.delete(holidays, 6) # index, remove Columbus day

    return [d.strftime('%m-%d') for d in holidays] + ['03-31']
