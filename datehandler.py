from datetime import datetime
import re

def fix(st):
    t = st.find('-')
    if t > 0:
        rest = st[t:]
        y = st[:t]
    else:
        rest = ''
        y = st
        
    return '%04d%s'%(int(y), rest)

def isValidDate(dt):
    try:
        if dt == '-':
            return True
        m = re.search('(\d{0,4}\-\d{0,2}-\d{0,2})|(\d{0,4}\-\d{0,2})|((\d{0,4}))', fix(dt))
        if m is None:
            print('Wrong format: ', dt)
            return False

        if m.group(1) != None:
            _ = datetime.strptime(m.group(1), '%Y-%m-%d')
        if m.group(2) != None:
            _ = datetime.strptime(m.group(2), '%Y-%m')
        if m.group(3) != None:
            _ = datetime.strptime(m.group(3), '%Y')
        return True
    except ValueError:
        print('Bad Date!', dt)
        return False

""" string to date """
def str2date(dt):
    m = re.search('(\d{0,4}\-\d{0,2}-\d{0,2})|(\d{0,4}\-\d{0,2})|((\d{4}))', dt)

    try:
        if m is None:
            #date = "0"
            return '0'

        if m.group(1) != None:
            return datetime.strptime(m.group(1), '%Y-%m-%d')
        if m.group(2) != None:
            return datetime.strptime(m.group(2), '%Y-%m')
        if m.group(3) != None:
            return datetime.strptime(m.group(3), '%Y')
            
    except ValueError:
        print('here!', dt)
        return '0'

def median(ti):
    a = str2date(ti[0])
    b = str2date(ti[1])
    return (a + (b - a)/2).strftime("%Y-%m-%d")

"""
body = [{predicate: 'hasChild', type: 'ts', ts: '2019'},
        {predicate: 'isMarried', type: 'ti', ti: [2009, 2012]}]
header = 'hasChild'
"""
def handleDates(body, header_predicate, flag=''):
    G, C, R = 0, 1, 2
    if len(body) == 1:
        if body[0]['type'] == 'ts': # case 1
            return G, body[0]['ts'], None
        elif body[0]['type'] == 'ti': # case 2
            return G, None, body[0]['ti']
        else:
            return G, None, None
    else:
        for atom in body:
            if atom['predicate'] == header_predicate: # case 1, 2 | p1 ts1  & p2 ts2 => p2 ts2
                if atom['type'] == 'ts': # case 1 |
                    return G, atom['ts'], None
                elif atom['type'] == 'ti': # case 2 |
                    return G, None, atom['ti']
                else:
                    return G, None, None
                
        # cases with p3
        
        # case 3
        if body[0]['type'] == 'ts' and body[1]['type'] == '':
            return G, body[0]['ts'], None
        if body[0]['type'] == '' and body[1]['type'] == 'ts':
            return G, body[1]['ts'], None
        
        # case 3 |
        if body[0]['type'] == 'ti' and body[1]['type'] == '':
            return G, None, body[0]['ti']
        if body[0]['type'] == '' and body[1]['type'] == 'ti':
            return G, None, body[1]['ti']
        
        # case 4
        if body[0]['type'] == 'ts' and body[1]['type'] == 'ts' and body[0]['ts'] == body[1]['ts']:
            return G, body[0]['ts'], None
        if body[0]['type'] == 'ti' and body[1]['type'] == 'ti' and body[0]['ti'] == body[1]['ti']:
            return G, None, body[0]['ti']
        
        # case 5
        if body[0]['type'] == 'ts' and body[1]['type'] == 'ts' and body[0]['ts'] != body[1]['ts']:
            return G, None, sorted([body[0]['ts'], body[1]['ts']]) # TODO check
        
        # case 6a
        if body[0]['type'] == 'ts' and body[1]['type'] == 'ti' and body[0]['ts'] <= body[1]['ti'][0]:
            return G, None, [body[0]['ts'], body[1]['ti'][1]]
        if body[1]['type'] == 'ts' and body[0]['type'] == 'ti' and body[1]['ts'] <= body[0]['ti'][0]:
            return G, None, [body[1]['ts'], body[0]['ti'][1]]
        
        # case 6b
        if body[0]['type'] == 'ts' and body[1]['type'] == 'ti' and body[0]['ts'] >= body[1]['ti'][1]:
            return G, None, [body[1]['ti'][0], body[0]['ts']]
        if body[1]['type'] == 'ts' and body[0]['type'] == 'ti' and body[1]['ts'] >= body[0]['ti'][1]:
            return G, None, [body[0]['ti'][0], body[1]['ts']]
        
        # case 6c
        if body[0]['type'] == 'ts' and body[1]['type'] == 'ti' and body[0]['ts'] > body[1]['ti'][0] and body[0]['ts'] < body[1]['ti'][1]:
            if flag == 'conservative':
                return C, None, body[1]['ti']
            elif flag == 'restrictive':
                return R, body[0]['ts'], None
            else:
                return G, None, None
        if body[1]['type'] == 'ts' and body[0]['type'] == 'ti' and body[1]['ts'] > body[0]['ti'][0] and body[1]['ts'] < body[0]['ti'][1]:
            if flag == 'conservative':
                return C, None, body[0]['ti']
            elif flag == 'restrictive':
                return R, body[1]['ts'], None
            else:
                return G, None, None
            
        # case 7a
        if body[0]['type'] == 'ti' and body[1]['type'] == 'ti' and body[0]['ti'][1] < body[1]['ti'][0]:
            if flag == 'conservative':
                return C, None, [body[0]['ti'][0], body[1]['ti'][1]]
            elif flag == 'restrictive':
                return R, None, [median(body[0]['ti']), median(body[1]['ti'])]
            else:
                return G, None, None
        if body[0]['type'] == 'ti' and body[1]['type'] == 'ti' and body[1]['ti'][1] < body[0]['ti'][0]:
            if flag == 'conservative':
                return C, None, [body[1]['ti'][0], body[0]['ti'][1]]
            elif flag == 'restrictive':
                return R, None, [median(body[1]['ti']), median(body[0]['ti'])]
            else:
                return G, None, None
            
        # case 7b
        if body[0]['type'] == 'ti' and body[1]['type'] == 'ti' and body[0]['ti'][0] >= body[1]['ti'][0] and body[0]['ti'][1] <= body[1]['ti'][1]:
            if flag == 'conservative':
                return C, None, body[1]['ti']
            elif flag == 'restrictive':
                return R, None, body[0]['ti']
            else:
                return G, None, None
        if body[0]['type'] == 'ti' and body[1]['type'] == 'ti' and body[1]['ti'][0] >= body[0]['ti'][0] and body[1]['ti'][1] <= body[0]['ti'][1]:
            if flag == 'conservative':
                return C, None, body[0]['ti']
            elif flag == 'restrictive':
                return R, None, body[1]['ti']
            else:
                return G, None, None
            
        # case 7c
        if body[0]['type'] == 'ti' and body[1]['type'] == 'ti' and body[0]['ti'][0] < body[1]['ti'][0] and body[0]['ti'][1] > body[1]['ti'][0]:
            if flag == 'conservative':
                return C, None, [body[0]['ti'][0], body[1]['ti'][1]]
            elif flag == 'restrictive':
                return R, None, [body[1]['ti'][0], body[0]['ti'][1]]
            else:
                return G, None, None
        if body[0]['type'] == 'ti' and body[1]['type'] == 'ti' and body[1]['ti'][0] < body[0]['ti'][0] and body[1]['ti'][1] > body[0]['ti'][0]:
            if flag == 'conservative':
                return C, None, [body[1]['ti'][0], body[0]['ti'][1]]
            elif flag == 'restrictive':
                return R, None, [body[0]['ti'][0], body[1]['ti'][1]]
            else:
                return G, None, None
            
        # case 7d
        if body[0]['type'] == 'ti' and body[1]['type'] == 'ti' and body[0]['ti'][1] == body[1]['ti'][0]:
            if flag == 'conservative':
                return C, None, [body[0]['ti'][0], body[1]['ti'][1]]
            elif flag == 'restrictive':
                return R, body[0]['ti'][1], None
            else:
                return G, None, None
        if body[0]['type'] == 'ti' and body[1]['type'] == 'ti' and body[1]['ti'][1] == body[0]['ti'][0]:
            if flag == 'conservative':
                return C, None, [body[1]['ti'][0], body[0]['ti'][1]]
            elif flag == 'restrictive':
                return R, body[1]['ti'][1], None
            else:
                return G, None, None

"""Parse a string date from Yago into a YYYY-MM-DD format."""
def parse_date(dt):
    m = re.search('(\d{0,4}\-\d{0,2}-\d{0,2})|((\d{4})\-##\-##)', dt)

    try:
        if m is None:
            #date = "0"
            return '0'

        if m.group(1) != None:
            #return datetime.strptime(m.group(1), '%Y-%m-%d')
            return m.group(1)
        if m.group(2) != None:
            #return datetime.strptime(m.group(3), '%Y')
            return m.group(3)

    except ValueError:
        return '0'


"""
Allen Date Checker
Based on https://github.com/crsmithdev/arrow/files/678027/Allen_interval_rules_arrow.txt
"""

# TODO delete all unused functions

def __getdates(d):
    return d[0] if d[0] else "9999", d[1] if d[1] else "9999"

def ContainedBy(x, y):
    xi, xf = __getdates(x)
    yi, yf = __getdates(y)
    return (xi > yi) and (xf < yf)


def Contains(x, y):
    xi, xf = __getdates(x)
    yi, yf = __getdates(y)
    return (yi > xi) and (yf < xf)


def FinishedBy(x, y):
    xi, xf = __getdates(x)
    yi, yf = __getdates(y)
    return (yf == xf) and (yi > xi)


def Finishes(x, y):
    return (xf == yf) and (xi > yi)


def IsEqualTo(x, y):
    xi, xf = __getdates(x)
    yi, yf = __getdates(y)
    return (xi == yi) and (xf == yf)


def Meets(x, y):
    xi, xf = __getdates(x)
    yi, yf = __getdates(y)
    return (xf == yi)


def MetBy(x, y):
    xi, xf = __getdates(x)
    yi, yf = __getdates(y)
    return (yf == xi)


def OverlapedBy(x, y):
    xi, xf = __getdates(x)
    yi, yf = __getdates(y)
    return (yi < xi) and ((yf > xi) and (yf < xf))


def Overlaps(x, y):
    xi, xf = __getdates(x)
    yi, yf = __getdates(y)
    return (xi < yi) and ((xf > yi) and (xf < yf))


def StartedBy(x, y):
    xi, xf = __getdates(x)
    yi, yf = __getdates(y)
    return (yi == xi) and (yf < xf)


def Starts(x, y):
    xi, xf = __getdates(x)
    yi, yf = __getdates(y)
    return (xi == yi) and (xf < yf)


def TakesPlaceAfter(x, y):
    xi, xf = __getdates(x)
    yi, yf = __getdates(y)
    return xi > yf
                

def TakesPlaceBefore(x, y):
    xi, xf = __getdates(x)
    yi, yf = __getdates(y)
    return xf < yi


    
"""
Using Allen Temporal Constrainst to pick 1 ranges from 2 ranges
"""
def getRange(range1, range2):
    if range1[0] <= range2[0]:
        first = range1
        second = range2
    else:
        first = range2
        second = range1
    if second[0] == first[1] or TakesPlaceBefore(first, second): # there is no intersection between the 2 ranges
        return (first[0], second[1])
    elif Contains(first, second):
        return second
    else:
        return (second[0], first[1])


"""
Obtain date from item result
"""
def getRangeFromItem(item):
    if 'date' in item:
        return (item['date'], None)
    else:
        r1 = (item['born'], item['died'])
        r2 = (item['start'], item['end'])
        return getRange(r1, r2)

"""
Choose dates from atoms and metafacts in body to propagate to header
"""
def pickRange2Propagate(range1, range2):
    if range1[1] == None:
        if range2[1] == None: # timestamp + timestamp
            return (min((range1[0], range2[0])), max((range1[0], range2[0])))
        else: # timestamp + interval
            return (min((range1[0], range2[0])), range2[1])
    else:
        if range2[1] == None: # interval + timestamp
            return (min((range1[0], range2[0])), range1[1])
        else: # interval + interval
            return getRange(range1, range2)
        
"""
Extract a valid range from a metafact
"""
def getRangeFromMF(mf):
    in_date_time = mf['inDateTime']
    after = mf['after']
    before = mf['before']
    return (in_date_time if after == None else after, before)


## ***************************************************************************************
## TODO evaluate if needed; if not, remove

"""#### Selecting a timestamp from a group of dates
```
timestamp timestamp -> timestamp
timestamp interval  -> timestamp
interval  timestamp -> timestamp
interval  interval  -> timestamp
```
In all cases we pick the lowest of all dates as **inDateTime**"""
def pickTimestamp(dates):
    temp = [x for x in dates if x != None]
    return min(temp)

"""#### Selecting a time interval from a group of dates
```
timestamp timestamp -> interval
timestamp interval  -> interval
interval  timestamp -> interval
interval  interval  -> interval
```
In all cases we pick the lowest of all dates as **after** and the greatest as **before**"""
def pickTimestamp(dates):
    temp = [x for x in dates if x != None]
    return min(temp), max(temp)

"""#### Obtain all the appropriate dates from a metafact and results form a query"""
def obtainDates(mf, item):
    in_date_time = mf['inDateTime']
    after = mf['after']
    before = mf['before']
    """
    f1 = after if after else in_date_time
    f2 = before
    f3 = item['date'] if 'date' in item else """
    
def selectTimestamp(mf, item, obj):
    in_date_time = mf['inDateTime']
    after = mf['after']
    before = mf['before']
