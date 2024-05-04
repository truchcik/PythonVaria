import time, datetime
from P4 import P4

def getCheckFromDays(hr, min=0, daysBack =0, ):
    # today = datetime.datetime.strptime('26 Sep 2012', '%d %b %Y')
    today = datetime.datetime.today().replace(hour=hr, minute=min, second=0, microsecond=0) - datetime.timedelta(days = daysBack)
    tCheckFrom = datetime.datetime.timestamp(today)
    return tCheckFrom


checkUsrs = ['DoMil', 'Kokosz']   #users to check for submits
validDesc = 'Validated on buildmachine' #properly validated CL should have this in description
checkPath = '//streamsDomi/mainlineDomi/01_learn/...'

tCheckFrom = getCheckFromDays(hr=13, min=5, daysBack = 0)

p4 = P4()
p4.port = '1666'
p4.connect()

#info = p4.run('changes', '-s', 'submitted', '{}@2020/01/01,@2024/05/05'.format(checkPath))  #with time restriction, to search bigger databases
info = p4.run('changes',  '-s', 'submitted', checkPath)

print ('\nCL submitted after {}, not having "{}" in desc:'.format(datetime.datetime.fromtimestamp(tCheckFrom),validDesc))
for usr in checkUsrs:  # checking users from list
    print('\nUnvalidated CLs from user "{}":'.format(usr))
    for i in info:
        if i['user']==usr:
            tSubmitted = int(i['time'])
            if tSubmitted > tCheckFrom:
                #print ('\tUser name:', i['user'], end='')
                #print('Submit time:', datetime.datetime.fromtimestamp(tSubmitted))
                #print ('Path:', i['path'])
                #print('Workspace:', i['client'])
                print('\tDesc: "{}". \tSubmitted: {}'.format( i['desc'].strip(), datetime.datetime.fromtimestamp(tSubmitted) ) )

p4.disconnect()

