from config import *

# TODO(maciej): a to powinno byc w konfiguracji? czy wyslane nam przez API?
MAX = {C1: 100, C2: 10, C3: 10, C4: 10, C5: 100}
MIN = {C1: 0, C2: 0, C3: 0, C4: 0, C5: 0}


class API:
    storage = {
        P1: 0,
        P2: 0,
        P3: 0,
        P4: 0,
        Y1: 0,
        Y2: 0,
        Y3: 0,
        C1: MAX[C1],
        C2: MIN[C2],
        C3: MIN[C3],
        C4: MIN[C4],
        C5: MIN[C5] + 1,
    }

    def send(self, key, val):
        # FIXME: send via request
        # print(f"API: send {key} {val}")
        # FIXME: fake sleep
        self.storage[key] = val

    def recv(self, key):
        # print(f"API: recv {key}")
        # FIXME: get from buffer (endpoint collector) / different script?
        # process
        return self.storage[key]
