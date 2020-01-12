import time
import asyncio as aio
import multiprocessing

print("--- HARDWARE ---")

from sanic import Sanic
from sanic.response import json

# FIXME: uzywamy tej samej symulacji do testu
from config import *
from model.simulation import SimulationModel


class SimulationModelSync(SimulationModel):
    def run_sync(self, delay=0.1):
        self.active = True

        while self.active:
            # XXX: print(self.state())
            self.state.update()
            self.fake_flow(delay)  # XXX
            time.sleep(delay)


environment = SimulationModelSync
purifier = environment()

service = Sanic(name="hardware")


@service.route("/send")
async def send(request):
    key = request.json["key"]
    val = request.json["val"]
    service.purifier.state[key] = val
    print(f"\033[92m (send) key={key} val={val} \
| state={service.purifier.state[key]}\033[m")
    return json({"result": "accepted"})


@service.route("/recv")
async def recv(request):
    key = request.json["key"]
    val = service.purifier.state[key]
    print(f"\033[92m (recv) key={key} val={val} \033[m")
    return json({"result": val})


if __name__ == "__main__":

    def run(obj):
        obj.run_sync()

    worker = multiprocessing.Process(target=run, args=[purifier])
    worker.start()

    service.purifier = purifier
    service.run(debug=True, host=HARDWARE_HOST, port=HARDWARE_PORT)
    worker.join()
