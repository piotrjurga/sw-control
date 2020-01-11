import asyncio as aio
from api import API
from config import *

# FIXME: pass in blackbox
__api__ = API()

delay = 0.01


class ProxyDict:
    storage = []

    def add(self, obj):
        self.storage.append(obj)

    def __getitem__(self, key):
        for obj in self.storage:
            if key in obj.state:
                return obj.state[key]
        return None

    def __setitem__(self, key, val):
        for obj in self.storage:
            if key in obj.state:
                # XXX: obj.state[key] = val
                # bo chcemy aby `.update()` to potwierdzil
                __api__.send(key, val)

    def __call__(self):
        result = {}
        for obj in self.storage:
            result.update(obj.state)
        return result

    def update(self):
        for obj in self.storage:
            for key in obj.state.keys():
                obj.state[key] = __api__.recv(key)


class Measure:
    def __init__(self):
        # FIXME: magic prefix
        self.state = {C1: None, C2: None, C3: None, C4: None, C5: None}


class Control:
    def __init__(self):
        # FIXME: magic prefix
        self.state = {
            P1: None,
            P2: None,
            P3: None,
            P4: None,
            Y1: None,
            Y2: None,
            Y3: None,
        }


class BlackBox:
    state = None
    active = False

    control = Control()
    measure = Measure()

    def __init__(self):
        self.state = ProxyDict()
        self.state.add(self.control)
        self.state.add(self.measure)

    async def run(self):
        self.active = True

        while self.active:
            print("ACTIVE --> run for control() + measure()")
            self.state.update()
            await aio.sleep(delay)
