import asyncio as aio
from core.api import API
from config import *


class ProxyDict:
    api = API()
    storage = []
    fake = False

    def __init__(self, fake=False):
        self.fake = fake

    def add(self, obj):
        self.storage.append(obj)

    def __getitem__(self, key):
        for obj in self.storage:
            if key in obj.state:
                return obj.state[key]
        print(f"\033[91 NONE????????? {key} \033[m")
        return None

    def __setitem__(self, key, val):
        for obj in self.storage:
            if key in obj.state:
                # (fake) bo chcemy aby `.update()` to potwierdzil
                if self.fake:
                    obj.state[key] = val
                self.api.send(key, val)

    def __call__(self):
        result = {}
        for obj in self.storage:
            result.update(obj.state)
        return result

    def update(self):
        for obj in self.storage:
            for key in obj.state.keys():
                obj.state[key] = self.api.recv(key)


class BlackBoxModel:
    state = ProxyDict()
    active = False

    def __init__(self):
        self.state.add(Control())
        self.state.add(Measure())

    async def run(self, delay=0.01):
        self.active = True

        while self.active:
            self.state.update()
            await aio.sleep(delay)
