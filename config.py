# FIXME: w nadziei ze bedzie mozna modelowac rozne struktury

# hardware information
HARDWARE_HOST = "0.0.0.0"
HARDWARE_PORT = 8044
HARDWARE_URI = f"http://{HARDWARE_HOST}:{str(HARDWARE_PORT)}"

# pump identifiers
PUMPS = P1, P2, P3, P4 = ["P1", "P2", "P3", "P4"]
# valve identifiers
VALVES = Y1, Y2, Y3 = ["Y1", "Y2", "Y3"]
# meter identifiers
METERS = C1, C2, C3, C4, C5 = ["C1", "C2", "C3", "C4", "C5"]


class Measure:
    state = {C1: None, C2: None, C3: None, C4: None, C5: None}


class Control:
    state = {
        P1: None,
        P2: None,
        P3: None,
        P4: None,
        Y1: None,
        Y2: None,
        Y3: None,
    }
