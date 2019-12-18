import asyncio as aio

# pump identifiers
PUMPS = P1, P2, P3, P4 = ['P1', 'P2', 'P3', 'P4']
# valve identifiers
VALVES = Y1, Y2, Y3 = ['Y1', 'Y2', 'Y3']
# meter identifiers
METERS = C1, C2, C3, C4, C5 = ['C1', 'C2', 'C3', 'C4', 'C5']
# state keys
KEYS = METERS + VALVES + PUMPS

MAX = {C1: 100, C2: 10, C3: 10, C4: 10, C5: 100}
MIN = {C1: 0, C2: 0, C3: 0, C4: 0, C5: 0}

# speeds in level units transported per second (assume equal diameters)
SPEED = {k: 0.5 for k in PUMPS + VALVES}

SOURCE = {P1: C5, P2: C1, P3: C1, P4: C1, Y1: C2, Y2: C3, Y3: C4}
TARGET = {P1: C1, P2: C2, P3: C3, P4: C4, Y1: C5, Y2: C5, Y3: C5}

delay = 0.01

class Purifier:
    def __init__(self):
        self.state = {
                P1: 0, P2: 0, P3: 0, P4: 0,
                Y1: 0, Y2: 0, Y3: 0,
                C1: MAX[C1],
                C2: MIN[C2], C3: MIN[C3], C4: MIN[C4], C5: MIN[C5]+1
                }
        active = False

    def read_state(self, id):
        assert(id in KEYS)
        return self.state[id]

    def transfer(self, source, target, amount):
        amount = min(amount, self.state[source])
        #amount = min(amount, MAX[target] + 0.1 - self.state[target])
        self.state[source] -= amount
        self.state[target] += amount

    def set_pump(self, id, val: bool):
        self.state[id] = val

    def set_valve(self, id, val: bool):
        self.state[id] = val

    async def run(self):
        self.active = True

        while self.active:
            for p in PUMPS + VALVES:
                if self.state[p]:
                    self.transfer(SOURCE[p], TARGET[p], SPEED[p]*delay)

            await aio.sleep(delay)
