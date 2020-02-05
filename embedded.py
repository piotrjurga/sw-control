import RPi.GPIO as GPIO
import sys
import signal
from time import time, sleep

sensors = {"C1" : 2, "C2" : 3, "C3" : 4, "C4" : 5, "C5" : 6, "P1" : 11, "P2" : 12, "P3" : 19, "P4" : 14, "Y1" : 15, "Y2" : 16, "Y3" : 17}

pinTrigger = 13
pinEchos = {2, 3, 4, 5, 6}
pinWrite = {11, 12, 19, 14, 15, 16, 17}

from collections import defaultdict

lastm = defaultdict(list)
def readData(sensorId):
    lastm[sensorId].append(_readData(sensorId))
    if len(lastm[sensorId]) > 6:
        lastm[sensorId].pop(0)
    return sum(lastm[sensorId]) / len(lastm[sensorId])

    for _ in range(10):
        lastm[sensorId] = (3*lastm[sensorId] + 1*_readData(sensorId))/4
    return lastm[sensorId]
    #return (_readData(sensorId) + _readData(sensorId))/2

def _readData(sensorId):
    pin = sensors[sensorId]
    GPIO.output(pinTrigger, 1)
    sleep(1e-5)
    GPIO.output(pinTrigger, 0)

    start = time()

    mean = 1
    ok = 0
    while mean > 0.0001:
        value = int(GPIO.input(pin))
        if ok == 0 and value == 0:
            start = time()
        mean = (mean + value) / 2 
        if value == 1:
            ok = 1
        if ok == 1 and value == 0:
            break
        sleep(0.00001)

    stop = time()
    
    return (stop - start) * 34300 / 2

def switchState(sensor, state):
    GPIO.output(sensors[sensor], 1-int(state))
    
def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pinTrigger, GPIO.OUT)
    for pinEcho in pinEchos:
        GPIO.setup(pinEcho, GPIO.IN)
    
    for pin in pinWrite:
        GPIO.setup(pin, GPIO.OUT)

def close(signal, frame):
    print("turn off")
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, close)
setup()

'''switchState('P2', True)
switchState('P3', True)
switchState('P4', True)'''
