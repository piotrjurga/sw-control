"""
Tutaj znajduje sie plik z algorytmem sterowania 
zgodny z wyslana specyfikacja.
"""

import asyncio as aio
import pandas as pd
import aiohttp

from sys import stderr
from os import path
from datetime import datetime
from time import time, sleep
from aiohttp import web
from aiohttp.web import Response

from config import *
#from embedded import *
def switchState(x,y): pass
def readData(x): return 0

# state keys
KEYS = ["timestamp"] + METERS + VALVES + PUMPS

# timings
measure_delay = 0.01
delay = 0.01
auto = True

# conditions for detecting an airlock
min_frames_without_change = 5
min_meter_delta = 0.5 * measure_delay

# current cycle
cycle = None

# aiohttp sessions
db_session_timeout = aiohttp.ClientTimeout(connect=DB_TIMEOUT)
db_session = None

def clip(x, mini, maxi):
    return max(min(x, maxi), mini)

def to_int(s):
    try:
        return int(s)
    except:
        return None

def jsonify(**kwargs):
    return web.json_response(kwargs)

class Cycle:
    """
    Akcje wykonywane po uplywie pelnego cyklu.
    (zapisanie do pliku, elapsed_time, potwierdzone stany)
    """

    def __init__(self):
        self.history = pd.DataFrame(columns=KEYS)
        self.start_time = time()
        self.state = {k: None for k in KEYS}
        self.active = True
        self.airlocked = False
        self.update_state()
        self.shift_state()

    def save_history(self, report_dir):
        report_name = f"{int(self.start_time)}.csv"
        report_path = path.join(report_dir, report_name)
        if not path.exists(report_dir):
            os.makedirs(report_dir)
        log(f"saving history at {report_path}")
        self.history.to_csv(report_path)

    def elapsed_time(self):
        return time() - self.start_time

    def shift_state(self):
        self.history = self.history.append([self.state], ignore_index=True)

    def update_state(self):
        self.state["timestamp"] = time()
        for i, id in enumerate(METERS):
            self.state[id] = max(0, C_cap[i] - readData(id))
            sleep(0.1)

        for id in VALVES + PUMPS:
            if self.state[id] is None:
                self.state[id] = 0
        print(', '.join(f'{x} {float(self.state[x]):.2f}' for x in METERS + VALVES))


# funkcja do wypisywania na ekran
def log(s, color=None):
    # todo: something more sophisticated
    if color is None:
        print(s, file=stderr)
    else:
        print(f"\033[{color}m{s}\033[m", file=stderr)


# mock: dla czasu
def get_elapsed() -> float:
    return cycle.elapsed_time()


# mock: dla czujnika poziomu wody
def get_level(id) -> float:
    assert id in METERS
    return cycle.state[id]


# rozkaz dla pompy
async def set_pump(id, state: bool):
    # todo: implement me
    assert id in PUMPS
    if state:
        while cycle.airlocked:
            await aio.sleep(delay)
    log(f"set pump {id} from {cycle.state[id]} to {state}")
    cycle.state[id] = state
    switchState(id, state)


# rozkad dla zawaru
def set_valve(id, state: bool):
    # todo: implement me
    assert id in VALVES
    log(f"set valve {id} from {cycle.state[id]} to {state}")
    cycle.state[id] = state
    switchState(id, state)


# sprawdzenie czy mamy zapowietzenie
async def check_for_airlock(pump, meter):
    assert pump in PUMPS
    assert meter in METERS
    recent_meter = cycle.history[meter][-min_frames_without_change:]
    recent_pump = cycle.history[pump][-min_frames_without_change:]
    if all(p == 1 for p in recent_pump):
        delta = max(recent_meter) - min(recent_meter)
        if delta < min_meter_delta:
            log(f"pump {pump} airlocked, locking other pumps")
            cycle.airlocked = True
            previous_state = {p: cycle.state[p] for p in PUMPS}
            for p in PUMPS:
                if p != pump:
                    await set_pump(p, 0)
            while max(recent_meter) - min(recent_meter) < delta:
                await aio.sleep(delay)
                recent_meter = cycle.history[meter][-min_frames_without_change:]
            for p in PUMPS:
                await set_pump(p, previous_state[p])
            cycle.airlocked = False
            log(f"airlock of {pump} resolved, unlocking other pumps")


async def phase_1():
    log("entered phase 1", color=92)
    if get_level(C1) >= C1_max:
        return

    await set_pump(P2, 0)
    await set_pump(P3, 0)
    await set_pump(P4, 0)

    await set_pump(P1, 1)
    while not (get_level(C1) >= C1_max):
        await aio.sleep(delay)
    await set_pump(P1, 0)
    log("exiting phase 1")


# FAZA 2
async def phase_2():
    log("entered phase 2", color=92)
    # TODO(piotr): should we check for airlocks here? the meter level
    # may be constant naturally as the pumps are potentially on
    while True:
        while get_elapsed() < T_ust1 and not (
            get_level(C1) < C1_max and get_level(C5) > C5_min
        ):
            await aio.sleep(delay)
        if get_elapsed() >= T_ust1:
            break
        await set_pump(P1, 1)
        while get_elapsed() < T_ust1 and not (
            get_level(C1) >= C1_max and get_level(C5) <= C5_min
        ):
            await aio.sleep(delay)
        if get_elapsed() >= T_ust1:
            break
        await set_pump(P1, 0)
    await set_pump(P1, 0)
    log("exiting phase 2")


async def phase_3(P_i, Y_i, C_i, c_min, c_rd, c_rg, t_ust):
    log(f"entered phase 3 (pump {P_i})", color=92)
    await set_pump(P_i, 1)
    while not get_level(C_i) > c_rd:
        await check_for_airlock(P_i, C_i)
        await aio.sleep(delay)
    set_valve(Y_i, 1)

    # TODO(piotr): should we check for airlocks here? the meter level
    # may be constant naturally as the valve is open
    while get_elapsed() < t_ust:
        while get_elapsed() < t_ust and not get_level(C_i) > c_rg:
            await aio.sleep(delay)
        if get_elapsed() >= t_ust:
            break
        await set_pump(P_i, 0)
        while get_elapsed() < t_ust and not get_level(C_i) < c_rd:
            await aio.sleep(delay)
        if get_elapsed() >= t_ust:
            break
        await set_pump(P_i, 1)

    await set_pump(P_i, 0)
    while not get_level(C_i) < c_min:
        await aio.sleep(delay)
    set_valve(Y_i, 0)
    log(f"exiting phase 3 (pump {P_i})")


async def phase_4():
    log(f"entered phase 4", color=92)
    if not get_level(C1) < C1_max:
        log(f"exiting phase 4")
        return
    await set_pump(P1, 1)
    while get_level(C1) < C1_max:
        await aio.sleep(delay)
    await set_pump(P1, 0)
    log(f"exiting phase 4")


async def measure(delay):
    log(f"measure={delay}", color=92)
    while cycle.active:
        cycle.update_state()
        cycle.shift_state()
        await post_vals()
        await aio.sleep(delay)


# rdzen algorytmu sterowania:
# czyli definicja przejsc z fazy do fazy
async def control():
    await phase_1()
    tasks = [
        phase_2(),
        phase_3(P2, Y1, C2, C2_min, C2_rd, C2_rg, T_ust2),
        phase_3(P3, Y2, C3, C3_min, C3_rd, C3_rg, T_ust3),
        phase_3(P4, Y3, C4, C4_min, C4_rd, C4_rg, T_ust4),
    ]
    await aio.gather(*tasks)
    await phase_4()
    cycle.active = False


# wypisywanie na ekran
async def print_vals():
    log("print_vals", color=92)
    while cycle.active:
        await aio.sleep(1)


async def post_vals():
    s = cycle.state
    ts = cycle.state['timestamp']
    ts = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%dT%H:%M:%S.%f')
    cs = [dict(container_id=str(i+1), container_state=cycle.state[x])
            for i, x in enumerate(METERS)]
    ys = [dict(valve_id=str(i+1), valve_state=bool(cycle.state[x]))
            for i, x in enumerate(VALVES)]
    ps = [dict(pump_id=str(i+1), pump_state=bool(cycle.state[x]))
            for i, x in enumerate(PUMPS)]
    ss = 'AU' if auto else 'MA'
    data = {
        'steering_state': ss, 'timestamp': ts,
        'valves': ys, 'containers': cs, 'pumps': ps,
    }
    try:
        await db_session.post(DB_URL, json=data)
    except:
        pass


# podczas cyklu nalezy:
#   1) mierzyc stany - measure(delay=measure_delay)
#   2) kontrolowac uklad - control()
#   3) wypisywac/zapisywac wartosci - print_vals()
async def cycle_loop():
    global cycle
    while True:
        log("--- started cycle ---", color=94)
        cycle = Cycle()
        tasks = [measure(delay=measure_delay), print_vals()]
        if auto:
            tasks.append(control())
        await aio.gather(*tasks)
        log("--- exiting cycle ---", color=94)
        cycle.save_history(report_dir)


async def on_startup(app):
    global db_session
    app['cycle'] = app.loop.create_task(cycle_loop())
    db_session = aiohttp.ClientSession(timeout=db_session_timeout)


async def on_cleanup(app):
    await db_session.close()


async def get_status(req):
    if cycle is None: return jsonify(state={})
    return jsonify(state=cycle.state)


async def get_config(req):
    return jsonify(C_min=C_min, C_max=C_max, C_cap=C_cap, T_ust=T_ust)


async def get_history(req):
    params = req.rel_url.query
    df = cycle.history
    tail = to_int(params.get('last', None))
    if tail is not None:
        df = df.tail(clip(tail, 0, len(df)))
    return jsonify(state=df.to_dict(orient='list'))


async def put_manual(req):
    global auto
    body = await req.json()
    state = body['steering_state']
    if state == 'RM': auto = False
    if state == 'ID': auto = True
    return Response(status=200)


async def put_state(req):
    if auto:
        return Response(status=403)

    body = await req.json()
    state = body['state']
    type = req.match_info['type']
    id = req.match_info['id']

    if type == 'pump':
        id = 'P'+id
        if id not in PUMPS:
            return Response(status=400)
        set_pump(id, state)

    if type == 'valve':
        id = 'Y'+id
        if id not in VALVES:
            return Response(status=400)
        set_valve(id, state)

    return Response(status=200)


def make_app(args):
    app = web.Application()
    app.router.add_get(r'/status', get_status)
    app.router.add_get(r'/config', get_config)
    app.router.add_get(r'/history', get_history)
    app.router.add_put(r'/manual', put_manual)
    app.router.add_put(r'/manual/{type:(pump|valve)}/{id}', put_state)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app


if __name__ == "__main__":
    web.run_app(make_app([]))
