import asyncio as aio
from config import *
from model.blackbox import ProxyDict, BlackBoxModel


class SimulationModel(BlackBoxModel):
    state = ProxyDict(fake=True)

    # speeds in level units transported per second (assume equal diameters)
    SPEED = {k: 0.5 for k in PUMPS + VALVES}

    SOURCE = {P1: C5, P2: C1, P3: C1, P4: C1, Y1: C2, Y2: C3, Y3: C4}
    TARGET = {P1: C1, P2: C2, P3: C3, P4: C4, Y1: C5, Y2: C5, Y3: C5}

    def transfer(self, source, target, amount):
        amount = min(amount, self.state[source])
        # amount = min(amount, MAX[target] + 0.1 - self.state[target])
        self.state[source] -= amount
        self.state[target] += amount

    def fake_flow(self, delay):
        for p in PUMPS + VALVES:
            if self.state[p]:
                self.transfer(self.SOURCE[p], self.TARGET[p],
                              self.SPEED[p] * delay)

    async def run(self, delay=0.01):
        self.active = True

        while self.active:
            self.state.update()
            self.fake_flow(delay)  # XXX
            await aio.sleep(delay)
