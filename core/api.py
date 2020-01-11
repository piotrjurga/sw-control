import requests
from config import *

# FIXME:
# (1) my wysylamy ze checemy zmienic
# (2) hardware wysyla ze cos ma nowego
# (3) my pytamy hardware o stan

# FIXME: async? non blocking!!!!


class API:
    # FIXME: kazde pole powinno miec czas
    #        kiedy ostatnio byl pomiar
    #        aby moc redukowac 'latency'
    #        albo odkryc ze czujnik sie popsul/nie reaguje

    buffer = {}

    def send(self, key, val):
        global HARDWARE_URI
        # FIXME: send via request
        # print(f"API: send {key} {val}")
        # FIXME: IS MEASURE?
        if key in Measure.state:
            raise Exception("przeciez to czujnik!")
        if val is None:
            return

        response = requests.get(f"{HARDWARE_URI}/send",
                                json={
                                    "key": key,
                                    "val": val
                                })
        # print("---------->", response.json())

        # self.storage[key] = val

    def recv(self, key):
        # FIXME: zlecaj tutaj taska na zaciagniecie tej danej

        global HARDWARE_URI
        # print(f"API: recv {key}")
        # FIXME: get from buffer (endpoint collector) / different script?
        # process
        # return self.storage[key]

        response = requests.get(f"{HARDWARE_URI}/recv", json={"key": key})
        # print("---------->", response.json())
        return response.json()["result"]
