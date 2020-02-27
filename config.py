"""
Tutaj znajduje sie konfiguracja calego ukladu, czyli takie informacje jak
ile jest pomp, zawarow albo czujnikow.
"""

# pump identifiers
PUMPS = P1, P2, P3, P4 = ["P1", "P2", "P3", "P4"]
# valve identifiers
VALVES = Y1, Y2, Y3 = ["Y1", "Y2", "Y3"]
# meter identifiers
METERS = C1, C2, C3, C4, C5 = ["C1", "C2", "C3", "C4", "C5"]
# settings
C_cap = [33, 20, 16, 21, 33]
# FIXME: HOT FIX (C3_czujnik)
C1_max, C2_max, C3_max, C4_max, C5_max = C_max = 14, 8, 9.0, 8, 20
C1_min, C2_min, C3_min, C4_min, C5_min = C_min = 8, 4, 8.9, 4, 5
T_ust1, T_ust2, T_ust3, T_ust4, T_ust5 = T_ust = 8, 8, 8, 8, 2
C2_rd, C3_rd, C4_rd = 1, 1, 1
C2_rg, C3_rg, C4_rg = 8, 8, 8
# where to write cycle reports
report_dir = "logs"

STATION_ID = 1
DB_HOST = 'http://127.0.0.1:8000'
DB_URL = f'{DB_HOST}/water/{STATION_ID}/stats/'
DB_TIMEOUT = 0.5
