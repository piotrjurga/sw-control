import time
import asyncio as aio
import multiprocessing

print("--- HARDWARE ---")

from sanic import Sanic
from sanic.response import json

# FIXME: uzywamy tej samej symulacji do testu
from config import *
from model.simulation import SimulationModel

# FIXME: switchState/readData sa na raspberry pi


class SimulationModelSync(SimulationModel):
    def run_sync(self, delay=0.1):
        self.active = True

        while self.active:
            # XXX: print(self.state())
            self.state.update()
            # FIXME: przetestowac czy mam byc `fake_flow`?
            # self.fake_flow(delay)  # XXX
            time.sleep(delay)


environment = SimulationModelSync
purifier = environment()

service = Sanic(name="hardware")

# <--- : prosba o zmiane stanu typu=config.Control
@service.route("/send")
async def send(request):
    key = request.json["key"]
    val = request.json["val"]
    switchState(key, val)
    service.purifier.state[key] = val  # FIXME: only on success
    print(
        f"\033[92m (send) key={key} val={val} \
| state={service.purifier.state[key]}\033[m"
    )
    return json({"result": "accepted"})


# ---> : prosba o wartosci danych
@service.route("/recv")
async def recv(request):
    key = request.json["key"]
    val = readData(key)
    if key in PUMPS or key in VALVES:
        val = service.purifier.state[key]  # FIXME: only on success
    print(f"\033[92m (recv) key={key} val={val} \033[m")
    return json({"result": val})


if __name__ == "__main__":

    # zczytywanie ze sprzetu moze byc asynchroniczne (1)
    def run(obj):
        obj.run_sync()

    # rozdzielamy tutaj wykowanie programu na dwa procesy:
    #  1) tylko zczytuje dane i przechowuje je w pamieci podrecznej
    #  2) tylko jest odpowiedzialny za przekazywanie ich na API
    worker = multiprocessing.Process(target=run, args=[purifier])
    worker.start()

    # tutaj mamy (2)
    service.purifier = purifier
    service.run(debug=True, host=HARDWARE_HOST, port=HARDWARE_PORT)
    worker.join()
