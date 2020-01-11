import asyncio as aio
from config import *
from blackbox import BlackBox

# state keys
KEYS = METERS + VALVES + PUMPS

MAX = {C1: 100, C2: 10, C3: 10, C4: 10, C5: 100}
MIN = {C1: 0, C2: 0, C3: 0, C4: 0, C5: 0}

# speeds in level units transported per second (assume equal diameters)
SPEED = {k: 0.5 for k in PUMPS + VALVES}

SOURCE = {P1: C5, P2: C1, P3: C1, P4: C1, Y1: C2, Y2: C3, Y3: C4}
TARGET = {P1: C1, P2: C2, P3: C3, P4: C4, Y1: C5, Y2: C5, Y3: C5}

delay = 0.01


class Simulation(BlackBox):
    def transfer(self, source, target, amount):
        amount = min(amount, self.state[source])
        # amount = min(amount, MAX[target] + 0.1 - self.state[target])
        self.state[source] -= amount
        self.state[target] += amount

    def fake_flow(self):
        for p in PUMPS + VALVES:
            if self.state[p]:
                self.transfer(SOURCE[p], TARGET[p], SPEED[p] * delay)

    async def run(self):
        self.active = True

        while self.active:
            self.state.update()
            self.fake_flow()  # XXX
            await aio.sleep(delay)
