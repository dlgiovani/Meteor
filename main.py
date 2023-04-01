from dht import DHT11 as dht
from machine import Pin

import time, utime, network, ntptime

sensor      = dht(Pin(23, Pin.IN))

relayOrange =     Pin(5,  Pin.OUT)
relayPurple =     Pin(18, Pin.OUT)

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
    
def controlRelays():
    relayOrange.value(sensor.temperature() >= 31)
    relayPurple.value(sensor.humidity() >= 70)
    
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

print('configuring time...')
ntptime.host=('pool.ntp.org')
ntptime.settime()
time.sleep(5)
print('time is configured. Now: {}'.format(getTime(time.time(), 'brtz')))

print('-- starting diagnosis --')
while True:
    time.sleep(5)
    getMeasurements()
    controlRelays()
