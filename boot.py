# This file is executed on every boot (including wake-boot from deepsleep)
import esp
import webrepl
import time

print('-- init boot --')
esp.osdebug(None)
webrepl.start()
print('-- booted --')