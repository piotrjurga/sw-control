import asyncio as aio
import pandas as pd

from sys import stderr
from time import time, sleep
from datetime import datetime
from box import Box
from hardware import read_level, write_state, METERS, VALVES, PUMPS

# settings
C1 = Box(id=METERS[0], min=2, max=20, cap=30, rd=5, rg=10, t_ust=60)
C2 = Box(id=METERS[1], min=2, max=10, cap=20, rd=5, rg=8,  t_ust=60)
C3 = Box(id=METERS[2], min=2, max=10, cap=20, rd=5, rg=8,  t_ust=60)
C4 = Box(id=METERS[3], min=2, max=10, cap=20, rd=5, rg=8,  t_ust=60)
C5 = Box(id=METERS[4], min=2, max=20, cap=30)
CONTAINERS = {x.id: x for x in [C1, C2, C3, C4, C5]}

# timings
DELAY = 0.0001

# state keys
P1, P2, P3, P4 = PUMPS
Y1, Y2, Y3 = VALVES
MODES = IDLE, MANUAL, AUTO = 'idle', 'manual', 'auto'


def log(s, color=0):
    print(f"\033[{color}m[info] {s}\033[m", file=stderr)


async def mock_post_update(station):
    return


class Station:
    def __init__(self):
        self.keys = ['time'] + METERS + VALVES + PUMPS
        self.history = pd.DataFrame(columns=self.keys)
        self.start_time = time()
        self.mode = AUTO
        self.cycle_task = None
        self.init_state()
        self.post_update = mock_post_update

    def init_state(self):
        self.state = {k: 0 for k in self.keys}
        self.state['time'] = time()
        self.state['mode'] = self.mode

    def shift_state(self):
        self.history = self.history.append([self.state], ignore_index=True)

    def update_state(self):
        self.state['time'] = time()
        self.state['mode'] = self.mode
        for x in CONTAINERS.values():
            self.state[x.id] = max(0, x.cap - read_level(id))
            sleep(0.1)

    def get_level(self, container: Box) -> float:
        return container.cap - self.state[container.id]

    def set_valve(self, id: str, state: bool):
        assert id in VALVES
        if self.state[id] == state: return
        write_state(id, state)
        log(f"set valve {id} from {self.state[id]} to {state}")
        self.state[id] = state

    def set_pump(self, id: str, state: bool):
        assert id in PUMPS
        if self.state[id] == state: return
        write_state(id, state)
        log(f"set pump {id} from {self.state[id]} to {state}")
        self.state[id] = state

    def set_mode(self, mode):
        if self.mode == mode: return
        log(f'set mode from {self.mode} to {mode}')
        self.mode = mode
        if mode == MANUAL:
            if self.cycle_task is not None:
                self.cycle_task.cancel()
        self.reset()

    def reset(self):
        log('reset station')
        for id in PUMPS:
            self.set_pump(id, 0)
        for id in VALVES:
            self.set_valve(id, 0)

    async def phase_1(self):
        get_level, set_valve, set_pump = self.get_level, self.set_valve, self.set_pump
        log("entered phase 1")
        while get_level(C1) < C1.rg:
            set_pump(P1, 1)
            await aio.sleep(DELAY)
        set_pump(P1, 0)
        log("exiting phase 1")

    async def phase_2(self, start_time):
        get_level, set_valve, set_pump = self.get_level, self.set_valve, self.set_pump
        log("entered phase 2", color=94)
        while time() - start_time < C1.t_ust:
            if get_level(C1) < C1.rd:
                set_pump(P1, 1)
            if get_level(C1) > C1.rg:
                set_pump(P1, 0)
            await aio.sleep(DELAY)
        set_pump(P1, 0)
        log("exiting phase 2", color=94)

    async def phase_3(self, start_time, P, Y, C, delta=1):
        get_level, set_valve, set_pump = self.get_level, self.set_valve, self.set_pump
        log(f"entered phase 3 (pump {P})", color=94)
        set_pump(P, 1)
        while get_level(C) < C.rd:
            await aio.sleep(DELAY)

        while time() - start_time < C.t_ust:
            if get_level(C) < C5.max:
                set_valve(Y, 1)
            if get_level(C) > C5.max + delta:
                set_valve(Y, 0)
            if get_level(C) < C.min:
                set_valve(Y, 0)

            if get_level(C) < C.rd:
                set_pump(P, 1)
            if get_level(C) > C.rg:
                set_pump(P, 0)
            await aio.sleep(DELAY)

        set_pump(P, 0)
        set_valve(Y, 1)
        while get_level(C) > C.min:
            if get_level(C5) < C5.max:
                set_valve(Y, 1)
            if get_level(C5) > C5.max + delta:
                set_valve(Y, 0)
            await aio.sleep(DELAY)
        set_valve(Y, 0)
        log(f"exiting phase 3 (pump {P})", color=94)

    async def phase_4(self):
        get_level, set_valve, set_pump = self.get_level, self.set_valve, self.set_pump
        log(f"entered phase 4", color=94)
        while get_level(C1) < C1.max:
            set_pump(P1, 1)
            await aio.sleep(DELAY)
        set_pump(P1, 0)
        log(f"exiting phase 4", color=94)

    async def phase_guard(self, delta=1, agresja=True):
        return
        get_level, set_valve, set_pump = self.get_level, self.set_valve, self.set_pump
        # important: rambo
        # TODO(piotr): change state to idle
        while True:
            t1, t2, t3, t4, t5 = [get_level(x) for x in CONTAINERS.values()]
            
            if t1 < C1.min - delta:
                set_pump(P2, 0)
                set_pump(P3, 0)
                set_pump(P4, 0)
            
            if t5 < C5.min - delta:
                set_pump(P1, 0)
                log('guard P1 off (C5 underflow)')
            if t2 < C2.min - delta: set_valve(Y1, 0)
            if t3 < C3.min - delta: set_valve(Y2, 0)
            if t4 < C4.min - delta: set_valve(Y3, 0)
            

            if t5 > C5.max + delta:
                set_valve(Y1, 0)
                set_valve(Y2, 0)
                set_valve(Y3, 0)

            if t1 > C1.max + delta:
                set_pump(P1, 0)
                log('guard P1 off (C1 overflow)')
            if t2 > C2.max + delta: set_pump(P2, 0)
            if t3 > C3.max + delta: set_pump(P3, 0)
            if t4 > C4.max + delta: set_pump(P4, 0)

            await aio.sleep(DELAY)

    async def run_cycle(self):
        self.reset()
        log('started cycle')
        await self.phase_1()
        t = time()
        await aio.gather(
            self.phase_2(t),
            self.phase_3(t, P2, Y1, C2),
            self.phase_3(t, P3, Y2, C3),
            self.phase_3(t, P4, Y3, C4),
        )
        await self.phase_4()
        log('ended cycle')

    async def cycle_loop(self):
        while True:
            try:
                while self.mode in [IDLE, MANUAL]:
                    await aio.sleep()
                self.cycle_task = aio.Task(self.run_cycle())
                await self.cycle_task
            except aio.CancelledError:
                log('cycle cancelled')
                self.reset()
                return

    async def update_loop(self):
        while True:
            self.update_state()
            self.shift_state()
            try:
                await self.post_update(self)
            except:
                pass
            await aio.sleep(0)

    async def print_loop(self):
        while True:
            print(', '.join(f'{x} {float(self.state[x]):.2f}' for x in METERS))
            await aio.sleep(1)

