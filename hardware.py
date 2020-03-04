#import RPi.GPIO as GPIO

from time import time, sleep
from statistics import median
from collections import defaultdict


# pump identifiers
PUMPS = ["P1", "P2", "P3", "P4"]
# valve identifiers
VALVES = ["Y1", "Y2", "Y3"]
# meter identifiers
METERS = ["C1", "C2", "C3", "C4", "C5"]

SENSOR_PINS = {
        "C1" : 2, "C2" : 3, "C3" : 21, "C4" : 5, "C5" : 6,
        "P1" : 11, "P2" : 12, "P3" : 19, "P4" : 14,
        "Y1" : 15, "Y2" : 16, "Y3" : 17}

TRIGGER_PIN = 13
OUT_PINS = {11, 12, 19, 14, 15, 16, 17}
IN_PINS = {2, 3, 21, 5, 6, TRIGGER_PIN}
LAST_LEVEL = defaultdict(list)


def read_level(sensor):
    LAST_LEVEL[sensor].append(read_level_raw(sensor))
    if len(LAST_LEVEL[sensor]) > 6:
        LAST_LEVEL[sensor].pop(0)
    return median(LAST_LEVEL[sensor])


def read_level_raw(sensor, delay=1e-5, delta=0.0001):
    pin = SENSOR_PINS[sensor]
    GPIO.output(TRIGGER_PIN, 1)
    sleep(delay)
    GPIO.output(TRIGGER_PIN, 0)
    start = time()

    mean = 1
    ok = 0
    while mean > delta:
        value = int(GPIO.input(pin))
        if ok == 0 and value == 0:
            start = time()
        mean = (mean + value) / 2 
        if value == 1:
            ok = 1
        if ok == 1 and value == 0:
            break
        sleep(delay)

    stop = time()
    return (stop - start) * 34300 / 2


def write_state(sensor: str, state: bool):
    GPIO.output(SENSOR_PINS[sensor], 1-int(state))


def startup_gpio():
    GPIO.setmode(GPIO.BCM)
    for pin in IN_PINS:
        GPIO.setup(pin, GPIO.IN)
    for pin in OUT_PINS:
        GPIO.setup(pin, GPIO.OUT)


def cleanup_gpio():
    GPIO.cleanup()


def read_level(x): return 0
def write_state(x, y): return
def startup_gpio(): return
def cleanup_gpio(): return
