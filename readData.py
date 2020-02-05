import time
import RPi.GPIO as GPIO
import sys
import signal

dictionary = {"C1" : 2,
              "C2" : 3,
              "C3" : 4,
              "C4" : 5,
              "C5" : 6,
              "P1" : 11,
              "P2" : 12,
              "P3" : 19,
              "P4" : 14,
              "Y1" : 15,
              "Y2" : 16,
              "Y3" : 17}
    
GPIO.setmode(GPIO.BCM)

pinTrigger=13
pinEchos = {2, 3, 4, 5, 6}
pinWrite = {11, 12, 19, 14, 15, 16, 17}

def close(signal,frame):
    print("turn off")
    GPIO.cleanup()
    sys.exit(0)
    
signal.signal(signal.SIGINT,close)

def readData(sensorId):
    pinEcho = dictionary[sensorId]
    GPIO.output(pinTrigger,True)
    time.sleep(0.00001)
    GPIO.output(pinTrigger,False)
    start=time.time()
    stop=time.time()

    while GPIO.input(pinEcho)==0:
        start=time.time()

    while GPIO.input(pinEcho)==1:
        stop=time.time()
    
    elapsed=stop-start
    distance=(elapsed*34300)/2
    return distance

def switchState(idWrite, state):
    pinWrite = dictionary[idWrite]
    if state:
        GPIO.output(pinWrite,True)
    else:
        GPIO.output(pinWrite,False)
    
def setup():
    print('SETUP')
    GPIO.setup(pinTrigger,GPIO.OUT)
    for pinEcho in pinEchos:
        GPIO.setup(pinEcho,GPIO.IN)
    
    for pin in pinWrite:
        GPIO.setup(pin, GPIO.OUT)    
    print('END')

setup()
switchState("Y3", 1)
