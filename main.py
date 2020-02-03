"""
Tutaj znajduje sie plik z algorytmem sterowania 
zgodny z wyslana specyfikacja.

Ten plik korzysta z konfiguracji oraz konteneru zawartego w `model/`
tam znajduje sie implementacja symulacji (SimulationModel) oraz
prawdziwego environmentu (BlackBoxModel).
"""

import asyncio as aio
import time
import pandas as pd

from sys import stderr
from os import path
from datetime import datetime

from config import *
from embedded import *

# state keys
KEYS = ["timestamp"] + METERS + VALVES + PUMPS

# settings
C1_max, C2_max, C3_max, C4_max, C5_max = 100, 10, 10, 10, 100
C1_min, C2_min, C3_min, C4_min, C5_min = 0.1, 0.1, 0.1, 0.1, 0.1
T_ust1, T_ust2, T_ust3, T_ust4, T_ust5 = 8, 8, 8, 8, 2
C2_rd, C3_rd, C4_rd = 1, 1, 1
C2_rg, C3_rg, C4_rg = 8, 8, 8
report_dir = "."

# timings
measure_delay = 0.01
delay = 0.01

# conditions for detecting an airlock
min_frames_without_change = 5
min_meter_delta = 0.5 * measure_delay

# current cycle
cycle = None


class Cycle:
    """
    Akcje wykonywane po uplywie pelnego cyklu.
    (zapisanie do pliku, elapsed_time, potwierdzone stany)
    """

    def __init__(self, purifier):
        self.history = pd.DataFrame(columns=KEYS)
        self.start_time = time.time()
        self.state = {k: None for k in KEYS}
        self.active = True
        self.airlocked = False
        self.purifier = purifier
        self.update_state()
        self.shift_state()

    def save_history(self, report_dir):
        report_name = f"{int(self.start_time)}.csv"
        report_path = path.join(report_dir, report_name)
        if not path.exists(report_dir):
            os.makedirs(report_dir)
        log(f"saving history at {report_path}")
        self.history.to_csv(report_path)

    def elapsed_time(self):
        return time.time() - self.start_time

    def shift_state(self):
        self.history = self.history.append([self.state], ignore_index=True)

    def update_state(self):
        self.state["timestamp"] = time.time()
        for id in VALVES + PUMPS + METERS:
            self.state[id] = readData(id)


# funkcja do wypisywania na ekran
def log(s, color=None):
    # todo: something more sophisticated
    if color is None:
        print(s, file=stderr)
    else:
        print(f"\033[{color}m{s}\033[m", file=stderr)


# mock: dla czasu
def get_elapsed() -> float:
    return cycle.elapsed_time()


# mock: dla czujnika poziomu wody
def get_level(id) -> float:
    assert id in METERS
    return cycle.state[id]


# rozkaz dla pompy
async def set_pump(id, state: bool):
    # todo: implement me
    assert id in PUMPS
    if state:
        while cycle.airlocked:
            await aio.sleep(delay)
    log(f"set pump {id} from {cycle.state[id]} to {state}")
    # XXX: cycle.purifier.control.set_pump(id, state)
    cycle.purifier.state[id] = state
    # cycle.state[id] = state


# rozkad dla zawaru
def set_valve(id, state: bool):
    # todo: implement me
    assert id in VALVES
    log(f"set valve {id} from {cycle.state[id]} to {state}")
    # XXX: cycle.purifier.control.set_valve(id, state)
    cycle.purifier.state[id] = state
    # cycle.state[id] = state


# sprawdzenie czy mamy zapowietzenie
async def check_for_airlock(pump, meter):
    assert pump in PUMPS
    assert meter in METERS
    recent_meter = cycle.history[meter][-min_frames_without_change:]
    recent_pump = cycle.history[pump][-min_frames_without_change:]
    if all(p == 1 for p in recent_pump):
        delta = max(recent_meter) - min(recent_meter)
        if delta < min_meter_delta:
            log(f"pump {pump} airlocked, locking other pumps")
            cycle.airlocked = True
            previous_state = {p: cycle.state[p] for p in PUMPS}
            for p in PUMPS:
                if p != pump:
                    await set_pump(p, 0)
            while max(recent_meter) - min(recent_meter) < delta:
                await aio.sleep(delay)
                recent_meter = cycle.history[meter][-min_frames_without_change:]
            for p in PUMPS:
                await set_pump(p, previous_state[p])
            cycle.airlocked = False
            log(f"airlock of {pump} resolved, unlocking other pumps")


# FAZA 1
async def phase_1():
    log("entered phase 1", color=92)
    if get_level(C1) >= C1_max:
        return
    await set_pump(P1, 1)
    while not (get_level(C1) >= C1_max):
        await aio.sleep(delay)
    await set_pump(P1, 0)
    log("exiting phase 1")


# FAZA 2
async def phase_2():
    log("entered phase 2", color=92)
    # TODO(piotr): should we check for airlocks here? the meter level
    # may be constant naturally as the pumps are potentially on
    while True:
        while get_elapsed() < T_ust1 and not (
            get_level(C1) < C1_max and get_level(C5) > C5_min
        ):
            await aio.sleep(delay)
        if get_elapsed() >= T_ust1:
            break
        await set_pump(P1, 1)
        while get_elapsed() < T_ust1 and not (
            get_level(C1) >= C1_max and get_level(C5) <= C5_min
        ):
            await aio.sleep(delay)
        if get_elapsed() >= T_ust1:
            break
        await set_pump(P1, 0)
    await set_pump(P1, 0)
    log("exiting phase 2")


# FAZA 3
async def phase_3(P_i, Y_i, C_i, c_min, c_rd, c_rg, t_ust):
    log(f"entered phase 3 (pump {P_i})", color=92)
    await set_pump(P_i, 1)
    while not get_level(C_i) > c_rd:
        await check_for_airlock(P_i, C_i)
        await aio.sleep(delay)
    set_valve(Y_i, 1)

    # TODO(piotr): should we check for airlocks here? the meter level
    # may be constant naturally as the valve is open
    while get_elapsed() < t_ust:
        while get_elapsed() < t_ust and not get_level(C_i) > c_rg:
            await aio.sleep(delay)
        if get_elapsed() >= t_ust:
            break
        await set_pump(P_i, 0)
        while get_elapsed() < t_ust and not get_level(C_i) < c_rd:
            await aio.sleep(delay)
        if get_elapsed() >= t_ust:
            break
        await set_pump(P_i, 1)

    await set_pump(P_i, 0)
    while not get_level(C_i) < c_min:
        await aio.sleep(delay)
    set_valve(Y_i, 0)
    log(f"exiting phase 3 (pump {P_i})")


# FAZA 4
async def phase_4():
    log(f"entered phase 4", color=92)
    if not get_level(C1) < C1_max:
        log(f"exiting phase 4")
        return
    await set_pump(P1, 1)
    while get_level(C1) < C1_max:
        await aio.sleep(delay)
    await set_pump(P1, 0)
    log(f"exiting phase 4")


async def measure(delay):
    log(f"measure={delay}", color=92)
    while cycle.active:
        cycle.update_state()
        cycle.shift_state()
        await aio.sleep(delay)


# rdzen algorytmu sterowania:
# czyli definicja przejsc z fazy do fazy
async def control():
    await phase_1()
    tasks = [
        phase_2(),
        phase_3(P2, Y1, C2, C2_min, C2_rd, C2_rg, T_ust2),
        phase_3(P3, Y2, C3, C3_min, C3_rd, C3_rg, T_ust3),
        phase_3(P4, Y3, C4, C4_min, C4_rd, C4_rg, T_ust4),
    ]
    await aio.gather(*tasks)
    await phase_4()
    cycle.active = False


# wypisywanie na ekran
async def print_vals():
    log("print_vals", color=92)
    while cycle.active:
        print(f"state: {cycle.purifier.state()}")
        print(f"time: {get_elapsed()}")
        await aio.sleep(1)


# podczas cyklu nalezy:
#   1) mierzyc stany - measure(delay=measure_delay)
#   2) kontrolowac uklad - control()
#   3) wypisywac/zapisywac wartosci - print_vals()
async def cycle_loop():
    global cycle
    while True:
        log("--- started cycle ---", color=94)
        cycle = Cycle(purifier)
        tasks = [measure(delay=measure_delay), control(), print_vals()]
        await aio.gather(*tasks)
        log("--- exiting cycle ---", color=94)
        cycle.save_history(report_dir)


# rozpoczynamy sterowanie:
#   1) polaczenie z I/O - purifier.run(delay=delay)
#   2) cykle sterowania - cycle_loop()
async def start():
    global purifier
    setup()
    purifier = environment()
    # XXX:   symulacja       sterowanie
    tasks = [purifier.run(delay=delay), cycle_loop()]
    await aio.gather(*tasks)


if __name__ == "__main__":
    aio.run(start())
