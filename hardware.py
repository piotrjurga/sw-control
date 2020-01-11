# FIXME: server ktory dziala jak core/api_stub? i ma lagi czy cos???
#        jakis napewno dziwny behavior?

print("--- HARDWARE ---")

from sanic.response import json

app = Sanic()

MAX = {C1: 100, C2: 10, C3: 10, C4: 10, C5: 100}
MIN = {C1: 0, C2: 0, C3: 0, C4: 0, C5: 0}

STORAGE = {
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


@app.route("/push")
async def push(request):
    global STORAGE
    key = request.args["key"]
    val = request.args["val"]
    if key in STORAGE:
        STORAGE[key] = val
    return json({"hello": "world"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
