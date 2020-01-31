"""
Tutaj znajduje sie konfiguracja calego ukladu, czyli takie informacje jak
ile jest pomp, zawarow albo czujnikow.
Wszystkie stany beda przechowywane w odpowiednich klasach.

Measure - tylko stany ktore mozemy z czytac ale nie modyfikowac
          (np. poziom wody, temperatura)
Control - stany ktore mozemy modyfikowac programowo
          (np. otwieranie/zamykanie zaworu, wlaczenie/wylaczenie pompy)

Dodatkowo:

METRICS_* - zmienne do zapisywania danych historycznych
HARDWARE_* - gdzie znajduje sie I/O intefejs ktorym chcemy sterowac
"""

# FIXME: w nadziei ze bedzie mozna modelowac rozne struktury

# hardware information
# FIXME: scrap maybe env.yml with: delay, workers_num
HARDWARE_HOST = "0.0.0.0"
HARDWARE_PORT = 8044
HARDWARE_URI = f"http://{HARDWARE_HOST}:{str(HARDWARE_PORT)}"

# our metrics for debugging states
# FIXME: scrap here `prometheus.yml`
METRICS_HOST = "0.0.0.0"
METRICS_PORT = 8111

# pump identifiers
PUMPS = P1, P2, P3, P4 = ["P1", "P2", "P3", "P4"]
# valve identifiers
VALVES = Y1, Y2, Y3 = ["Y1", "Y2", "Y3"]
# meter identifiers
METERS = C1, C2, C3, C4, C5 = ["C1", "C2", "C3", "C4", "C5"]


class Device:
    def __init__(self, manager):
        self.state = manager.dict(self.state)


class Measure(Device):
    state = {C1: None, C2: None, C3: None, C4: None, C5: None}


class Control(Device):
    state = {
        P1: None,
        P2: None,
        P3: None,
        P4: None,
        Y1: None,
        Y2: None,
        Y3: None,
    }
