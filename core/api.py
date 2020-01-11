from config import *

# FIXME:
# (1) my wysylamy ze checemy zmienic
# (2) hardware wysyla ze cos ma nowego
# (3) my pytamy hardware o stan


class API:
    def send(self, key, val):
        # FIXME: send via request
        print(f"API: send {key} {val}")
        # FIXME: IS MEASURE?
        if key in Measure.state:
            raise Exception("przeciez to czujnik!")
        if val is None:
            return
        # self.storage[key] = val

    def recv(self, key):
        print(f"API: recv {key}")
        # FIXME: get from buffer (endpoint collector) / different script?
        # process
        # return self.storage[key]
