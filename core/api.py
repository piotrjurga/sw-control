import requests
from config import *
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

# FIXME:
# (1) [done] my wysylamy ze checemy zmienic
# (2) [    ] hardware wysyla ze cos ma nowego
# (3) [done] my pytamy hardware o stan


class API:
    # FIXME: kazde pole powinno miec czas
    #        kiedy ostatnio byl pomiar
    #        aby moc redukowac 'latency'
    #        albo odkryc ze czujnik sie popsul/nie reaguje

    buffer = defaultdict(int)
    thread = {}
    executor = None

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)

    def lazy_request(self, uri, data):
        response = requests.get(uri, json=data)
        return response.json()["result"]

    def send(self, key, val):
        global HARDWARE_URI

        if val is None:
            return
        if key in Measure.state:
            raise Exception("przeciez to czujnik!")

        url = f"{HARDWARE_URI}/send"
        data = {"key": key, "val": val}

        self.thread["send" + key] = self.executor.submit(
            self.lazy_request, url, data)

    def recv(self, key):
        global HARDWARE_URI

        url = f"{HARDWARE_URI}/recv"
        data = {"key": key}

        if "recv" + key not in self.thread:
            self.thread["recv" + key] = self.executor.submit(
                self.lazy_request, url, data)
            return self.buffer[key]
        if self.thread["recv" + key].running():
            return self.buffer[key]

        self.buffer[key] = self.thread["recv" + key].result()
        return self.buffer[key]
