from dht 		import DHT11 as dht
from machine 	import Pin
from microdot_asyncio import Microdot

import time, utime, network, ntptime, urequests, gc

import upip

import uasyncio

# active low
relay_ON  = 0
relay_OFF = 1

sensor      = dht(Pin(23, Pin.IN))

relayOrange =     Pin(5,  Pin.OUT)
relayPurple =     Pin(18, Pin.OUT)

isConnected = False

class Timer:
    def start(self):
        self.start_time = time.time()
        
    def check(self):
        return time.time() - self.start_time
            

def getTime(timestamp, timezone):
    UTC  = time.localtime(timestamp)
    BRTZ = time.localtime(time.mktime(UTC)-3*60*60)
    
    utc  = "utc: {:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(UTC[0], UTC[1], UTC[2], UTC[3], UTC[4], UTC[5])
    brtz = "brtz: {:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(BRTZ[0], BRTZ[1], BRTZ[2], BRTZ[3], BRTZ[4], BRTZ[5])
    
    if timezone.lower() == 'utc':
        return utc
    elif timezone.lower() == 'brtz':
        return brtz
    else:
        return '{} - available timezones: utc, brtz'

def getMeasurements():
    timestamp = time.time()
    nowTime   = getTime(timestamp, 'brtz')
    
    sensor.measure()
    print('Temperature: {} | Humidity: {} | {}'.format(sensor.temperature(), sensor.humidity(), nowTime))
    
def getRequisition():
    requestsParameters = {"temperature": 0, "humidity": 0}
    temperatures = []
    humidity     = []
    for i in range(10):
        time.sleep(2)
        sensor.measure()
        temperatures.append(sensor.temperature())
        humidity.append(sensor.humidity())
    
    requestsParameters["temperature"] = sum(temperatures)/len(temperatures)
    requestsParameters["humidity"]    = sum(humidity)/len(humidity)

    relayOrange.value(relay_ON if requestsParameters["temperature"] >= 31 else relay_OFF)
    relayPurple.value(relay_ON if requestsParameters["humidity"]    >= 70 else relay_OFF)
    
    requestsParameters["relayOrange"] = relayOrange.value()
    requestsParameters["relayPurple"] = relayPurple.value()
    
    print(requestsParameters)
    return(requestsParameters)
        
    
def writeThingSpeak(parm):
    request = "https://api.thingspeak.com/update?api_key=R4YPOMPB7B6TTBTV&field1={}&field2={}&field3={}&field4={}".format(parm["temperature"], parm["humidity"], parm["relayOrange"], parm["relayPurple"])
    print('{} | {}'.format(request, getTime(time.time(), 'brtz')))
    response = urequests.get(request)
    print(response.text)
    response.close()
    
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

print('setting up...')
print('setting up connection...')
wlan.scan()

wlan.connect('homeLink', '%mamoreBa7bole%')

timer = Timer()
timeout = 60
print('awaiting connection. Timeout: {} seconds'.format(timeout))

timer.start()
while timer.check() < timeout:
    if wlan.isconnected():
        print('connected successfully. ({} seconds)'.format(timer.check()))
        break

print('is connected: {}'.format(wlan.isconnected()))
    
print('syncing time...')
ntptime.host=('pool.ntp.org')
ntptime.settime()
time.sleep(5)
print('time is synced. Now: {}'.format(getTime(time.time(), 'brtz')))
    
# the code below works fine, but I found out I wasn't supposed to host an API, but rather send data to one haha
# app = Microdot()
#     
# @app.route('/')
# async def default(request):
#     return 'the service is running.'
# 
# @app.route('/getHumidity')
# async def getHumidity(request):
#     sensor.measure()
#     return '{}'.format(sensor.humidity())
# 
# @app.route('/getTemperature')
# async def getTemperature(request):
#     sensor.measure()
#     return '{}'.format(sensor.temperature())
# 
# @app.route('/getMeasures')
# async def getMeasures(request):
#     sensor.measure()
#     return '{{"temperature": {}, "humidity" : {}}}'.format(sensor.temperature(), sensor.humidity())

# print('Starting microdot app')
# try:
#     print(wlan.ifconfig()[0])
#     app.run(port=80)
#     print('success')
# except Exception as e:
#     app.shutdown()
#     print(e)

print('-- starting diagnosis --')

nextRequestTime  = time.time()
while True:
    if time.time() >= nextRequestTime:
        parm = getRequisition()
        writeThingSpeak(parm)
        gc.collect()
        
        nextRequestTime += 1800
        print('next log at {}'.format(getTime(nextRequestTime, 'brtz')))
    time.sleep(15)

