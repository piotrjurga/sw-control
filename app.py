import asyncio as aio
import aiohttp
import hardware as hw

from datetime import datetime
from aiohttp import web
from aiohttp.web import Response
from station import *


# aiohttp session
STATION_ID = 1
DB_HOST = 'http://10.42.0.1:8000'
DB_URL = f'{DB_HOST}/water/{STATION_ID}/stats/'
DB_TIMEOUT = 0.5
DB_SESSION_TIMEOUT = aiohttp.ClientTimeout(connect=DB_TIMEOUT)
DB_SESSION = aiohttp.ClientSession(timeout=DB_SESSION_TIMEOUT)


def clip(x, mini, maxi):
    return max(min(x, maxi), mini)

def to_int(s):
    try: return int(s)
    except: return None

def jsonify(**kwargs):
    return web.json_response(kwargs)

def ok(status=200):
    return Response(status=status)

def error(status, text):
    return Response(status=status, text=f'{status} {text}\n')

async def post_update(station):
    s = station.state
    ts = s['time']
    ts = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%dT%H:%M:%S.%f')
    cs = [dict(container_id=str(i+1), container_state=s[x]) for i, x in enumerate(METERS)]
    ys = [dict(valve_id=str(i+1), valve_state=bool(s[x])) for i, x in enumerate(VALVES)]
    ps = [dict(pump_id=str(i+1), pump_state=bool(s[x])) for i, x in enumerate(PUMPS)]
    ss = 'RM' if station.mode == MANUAL else 'AU'
    data = dict(steering_state=ss, timestamp=ts, valves=ys, containers=cs, pumps=ps)
    try:
        #log('post update')
        await DB_SESSION.post(DB_URL, json=data)
    except aiohttp.ServerTimeoutError:
        #log('post update timeout!')
        raise

async def get_info(req):
    log('GET /info', color=93)
    return jsonify(containers=METERS, pumps=PUMPS, valves=VALVES)

async def get_history(req):
    log('GET /history', color=93)
    params = req.rel_url.query
    last = to_int(params.get('last', None))
    if last == None: last = 10
    df = station.history
    df = df.tail(clip(last, 1, len(df)))
    return jsonify(**df.to_dict(orient='list'))

async def get_state(req):
    log('GET /state', color=93)
    return jsonify(**station.state)

async def put_state(req):
    log('PUT /state', color=93)
    json = await req.json()
    if 'mode' in json:
        mode = json['mode']
        if mode not in MODES: return error(400, 'bad mode')
        station.set_mode(mode)

    for id in VALVES:
        if id not in json: continue
        state = json[id]
        if state not in [0, 1]: return error(400, 'bad state')
        if station.mode != MANUAL: return error(403, 'not in manual')
        station.set_valve(id, state)

    for id in PUMPS:
        if id not in json: continue
        state = json[id]
        if state not in [0, 1]: return error(400, 'bad state')
        if station.mode != MANUAL: return error(403, 'not in manual')
        station.set_pump(id, state)

    return Response(status=200)


async def get_config(req):
    log('GET /config', color=93)
    data = dict()
    for id, C in CONTAINERS.items():
        data[id] = C.to_dict()
        del data[id]['id']
    return jsonify(**data)


async def put_config(req):
    log('PUT /config', color=93)
    json = await req.json()
    for id in CONTAINERS:
        if id not in json: continue
        for key in CONTAINERS[id].keys():
            if key not in json[id]: continue
            CONTAINERS[id][key] = json[id][key]
    return Response(status=200)

async def main():
    global station
    try:
        log('startup gpio')
        hw.startup_gpio()
        station = Station()
        station.post_update = post_update
        station.reset()
        await aio.gather(
            station.cycle_loop(),
            station.update_loop(),
            station.print_loop(),
            station.phase_guard(),
        )
    except aio.CancelledError:
        log('cancelled server job')
    finally:
        station.reset()
        log('cleanup gpio')
        hw.cleanup_gpio()

async def on_startup(app):
    log('aiohttp: on_startup')
    app['main'] = aio.Task(main())

async def on_cleanup(app):
    log('aiohttp: on_cleanup')
    app['main'].cancel()
    await DB_SESSION.close()

def make_app(args):
    app = web.Application()
    app.router.add_get('/info', get_info)
    app.router.add_get('/history', get_history)
    app.router.add_get('/state', get_state)
    app.router.add_put('/state', put_state)
    app.router.add_get('/config', get_config)
    app.router.add_put('/config', put_config)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app

if __name__ == "__main__":
    web.run_app(make_app([]))

