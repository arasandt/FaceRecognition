from datetime import datetime, timedelta
from dateutil import tz

def getFileTime(dt):
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('America/New_York')    
    microseconds = int(dt, 16) / 10
    #print('Microseconds ', microseconds)
    seconds, microseconds = divmod(microseconds, 1000000)
    days, seconds = divmod(seconds, 86400)
    utc = datetime(1601, 1, 1) + timedelta(days, seconds, microseconds)
    utc = utc.replace(tzinfo=from_zone)
    est = utc.astimezone(to_zone)
    return est #.strftime('%m/%d/%Y %I:%M:%S %p %Z')
 
def getFileHex(dt):
    from_zone = tz.gettz('America/New_York')    
    to_zone = tz.gettz('UTC')
    est = datetime.strptime(dt,'%m/%d/%Y %I:%M:%S %p')
    est = est.replace(tzinfo=from_zone)
    utc = est.astimezone(to_zone)
    microseconds = (utc.replace(tzinfo=None) - datetime(1601, 1, 1)).total_seconds() * 1000000
    #print('Microseconds ', microseconds)
    return hex(int(microseconds * 10))[2:]
 
if __name__ == '__main__':
    data_hex = ['1d4750c785cec00']
    data_time = ['11/05/2018 08:35:52 AM']
    print(data_hex[0], "-->", getFileTime(data_hex[0]).strftime('%m/%d/%Y %I:%M:%S %p %Z'))
    print(data_time[0], "EST -->", getFileHex(data_time[0]))
