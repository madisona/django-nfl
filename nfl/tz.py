
"""
Helps convert to/from UTC and other time zones. Note this
will only work when the Daylight Savings starts on the
Second Sunday of March and Ends on the First Sunday of November.
(it usually does, but it can be off)
"""

from datetime import datetime, tzinfo, timedelta

class Zone(tzinfo):

    def __init__(self, offset, name):
        self.offset = offset
        self.name = name

    def __str__(self):
        return unicode(self.name + " " + str(self.offset))

    def __repr__(self):
        return str(self)

    def utcoffset(self, dt):
        return timedelta(hours=self.offset) + self.dst(dt)

    def dst(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return self.name

class StandardAmericanZone(Zone):

    def dst(self, dt):
        if self.get_dst_start(dt) <= dt.replace(tzinfo=None) < self.get_dst_end(dt):
            return timedelta(hours=1)
        return timedelta(0)

    def get_dst_start(self, dt):
        """
        Daylight savings starts second Sunday in March
        """
        d = datetime(dt.year, 3, 1)
        return self._get_next_sunday(d, 7)

    def get_dst_end(self, dt):
        """
        Daylight savings ends first Sunday in November
        """
        d = datetime(dt.year, 11, 1)
        return self._get_next_sunday(d)

    def _get_next_sunday(self, dt, days_to_add=0):
        """
        6 is weekday integer for Sunday
        """
        if dt.weekday() != 6:
            days_to_add += 6 - dt.weekday()
        return dt + timedelta(days=days_to_add)

UTC      = Zone(0, 'UTC')

# Standard zones
EASTERN  = StandardAmericanZone(-5, 'America/New_York')
CENTRAL  = StandardAmericanZone(-6, 'America/Chicago')
MOUNTAIN = StandardAmericanZone(-7, 'America/Denver')
PACIFIC  = StandardAmericanZone(-8, 'America/Los_Angeles')

# Returns current time for standard zone requested
def get_current_time(tz=EASTERN):
    utc_time = datetime.utcnow().replace(tzinfo=UTC)
    return utc_time.astimezone(tz)

def get_datetime_from_string(date_string):
    # For some reason appengine doesn't like me using strptime...
#    return datetime.datetime.strptime(date_string, "%m/%d/%Y")
    month, day, year = [int(v) for v in date_string.split('/')]
    return datetime(year, month, day)
