import RPi.GPIO as GPIO
import sys
import signal
from time import time, sleep

sensors = {"C1" : 2, "C2" : 3, "C3" : 4, "C4" : 5, "C5" : 6, "P1" : 11, "P2" : 12, "P3" : 19, "P4" : 14, "Y1" : 15, "Y2" : 16, "Y3" : 17}

pinTrigger = 13
pinEchos = {2, 3, 4, 5, 6}
pinWrite = {11, 12, 19, 14, 15, 16, 17}

def readData(sensorId):
    pin = sensors[sensorId]
    GPIO.output(pinTrigger, 1)
    sleep(0.00001)
    GPIO.output(pinTrigger, 0)

    start = time()
    while GPIO.input(pin) == 0:
        start = time()

    stop = time()
    while GPIO.input(pin) == 1:
        stop = time()
    
    return (stop - start) * 34300 / 2

def switchState(sensor, state):
    GPIO.output(sensors[sensor], state)
    
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

