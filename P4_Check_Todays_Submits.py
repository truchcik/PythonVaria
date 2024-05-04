import time, datetime
from P4 import P4

def getTodayTime(startHour):
    #today = datetime.date.today()
    today = datetime.datetime.strptime('26 Sep 2012', '%d %b %Y')
    newdatetime = today.replace(hour=11, minute=59)


def getCheckFrom(checkNDays):
    tNow = (time.time())
    tCheckFrom = tNow - (24 * 60 * 60 * checkNDays)
    print ('Checking sumbits between {} and {}'.format(datetime.datetime.fromtimestamp(tNow),
                                                       datetime.datetime.fromtimestamp(tCheckFrom)))
    return tCheckFrom

checkUsrs = ['DoMil']   #users to check for submits
checkNDays = .06       #how many days to check
validDesc = 'Validated on buildmachine' #properly validated CL should have this in description

tCheckFrom = getCheckFrom(checkNDays)
getTodayTime('10:30')

p4 = P4()
p4.port = "1666"
p4.connect()

#with time restriction, to search bigger databases
#info = p4.run("changes", "-s", "submitted", "//streamsDomi/mainlineDomi/01_learn/...@2020/01/01,@2024/05/05")
info = p4.run("changes",  "-s", "submitted")

print ('\nCL submitted within {} days from now, not having "{}" in desc:\n'.format(checkNDays,validDesc))
for i in info:
    for usr in checkUsrs: #checking users from list
        if i['user']==usr:
            tSubmitted = int(i['time'])
            if tSubmitted > tCheckFrom:
                print ('\tUser name:', i['user'], end='')
                #print('Submit time:', datetime.datetime.fromtimestamp(tSubmitted))
                #print ('Path:', i['path'])
                #print('Workspace:', i['client'])
                print('\tDesc: "{}"'.format(i['desc'].strip()))

p4.disconnect()

